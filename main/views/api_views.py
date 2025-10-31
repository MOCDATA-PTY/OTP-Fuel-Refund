from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

import os
import json
import mimetypes
import logging
import base64
import time
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("⚠️ Gmail API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

from ..models import UserDocument

# Setup enhanced logging
logger = logging.getLogger(__name__)

# Gmail API Configuration
GMAIL_CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, 'gmail_credentials.json')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GMAIL_TOKEN_FILE = os.path.join(settings.BASE_DIR, 'gmail_token.json')

def get_enhanced_gmail_service():
    """Enhanced Gmail API service with better error handling for corporate emails"""
    if not GMAIL_AVAILABLE:
        return None, "Gmail API libraries not installed"
    
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
                    print("✅ Gmail credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    print(f"❌ Token refresh failed: {e}")
                    return None, f"Token refresh failed: {e}"
            else:
                # First time setup
                if not os.path.exists(GMAIL_CLIENT_SECRETS_FILE):
                    error_msg = f"Gmail credentials file not found: {GMAIL_CLIENT_SECRETS_FILE}"
                    print(f"❌ {error_msg}")
                    return None, error_msg
                
                flow = Flow.from_client_secrets_file(GMAIL_CLIENT_SECRETS_FILE, GMAIL_SCOPES)
                
                # Dynamic redirect URI
                if settings.DEBUG:
                    flow.redirect_uri = 'http://localhost:8000/oauth/callback/'
                else:
                    flow.redirect_uri = 'https://fuelrefundinstitute.com/oauth/callback/'
                
                auth_url, _ = flow.authorization_url(prompt='consent')
                error_msg = f"Authorization required. Visit: {auth_url}"
                print(f"🔗 {error_msg}")
                return None, error_msg
                
            # Save credentials
            if creds:
                with open(GMAIL_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
        
        # Build service
        service = build('gmail', 'v1', credentials=creds)
        return service, "Gmail service ready"
        
    except Exception as e:
        error_msg = f"Gmail service setup error: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return None, error_msg

def create_improved_corporate_email_template(template_type, context):
    """Improved email template optimized for deliverability and avoiding spam filters"""
    
    # Build email content based on type
    if template_type == 'reminder':
        content = f"""
        <tr>
            <td style="padding: 25px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #2c3e50;">
                <p style="margin: 0 0 20px 0;">Hello {context['user_name']},</p>
                
                <p style="margin: 0 0 20px 0;">
                    This is a status update regarding your tax documentation submitted to our office. 
                    Our records indicate additional items are needed to complete your file.
                </p>
                
                <table width="100%" cellpadding="15" cellspacing="0" style="background-color: #f8f9fa; border-left: 4px solid #28a745; margin: 20px 0;">
                    <tr>
                        <td style="font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50;">
                            <strong style="color: #28a745;">Required Documentation Status</strong><br><br>
                            {context['requirements_html']}
                        </td>
                    </tr>
                </table>
                
                <p style="margin: 0 0 15px 0;">Please submit the following at your earliest convenience:</p>
                <ul style="margin: 0 0 20px 20px; padding: 0;">
                    <li style="margin-bottom: 5px;">Log into your client portal</li>
                    <li style="margin-bottom: 5px;">Upload any missing documentation</li>
                    <li style="margin-bottom: 5px;">Review your application status</li>
                </ul>
                
                <table width="100%" cellpadding="12" cellspacing="0" style="background-color: #e9ecef; margin: 20px 0; border: 1px solid #dee2e6;">
                    <tr>
                        <td style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #495057;">
                            <strong>Client Reference Information</strong><br>
                            Account: {context['username']}<br>
                            Email: {context['email']}<br>
                            Business: {context['business_name']}
                        </td>
                    </tr>
                </table>
                
                <p style="margin: 0 0 20px 0;">
                    If you have questions, please contact our office during business hours at (424) 222-5290.
                </p>
                
                <p style="margin: 0 0 5px 0;">Regards,</p>
                <p style="margin: 0 0 5px 0;"><strong>Client Services</strong></p>
                <p style="margin: 0;">Fuel Refund Institute</p>
            </td>
        </tr>
        """
    
    elif template_type == 'custom':
        content = f"""
        <tr>
            <td style="padding: 25px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #2c3e50;">
                <p style="margin: 0 0 20px 0;">Hello {context['user_name']},</p>
                
                <div style="margin: 20px 0; color: #2c3e50; line-height: 1.6;">
                    {context['custom_message']}
                </div>
                
                <table width="100%" cellpadding="12" cellspacing="0" style="background-color: #e9ecef; margin: 20px 0; border: 1px solid #dee2e6;">
                    <tr>
                        <td style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #495057;">
                            <strong>Client Information</strong><br>
                            Account: {context['username']}<br>
                            Email: {context['email']}<br>
                            Business: {context['business_name']}
                        </td>
                    </tr>
                </table>
                
                <p style="margin: 0 0 20px 0;">
                    Please contact our office if you need assistance: (424) 222-5290
                </p>
                
                <p style="margin: 0 0 5px 0;">Best regards,</p>
                <p style="margin: 0 0 5px 0;"><strong>{context['sender_name']}</strong></p>
                <p style="margin: 0;">Fuel Refund Institute</p>
            </td>
        </tr>
        """
    
    elif template_type == 'test':
        content = f"""
        <tr>
            <td style="padding: 25px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #2c3e50;">
                <p style="margin: 0 0 20px 0;">Hello,</p>
                
                <p style="margin: 0 0 20px 0;">
                    This is a system verification message from our office to confirm email delivery functionality.
                </p>
                
                <table width="100%" cellpadding="15" cellspacing="0" style="background-color: #f8f9fa; border-left: 4px solid #28a745; margin: 20px 0;">
                    <tr>
                        <td style="font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50;">
                            <strong>System Verification</strong><br><br>
                            Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                            Recipient: {context.get('email', 'Test Recipient')}<br>
                            Status: Email System Operational
                        </td>
                    </tr>
                </table>
                
                <p style="margin: 0 0 20px 0;">
                    If you receive this message, our communication system is functioning correctly.
                </p>
                
                <p style="margin: 0 0 5px 0;">Thank you,</p>
                <p style="margin: 0 0 5px 0;"><strong>Technical Services</strong></p>
                <p style="margin: 0;">Fuel Refund Institute</p>
            </td>
        </tr>
        """
    
    # Simplified, clean HTML structure optimized for deliverability
    html_email = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context.get('subject', 'Client Communication')}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border: 1px solid #dee2e6;">
                    
                    <!-- Simple Header -->
                    <tr>
                        <td style="background-color: #28a745; padding: 20px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 18px; font-weight: 600;">
                                FUEL REFUND INSTITUTE
                            </h1>
                            <p style="margin: 5px 0 0 0; color: #ffffff; font-size: 12px;">
                                Tax Services
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    {content}
                    
                    <!-- Simple Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                            <p style="margin: 0; font-size: 11px; color: #6c757d;">
                                Fuel Refund Institute<br>
                                12901 Simms Ave, Hawthorne, CA 90250<br>
                                Phone: (424) 222-5290 | Email: fuelrefundinstitute@gmail.com
                            </p>
                            <p style="margin: 10px 0 0 0; font-size: 10px; color: #6c757d;">
                                This email was sent to a registered client. 
                                <a href="mailto:fuelrefundinstitute@gmail.com" style="color: #28a745;">Contact us</a> with questions.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
    
    return html_email

def send_email_with_proper_headers(service, to_email, subject, html_content, sender_name="Client Services"):
    """Send email with proper headers for better deliverability"""
    try:
        # Create message with proper headers
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f'Fuel Refund Institute <fuelrefundinstitute@gmail.com>'
        message['To'] = to_email
        message['Reply-To'] = 'fuelrefundinstitute@gmail.com'
        
        # Add authentication and deliverability headers
        message['List-Unsubscribe'] = '<mailto:fuelrefundinstitute@gmail.com?subject=unsubscribe>'
        message['X-Mailer'] = 'Fuel Refund Institute Client Portal'
        message['Organization'] = 'Fuel Refund Institute'
        message['X-Priority'] = '3'  # Normal priority
        message['X-MSMail-Priority'] = 'Normal'
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send email
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True, f"Email sent successfully. Message ID: {result.get('id')}"
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return False, f"Gmail API error: {error}"
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return False, f"Email sending error: {e}"

# API: Get user details with document categorization
@login_required
def user_details_api(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = get_user_model().objects.get(id=user_id)
        documents = UserDocument.objects.filter(user=user)
        
        # Group documents by type
        fuel_statements = documents.filter(document_type='fuel_statement')
        asset_registers = documents.filter(document_type='asset_register')
        other_documents = documents.filter(document_type='other')
        
        # Prepare user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'middle_names': user.middle_names,
            'surname': user.surname,
            'email': user.email,
            'phone_number': user.phone_number,
            'ssn': user.ssn,
            'business_name': user.business_name,
            'business_type': user.business_type,
            'tax_id': user.tax_id,
            'business_address': user.business_address,
            'city': getattr(user, 'city', ''),
            'state': getattr(user, 'state', ''),
            'zip_code': getattr(user, 'zip_code', ''),
            'total_documents': documents.count(),
            'has_fuel_statements': fuel_statements.exists(),
            'has_asset_register': asset_registers.exists(),
            'requirements_met': fuel_statements.exists() and asset_registers.exists(),
            'document_counts': {
                'fuel_statements': fuel_statements.count(),
                'asset_registers': asset_registers.count(),
                'other_documents': other_documents.count(),
            },
            'documents': [
                {
                    'id': doc.id,
                    'name': os.path.basename(doc.document.name),
                    'document_type': doc.document_type,
                    'document_type_display': doc.get_document_type_display(),
                    'description': doc.description,
                    'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                } for doc in documents
            ]
        }
        
        return JsonResponse(user_data)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# API: Get user details by username with document categorization
@login_required
def user_details_by_username_api(request, username):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = get_user_model().objects.get(username=username)
        documents = UserDocument.objects.filter(user=user)
        
        # Group documents by type
        fuel_statements = documents.filter(document_type='fuel_statement')
        asset_registers = documents.filter(document_type='asset_register')
        other_documents = documents.filter(document_type='other')
        
        # Prepare user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'middle_names': user.middle_names,
            'surname': user.surname,
            'email': user.email,
            'phone_number': user.phone_number,
            'ssn': user.ssn,
            'business_name': user.business_name,
            'business_type': user.business_type,
            'tax_id': user.tax_id,
            'business_address': user.business_address,
            'city': getattr(user, 'city', ''),
            'state': getattr(user, 'state', ''),
            'zip_code': getattr(user, 'zip_code', ''),
            'total_documents': documents.count(),
            'has_fuel_statements': fuel_statements.exists(),
            'has_asset_register': asset_registers.exists(),
            'requirements_met': fuel_statements.exists() and asset_registers.exists(),
            'document_counts': {
                'fuel_statements': fuel_statements.count(),
                'asset_registers': asset_registers.count(),
                'other_documents': other_documents.count(),
            },
            'documents': [
                {
                    'id': doc.id,
                    'name': os.path.basename(doc.document.name),
                    'document_type': doc.document_type,
                    'document_type_display': doc.get_document_type_display(),
                    'description': doc.description,
                    'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                } for doc in documents
            ]
        }
        
        return JsonResponse(user_data)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# API: Update user with new fields
@login_required
@require_POST
def user_update_api(request, username):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = get_user_model().objects.get(username=username)
        
        # Get data from request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Update user fields
        if 'name' in data:
            user.name = data['name']
        if 'middle_names' in data:
            user.middle_names = data['middle_names']
        if 'surname' in data:
            user.surname = data['surname']
        if 'email' in data:
            user.email = data['email']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'ssn' in data:
            user.ssn = data['ssn']
        if 'business_name' in data:
            user.business_name = data['business_name']
        if 'business_type' in data:
            user.business_type = data['business_type']
        if 'tax_id' in data:
            user.tax_id = data['tax_id']
        if 'business_address' in data:
            user.business_address = data['business_address']
        if 'city' in data:
            user.city = data['city']
        if 'state' in data:
            user.state = data['state']
        if 'zip_code' in data:
            user.zip_code = data['zip_code']
        
        # Save the user
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'User updated successfully'
        })
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# API: Delete user
@login_required
@require_POST
def user_delete_api(request, username):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = get_user_model().objects.get(username=username)
        
        # Don't allow deleting yourself
        if user == request.user:
            return JsonResponse({'error': 'Cannot delete your own account'}, status=400)
        
        # Delete user
        user.delete()
        return JsonResponse({'status': 'success'})
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# API: Send reminder email with improved deliverability
@login_required
@require_POST 
def send_reminder_email_api(request, username):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = get_user_model().objects.get(username=username)
        
        if not user.email:
            return JsonResponse({'error': 'User has no email address'}, status=400)
        
        # Get Gmail service
        service, error_msg = get_enhanced_gmail_service()
        if not service:
            return JsonResponse({'error': f'Gmail service error: {error_msg}'}, status=500)
        
        # Check what documents are missing
        documents = UserDocument.objects.filter(user=user)
        fuel_statements = documents.filter(document_type='fuel_statement')
        asset_registers = documents.filter(document_type='asset_register')
        
        missing_items = []
        if not fuel_statements.exists():
            missing_items.append("• Fuel statements or receipts")
        if not asset_registers.exists():
            missing_items.append("• Asset register or equipment list")
        
        requirements_html = "<br>".join(missing_items) if missing_items else "All required documents submitted"
        
        # Prepare context for email template
        context = {
            'user_name': user.get_full_name() or user.username,
            'username': user.username,
            'email': user.email,
            'business_name': user.business_name or 'N/A',
            'requirements_html': requirements_html,
            'subject': 'Document Request - Client Account Update'
        }
        
        # Generate improved email template
        html_content = create_improved_corporate_email_template('reminder', context)
        
        # Administrative subject line (avoiding promotional language)
        subject = 'Document Request - Client Account Update'
        
        # Send email with proper headers
        success, message = send_email_with_proper_headers(service, user.email, subject, html_content)
        
        if success:
            logger.info(f"Reminder email sent successfully to {user.email}")
            return JsonResponse({
                'status': 'success',
                'message': f'Reminder email sent to {user.email}'
            })
        else:
            logger.error(f"Failed to send reminder email to {user.email}: {message}")
            return JsonResponse({'error': message}, status=500)
            
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error sending reminder email: {e}")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

