from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    name = models.CharField(max_length=100)
    middle_names = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    ssn = models.CharField(max_length=11)
    email = models.EmailField(unique=True)

    business_name = models.CharField(max_length=150)
    business_type = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50)
    business_address = models.TextField()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username


class UserDocument(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.document.name}"
