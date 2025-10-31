from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import TemplateView
import os

def google_verification(request):
    """Serve Google Search Console verification file"""
    verification_content = "google-site-verification: googlee6363b8028cb5788.html"
    return HttpResponse(verification_content, content_type='text/html')

def sitemap_xml(request):
    """Serve sitemap.xml for SEO"""
    sitemap_path = os.path.join(settings.BASE_DIR, 'sitemap.xml')
    try:
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/xml')
    except FileNotFoundError:
        return HttpResponse('Sitemap not found', status=404)

def robots_txt(request):
    """Serve robots.txt for SEO"""
    robots_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    try:
        with open(robots_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain')
    except FileNotFoundError:
        return HttpResponse('Robots.txt not found', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('googlee6363b8028cb5788.html', google_verification, name='google_verification'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('', include('main.urls')),  # This should include main.urls, not import views
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)