# API: Send custom email with improved deliverability
@login_required
@require_POST
def send_custom_email_api(request, username):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = get_user_model().objects.get(username=username)
        
        if not user.email:
            return JsonResponse({'error': 'User has no email address'}, status=400)
        
        # Get form data
        subject = request.POST.get('subject', '').strip()
        custom_message = request.POST.get('message', '').strip()
        
        if not subject or not custom_message:
            return JsonResponse({'error': 'Subject and message are required'}, status=400)
        
        # Get Gmail service
        service, error_msg = get_enhanced_gmail_service()
        if not service:
            return JsonResponse({'error': f'Gmail service error: {error_msg}'}, status=500)
        
        # Prepare context for email template
        context = {
            'user_name': user.get_full_name() or user.username,
            'username': user.username,
            'email': user.email,
            'business_name': user.business_name or 'N/A',
            'custom_message': custom_message,
            'sender_name': request.user.get_full_name() or 'Client Services',
            'subject': subject
        }
        
        # Generate improved email template
        html_content = create_improved_corporate_email_template('custom', context)
        
        # Send email with proper headers
        success, message = send_email_with_proper_headers(
            service, 
            user.email, 
            subject, 
            html_content, 
            context['sender_name']
        )
        
        if success:
            logger.info(f"Custom email sent successfully to {user.email}")
            return JsonResponse({
                'status': 'success',
                'message': f'Email sent successfully to {user.email}'
            })
        else:
            logger.error(f"Failed to send custom email to {user.email}: {message}")
            return JsonResponse({'error': message}, status=500)
            
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error sending custom email: {e}")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

