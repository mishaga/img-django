from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from app.helpers import Response, Size
from images.decorators import image_method, token_protected_method
from images.forms import ResizeImageForm, UploadImageForm
from images.models import Image


@method_decorator(csrf_exempt, name='dispatch')
class ImageCreateView(View):
    """View for uploading an image."""

    @token_protected_method
    def post(self, request: WSGIRequest) -> HttpResponse:
        """Upload method."""
        # validating post data
        form = UploadImageForm(request.POST, request.FILES)
        if not form.is_valid():
            return Response.json(Response.INVALID_PARAMETER, form.errors, 400)

        form_data = form.clean()

        upload = Image.upload(
            form_data['file'],
            form_data['sizes'],
            request.FILES.get('file'),
            request.user
        )

        return Response.json(Response.OKAY, upload)


@method_decorator(csrf_exempt, name='dispatch')
class ImageResizeDeleteView(View):
    """View for resize and deletion of an image."""

    @token_protected_method
    @image_method
    def post(self, request: WSGIRequest, filename: str) -> HttpResponse:
        """Resize method."""
        form = ResizeImageForm(request.POST)
        if not form.is_valid():
            return Response.json(Response.INVALID_PARAMETER, form.errors, 400)

        form_data = form.clean()
        size = Size(form_data['width'], form_data['height'])
        url = request.image.resize(size)

        return Response.json(Response.OKAY, url, 201)

    @token_protected_method
    @image_method
    def delete(self, request: WSGIRequest, filename: str) -> HttpResponse:
        """Delete method."""
        request.image.delete()

        return Response.json(Response.OKAY, 'Deleted')
