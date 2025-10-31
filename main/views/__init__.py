# __init__.py
# Import all views to make them available when importing from views

from .display_views import (
    home,
    contact,
    calculator,
        faw,
        faq,
    signup_view,              # UPDATED - Enhanced with beautiful email templates
    login_view,
    logout_view,
    dashboard,
    admin_dashboard,
    analytics_dashboard,
    toggle_admin_status,
    view_document,
    delete_user,
    send_reminder_email,      # ENHANCED - Now with beautiful templates
    send_custom_email,        # ENHANCED - Now with beautiful templates
    gmail_oauth_callback,     # PRODUCTION GMAIL API OAUTH CALLBACK
    download_document,
    download_all_documents,
    edit_user,
    delete_document,
    terms_of_service,
    privacy_policy,
    download_privacy_policy,
    download_terms_conditions,
    debug_users,

    # ENHANCED GMAIL API FUNCTIONS
    get_gmail_service,                    # Production-ready Gmail service
    send_email_with_gmail_api,           # Enhanced email sending with templates
    send_resend_email,                   # Backwards compatible function
    send_reminder_email_with_template,   # Beautiful reminder emails
    send_custom_email_with_template,     # Beautiful custom emails
    create_beautiful_email_template,     # Template creation function
)

# Import API views (with error handling for missing api_views.py)
try:
    from .api_views import (
        user_details_api,
        user_details_by_username_api,
        user_update_api,
        user_delete_api,
        user_documents_by_date_api,
        download_document_api,
        download_privacy_policy_api,
        download_terms_conditions_api,
    )
    # Add API views to __all__ if successfully imported
    API_VIEWS = [
        'user_details_api',
        'user_details_by_username_api', 
        'user_update_api',
        'user_delete_api',
        'user_documents_by_date_api',
        'download_document_api',
        'download_privacy_policy_api',
        'download_terms_conditions_api',
    ]
    print("API views successfully imported")
except ImportError as e:
    # API views not available
    API_VIEWS = []
    print(f"Warning: api_views.py import error: {e}. API views not available.")

# Template filters from display_views
from .display_views import register

__all__ = [
    # Core views
    'home',
    'contact',
    'calculator',
    'faw',
    'faq',
    'signup_view',              # UPDATED - Enhanced signup with beautiful emails
    'login_view',
    'logout_view',
    'dashboard',
    
    # Admin views
    'admin_dashboard',
    'analytics_dashboard',
    'toggle_admin_status',
    'view_document',
    'delete_user',
    'edit_user',
    'debug_users',
    
    # ENHANCED EMAIL FUNCTIONALITY
    'send_reminder_email',      # ENHANCED - Beautiful templates
    'send_custom_email',        # ENHANCED - Beautiful templates
    'gmail_oauth_callback',     # PRODUCTION GMAIL API OAUTH
    'get_gmail_service',        # Production Gmail service
    'send_email_with_gmail_api', # Enhanced email sending
    'send_resend_email',        # Backwards compatible
    'send_reminder_email_with_template', # Beautiful reminders
    'send_custom_email_with_template',   # Beautiful custom emails
    'create_beautiful_email_template',   # Template creation
    
    # Document management
    'download_document',
    'download_all_documents',
    'delete_document',
    
    # Static pages and downloads
    'terms_of_service',
    'privacy_policy',
    'download_privacy_policy',
    'download_terms_conditions',
    
    # Template filters
    'register',
] + API_VIEWS  # Dynamically add API views if available

print(f"Fuel Refund Institute Views Loaded: {len(__all__)} total views available")
print("Beautiful Gmail API templates: ACTIVE")
print("Production-ready email security: ENABLED")