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
from django.core.cache import cache
import json

import os
import zipfile
import tempfile
import mimetypes
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..models import CustomUser, UserDocument, UserSubmissionStatus
from ..forms import CustomUserCreationForm, DocumentUploadForm

# Setup logging
logger = logging.getLogger(__name__)

# Production Gmail API Configuration
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
    """Production-ready Gmail API service with caching and error handling"""
    
    # Check cache first (5 minute cache)
    cached_service = cache.get('gmail_service')
    if cached_service:
        return cached_service
    
    try:
        creds = None
        
        # Load existing credentials
        if os.path.exists(GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)
        
        # Handle expired/invalid credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Gmail credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    # Delete expired token and re-authorize
                    if os.path.exists(GMAIL_TOKEN_FILE):
                        os.remove(GMAIL_TOKEN_FILE)
                    return None
            else:
                # First time setup - manual authorization needed
                if not os.path.exists(GMAIL_CLIENT_SECRETS_FILE):
                    print(f"❌ Gmail credentials file not found: {GMAIL_CLIENT_SECRETS_FILE}")
                    return None
                
                flow = Flow.from_client_secrets_file(GMAIL_CLIENT_SECRETS_FILE, GMAIL_SCOPES)
                
                # PRODUCTION FIX: Dynamic redirect URI based on environment
                if settings.DEBUG:
                    flow.redirect_uri = 'http://localhost:8000/oauth/callback/'
                else:
                    # Production domain
                    flow.redirect_uri = 'https://fuelrefundinstitute.com/oauth/callback/'
                
                # Get authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')
                print(f"\n🔗 AUTHORIZATION REQUIRED:")
                print(f"🔗 Copy this URL and open in browser: {auth_url}")
                print(f"🔗 After authorization, anti-spam emails will work automatically!\n")
                
                return None
                
            # Save credentials for future use
            if creds:
                with open(GMAIL_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
        
        # Build and cache service
        service = build('gmail', 'v1', credentials=creds)
        cache.set('gmail_service', service, 300)  # Cache for 5 minutes
        return service
        
    except Exception as e:
        logger.error(f"Gmail service setup error: {e}")
        print(f"❌ Gmail API Error: {e}")
        return None

def create_beautiful_email_template(template_type, context):
    """Create stunning anti-spam HTML email templates with professional design"""
    
    base_style = """
    <style>
        body { margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; color: #1f2937; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 700; }
        .header p { margin: 8px 0 0 0; opacity: 0.9; font-size: 16px; }
        .content { padding: 40px 30px; }
        .greeting { font-size: 20px; color: #1e293b; margin-bottom: 20px; font-weight: 600; }
        .message { color: #475569; font-size: 16px; line-height: 1.6; margin-bottom: 20px; }
        .highlight-box { background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 8px; padding: 20px; margin: 25px 0; }
        .requirements { background: #fef7ff; border: 2px solid #a855f7; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .requirement-item { display: flex; align-items: center; margin: 10px 0; font-size: 15px; }
        .status-complete { color: #059669; font-weight: 600; }
        .status-missing { color: #dc2626; font-weight: 600; }
        .button { display: inline-block; background: linear-gradient(135deg, #f97316, #ea580c); color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f8fafc; padding: 30px; text-align: center; color: #64748b; border-top: 1px solid #e2e8f0; font-size: 14px; }
        .account-info { background: #f1f5f9; border-radius: 8px; padding: 15px; margin: 20px 0; font-family: Arial, sans-serif; }
        .business-footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }
        .contact-info { margin: 10px 0; }
        .unsubscribe { margin-top: 15px; font-size: 11px; }
        .unsubscribe a { color: #6b7280; text-decoration: none; }
    </style>
    """
    
    # Business footer for anti-spam compliance - Updated with production phone
    business_footer = f"""
    <div class="business-footer">
        <div class="contact-info">
            <strong>Fuel Refund Institute</strong><br>
            Professional Tax Services<br>
            123 Business Street, Houston, TX 77001<br>
            Phone: +1 (424) 222-5290<br>
            Email: fuelrefundinstitute@gmail.com<br>
            Website: https://fuelrefundinstitute.com
        </div>
        <div class="unsubscribe">
            <p>You received this email because you have an active account with Fuel Refund Institute.</p>
            <p><a href="mailto:fuelrefundinstitute@gmail.com?subject=Unsubscribe">Unsubscribe</a> | 
               <a href="https://fuelrefundinstitute.com/privacy-policy">Privacy Policy</a> | 
               <a href="https://fuelrefundinstitute.com/terms-of-service">Terms of Service</a></p>
        </div>
    </div>
    """
    
    if template_type == 'reminder':
        content = f"""
        <div class="greeting">Hello {context['user_name']}!</div>
        
        <div class="message">
            We hope you're doing well. We're reaching out regarding your <strong>fuel refund application</strong> 
            with Fuel Refund Institute. We noticed there are a few documents still needed to complete your submission.
        </div>
        
        <div class="highlight-box">
            <strong>📋 Document Status Update:</strong><br><br>
            {context['requirements_html']}
        </div>
        
        <div class="message">
            <strong>Next Steps:</strong><br>
            1. 🔐 Log into your secure account at <a href="https://fuelrefundinstitute.com/login/">fuelrefundinstitute.com</a><br>
            2. 📄 Upload the missing documents<br>
            3. ✅ Submit for professional review<br>
            4. 💰 Receive your fuel tax refund processing
        </div>
        
        <div class="account-info">
            <strong>Your Account Information:</strong><br>
            Username: {context['username']}<br>
            Email: {context['email']}<br>
            Business: {context['business_name']}
        </div>
        
        <div class="message">
            Our professional support team is available to assist you with any questions about your fuel refund application.
        </div>
        """
    
    elif template_type == 'custom':
        content = f"""
        <div class="greeting">Hello {context['user_name']}!</div>
        
        <div class="message">
            {context['custom_message']}
        </div>
        
        <div class="account-info">
            <strong>Your Account Information:</strong><br>
            Username: {context['username']}<br>
            Email: {context['email']}<br>
            Business: {context['business_name']}
        </div>
        
        <div class="message">
            If you have any questions about our fuel refund services, please feel free to contact our professional support team.
        </div>
        
        <div class="message">
            <strong>Best regards,</strong><br>
            {context['sender_name']}<br>
            <em>Fuel Refund Institute Team</em>
        </div>
        """
    
    elif template_type == 'welcome':
        content = f"""
        <div class="greeting">Welcome to Fuel Refund Institute, {context['user_name']}! 🎉</div>
        
        <div class="message">
            Thank you for joining our professional fuel refund services. We're committed to helping you 
            recover your fuel tax refunds efficiently and accurately.
        </div>
        
        <div class="requirements">
            <strong>🚀 Your Next Steps:</strong><br><br>
            1. 📊 Upload your <strong>Fuel Statements</strong> (3 years back)<br>
            2. 📋 Upload your <strong>Asset Register</strong> for fuel equipment<br>
            3. ✅ Submit for professional review by our tax experts<br>
            4. 💰 Receive your fuel tax refund processing
        </div>
        
        <div class="message">
            Our secure platform makes document submission simple and tracks your refund status in real-time.
            Visit <a href="https://fuelrefundinstitute.com/dashboard/">your dashboard</a> to get started.
        </div>
        """
    
    html_email = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{context.get('subject', 'Fuel Refund Institute')}</title>
        {base_style}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛢️ Fuel Refund Institute</h1>
                <p>Professional Fuel Tax Refund Services</p>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p><strong>Fuel Refund Institute</strong></p>
                <p>Professional Tax Services | Trusted Partner Since 2024</p>
                <p>📧 fuelrefundinstitute@gmail.com | 📞 +1 (424) 222-5290</p>
                <p>🌐 <a href="https://fuelrefundinstitute.com">fuelrefundinstitute.com</a></p>
                {business_footer}
                <p style="margin-top: 20px; opacity: 0.7;">
                    © {datetime.now().year} Fuel Refund Institute. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_email

def send_email_with_gmail_api(recipient_email, subject, body, template_type='custom', context=None):
    """
    Production-ready Gmail API email sending with anti-spam headers and beautiful templates
    """
    try:
        service = get_gmail_service()
        
        if not service:
            return False, "Gmail API not authorized. Check console for authorization URL."
        
        # Create beautiful HTML email
        if context:
            html_content = create_beautiful_email_template(template_type, context)
        else:
            # Fallback to styled email
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en"><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
            <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <h1 style="margin: 0;">🛢️ Fuel Refund Institute</h1>
                <p style="margin: 5px 0 0 0;">Professional Fuel Tax Refund Services</p>
            </div>
            <div style="line-height: 1.6; color: #333;">
                {body.replace(chr(10), '<br>')}
            </div>
            <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; color: #666; font-size: 14px;">
                <p><strong>Fuel Refund Institute</strong></p>
                <p>📧 fuelrefundinstitute@gmail.com | 📞 +1 (424) 222-5290</p>
                <p>🌐 <a href="https://fuelrefundinstitute.com" style="color: #666;">fuelrefundinstitute.com</a></p>
                <p style="font-size: 12px; margin-top: 15px;">123 Business Street, Houston, TX 77001</p>
                <p style="font-size: 11px; margin-top: 10px;">
                    <a href="mailto:fuelrefundinstitute@gmail.com?subject=Unsubscribe" style="color: #666;">Unsubscribe</a>
                </p>
            </div>
            </body></html>
            """
        
        # Create message with anti-spam headers
        msg = MIMEMultipart('alternative')
        
        # Enhanced anti-spam headers for production
        msg['From'] = 'Fuel Refund Institute <fuelrefundinstitute@gmail.com>'
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg['Reply-To'] = 'fuelrefundinstitute@gmail.com'
        msg['X-Mailer'] = 'Fuel Refund Institute Professional Services'
        msg['Organization'] = 'Fuel Refund Institute'
        msg['X-Priority'] = '3'
        msg['X-MSMail-Priority'] = 'Normal'
        msg['List-Unsubscribe'] = '<mailto:fuelrefundinstitute@gmail.com?subject=Unsubscribe>'
        msg['Return-Path'] = 'fuelrefundinstitute@gmail.com'
        msg['Message-ID'] = f'<{datetime.now().strftime("%Y%m%d%H%M%S")}.{recipient_email.replace("@", ".")}@fuelrefundinstitute.com>'
        
        # Add both plain text and HTML versions
        # Create plain text version
        plain_text = f"""
        Fuel Refund Institute - Professional Tax Services

        {body}

        ---
        Fuel Refund Institute
        Professional Tax Services
        123 Business Street, Houston, TX 77001
        Phone: +1 (424) 222-5290
        Email: fuelrefundinstitute@gmail.com
        Website: https://fuelrefundinstitute.com

        To unsubscribe, reply with "Unsubscribe" in the subject line.
        """
        
        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        
        message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ PRODUCTION ANTI-SPAM EMAIL SENT SUCCESSFULLY!")
        print(f"📧 From: Fuel Refund Institute (fuelrefundinstitute.com)")
        print(f"📧 To: {recipient_email}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Template: {template_type}")
        print(f"📧 Message ID: {message['id']}")
        print(f"🛡️ Production anti-spam headers: APPLIED")
        
        return True, f"Email sent successfully (ID: {message['id']})"
        
    except HttpError as error:
        error_details = error.error_details[0] if error.error_details else {}
        error_message = error_details.get('message', str(error))
        logger.error(f"Gmail API HTTP Error: {error_message}")
        print(f"❌ Gmail API Error: {error_message}")
        return False, f"Gmail API error: {error_message}"
        
    except Exception as e:
        logger.error(f"Gmail API general error: {str(e)}")
        print(f"❌ Gmail Error: {str(e)}")
        return False, f"Email error: {str(e)}"

def send_resend_email(recipient_email, subject, body):
    """
    Enhanced email sending function - backwards compatible with anti-spam
    """
    print(f"📧 Preparing to send production anti-spam email via Gmail API...")
    print(f"📧 To: {recipient_email}")
    print(f"📧 Subject: {subject}")
    
    return send_email_with_gmail_api(recipient_email, subject, body)

def send_reminder_email_with_template(user):
    """Send beautiful reminder email using anti-spam template"""
    
    # Check missing documents
    docs = UserDocument.objects.filter(user=user)
    fuel_statements = docs.filter(document_type='fuel_statement')
    asset_registers = docs.filter(document_type='asset_register')
    
    has_fuel = fuel_statements.exists()
    has_assets = asset_registers.exists()
    
    # Create requirements HTML
    requirements_html = ""
    if not has_fuel:
        requirements_html += '<div class="requirement-item">❌ <span class="status-missing">Fuel Statements - Required</span></div>'
    else:
        requirements_html += '<div class="requirement-item">✅ <span class="status-complete">Fuel Statements - Complete</span></div>'
    
    if not has_assets:
        requirements_html += '<div class="requirement-item">❌ <span class="status-missing">Asset Register - Required</span></div>'
    else:
        requirements_html += '<div class="requirement-item">✅ <span class="status-complete">Asset Register - Complete</span></div>'
    
    # Professional email context
    context = {
        'subject': 'Fuel Refund Application - Document Submission Required',
        'user_name': user.get_full_name() or user.username,
        'username': user.username,
        'email': user.email,
        'business_name': user.business_name or 'Not provided',
        'requirements_html': requirements_html
    }
    
    return send_email_with_gmail_api(
        recipient_email=user.email,
        subject=context['subject'],
        body="Please complete your fuel refund application by submitting the required documents.",
        template_type='reminder',
        context=context
    )

def send_custom_email_with_template(user, subject, message, sender_name):
    """Send beautiful custom email using anti-spam template"""
    
    # Make subject more professional and less spammy
    if not any(word in subject.lower() for word in ['fuel', 'refund', 'institute', 'application', 'document']):
        subject = f"Fuel Refund Institute - {subject}"
    
    context = {
        'subject': subject,
        'user_name': user.get_full_name() or user.username,
        'username': user.username,
        'email': user.email,
        'business_name': user.business_name or 'Not provided',
        'custom_message': message,
        'sender_name': sender_name
    }
    
    return send_email_with_gmail_api(
        recipient_email=user.email,
        subject=subject,
        body=message,
        template_type='custom',
        context=context
    )

# Public landing page
def home(request):
    return render(request, 'main/home.html')

# Calculator page view
def calculator(request):
    return render(request, 'main/calculator.html')

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
    """
    Enhanced signup view with proper form handling and field mapping
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the user (form handles all field mapping)
                    user = form.save()
                    
                    # Create user submission status
                    UserSubmissionStatus.objects.create(user=user)
                    
                    # Auto-login the user
                    login(request, user)
                    
                    # Success message
                    display_name = user.get_full_name() or user.username
                    messages.success(
                        request, 
                        f'Welcome to Fuel Refund Institute, {display_name}! Your account has been created successfully.'
                    )
                    
                    return redirect('dashboard')
                    
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        # Let Django form handle its own validation errors - no generic message needed
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'main/signup.html', {'form': form})

