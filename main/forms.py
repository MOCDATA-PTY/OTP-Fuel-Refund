from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
from .models import CustomUser, UserDocument

class CustomUserCreationForm(UserCreationForm):
    # Define choices for state dropdown
    STATE_CHOICES = [
        ('', 'Select State...'),
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
        ('DC', 'District of Columbia'),
    ]
    
    # Define choices for business type dropdown
    BUSINESS_TYPE_CHOICES = [
        ('', 'Select Business Type...'),
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('llc', 'Limited Liability Company (LLC)'),
        ('corporation', 'Corporation'),
        ('s_corp', 'S Corporation'),
        ('c_corp', 'C Corporation'),
        ('nonprofit', 'Nonprofit Organization'),
        ('other', 'Other'),
    ]
    
    # Account Information Fields
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'id': 'email'
        }),
        label='Email Address'
    )
    
    # Personal Information Fields - these map to model fields
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name',
            'id': 'first_name'
        }),
        label='First Name'
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name',
            'id': 'last_name'
        }),
        label='Last Name'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
            'id': 'phone',
            'type': 'tel'
        }),
        label='Phone Number'
    )
    
    # Business Information Fields - these map to model fields
    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter company name',
            'id': 'company_name'
        }),
        label='Company Name'
    )
    
    business_type = forms.ChoiceField(
        choices=BUSINESS_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'business_type'
        }),
        label='Business Type'
    )
    
    tax_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Tax ID or EIN',
            'id': 'tax_id'
        }),
        help_text='Your business tax identification number',
        label='Tax ID/EIN'
    )
    
    business_address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter business address',
            'id': 'business_address'
        }),
        label='Business Address'
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter city',
            'id': 'city'
        }),
        label='City'
    )
    
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'state'
        }),
        label='State'
    )
    
    zip_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ZIP code',
            'id': 'zip_code'
        }),
        label='ZIP Code'
    )
    
    # Terms checkbox
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'terms'
        }),
        label="I agree to the Terms of Service and Privacy Policy",
        error_messages={'required': 'You must accept the terms and conditions.'}
    )
    
    class Meta:
        model = CustomUser
        # Only include fields that actually exist on the CustomUser model
        fields = [
            'username', 'email', 'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username',
                'id': 'username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure username field
        self.fields['username'].help_text = '150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['username'].label = 'Username'
        
        # Configure password fields with proper styling
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password',
            'id': 'password1'
        })
        self.fields['password1'].help_text = 'Your password can\'t be too similar to your other personal information. Must contain at least 8 characters. Can\'t be entirely numeric.'
        self.fields['password1'].label = 'Password'
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'password2'
        })
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'
        self.fields['password2'].label = 'Confirm Password'
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email:
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError("A user with this email address already exists.")
        return email
    
    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-numeric characters
            phone_clean = re.sub(r'[^\d]', '', phone)
            if len(phone_clean) < 10:
                raise ValidationError("Phone number must be at least 10 digits.")
            # Optional: Format the phone number
            if len(phone_clean) == 10:
                return f"({phone_clean[:3]}) {phone_clean[3:6]}-{phone_clean[6:]}"
            elif len(phone_clean) == 11 and phone_clean[0] == '1':
                return f"+1 ({phone_clean[1:4]}) {phone_clean[4:7]}-{phone_clean[7:]}"
        return phone
    
    def clean_zip_code(self):
        """Validate ZIP code format"""
        zip_code = self.cleaned_data.get('zip_code')
        if zip_code:
            # US ZIP code validation (5 digits or 5+4 format)
            if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
                raise ValidationError("Enter a valid ZIP code (e.g., 12345 or 12345-6789).")
        return zip_code
    
    def clean_tax_id(self):
        """Validate Tax ID/EIN format"""
        tax_id = self.cleaned_data.get('tax_id')
        if tax_id:
            # Remove hyphens and spaces
            tax_id_clean = re.sub(r'[-\s]', '', tax_id)
            # EIN format: XX-XXXXXXX (9 digits total)
            if len(tax_id_clean) == 9 and tax_id_clean.isdigit():
                # Format as XX-XXXXXXX
                return f"{tax_id_clean[:2]}-{tax_id_clean[2:]}"
            elif len(tax_id_clean) != 9 or not tax_id_clean.isdigit():
                raise ValidationError("Enter a valid Tax ID/EIN (9 digits, format: XX-XXXXXXX).")
        return tax_id
    
    def clean_username(self):
        """Validate username uniqueness and format"""
        username = self.cleaned_data.get('username')
        if username:
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError("A user with this username already exists.")
            # Additional username validation
            if len(username) < 3:
                raise ValidationError("Username must be at least 3 characters long.")
        return username
    
    def save(self, commit=True):
        """Save user with mapped fields"""
        user = super().save(commit=False)
        
        # Map the extra form fields to your model fields  
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['first_name']
        user.surname = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone', '')
        user.business_name = self.cleaned_data.get('company_name', '')
        user.business_type = self.cleaned_data.get('business_type', '')
        user.tax_id = self.cleaned_data.get('tax_id', '')
        user.business_address = self.cleaned_data.get('business_address', '')
        user.city = self.cleaned_data.get('city', '')
        user.state = self.cleaned_data.get('state', '')
        user.zip_code = self.cleaned_data.get('zip_code', '')
        
        if commit:
            user.save()
        return user


# Enhanced Document Upload Form
class DocumentUploadForm(forms.Form):
    # Document type choices - updated for fuel refund requirements
    DOCUMENT_TYPE_CHOICES = [
        ('', 'Select document type...'),
        ('fuel_statement', 'Fuel Statements (3 Years Back)'),
        ('asset_register', 'Asset Register for Fuel Equipment'),
        ('other', 'Other Supporting Documents'),
    ]
    
    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'document_type'
        }),
        label="Document Type",
        help_text='Select the type of documents you are uploading'
    )
    
    description = forms.CharField(
        required=False,
        max_length=500,
        label="Description (Optional)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of the documents (optional)',
            'maxlength': '500',
            'rows': 3,
            'id': 'description'
        }),
        help_text='Optional description of the documents you are uploading'
    )
    
    def clean_document_type(self):
        """Validate document type selection"""
        document_type = self.cleaned_data.get('document_type')
        if not document_type:
            raise ValidationError("Please select a document type.")
        return document_type
    
    def clean_description(self):
        """Clean and validate description"""
        description = self.cleaned_data.get('description', '')
        if description:
            description = description.strip()
        return description


# Alternative: If you want a model-based document form
class DocumentUploadModelForm(forms.ModelForm):
    """Model-based document upload form"""
    
    class Meta:
        model = UserDocument
        fields = ['document_type', 'description']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'document_type'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the documents (optional)',
                'maxlength': '500',
                'rows': 3,
                'id': 'description'
            }),
        }
        help_texts = {
            'document_type': 'Select the type of documents you are uploading',
            'description': 'Optional description of the documents you are uploading'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].empty_label = "Select document type..."
        self.fields['description'].required = False