# API: Get user documents filtered by date with document types
@login_required
def user_documents_by_date_api(request, user_id):
    """
    API endpoint to get user documents filtered by date range with document categorization
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    # Get date range and document type from query parameters
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    document_type = request.GET.get('document_type')
        
    try:
        user = get_user_model().objects.get(id=user_id)
        documents = UserDocument.objects.filter(user=user)
        
        # Apply date filtering if provided
        if from_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            documents = documents.filter(uploaded_at__date__gte=from_date)
        
        if to_date:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            # Add 1 day to include the entire 'to_date'
            to_date = to_date + timedelta(days=1)
            documents = documents.filter(uploaded_at__date__lt=to_date)
        
        # Apply document type filtering if provided
        if document_type:
            documents = documents.filter(document_type=document_type)
        
        # Prepare document data
        document_data = [
            {
                'id': doc.id,
                'name': os.path.basename(doc.document.name),
                'document_type': doc.document_type,
                'document_type_display': doc.get_document_type_display(),
                'description': doc.description,
                'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
            } for doc in documents
        ]
        
        return JsonResponse({
            'user_id': user.id,
            'username': user.username,
            'documents': document_data,
            'has_documents_in_range': len(document_data) > 0,
            'filters_applied': {
                'from_date': from_date.strftime('%Y-%m-%d') if from_date else None,
                'to_date': to_date.strftime('%Y-%m-%d') if to_date else None,
                'document_type': document_type
            }
        })
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

# API: Download document by ID
@login_required
def download_document_api(request, doc_id):
    """
    API endpoint to download a specific document by ID
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        # Get file path
        file_path = document.document.path
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise Http404("Document file not found")
        
        # Get file content type
        content_type, encoding = mimetypes.guess_type(file_path)
        
        # Default to application/octet-stream if type not determined
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create response
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        
        # Set content disposition to attachment for download
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except UserDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error downloading document: {str(e)}'}, status=500)