# Enhanced Login view that forces re-authentication
def login_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Please log in again for security.")
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Basic validation
        if not username or not password:
            messages.warning(request, "Please enter both username and password.")
        else:
            # Try to authenticate
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Login the user
                    login(request, user)
                    
                    display_name = user.get_full_name() or user.username
                    messages.success(request, f"Welcome back, {display_name}!")
                    
                    # Check if user is admin (superuser or staff) for dashboard access
                    if user.is_superuser or user.is_staff:
                        next_page = request.GET.get('next', 'admin_dashboard')
                    else:
                        # Regular users go to their profile/home page
                        next_page = request.GET.get('next', 'home')
                    
                    return redirect(next_page)
                else:
                    messages.error(request, "Your account has been disabled. Please contact support.")
            else:
                # Wrong credentials - show error
                messages.error(request, "Invalid username or password. Please try again.")
        
        # Create form with submitted data for display
        form = AuthenticationForm(request, data=request.POST)
    else:
        form = AuthenticationForm()
    
    return render(request, 'main/login.html', {
        'form': form
    })


# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# Updated dashboard with unlimited uploads and document categories
@login_required
def dashboard(request):
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
    Send beautiful anti-spam reminder email to user with incomplete documents.
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
        
        if has_fuel_statements and has_asset_registers:
            messages.info(request, f"User '{username}' has already submitted all required documents.")
            return redirect('admin_dashboard')
        
        # Use the beautiful anti-spam template function
        success, message = send_reminder_email_with_template(user)
        
        if success:
            messages.success(request, f"✅ Professional reminder email sent to {user.email}")
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
    Send beautiful anti-spam custom email to a user.
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
        
        sender_name = request.user.get_full_name() or request.user.username
        
        print(f"📧 Sending professional custom email to {user.email}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Message length: {len(message)} characters")
        
        # Use the beautiful anti-spam template function
        success, result_message = send_custom_email_with_template(user, subject, message, sender_name)
        
        print(f"📧 Email send result: {success}, Message: {result_message}")
        
        if success:
            return JsonResponse({'success': True, 'message': f'Professional email sent successfully to {user.email}'})
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
    Simple Control Panel Analytics dashboard with live client data.
    Only accessible by superusers.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    import calendar
    
    # Get current date for calculations
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    
    # Basic user statistics
    all_users = get_user_model().objects.filter(is_superuser=False)
    total_users = all_users.count()
    
    # New users this month
    new_users_this_month = all_users.filter(
        date_joined__year=current_year,
        date_joined__month=current_month
    ).count()
    
    # New users this week
    week_ago = now - timedelta(days=7)
    new_users_this_week = all_users.filter(date_joined__gte=week_ago).count()
    
    # Document statistics
    all_documents = UserDocument.objects.all()
    total_documents = all_documents.count()
    
    # Documents uploaded this week
    documents_this_week = all_documents.filter(uploaded_at__gte=week_ago).count()
    
    # User completion statistics
    users_with_fuel = all_users.filter(
        documents__document_type='fuel_statement'
    ).distinct().count()
    
    users_with_assets = all_users.filter(
        documents__document_type='asset_register'
    ).distinct().count()
    
    # Users who have both required documents (completed)
    users_complete = all_users.filter(
        documents__document_type='fuel_statement'
    ).filter(
        documents__document_type='asset_register'
    ).distinct().count()
    
    # Users with partial completion
    users_with_partial = all_users.filter(
        Q(documents__document_type='fuel_statement') | 
        Q(documents__document_type='asset_register')
    ).distinct().count() - users_complete
    
    # Users who haven't started
    users_incomplete = total_users - users_with_partial - users_complete
    
    # Completion rate
    completion_rate = round((users_complete / total_users * 100), 1) if total_users > 0 else 0
    
    # Monthly registration data for chart
    monthly_registrations = []
    for month in range(1, 13):
        month_count = all_users.filter(
            date_joined__year=current_year,
            date_joined__month=month
        ).count()
        monthly_registrations.append(month_count)
    
    # Business type distribution
    business_type_data = all_users.values('business_type').annotate(
        count=Count('business_type')
    ).order_by('-count')
    
    # Format business type data for display
    formatted_business_types = []
    business_type_mapping = {
        'llc': 'Limited Liability Company (LLC)',
        'corporation': 'Corporation', 
        'sole_proprietorship': 'Sole Proprietorship',
        'partnership': 'Partnership',
        's_corp': 'S Corporation',
        'c_corp': 'C Corporation',
        'nonprofit': 'Nonprofit Organization',
        'other': 'Other Business Type',
        '': 'Not Specified'
    }
    
    for item in business_type_data:
        business_type = item['business_type'] or ''
        label = business_type_mapping.get(business_type, business_type.title() if business_type else 'Not Specified')
        formatted_business_types.append((label, item['count']))
    
    # Geographic distribution (by state) - Top 10
    state_data = all_users.values('state').annotate(
        count=Count('state')
    ).exclude(state='').order_by('-count')[:10]
    
    # Also include "Not Specified" states
    unspecified_states = all_users.filter(state='').count()
    if unspecified_states > 0:
        state_data = list(state_data)
        state_data.append({'state': '', 'count': unspecified_states})
    
    # Daily upload activity for the last 30 days
    daily_uploads = []
    upload_dates = []
    
    for i in range(30):
        date = (now - timedelta(days=29-i)).date()
        upload_dates.append(date)
        daily_count = all_documents.filter(uploaded_at__date=date).count()
        daily_uploads.append(daily_count)
    
    # Document type breakdown
    doc_type_stats = {
        'fuel_statement': all_documents.filter(document_type='fuel_statement').count(),
        'asset_register': all_documents.filter(document_type='asset_register').count(),
        'other': all_documents.filter(document_type='other').count(),
    }
    
    # Recent user activity
    recent_users = all_users.filter(date_joined__gte=week_ago).order_by('-date_joined')[:5]
    
    # Recent document uploads
    recent_documents = all_documents.filter(uploaded_at__gte=week_ago).order_by('-uploaded_at')[:10]
    
    context = {
        # Basic stats
        'total_users': total_users,
        'new_users_this_month': new_users_this_month,
        'new_users_this_week': new_users_this_week,
        'total_documents': total_documents,
        'documents_this_week': documents_this_week,
        'users_complete': users_complete,
        'users_with_partial': users_with_partial,
        'users_incomplete': users_incomplete,
        'completion_rate': completion_rate,
        'users_with_fuel': users_with_fuel,
        'users_with_assets': users_with_assets,
        
        # Chart data
        'monthly_registrations': ','.join(map(str, monthly_registrations)),
        'daily_uploads': ','.join(map(str, daily_uploads)),
        'upload_dates': upload_dates,
        
        # Business and geographic data
        'business_type_data': formatted_business_types,
        'top_states': state_data,
        
        # Additional stats
        'doc_type_stats': doc_type_stats,
        'recent_users': recent_users,
        'recent_documents': recent_documents,
        
        # Current period info
        'current_month': calendar.month_name[current_month],
        'current_year': current_year,
        
        # System status
        'system_status': 'ONLINE',
        'last_updated': now.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'main/analytics_dashboard.html', context)

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


def faw(request):
    """Render the FAW (replacement for About) page."""
    return render(request, 'main/faw.html')


def faq(request):
    """Render the FAQ page."""
    return render(request, 'main/faq.html')

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
    """Handle OAuth callback from Google - Production Ready"""
    try:
        # Get authorization code from callback
        code = request.GET.get('code')
        if not code:
            messages.error(request, "No authorization code received")
            return redirect('admin_dashboard')
        
        # Exchange code for credentials
        flow = Flow.from_client_secrets_file(GMAIL_CLIENT_SECRETS_FILE, GMAIL_SCOPES)
        
        # PRODUCTION FIX: Dynamic redirect URI
        if settings.DEBUG:
            flow.redirect_uri = 'http://localhost:8000/oauth/callback/'
        else:
            # Production domain
            flow.redirect_uri = 'https://fuelrefundinstitute.com/oauth/callback/'
            
        flow.fetch_token(code=code)
        
        # Save credentials
        creds = flow.credentials
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        messages.success(request, "🎉 Gmail API authorization successful! Production anti-spam email functionality is now active.")
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