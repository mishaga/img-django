from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from app.helpers import Response
from app.settings import env


@require_http_methods(['GET'])
def main_page_view(request) -> HttpResponse:
    """View for main page."""
    version = env('PROJECT_VERSION', 'unknown')
    return Response.text(f'img project (version {version})')
