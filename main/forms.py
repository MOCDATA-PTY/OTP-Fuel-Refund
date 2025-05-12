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
        # Add more states as needed
    ]
    
    # Define choices for business type dropdown
    BUSINESS_TYPE_CHOICES = [
        ('', 'Select business type'),
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('llc', 'Limited Liability Company (LLC)'),
        ('corporation', 'Corporation'),
        ('other', 'Other'),
    ]
    
    # Add form fields to match HTML
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    company_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    business_type = forms.ChoiceField(
        choices=BUSINESS_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tax_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Enter your business tax identification number.'
    )
    
    business_address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    zip_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(),
        label="I agree to the Terms of Service and Privacy Policy"
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'company_name', 'business_type', 'tax_id', 'business_address',
            'city', 'state', 'zip_code', 'password1', 'password2'
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
        # Add help text for password fields
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and can\'t be entirely numeric.'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Map field values to your model fields
        user.email = self.cleaned_data['email']
        
        # Handle existing fields in your model with different names
        user.name = self.cleaned_data['first_name']
        user.surname = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone']
        user.business_name = self.cleaned_data['company_name']
        
        # Set additional fields
        user.business_type = self.cleaned_data['business_type']
        user.tax_id = self.cleaned_data['tax_id']
        user.business_address = self.cleaned_data['business_address']
        
        if commit:
            user.save()
        return user

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = UserDocument
        fields = ['document']