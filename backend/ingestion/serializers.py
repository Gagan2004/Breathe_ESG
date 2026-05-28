from rest_framework import serializers
from .models import Organization, User, IngestionJob, RawRecord, NormalizedActivity, AuditTrail

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'organization', 'organization_name', 'is_staff']

class IngestionJobSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    records_count = serializers.SerializerMethodField()
    failed_records_count = serializers.SerializerMethodField()

    class Meta:
        model = IngestionJob
        fields = [
            'id', 'organization', 'uploaded_by', 'uploaded_by_username',
            'source_type', 'filename', 'status', 'error_log',
            'created_at', 'completed_at', 'records_count', 'failed_records_count'
        ]
        read_only_fields = ['organization', 'uploaded_by', 'status', 'error_log', 'completed_at']

    def get_records_count(self, obj):
        return obj.raw_records.count()

    def get_failed_records_count(self, obj):
        return obj.raw_records.filter(status='ERROR').count()

class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ['id', 'job', 'row_index', 'raw_data', 'status', 'error_message']

class AuditTrailSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditTrail
        fields = ['id', 'activity', 'user', 'user_username', 'action', 'timestamp', 'notes', 'changes']

class NormalizedActivitySerializer(serializers.ModelSerializer):
    raw_record_data = serializers.DictField(source='raw_record.raw_data', read_only=True)
    raw_record_status = serializers.CharField(source='raw_record.status', read_only=True)
    job_filename = serializers.CharField(source='job.filename', read_only=True)
    audit_history = AuditTrailSerializer(source='audit_trails', many=True, read_only=True)
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)

    class Meta:
        model = NormalizedActivity
        fields = [
            'id', 'organization', 'raw_record', 'raw_record_data', 'raw_record_status',
            'job', 'job_filename', 'activity_date', 'activity_start_date', 'activity_end_date',
            'activity_category', 'emissions_scope', 'raw_quantity', 'raw_unit',
            'normalized_quantity', 'normalized_unit', 'review_state', 'flags',
            'reviewer', 'reviewer_username', 'reviewed_at', 'locked_at', 'audit_history'
        ]
        read_only_fields = [
            'organization', 'raw_record', 'job', 'flags', 'reviewer', 'reviewed_at', 'locked_at'
        ]

    def validate(self, attrs):
        # Prevent editing if the record is locked
        if self.instance and self.instance.review_state == 'LOCKED':
            raise serializers.ValidationError("This activity is locked for audit and cannot be modified.")
        return attrs
