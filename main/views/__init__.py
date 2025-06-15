# __init__.py
# Import all views to make them available when importing from views
from .display_views import (
    home,
    contact,
    signup_view,
    login_view,
    logout_view,
    dashboard,
    admin_dashboard,
    analytics_dashboard,      # ADDED
    toggle_admin_status,      # ADDED
    view_document,           # ADDED
    delete_user,             # ADDED
    send_reminder_email,     # ADDED
    send_custom_email,       # CRITICAL ADDITION - FIXES 404 ERROR
    gmail_oauth_callback,    # GMAIL API OAUTH CALLBACK
    download_document,
    download_all_documents,
    edit_user,
    delete_document,
    terms_of_service,
    privacy_policy,
    download_privacy_policy,
    download_terms_conditions,
    debug_users,             # ADDED
)

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

# Template filters
from .display_views import register

__all__ = [
    # Display views
    'home',
    'contact', 
    'signup_view',
    'login_view',
    'logout_view',
    'dashboard',
    'admin_dashboard',
    'analytics_dashboard',      # ADDED
    'toggle_admin_status',      # ADDED
    'view_document',           # ADDED
    'delete_user',             # ADDED
    'send_reminder_email',     # ADDED
    'send_custom_email',       # CRITICAL ADDITION - FIXES 404 ERROR
    'gmail_oauth_callback',    # GMAIL API OAUTH CALLBACK
    'download_document',
    'download_all_documents',
    'edit_user',
    'delete_document',
    'terms_of_service',
    'privacy_policy',
    'download_privacy_policy',
    'download_terms_conditions',
    'debug_users',             # ADDED
    # API views
    'user_details_api',
    'user_details_by_username_api', 
    'user_update_api',
    'user_delete_api',
    'user_documents_by_date_api',
    'download_document_api',
    'download_privacy_policy_api',
    'download_terms_conditions_api',
    # Template filters
    'register',
]