import csv
import json
from rest_framework import viewsets, status, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from .models import Organization, User, IngestionJob, RawRecord, NormalizedActivity, AuditTrail
from .serializers import (
    UserSerializer, IngestionJobSerializer, RawRecordSerializer,
    NormalizedActivitySerializer, AuditTrailSerializer
)
from .parsers import SAPParser, UtilityParser, TravelParser

# ---------------------------------------------------------
# Auth Views
# ---------------------------------------------------------
class CustomAuthToken(ObtainAuthToken):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

# ---------------------------------------------------------
# Ingestion Job ViewSet
# ---------------------------------------------------------
class IngestionJobViewSet(viewsets.ModelViewSet):
    serializer_class = IngestionJobSerializer

    def get_queryset(self):
        return IngestionJob.objects.filter(organization=self.request.user.organization).order_by('-created_at')

    def perform_create(self, serializer):
        # Prevent creation if user has no organization
        user = self.request.user
        if not user.organization:
            raise ValidationError("Authenticated user is not assigned to an organization.")
        
        # We handle file reading directly in the create action
        pass

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.organization:
            return Response({"error": "User organization not set."}, status=status.HTTP_400_BAD_REQUEST)

        source_type = request.data.get('source_type')
        uploaded_file = request.FILES.get('file')

        if not source_type or not uploaded_file:
            return Response({"error": "Missing source_type or file."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate source type
        valid_sources = [s[0] for s in IngestionJob.SOURCE_CHOICES]
        if source_type not in valid_sources:
            return Response({"error": f"Invalid source_type. Must be one of {valid_sources}"}, status=status.HTTP_400_BAD_REQUEST)

        # Read file contents
        try:
            # Try decoding as utf-8 (CSV) or read as text
            raw_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response({"error": "Failed to decode file as UTF-8 text."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the job
        with transaction.atomic():
            job = IngestionJob.objects.create(
                organization=user.organization,
                uploaded_by=user,
                source_type=source_type,
                filename=uploaded_file.name,
                raw_file_content=raw_content,
                status='PENDING'
            )

        # Run parser synchronously for the prototype/simple execution
        # In prod this could be delegated to Celery
        try:
            if source_type == 'SAP':
                parser = SAPParser(job)
            elif source_type == 'UTILITY':
                parser = UtilityParser(job)
            elif source_type == 'TRAVEL':
                parser = TravelParser(job)
            
            parser.run()
            
            # Refresh from DB
            job.refresh_from_db()
            return Response(IngestionJobSerializer(job).data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            job.refresh_from_db()
            return Response({
                "error": f"Parsing failed: {str(e)}",
                "job": IngestionJobSerializer(job).data
            }, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------------------------------------
# Normalized Activity ViewSet
# ---------------------------------------------------------
class NormalizedActivityViewSet(viewsets.ModelViewSet):
    serializer_class = NormalizedActivitySerializer

    def get_queryset(self):
        user = self.request.user
        qs = NormalizedActivity.objects.filter(organization=user.organization).prefetch_related('audit_trails').order_by('-activity_date')
        
        # Filtering parameters
        review_state = self.request.query_params.get('review_state')
        emissions_scope = self.request.query_params.get('emissions_scope')
        activity_category = self.request.query_params.get('activity_category')
        job_id = self.request.query_params.get('job_id')

        if review_state:
            qs = qs.filter(review_state=review_state)
        if emissions_scope:
            qs = qs.filter(emissions_scope=emissions_scope)
        if activity_category:
            qs = qs.filter(activity_category=activity_category)
        if job_id:
            qs = qs.filter(job_id=job_id)
            
        return qs

    def perform_update(self, serializer):
        # We handle audit trailing in update()
        pass

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if instance.review_state == 'LOCKED':
            return Response({"error": "Cannot edit a locked record."}, status=status.HTTP_400_BAD_REQUEST)

        edit_reason = request.data.get('edit_reason')
        if not edit_reason:
            return Response({"error": "An edit reason is required to update sustainability records."}, status=status.HTTP_400_BAD_REQUEST)

        # Track changes
        old_values = {
            'normalized_quantity': str(instance.normalized_quantity),
            'activity_date': str(instance.activity_date),
            'activity_category': instance.activity_category,
        }

        # Validate and save
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                updated_instance = serializer.save()
                
                # Check what changed
                changes = {}
                for field in old_values:
                    new_val = str(getattr(updated_instance, field))
                    if old_values[field] != new_val:
                        changes[field] = [old_values[field], new_val]

                # If no values changed, but reason was provided, still save audit
                AuditTrail.objects.create(
                    activity=updated_instance,
                    user=user,
                    action='EDIT',
                    notes=edit_reason,
                    changes=changes
                )
                
                # Re-verify and clear or update flags.
                # If they edited the quantity to be positive, we can auto-clear "Negative quantity" flag
                flags = updated_instance.flags
                new_flags = []
                for flag in flags:
                    if "Negative quantity" in flag and updated_instance.normalized_quantity >= 0:
                        continue
                    if "Zero quantity" in flag and updated_instance.normalized_quantity > 0:
                        continue
                    new_flags.append(flag)
                
                updated_instance.flags = new_flags
                if not new_flags and updated_instance.review_state == 'FLAGGED':
                    updated_instance.review_state = 'INGESTED'
                updated_instance.save()
                
                # Return updated
                return Response(self.get_serializer(updated_instance).data)

        except DjangoValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        activity = self.get_object()
        user = request.user

        if activity.review_state == 'LOCKED':
            return Response({"error": "Cannot approve a locked record."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            activity.review_state = 'APPROVED'
            activity.reviewer = user
            activity.reviewed_at = timezone.now()
            activity.save()

            AuditTrail.objects.create(
                activity=activity,
                user=user,
                action='APPROVE',
                notes="Approved by sustainability analyst."
            )

        return Response(NormalizedActivitySerializer(activity).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject/Flag action."""
        activity = self.get_object()
        user = request.user
        reason = request.data.get('reason', 'Flagged by analyst.')

        if activity.review_state == 'LOCKED':
            return Response({"error": "Cannot flag a locked record."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            activity.review_state = 'FLAGGED'
            if reason not in activity.flags:
                activity.flags.append(reason)
            activity.save()

            AuditTrail.objects.create(
                activity=activity,
                user=user,
                action='REJECT',
                notes=f"Flagged by analyst: {reason}"
            )

        return Response(NormalizedActivitySerializer(activity).data)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        activity = self.get_object()
        user = request.user

        if activity.review_state != 'APPROVED':
            return Response({"error": "Only approved records can be locked for audit."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            activity.review_state = 'LOCKED'
            activity.locked_at = timezone.now()
            activity.save()

            AuditTrail.objects.create(
                activity=activity,
                user=user,
                action='LOCK',
                notes="Locked and sealed for audit readiness. Record is now immutable."
            )

        return Response(NormalizedActivitySerializer(activity).data)

    @action(detail=False, methods=['post'])
    def bulk_lock(self, request):
        user = request.user
        approved_activities = NormalizedActivity.objects.filter(
            organization=user.organization,
            review_state='APPROVED'
        )
        
        count = approved_activities.count()
        if count == 0:
            return Response({"message": "No approved records found to lock."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for activity in approved_activities:
                activity.review_state = 'LOCKED'
                activity.locked_at = timezone.now()
                activity.save()

                AuditTrail.objects.create(
                    activity=activity,
                    user=user,
                    action='LOCK',
                    notes="Bulk locked and sealed for audit readiness."
                )

        return Response({"message": f"Successfully locked {count} records."}, status=status.HTTP_200_OK)

# ---------------------------------------------------------
# Audit Trail View
# ---------------------------------------------------------
class AuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditTrailSerializer

    def get_queryset(self):
        return AuditTrail.objects.filter(
            activity__organization=self.request.user.organization
        ).order_by('-timestamp')
