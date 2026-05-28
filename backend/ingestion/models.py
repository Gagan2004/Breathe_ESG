import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='users')

    def __str__(self):
        return f"{self.username} ({self.organization.name if self.organization else 'No Org'})"

class IngestionJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    SOURCE_CHOICES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ingestion_jobs')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_jobs')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_log = models.TextField(null=True, blank=True)
    raw_file_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.source_type} upload: {self.filename} ({self.status})"

class RawRecord(models.Model):
    STATUS_CHOICES = [
        ('UNPROCESSED', 'Unprocessed'),
        ('NORMALIZED', 'Normalized'),
        ('FLAGGED', 'Flagged'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='raw_records')
    row_index = models.IntegerField()  # Row number from original file (1-indexed)
    raw_data = models.JSONField()  # Full row representation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPROCESSED')
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Raw Record {self.row_index} for Job {self.job.id}"

class NormalizedActivity(models.Model):
    STATE_CHOICES = [
        ('INGESTED', 'Ingested'),
        ('FLAGGED', 'Flagged'),
        ('APPROVED', 'Approved'),
        ('LOCKED', 'Locked'),
    ]
    SCOPE_CHOICES = [
        ('SCOPE_1', 'Scope 1'),
        ('SCOPE_2', 'Scope 2'),
        ('SCOPE_3', 'Scope 3'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='activities')
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name='normalized_activity')
    job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='normalized_activities')
    
    activity_date = models.DateField()
    activity_start_date = models.DateField(null=True, blank=True)
    activity_end_date = models.DateField(null=True, blank=True)
    
    activity_category = models.CharField(max_length=100)
    emissions_scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    
    raw_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    raw_unit = models.CharField(max_length=50)
    
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    normalized_unit = models.CharField(max_length=50)
    
    review_state = models.CharField(max_length=20, choices=STATE_CHOICES, default='INGESTED')
    flags = models.JSONField(default=list, blank=True)  # List of error strings/warnings
    
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_activities')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.pk:
            try:
                original = NormalizedActivity.objects.get(pk=self.pk)
                if original.review_state == 'LOCKED':
                    raise ValidationError("This record is locked for audit and cannot be modified.")
            except NormalizedActivity.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.review_state == 'LOCKED':
            raise ValidationError("This record is locked for audit and cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.activity_category} - {self.normalized_quantity} {self.normalized_unit} ({self.review_state})"

class AuditTrail(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('EDIT', 'Edited'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected/Flagged'),
        ('LOCK', 'Locked for Audit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(NormalizedActivity, on_delete=models.CASCADE, related_name='audit_trails')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)  # Format: {"field_name": [old_val, new_val]}

    def __str__(self):
        return f"{self.action} on {self.activity.id} by {self.user.username if self.user else 'System'}"
