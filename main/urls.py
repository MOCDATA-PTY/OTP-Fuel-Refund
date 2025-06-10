from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User management
    path('user/edit/<str:username>/', views.edit_user, name='edit_user'),
    
    # Document handling (download and delete)
    path('document/download/<int:doc_id>/', views.download_document, name='download_document'),
    path('document/download-all/<int:user_id>/', views.download_all_documents, name='download_all_documents'),
    path('document/delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    
    # Static document downloads - NEW
    path('download/privacy-policy/', views.download_privacy_policy, name='download_privacy_policy'),
    path('download/terms-conditions/', views.download_terms_conditions, name='download_terms_conditions'),
    
    # API endpoints for admin dashboard
    path('api/user/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
    path('api/user/<str:username>/details/', views.user_details_by_username_api, name='user_details_by_username_api'),
    path('api/user/<str:username>/update/', views.user_update_api, name='user_update_api'),
    path('api/user/<str:username>/delete/', views.user_delete_api, name='user_delete_api'),
    path('api/user/<int:user_id>/documents/by-date/', views.user_documents_by_date_api, name='user_documents_by_date_api'),
    
    # API document downloads - NEW
    path('api/download-document/<int:doc_id>/', views.download_document_api, name='download_document_api'),
    path('api/download-privacy-policy/', views.download_privacy_policy_api, name='download_privacy_policy_api'),
    path('api/download-terms-conditions/', views.download_terms_conditions_api, name='download_terms_conditions_api'),
]