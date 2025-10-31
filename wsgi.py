"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Production WSGI application
application = get_wsgi_application()

# For debugging in production
if os.environ.get('DJANGO_ENV') == 'production':
    try:
        from whitenoise import WhiteNoise
        application = WhiteNoise(application, root='static/')
        application.add_files('static/', prefix='static/')
        application.add_files('media/', prefix='media/')
    except ImportError:
        pass
