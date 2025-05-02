from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponse, Http404, FileResponse
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from django.conf import settings
from django.template import Library

import os
import json
import zipfile
import tempfile
import mimetypes
from datetime import datetime, timedelta
from wsgiref.util import FileWrapper

from .models import CustomUser, UserDocument
from .forms import CustomUserCreationForm, DocumentUploadForm

# Create a register object
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
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'main/signup.html', {'form': form})

# Login view
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'main/login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# Regular user dashboard
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
        current_count = documents.count()
        files = request.FILES.getlist('document')
        
        # Check if adding these files would exceed the limit
        if current_count + len(files) > 7:
            messages.warning(request, f"You can only upload a maximum of 7 documents. You have {current_count} already.")
        else:
            description = request.POST.get('description', '')
            
            # Process each file
            files_uploaded = 0
            for file in files:
                new_doc = UserDocument(
                    user=request.user,
                    document=file,
                    description=description
                )
                new_doc.save()
                files_uploaded += 1
            
            # Update the count after uploads
            updated_count = UserDocument.objects.filter(user=request.user).count()
            
            if files_uploaded > 0:
                if updated_count == 7:
                    messages.success(request, f"Uploaded {files_uploaded} document(s). All required documents have been submitted. Our team will begin processing your refund claim.")
                else:
                    messages.success(request, f"Successfully uploaded {files_uploaded} document(s). You have {updated_count} of 7 required documents.")
            
            return redirect('dashboard')
    
    # Check if all documents are uploaded to show completion message in template
    documents_complete = (documents.count() == 7)
    documents_remaining = 7 - documents.count()
    
    return render(request, 'main/dashboard.html', {
        'user': request.user,
        'form': form,
        'documents': documents,
        'documents_complete': documents_complete,
        'documents_remaining': documents_remaining,
    })

# Admin dashboard to see all users & docs
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    all_users = get_user_model().objects.all().order_by('username')
    
    # Create dictionaries with document counts and document lists
    user_docs = {}
    user_doc_counts = {}
    
    for user in all_users:
        docs = UserDocument.objects.filter(user=user)
        user_docs[user.id] = docs  # Store by ID to make it easier to access
        user_doc_counts[user.id] = docs.count()  # Store the count
        
        # Add display name to each document
        for doc in docs:
            doc.display_name = os.path.basename(doc.document.name)
    
    return render(request, 'main/admin_dashboard.html', {
        'all_users': all_users,
        'user_docs': user_docs,
        'user_doc_counts': user_doc_counts
    })

# API: Get user details
@login_required
def user_details_api(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        user = get_user_model().objects.get(id=user_id)
        documents = UserDocument.objects.filter(user=user)
        
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
            'documents': [
                {
                    'id': doc.id,
                    'name': os.path.basename(doc.document.name),  # Return only filename
                    'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                } for doc in documents
            ]
        }
        
        return JsonResponse(user_data)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# API: Get user details by username
@login_required
def user_details_by_username_api(request, username):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        user = get_user_model().objects.get(username=username)
        documents = UserDocument.objects.filter(user=user)
        
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
            'documents': [
                {
                    'id': doc.id,
                    'name': os.path.basename(doc.document.name),  # Return only filename
                    'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                } for doc in documents
            ]
        }
        
        return JsonResponse(user_data)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# API: Update user
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

# API: Get user documents filtered by date
@login_required
def user_documents_by_date_api(request, user_id):
    """
    API endpoint to get user documents filtered by date range
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get date range from query parameters
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
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
        
        # Prepare document data
        document_data = [
            {
                'id': doc.id,
                'name': os.path.basename(doc.document.name),  # Return only filename
                'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
            } for doc in documents
        ]
        
        return JsonResponse({
            'user_id': user.id,
            'username': user.username,
            'documents': document_data,
            'has_documents_in_range': len(document_data) > 0
        })
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

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
            raise Http404("Document not found")
        
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

# Download all documents as ZIP
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
                    # Add file to zip with original filename
                    zip_file.write(file_path, os.path.basename(file_path))
        
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

# User edit view (placeholder)
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
            
            user.save()
            messages.success(request, f"User {username} has been updated successfully.")
            return redirect('admin_dashboard')
        
        return render(request, 'main/edit_user.html', {
            'user_to_edit': user
        })
    except get_user_model().DoesNotExist:
        raise Http404("User not found")

# Delete document view
@login_required
def delete_document(request, doc_id):
    try:
        document = UserDocument.objects.get(id=doc_id)
        
        # Check permissions
        if document.user != request.user:
            messages.error(request, "You don't have permission to delete this document.")
            return redirect('dashboard')
        
        # Get document name before deletion for the success message
        document_name = os.path.basename(document.document.name)
        
        # Delete the document
        document.delete()
        
        messages.success(request, f"Document '{document_name}' has been deleted. You can upload a replacement file.")
        return redirect('dashboard')
    except UserDocument.DoesNotExist:
        messages.error(request, "Document not found.")
        return redirect('dashboard')