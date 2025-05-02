from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserDocument

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'name', 'middle_names', 'surname',
            'phone_number', 'ssn', 'business_name', 'business_type',
            'tax_id', 'business_address'
        ]
        widgets = {
            'business_address': forms.TextInput(),
        }

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = UserDocument
        fields = ['document']
