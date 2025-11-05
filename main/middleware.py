"""
Performance optimization middleware
Adds caching and compression headers for better Lighthouse scores
"""

class PerformanceMiddleware:
    """
    Middleware to add performance-optimizing headers
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add caching headers for static files
        if request.path.startswith('/static/'):
            # Cache static files for 1 year
            response['Cache-Control'] = 'public, max-age=31536000, immutable'

            # Add compression hint
            if not response.has_header('Vary'):
                response['Vary'] = 'Accept-Encoding'

        return response
