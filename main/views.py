from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import CustomUser, UserSubmissionStatus
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import UserProfile

# The signup view has been moved to main/views/display_views.py

def signup(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        company_name = request.POST.get('company_name')
        business_type = request.POST.get('business_type')
        tax_id = request.POST.get('tax_id')
        business_address = request.POST.get('business_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')

        # Basic validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup')

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )

            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                phone=phone,
                company_name=company_name,
                business_type=business_type,
                tax_id=tax_id,
                business_address=business_address,
                city=city,
                state=state,
                zip_code=zip_code
            )

            # Log the user in
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('signup')

    return render(request, 'main/signup.html')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'main/dashboard.html')
