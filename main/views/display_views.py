from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404, FileResponse, JsonResponse
from django.template import Library
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

import os
import zipfile
import tempfile
import mimetypes
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from ..models import CustomUser, UserDocument, UserSubmissionStatus
from ..forms import CustomUserCreationForm, DocumentUploadForm

# Gmail API Configuration
GMAIL_CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, 'gmail_credentials.json')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GMAIL_TOKEN_FILE = os.path.join(settings.BASE_DIR, 'gmail_token.json')

# Create a register object for template filters
register = Library()

# Template filter to access dictionary values
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# Template filter to get only the filename from a path
@register.filter
def filename(value):
    """Returns just the filename from a full path."""
    return os.path.basename(value)

def get_gmail_service():
    """Get authenticated Gmail API service"""
    creds = None
    
    # Load existing credentials
    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)
    
    # If no valid credentials, need to authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # First time setup - manual authorization needed
            flow = Flow.from_client_secrets_file(GMAIL_CLIENT_SECRETS_FILE, GMAIL_SCOPES)
            flow.redirect_uri = 'http://localhost:8000/oauth/callback/'
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"🔗 Go to this URL to authorize Gmail API: {auth_url}")
            
            # This will be handled by the oauth callback
            return None
            
        # Save credentials for future use
        if creds:
            with open(GMAIL_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def send_email_with_gmail_api(recipient_email, subject, body):
    """
    Send email using Gmail API - appears from fuelrefundinstitute@outlook.com
    """
    try:
        service = get_gmail_service()
        
        if not service:
            return False, "Gmail API not authorized. Check console for authorization URL."
        
        # Create message with custom From address
        msg = MIMEMultipart()
        msg['From'] = 'Fuel Refund Institute <fuelrefundinstitute@outlook.com>'  # What clients see
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg['Reply-To'] = 'fuelrefundinstitute@outlook.com'
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        
        # Send email
        message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ Email sent! Appears from: fuelrefundinstitute@outlook.com")
        print(f"📧 To: {recipient_email}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Message ID: {message['id']}")
        return True, f"Email sent successfully"
        
    except Exception as e:
        print(f"❌ Gmail API error: {str(e)}")
        return False, f"Gmail API error: {str(e)}"

def send_resend_email(recipient_email, subject, body):
    """
    Send email via Gmail API - appears from fuelrefundinstitute@outlook.com
    """
    print("📧 Sending email via Gmail API...")
    print(f"📧 From (what clients see): fuelrefundinstitute@outlook.com")
    print(f"📧 To: {recipient_email}")
    
    return send_email_with_gmail_api(recipient_email, subject, body)

# Public landing page
def home(request):
    return render(request, 'main/home.html')

# Contact page view
def contact(request):
    """
    View function for the contact page
    """
    if request.method == 'POST':
        messages.success(request, "Your message has been sent. We'll get back to you soon.")
        return redirect('contact')
        
    return render(request, 'main/contact.html')

# Enhanced signup view with proper form handling
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    UserSubmissionStatus.objects.create(user=user)
                    messages.success(request, 'Account created successfully! Please log in.')
                    return redirect('login')
                    
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label or field.replace('_', ' ').title()
                        messages.error(request, f'{field_label}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'main/signup.html', {'form': form})

# Enhanced Login view that forces re-authentication
def login_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Please log in again for security.")
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    display_name = user.get_full_name() or user.username
                    messages.success(request, f"Welcome back, {display_name}!")
                    
                    next_page = request.GET.get('next', 'dashboard')
                    return redirect(next_page)
                else:
                    messages.error(request, "Your account has been disabled. Please contact support.")
            else:
                messages.error(request, "Invalid username or password. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'main/login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# Updated dashboard with unlimited uploads and document categories
@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
        
    documents = UserDocument.objects.filter(user=request.user)
    form = DocumentUploadForm()
        
    for doc in documents:
        doc.display_name = os.path.basename(doc.document.name)
        
    if request.method == 'POST':
        files = request.FILES.getlist('document')
        document_type = request.POST.get('document_type', '')
        description = request.POST.get('description', '')
        
        if not files:
            messages.warning(request, "Please select at least one file to upload.")
        elif not document_type:
            messages.warning(request, "Please select a document type.")
        else:
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.txt', '.xls', '.xlsx']
            max_file_size = 10 * 1024 * 1024  # 10MB
            
            valid_files = []
            errors = []
            
            for file in files:
                file_name = file.name.lower()
                file_ext = None
                
                for ext in allowed_extensions:
                    if file_name.endswith(ext):
                        file_ext = ext
                        break
                
                if not file_ext:
                    errors.append(f"'{file.name}' has an unsupported format. Allowed: PDF, Word, Images, Text, Excel files.")
                    continue
                
                if file.size > max_file_size:
                    file_size_mb = file.size / (1024 * 1024)
                    errors.append(f"'{file.name}' is too large ({file_size_mb:.1f}MB). Maximum size is 10MB.")
                    continue
                
                valid_files.append(file)
            
            if errors:
                for error in errors:
                    messages.error(request, error)
            
            if valid_files:
                files_uploaded = 0
                for file in valid_files:
                    try:
                        new_doc = UserDocument(
                            user=request.user,
                            document=file,
                            document_type=document_type,
                            description=description
                        )
                        new_doc.save()
                        files_uploaded += 1
                    except Exception as e:
                        messages.error(request, f"Error uploading '{file.name}': {str(e)}")
                
                if files_uploaded > 0:
                    doc_type_choices = dict(DocumentUploadForm.DOCUMENT_TYPE_CHOICES)
                    doc_type_display = doc_type_choices.get(document_type, 'document(s)')
                    
                    if files_uploaded == 1:
                        messages.success(request, f"Successfully uploaded 1 {doc_type_display.lower()}.")
                    else:
                        messages.success(request, f"Successfully uploaded {files_uploaded} {doc_type_display.lower()}.")
                    
                    if errors and valid_files:
                        rejected_count = len(files) - files_uploaded
                        if rejected_count > 0:
                            messages.warning(request, f"Note: {rejected_count} file(s) were rejected due to validation errors.")
                    
        return redirect('dashboard')
    
    fuel_statements = documents.filter(document_type='fuel_statement')
    asset_registers = documents.filter(document_type='asset_register')
    other_documents = documents.filter(document_type='other')
    
    has_fuel_statements = fuel_statements.exists()
    has_asset_register = asset_registers.exists()
    
    requirements_met = has_fuel_statements and has_asset_register
    
    return render(request, 'main/dashboard.html', {
        'user': request.user,
        'form': form,
        'documents': documents,
        'fuel_statements': fuel_statements,
        'asset_registers': asset_registers,
        'other_documents': other_documents,
        'has_fuel_statements': has_fuel_statements,
        'has_asset_register': has_asset_register,
        'requirements_met': requirements_met,
        'fuel_statements_count': fuel_statements.count(),
        'asset_registers_count': asset_registers.count(),
        'other_documents_count': other_documents.count(),
        'total_documents': documents.count(),
    })

@login_required
def admin_dashboard(request):
    """
    Admin dashboard view that shows all non-admin users and their documents.
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    all_users = get_user_model().objects.filter(is_superuser=False).order_by('username')
    
    for user in all_users:
        docs = UserDocument.objects.filter(user=user)
        fuel_statements = docs.filter(document_type='fuel_statement')
        asset_registers = docs.filter(document_type='asset_register')
        
        user.user_docs = docs
        user.doc_count = docs.count()
        user.has_fuel_statements = fuel_statements.exists()
        user.has_asset_registers = asset_registers.exists()
        user.requirements_met = fuel_statements.exists() and asset_registers.exists()
        
        for doc in docs:
            doc.display_name = os.path.basename(doc.document.name)
    
    total_users = all_users.count()
    users_with_fuel = sum(1 for user in all_users if user.has_fuel_statements)
    users_with_assets = sum(1 for user in all_users if user.has_asset_registers)
    users_complete = sum(1 for user in all_users if user.requirements_met)
    total_documents = sum(user.doc_count for user in all_users)
    
    context = {
        'all_users': all_users,
        'total_users': total_users,
        'users_with_fuel': users_with_fuel,
        'users_with_assets': users_with_assets,
        'users_complete': users_complete,
        'users_pending': total_users - users_complete,
        'total_documents': total_documents,
    }
    
    return render(request, 'main/admin_dashboard.html', context)

@login_required
def send_reminder_email(request, username):
    """
    Send reminder email to user with incomplete documents.
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    try:
        user = get_user_model().objects.get(username=username)
        
        if not user.email:
            messages.error(request, f"No email address found for user '{username}'.")
            return redirect('admin_dashboard')
        
        # Check what documents are missing
        docs = UserDocument.objects.filter(user=user)
        fuel_statements = docs.filter(document_type='fuel_statement')
        asset_registers = docs.filter(document_type='asset_register')
        
        has_fuel_statements = fuel_statements.exists()
        has_asset_registers = asset_registers.exists()
        
        missing_docs = []
        if not has_fuel_statements:
            missing_docs.append("Fuel Statements")
        if not has_asset_registers:
            missing_docs.append("Asset Register")
        
        if not missing_docs:
            messages.info(request, f"User '{username}' has already submitted all required documents.")
            return redirect('admin_dashboard')
        
        subject = "Reminder: Complete Your Fuel Refund Application"
        full_name = user.get_full_name() if user.get_full_name() else user.username
        
        email_body = f"""Dear {full_name},

This is a friendly reminder that your fuel refund application is incomplete.

Missing Documents:
{chr(10).join(['• ' + doc for doc in missing_docs])}

To complete your application, please:
1. Log in to your account at our website
2. Upload the missing documents listed above
3. Ensure all information is accurate and complete

Your Account Details:
- Username: {user.username}
- Email: {user.email}
- Business: {user.business_name if user.business_name else 'Not provided'}

If you have any questions or need assistance, please contact our support team.

Thank you for your cooperation.

Best regards,
Fuel Refund Institute
Email: fuelrefundinstitute@outlook.com
"""

        # Send email using Gmail API
        success, message = send_resend_email(user.email, subject, email_body)
        
        if success:
            messages.success(request, f"✅ Reminder email sent successfully to {user.email}")
        else:
            messages.error(request, f"❌ Failed to send email: {message}")
            
    except get_user_model().DoesNotExist:
        messages.error(request, "User not found.")
    except Exception as e:
        messages.error(request, f"Error sending reminder: {str(e)}")
    
    return redirect('admin_dashboard')

@login_required 
@require_http_methods(["POST"])
def send_custom_email(request, username):
    """
    Send custom email to a user.
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    try:
        user = get_user_model().objects.get(username=username)
        
        if not user.email:
            return JsonResponse({'success': False, 'message': f'No email address found for user {username}'})
        
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not subject or not message:
            return JsonResponse({'success': False, 'message': 'Subject and message are required'})
        
        full_name = user.get_full_name() if user.get_full_name() else user.username
        
        email_body = f"""Dear {full_name},

{message}

Best regards,
{request.user.get_full_name() or request.user.username}
Fuel Refund Institute
Email: fuelrefundinstitute@outlook.com
"""

        print(f"📧 Sending custom email to {user.email}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Message length: {len(message)} characters")
        
        success, result_message = send_resend_email(user.email, subject, email_body)
        
        print(f"📧 Email send result: {success}, Message: {result_message}")
        
        if success:
            return JsonResponse({'success': True, 'message': f'Email sent successfully to {user.email}'})
        else:
            return JsonResponse({'success': False, 'message': f'Failed to send email: {result_message}'})
            
    except get_user_model().DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'})
    except Exception as e:
        print(f"❌ Exception in send_custom_email: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error sending email: {str(e)}'})

@login_required
def toggle_admin_status(request, username):
    """
    Toggle a user's admin status (promote to admin or demote from admin).
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    try:
        user = get_user_model().objects.get(username=username)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'promote':
                user.is_superuser = True
                user.is_staff = True
                user.save()
                messages.success(request, f"User '{username}' has been promoted to administrator.")
                
            elif action == 'demote':
                user.is_superuser = False
                user.is_staff = False
                user.save()
                messages.success(request, f"Administrator '{username}' has been demoted to regular user.")
                
            else:
                messages.error(request, "Invalid action specified.")
        
        return redirect('admin_dashboard')
        
    except get_user_model().DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f"Error updating user status: {str(e)}")
        return redirect('admin_dashboard')

@login_required
def analytics_dashboard(request):
    """
    Analytics dashboard with Power BI integration.
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    powerbi_url = "https://app.powerbi.com/view?r=YOUR_POWER_BI_REPORT_ID"
    
    return render(request, 'main/analytics_dashboard.html', {
        'powerbi_url': powerbi_url
    })

@login_required
def view_document(request, doc_id):
    """
    View document details and provide download option.
    """
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        if not request.user.is_superuser and document.user != request.user:
            raise Http404("Document not found")
        
        file_path = document.document.path if document.document else None
        file_exists = file_path and os.path.exists(file_path)
        file_size = None
        file_size_mb = None
        
        if file_exists:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
        
        context = {
            'document': document,
            'file_exists': file_exists,
            'file_size': file_size,
            'file_size_mb': file_size_mb,
            'can_download': file_exists,
        }
        
        return render(request, 'main/view_document.html', context)
        
    except UserDocument.DoesNotExist:
        raise Http404("Document not found")

@login_required
def delete_user(request, username):
    """
    Delete a user account (admin only).
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    try:
        user_to_delete = get_user_model().objects.get(username=username)
        
        if user_to_delete.is_superuser:
            messages.error(request, "Cannot delete administrator accounts.")
            return redirect('admin_dashboard')
        
        if user_to_delete == request.user:
            messages.error(request, "Cannot delete your own account.")
            return redirect('admin_dashboard')
        
        if request.method == 'POST':
            UserDocument.objects.filter(user=user_to_delete).delete()
            user_to_delete.delete()
            messages.success(request, f"User '{username}' has been deleted successfully.")
            
        return redirect('admin_dashboard')
        
    except get_user_model().DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f"Error deleting user: {str(e)}")
        return redirect('admin_dashboard')

@login_required
def download_document(request, doc_id):
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        if not request.user.is_superuser and document.user != request.user:
            raise Http404("Document not found")
        
        file_path = document.document.path
        
        if not os.path.exists(file_path):
            raise Http404("Document file not found")
        
        content_type, encoding = mimetypes.guess_type(file_path)
        
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except UserDocument.DoesNotExist:
        raise Http404("Document not found")
    except Exception as e:
        raise Http404(f"Error downloading document: {str(e)}")

@login_required
def download_all_documents(request, user_id):
    try:
        user = get_user_model().objects.get(id=user_id)
        
        if not request.user.is_superuser and user != request.user:
            raise Http404("User not found")
        
        documents = UserDocument.objects.filter(user=user)
        
        if not documents:
            messages.warning(request, "No documents found to download.")
            return redirect('admin_dashboard' if request.user.is_superuser else 'dashboard')
        
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for document in documents:
                file_path = document.document.path
                
                if os.path.exists(file_path):
                    doc_type = document.get_document_type_display() if hasattr(document, 'document_type') else 'Other'
                    folder_name = doc_type.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
                    zip_path = f"{folder_name}/{os.path.basename(file_path)}"
                    zip_file.write(file_path, zip_path)
        
        temp_file.close()
        
        with open(temp_file.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{user.username}_documents.zip"'
        
        os.unlink(temp_file.name)
        
        return response
    except get_user_model().DoesNotExist:
        raise Http404("User not found")
    except Exception as e:
        raise Http404(f"Error creating ZIP file: {str(e)}")

@login_required
def edit_user(request, username):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    try:
        user = get_user_model().objects.get(username=username)
        
        if request.method == 'POST':
            user.name = request.POST.get('name', user.name)
            user.middle_names = request.POST.get('middle_names', user.middle_names)
            user.surname = request.POST.get('surname', user.surname)
            user.email = request.POST.get('email', user.email)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.ssn = request.POST.get('ssn', user.ssn)
            user.business_name = request.POST.get('business_name', user.business_name)
            user.business_type = request.POST.get('business_type', user.business_type)
            user.tax_id = request.POST.get('tax_id', user.tax_id)
            user.business_address = request.POST.get('business_address', user.business_address)
            user.city = request.POST.get('city', user.city)
            user.state = request.POST.get('state', user.state)
            user.zip_code = request.POST.get('zip_code', user.zip_code)
            
            user.save()
            messages.success(request, f"User {username} has been updated successfully.")
            return redirect('admin_dashboard')
        
        return render(request, 'main/edit_user.html', {
            'user_to_edit': user
        })
    except get_user_model().DoesNotExist:
        raise Http404("User not found")

@login_required
def delete_document(request, doc_id):
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        if document.user != request.user and not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete this document.")
            return redirect('dashboard')
        
        document_name = os.path.basename(document.document.name)
        document_type = document.get_document_type_display() if hasattr(document, 'document_type') else 'document'
        
        try:
            if os.path.exists(document.document.path):
                os.remove(document.document.path)
        except Exception as e:
            print(f"Error deleting file {document.document.path}: {e}")
        
        document.delete()
        
        messages.success(request, f"{document_type} '{document_name}' has been deleted successfully.")
        return redirect('admin_dashboard' if request.user.is_superuser else 'dashboard')
    except UserDocument.DoesNotExist:
        messages.error(request, "Document not found.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error deleting document: {str(e)}")
        return redirect('dashboard')

def download_privacy_policy(request):
    """
    View to download Privacy Policy document
    """
    try:
        file_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Privacy Policy.docx')
        
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = 'attachment; filename="Privacy Policy.docx"'
            return response
        else:
            raise Http404("Privacy Policy document not found")
    except Exception as e:
        raise Http404("Error downloading Privacy Policy")

def download_terms_conditions(request):
    """
    View to download Terms and Conditions document
    """
    try:
        file_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Terms and Conditions.docx')
        
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = 'attachment; filename="Terms and Conditions.docx"'
            return response
        else:
            raise Http404("Terms and Conditions document not found")
    except Exception as e:
        raise Http404("Error downloading Terms and Conditions")

def terms_of_service(request):
    return render(request, 'main/terms_of_service.html')

def privacy_policy(request):
    return render(request, 'main/privacy_policy.html')

def debug_users(request):
    """Quick debug view to see all users in the database"""
    users = CustomUser.objects.all()
    debug_info = []
    
    for user in users:
        debug_info.append({
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'surname': user.surname,
            'business_name': user.business_name,
            'phone_number': user.phone_number,
            'city': user.city,
            'state': user.state,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
        })
    
    return render(request, 'main/debug.html', {
        'users': debug_info,
        'total_users': users.count()
    })

def gmail_oauth_callback(request):
    """Handle OAuth callback from Google"""
    try:
        # Get authorization code from callback
        code = request.GET.get('code')
        if not code:
            messages.error(request, "No authorization code received")
            return redirect('admin_dashboard')
        
        # Exchange code for credentials
        flow = Flow.from_client_secrets_file(GMAIL_CLIENT_SECRETS_FILE, GMAIL_SCOPES)
        flow.redirect_uri = 'http://localhost:8000/oauth/callback/'
        flow.fetch_token(code=code)
        
        # Save credentials
        creds = flow.credentials
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        messages.success(request, "Gmail API authorization successful! Email functionality is now active.")
        return redirect('admin_dashboard')
        
    except Exception as e:
        messages.error(request, f"OAuth error: {str(e)}")
        return redirect('admin_dashboard')

# Import API views for URL routing (if you have them)
try:
    from .api_views import (
        user_details_api,
        user_details_by_username_api,
        user_update_api,
        user_delete_api,
        user_documents_by_date_api,
        download_document_api,
        download_privacy_policy_api,
        download_terms_conditions_api
    )
except ImportError:
    pass