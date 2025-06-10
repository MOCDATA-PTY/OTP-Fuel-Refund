from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404, FileResponse
from django.template import Library
from django.conf import settings

import os
import zipfile
import tempfile
import mimetypes

from ..models import CustomUser, UserDocument
from ..forms import CustomUserCreationForm, DocumentUploadForm

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

# Public landing page
def home(request):
    return render(request, 'main/home.html')

# Contact page view
def contact(request):
    """
    View function for the contact page
    """
    if request.method == 'POST':
        # Handle form submission here if you have a contact form
        # For example:
        # name = request.POST.get('name')
        # email = request.POST.get('email')
        # message = request.POST.get('message')
        # 
        # # Process contact form data
        # # ...
        
        messages.success(request, "Your message has been sent. We'll get back to you soon.")
        return redirect('contact')
        
    return render(request, 'main/contact.html')

# Signup view
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome {user.get_full_name() or user.username}! Your account has been created successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'main/signup.html', {'form': form})

# Login view - COMPLETELY FIXED VERSION
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Create a clean form for rendering
    form = AuthenticationForm()
        
    if request.method == 'POST':
        # Check credentials manually to avoid form errors
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('dashboard')
        else:
            # Only show our custom error message
            messages.error(request, "Invalid username or password.")
        
    return render(request, 'main/login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# Updated dashboard with unlimited uploads and document categories
@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
        
    documents = UserDocument.objects.filter(user=request.user)
    form = DocumentUploadForm()
        
    # Add display_name to each document (just the filename without the path)
    for doc in documents:
        doc.display_name = os.path.basename(doc.document.name)
        
    if request.method == 'POST':
        # Handle file upload manually since we're not using Django's FileField
        files = request.FILES.getlist('document')  # Get multiple files
        document_type = request.POST.get('document_type', '')
        description = request.POST.get('description', '')
        
        # Validation
        if not files:
            messages.warning(request, "Please select at least one file to upload.")
        elif not document_type:
            messages.warning(request, "Please select a document type.")
        else:
            # File validation
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.txt', '.xls', '.xlsx']
            max_file_size = 10 * 1024 * 1024  # 10MB
            
            valid_files = []
            errors = []
            
            for file in files:
                # Check file extension
                file_name = file.name.lower()
                file_ext = None
                
                for ext in allowed_extensions:
                    if file_name.endswith(ext):
                        file_ext = ext
                        break
                
                if not file_ext:
                    errors.append(f"'{file.name}' has an unsupported format. Allowed: PDF, Word, Images, Text, Excel files.")
                    continue
                
                # Check file size
                if file.size > max_file_size:
                    file_size_mb = file.size / (1024 * 1024)
                    errors.append(f"'{file.name}' is too large ({file_size_mb:.1f}MB). Maximum size is 10MB.")
                    continue
                
                valid_files.append(file)
            
            # Show errors if any
            if errors:
                for error in errors:
                    messages.error(request, error)
            
            # Upload valid files
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
                    # Get readable document type name
                    doc_type_choices = dict(DocumentUploadForm.DOCUMENT_TYPE_CHOICES)
                    doc_type_display = doc_type_choices.get(document_type, 'document(s)')
                    
                    if files_uploaded == 1:
                        messages.success(request, f"Successfully uploaded 1 {doc_type_display.lower()}.")
                    else:
                        messages.success(request, f"Successfully uploaded {files_uploaded} {doc_type_display.lower()}.")
                    
                    # If no errors occurred with valid files, also mention any rejected files
                    if errors and valid_files:
                        rejected_count = len(files) - files_uploaded
                        if rejected_count > 0:
                            messages.warning(request, f"Note: {rejected_count} file(s) were rejected due to validation errors.")
                    
        return redirect('dashboard')
    
    # Group documents by type for better organization
    fuel_statements = documents.filter(document_type='fuel_statement')
    asset_registers = documents.filter(document_type='asset_register')
    other_documents = documents.filter(document_type='other')
    
    # Check if required document types are present
    has_fuel_statements = fuel_statements.exists()
    has_asset_register = asset_registers.exists()
    
    # Calculate completion status
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

# Enhanced admin dashboard to see all users & docs with new categorization
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    all_users = get_user_model().objects.all().order_by('username')
        
    # Create dictionaries with document counts and document lists
    user_docs = {}
    user_doc_counts = {}
    user_fuel_statements = {}
    user_asset_registers = {}
    user_requirements_met = {}
        
    for user in all_users:
        docs = UserDocument.objects.filter(user=user)
        fuel_statements = docs.filter(document_type='fuel_statement')
        asset_registers = docs.filter(document_type='asset_register')
        
        user_docs[user.id] = docs  # Store by ID to make it easier to access
        user_doc_counts[user.id] = docs.count()  # Store the count
        user_fuel_statements[user.id] = fuel_statements.exists()
        user_asset_registers[user.id] = asset_registers.exists()
        user_requirements_met[user.id] = fuel_statements.exists() and asset_registers.exists()
        
        # Add display name to each document
        for doc in docs:
            doc.display_name = os.path.basename(doc.document.name)
        
    return render(request, 'main/admin_dashboard.html', {
        'all_users': all_users,
        'user_docs': user_docs,
        'user_doc_counts': user_doc_counts,
        'user_fuel_statements': user_fuel_statements,
        'user_asset_registers': user_asset_registers,
        'user_requirements_met': user_requirements_met,
    })

# Download document
@login_required
def download_document(request, doc_id):
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        # Check permissions
        if not request.user.is_superuser and document.user != request.user:
            raise Http404("Document not found")
        
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
        raise Http404("Document not found")
    except Exception as e:
        raise Http404(f"Error downloading document: {str(e)}")

# Enhanced download all documents as ZIP with organized folders
@login_required
def download_all_documents(request, user_id):
    try:
        user = get_user_model().objects.get(id=user_id)
        
        # Check permissions
        if not request.user.is_superuser and user != request.user:
            raise Http404("User not found")
        
        documents = UserDocument.objects.filter(user=user)
        
        if not documents:
            messages.warning(request, "No documents found to download.")
            return redirect('admin_dashboard' if request.user.is_superuser else 'dashboard')
        
        # Create a zip file in memory
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for document in documents:
                file_path = document.document.path
                
                if os.path.exists(file_path):
                    # Create organized folder structure in ZIP
                    doc_type = document.get_document_type_display() if hasattr(document, 'document_type') else 'Other'
                    folder_name = doc_type.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
                    zip_path = f"{folder_name}/{os.path.basename(file_path)}"
                    
                    # Add file to zip with organized path
                    zip_file.write(file_path, zip_path)
        
        temp_file.close()
        
        # Prepare the response with the zip file
        with open(temp_file.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{user.username}_documents.zip"'
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
        
        return response
    except get_user_model().DoesNotExist:
        raise Http404("User not found")
    except Exception as e:
        raise Http404(f"Error creating ZIP file: {str(e)}")

# User edit view
@login_required
def edit_user(request, username):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    try:
        user = get_user_model().objects.get(username=username)
        
        if request.method == 'POST':
            # Handle form submission
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

# Enhanced delete document view with document type information
@login_required
def delete_document(request, doc_id):
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        # Check permissions
        if document.user != request.user and not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete this document.")
            return redirect('dashboard')
        
        # Get document name and type before deletion for the success message
        document_name = os.path.basename(document.document.name)
        document_type = document.get_document_type_display() if hasattr(document, 'document_type') else 'document'
        
        # Delete the document file from filesystem
        try:
            if os.path.exists(document.document.path):
                os.remove(document.document.path)
        except Exception as e:
            # Log the error but don't fail the deletion
            print(f"Error deleting file {document.document.path}: {e}")
        
        # Delete the document record
        document.delete()
        
        messages.success(request, f"{document_type} '{document_name}' has been deleted successfully.")
        return redirect('admin_dashboard' if request.user.is_superuser else 'dashboard')
    except UserDocument.DoesNotExist:
        messages.error(request, "Document not found.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Error deleting document: {str(e)}")
        return redirect('dashboard')

# Download Privacy Policy document
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

# Download Terms and Conditions document
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

# Import API views for URL routing
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

def terms_of_service(request):
    return render(request, 'main/terms_of_service.html')

def privacy_policy(request):
    return render(request, 'main/privacy_policy.html')