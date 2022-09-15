from typing import Callable

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.generic import View

from app.helpers import Response
from images.models import Image
from tokens.models import Token


def token_protected_method(func: Callable):
    """Check token.

    Enriches request with user variable if one was found.
    If not, returns 403 (if token not passed) or 404 (if user not found by the token).
    """
    def wrapper(
            self: View, request: WSGIRequest, *args, **kwargs
    ) -> HttpResponse:
        """Wrap."""
        token_str = request.headers.get('X-Auth-Token')
        if not token_str:
            return Response.json(Response.INVALID_REQUEST, 'Forbidden', 403)

        token = Token.objects.filter(token=token_str).first()
        if not token:
            return Response.json(
                Response.INVALID_REQUEST, 'User not found', 404)

        request.user = token.user

        return func(self, request, *args, **kwargs)

    return wrapper


def image_method(func: Callable):
    """Enriches request with image variable."""
    def wrapper(
            self: View, request: WSGIRequest, filename: str, *args, **kwargs
    ) -> HttpResponse:
        """Wrap."""
        image: Image = Image.objects.filter(
            user=request.user, filename=filename).first()

        if not image:
            return Response.json(
                Response.INVALID_REQUEST, 'Image not found', 404)

        request.image = image

        return func(self, request, filename, *args, **kwargs)

    return wrapper
