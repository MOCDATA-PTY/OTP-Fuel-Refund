from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # API endpoints for admin dashboard
    path('api/user/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
    path('api/user/<str:username>/details/', views.user_details_by_username_api, name='user_details_by_username_api'),
    path('api/user/<str:username>/update/', views.user_update_api, name='user_update_api'),
    path('api/user/<str:username>/delete/', views.user_delete_api, name='user_delete_api'),
    path('api/user/<int:user_id>/documents/by-date/', views.user_documents_by_date_api, name='user_documents_by_date_api'),
    
    # Document handling (download and delete)
    path('document/download/<int:doc_id>/', views.download_document, name='download_document'),
    path('document/download-all/<int:user_id>/', views.download_all_documents, name='download_all_documents'),
    path('document/delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    
    # User edit
    path('user/edit/<str:username>/', views.edit_user, name='edit_user'),
    path('contact/', views.contact, name='contact'),
]