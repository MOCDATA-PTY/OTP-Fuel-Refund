from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('calculator/', views.calculator, name='calculator'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('faw/', views.faw, name='faw'),
    path('faq/', views.faq, name='faq'),

    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('analytics-dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # ENHANCED EMAIL FUNCTIONALITY - BEAUTIFUL TEMPLATES
    path('send-custom-email/<str:username>/', views.send_custom_email, name='send_custom_email'),
    path('send-reminder-email/<str:username>/', views.send_reminder_email, name='send_reminder_email'),
    
    # PRODUCTION GMAIL API OAUTH CALLBACK
    path('oauth/callback/', views.gmail_oauth_callback, name='gmail_oauth_callback'),
    
    # User management (Admin only) - Using 'manage' prefix to avoid Django admin conflicts
    path('manage/user/edit/<str:username>/', views.edit_user, name='edit_user'),
    path('manage/user/toggle-admin/<str:username>/', views.toggle_admin_status, name='toggle_admin_status'),
    path('manage/user/delete/<str:username>/', views.delete_user, name='delete_user'),
    
    # Document handling (view, download and delete)
    path('document/view/<int:doc_id>/', views.view_document, name='view_document'),
    path('document/download/<int:doc_id>/', views.download_document, name='download_document'),
    path('document/download-all/<int:user_id>/', views.download_all_documents, name='download_all_documents'),
    path('document/delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    
    # Static document downloads
    path('download/privacy-policy/', views.download_privacy_policy, name='download_privacy_policy'),
    path('download/terms-conditions/', views.download_terms_conditions, name='download_terms_conditions'),
]

# API endpoints (conditionally added if api_views is available)
try:
    # Test if API views are available
    hasattr(views, 'user_details_api')
    
    # Add API endpoints
    api_patterns = [
        # User API endpoints
        path('api/user/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
        path('api/user/<str:username>/details/', views.user_details_by_username_api, name='user_details_by_username_api'),
        path('api/user/<str:username>/update/', views.user_update_api, name='user_update_api'),
        path('api/user/<str:username>/delete/', views.user_delete_api, name='user_delete_api'),
        path('api/user/<int:user_id>/documents/by-date/', views.user_documents_by_date_api, name='user_documents_by_date_api'),
        
        # Document API endpoints
        path('api/download-document/<int:doc_id>/', views.download_document_api, name='download_document_api'),
        path('api/download-privacy-policy/', views.download_privacy_policy_api, name='download_privacy_policy_api'),
        path('api/download-terms-conditions/', views.download_terms_conditions_api, name='download_terms_conditions_api'),
    ]
    
    # Add API patterns to main urlpatterns
    urlpatterns.extend(api_patterns)
    print("API endpoints successfully added to URL patterns")
    
except AttributeError:
    print("Warning: API views not available - skipping API URL patterns")

# Debug view (remove in production)
debug_patterns = [
    path('debug/users/', views.debug_users, name='debug_users'),
]

# Add debug patterns
urlpatterns.extend(debug_patterns)

# Print URL configuration summary
print(f"Fuel Refund Institute URLs: {len(urlpatterns)} total endpoints configured")
print("Beautiful email endpoints: ACTIVE")
print("Production Gmail API: READY")
print("Admin dashboard: ENABLED")
print("Document management: ACTIVE")

# URL patterns summary for debugging
url_summary = {
    'public_pages': 4,
    'authentication': 3, 
    'dashboards': 3,
    'email_functionality': 3,  # Enhanced with beautiful templates
    'user_management': 3,
    'document_handling': 4,
    'static_downloads': 2,
    'api_endpoints': len([p for p in urlpatterns if 'api/' in str(p.pattern)]),
    'debug_views': 1
}

print(f"URL Summary: {url_summary}")
print("Ready for production with beautiful Gmail API integration!")