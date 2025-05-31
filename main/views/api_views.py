from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST

import os
import json
from datetime import datetime, timedelta

from ..models import UserDocument

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