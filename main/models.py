from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Personal Information
    name = models.CharField(max_length=100, blank=True)
    middle_names = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    ssn = models.CharField(max_length=20, blank=True)
    
    # Business Information
    business_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    business_address = models.TextField(blank=True)
    
    # Additional fields for address components
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """Return the full name of the user."""
        full_name = f"{self.name} {self.surname}".strip()
        return full_name if full_name else self.username
    
    def get_business_address_formatted(self):
        """Return formatted business address."""
        address_parts = []
        if self.business_address:
            address_parts.append(self.business_address)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.zip_code:
            address_parts.append(self.zip_code)
        return ", ".join(address_parts)

class UserDocument(models.Model):
    # Document type choices for fuel refund requirements
    DOCUMENT_TYPES = [
        ('fuel_statement', 'Fuel Statements (3 Years Back)'),
        ('asset_register', 'Asset Register for Fuel Equipment'),
        ('other', 'Other Supporting Documents'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='user_documents/')
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPES, 
        default='other',
        help_text='Select the type of document being uploaded'
    )
    description = models.TextField(
        blank=True, 
        help_text='Optional description of the document'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Add file size and type tracking
    file_size = models.BigIntegerField(null=True, blank=True, help_text='File size in bytes')
    file_type = models.CharField(max_length=100, blank=True, help_text='File MIME type')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"
    
    def get_file_name(self):
        """Return just the filename without the path."""
        import os
        return os.path.basename(self.document.name)
    
    def get_file_size_formatted(self):
        """Return human-readable file size."""
        if not self.file_size:
            return "Unknown size"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024
        return f"{self.file_size:.1f} TB"
    
    def save(self, *args, **kwargs):
        # Auto-populate file size and type if not set
        if self.document and not self.file_size:
            try:
                self.file_size = self.document.size
            except:
                pass
        
        if self.document and not self.file_type:
            try:
                import mimetypes
                self.file_type = mimetypes.guess_type(self.document.name)[0] or 'application/octet-stream'
            except:
                pass
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "User Document"
        verbose_name_plural = "User Documents"
        
        # Add indexes for better query performance
        indexes = [
            models.Index(fields=['user', 'document_type']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['document_type']),
        ]

# Optional: Add a model to track user progress/status
class UserSubmissionStatus(models.Model):
    STATUS_CHOICES = [
        ('incomplete', 'Incomplete'),
        ('pending_review', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='submission_status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    has_fuel_statements = models.BooleanField(default=False)
    has_asset_register = models.BooleanField(default=False)
    submission_date = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text='Internal notes about the submission')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"
    
    def update_document_status(self):
        """Update document completion status based on uploaded documents."""
        user_docs = self.user.documents.all()
        self.has_fuel_statements = user_docs.filter(document_type='fuel_statement').exists()
        self.has_asset_register = user_docs.filter(document_type='asset_register').exists()
        
        # Auto-update status based on document completion
        if self.has_fuel_statements and self.has_asset_register:
            if self.status == 'incomplete':
                self.status = 'pending_review'
                from django.utils import timezone
                if not self.submission_date:
                    self.submission_date = timezone.now()
        
        self.save()
    
    def get_completion_percentage(self):
        """Return completion percentage based on required documents."""
        completed = 0
        total = 2  # fuel_statements and asset_register
        
        if self.has_fuel_statements:
            completed += 1
        if self.has_asset_register:
            completed += 1
            
        return int((completed / total) * 100)
    
    class Meta:
        verbose_name = "User Submission Status"
        verbose_name_plural = "User Submission Statuses"

class BusinessProfile(models.Model):
    BUSINESS_TYPES = [
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('llc', 'Limited Liability Company (LLC)'),
        ('corporation', 'Corporation'),
        ('s_corp', 'S Corporation'),
        ('c_corp', 'C Corporation'),
        ('nonprofit', 'Nonprofit Organization'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='business_profile')
    company_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    business_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"

    class Meta:
        verbose_name = "Business Profile"
        verbose_name_plural = "Business Profiles"