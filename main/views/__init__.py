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
    download_document,
    download_all_documents,
    edit_user,
    delete_document,
    terms_of_service,
    privacy_policy,
)

from .api_views import (
    user_details_api,
    user_details_by_username_api,
    user_update_api,
    user_delete_api,
    user_documents_by_date_api,
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
    'download_document',
    'download_all_documents',
    'edit_user',
    'delete_document',
    'terms_of_service',
    'privacy_policy',
    # API views
    'user_details_api',
    'user_details_by_username_api', 
    'user_update_api',
    'user_delete_api',
    'user_documents_by_date_api',
    # Template filters
    'register',
]