# API: Get document type statistics
@login_required
def document_statistics_api(request):
    """
    API endpoint to get document statistics across all users
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get all documents grouped by type
        fuel_statements = UserDocument.objects.filter(document_type='fuel_statement')
        asset_registers = UserDocument.objects.filter(document_type='asset_register')
        other_documents = UserDocument.objects.filter(document_type='other')
        
        # Get users with complete requirements
        all_users = get_user_model().objects.all()
        users_with_fuel = set(fuel_statements.values_list('user_id', flat=True))
        users_with_assets = set(asset_registers.values_list('user_id', flat=True))
        users_complete = users_with_fuel.intersection(users_with_assets)
        
        statistics = {
            'total_documents': UserDocument.objects.count(),
            'total_users': all_users.count(),
            'document_types': {
                'fuel_statements': fuel_statements.count(),
                'asset_registers': asset_registers.count(),
                'other_documents': other_documents.count(),
            },
            'user_completion': {
                'users_with_fuel_statements': len(users_with_fuel),
                'users_with_asset_register': len(users_with_assets),
                'users_with_complete_requirements': len(users_complete),
                'completion_percentage': round((len(users_complete) / max(all_users.count(), 1)) * 100, 2)
            }
        }
        
        return JsonResponse(statistics)
    except Exception as e:
        return JsonResponse({'error': f'Error generating statistics: {str(e)}'}, status=500)

# API: Download Privacy Policy document
@login_required 
def download_privacy_policy_api(request):
    """
    API endpoint to download the Privacy Policy document
    """
    try:
        # Import Django settings
        from django.conf import settings
        
        # Path to the privacy policy document in static files
        file_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Privacy Policy.docx')
        
        # Check if file exists
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'Privacy Policy document not found'}, status=404)
        
        # Get file content type
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # Create response
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        
        # Set content disposition to attachment for download
        response['Content-Disposition'] = 'attachment; filename="Privacy Policy.docx"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Error downloading Privacy Policy: {str(e)}'}, status=500)

# API: Download Terms and Conditions document  
@login_required
def download_terms_conditions_api(request):
    """
    API endpoint to download the Terms and Conditions document
    """
    try:
        # Import Django settings
        from django.conf import settings
        
        # Path to the terms and conditions document in static files
        file_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Terms and Conditions.docx')
        
        # Check if file exists
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'Terms and Conditions document not found'}, status=404)
        
        # Get file content type
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # Create response
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        
        # Set content disposition to attachment for download
        response['Content-Disposition'] = 'attachment; filename="Terms and Conditions.docx"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Error downloading Terms and Conditions: {str(e)}'}, status=500)