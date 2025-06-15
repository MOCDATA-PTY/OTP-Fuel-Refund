from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserDocument

class CustomUserCreationForm(UserCreationForm):
    # Define choices for state dropdown
    STATE_CHOICES = [
        ('', 'Select state'),
        ('CA', 'California'),
        ('NV', 'Nevada'),
        ('AZ', 'Arizona'),
        ('OR', 'Oregon'),
        ('WA', 'Washington'),
        ('TX', 'Texas'),
        ('FL', 'Florida'),
        ('NY', 'New York'),
        ('IL', 'Illinois'),
        ('PA', 'Pennsylvania'),
        ('OH', 'Ohio'),
        ('GA', 'Georgia'),
        ('NC', 'North Carolina'),
        ('MI', 'Michigan'),
        ('NJ', 'New Jersey'),
        ('VA', 'Virginia'),
        ('TN', 'Tennessee'),
        ('IN', 'Indiana'),
        ('MO', 'Missouri'),
        ('MD', 'Maryland'),
        ('WI', 'Wisconsin'),
        ('CO', 'Colorado'),
        ('MN', 'Minnesota'),
        ('SC', 'South Carolina'),
        ('AL', 'Alabama'),
        ('LA', 'Louisiana'),
        ('KY', 'Kentucky'),
        ('UT', 'Utah'),
        ('AR', 'Arkansas'),
        ('CT', 'Connecticut'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('MS', 'Mississippi'),
        ('NE', 'Nebraska'),
        ('NM', 'New Mexico'),
        ('WV', 'West Virginia'),
        ('ID', 'Idaho'),
        ('HI', 'Hawaii'),
        ('NH', 'New Hampshire'),
        ('ME', 'Maine'),
        ('MT', 'Montana'),
        ('RI', 'Rhode Island'),
        ('DE', 'Delaware'),
        ('SD', 'South Dakota'),
        ('ND', 'North Dakota'),
        ('AK', 'Alaska'),
        ('VT', 'Vermont'),
        ('WY', 'Wyoming'),
        ('DC', 'District of Columbia'),
    ]
    
    # Define choices for business type dropdown
    BUSINESS_TYPE_CHOICES = [
        ('', 'Select business type'),
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('llc', 'Limited Liability Company (LLC)'),
        ('corporation', 'Corporation'),
        ('s_corp', 'S Corporation'),
        ('c_corp', 'C Corporation'),
        ('nonprofit', 'Nonprofit Organization'),
        ('other', 'Other'),
    ]
    
    # Add form fields - these are EXTRA fields not in the model
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='First Name'
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Last Name'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Email Address'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
        label='Phone Number'
    )
    
    company_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Company/Business Name'
    )
    
    business_type = forms.ChoiceField(
        choices=BUSINESS_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Business Type'
    )
    
    tax_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XX-XXXXXXX'}),
        help_text='Enter your business tax identification number (EIN).',
        label='Tax ID/EIN'
    )
    
    business_address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Business Address'
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='City'
    )
    
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='State'
    )
    
    zip_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345'}),
        label='ZIP Code'
    )
    
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I agree to the Terms of Service and Privacy Policy"
    )
    
    class Meta:
        model = CustomUser
        # FIXED: Only include fields that actually exist on the CustomUser model
        fields = [
            'username', 'email', 'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for username field
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['username'].label = 'Username'
        
        # Add help text for password fields
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and can\'t be entirely numeric.'
        self.fields['password1'].label = 'Password'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'
        self.fields['password2'].label = 'Confirm Password'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Map the extra form fields to your model fields  
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['first_name']
        user.surname = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone']
        user.business_name = self.cleaned_data['company_name']
        user.business_type = self.cleaned_data['business_type']
        user.tax_id = self.cleaned_data['tax_id']
        user.business_address = self.cleaned_data['business_address']
        user.city = self.cleaned_data['city']
        user.state = self.cleaned_data['state']
        user.zip_code = self.cleaned_data['zip_code']
        
        if commit:
            user.save()
        return user

# Simple form that handles document uploads manually
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
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Document Type",
        help_text='Select the type of documents you are uploading'
    )
    
    description = forms.CharField(
        required=False,
        max_length=500,
        label="Description (Optional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of the documents (optional)',
            'maxlength': '500'
        }),
        help_text='Optional description of the documents you are uploading'
    )
    
    def clean_document_type(self):
        document_type = self.cleaned_data.get('document_type')
        if not document_type:
            raise forms.ValidationError("Please select a document type.")
        return document_type
    
    # Note: We don't include the file field here to avoid Django's FileInput multiple file restrictions
    # Files are handled manually in the view using request.FILES.getlist('document')