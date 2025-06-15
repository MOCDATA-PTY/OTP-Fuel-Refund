from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST

import os
import json
import mimetypes
from datetime import datetime, timedelta

from ..models import UserDocument

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