import re
from tempfile import NamedTemporaryFile
from unittest import mock
from uuid import uuid4

from PIL import Image as PillowImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from app.helpers import Response
from app.settings import env
from images.models import Image
from images.tests.mixins import TestImageViewBase


class UploadViewTestCase(TestImageViewBase, TestCase):
    """Tests for upload view."""

    @property
    def url(self) -> str:
        """Return URL for upload."""
        return reverse('upload')

    def test_forbidden_methods(self) -> None:
        """Tests forbidden HTTP-methods."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.put(self.url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.patch(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_no_token(self) -> None:
        """No token – 403 error."""
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_REQUEST)
        self.assertEqual(response['message'], 'Forbidden')

    def test_unknown_token(self) -> None:
        """Incorrect token – 404 error."""
        resp = self.client.post(self.url, HTTP_X_AUTH_TOKEN=uuid4().hex)
        self.assertEqual(resp.status_code, 404)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_REQUEST)
        self.assertEqual(response['message'], 'User not found')

    def test_no_files(self) -> None:
        """No required parameter file – 400 error.

        Maybe it's better to use 422 code.
        """
        user, token = self.create_user_with_token()
        resp = self.client.post(self.url, HTTP_X_AUTH_TOKEN=token.token)
        self.assertEqual(resp.status_code, 400)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_PARAMETER)
        self.assertEqual(response['message'], {'file': ['File was not received']})

    def test_incorrect_file(self) -> None:
        """If file is not valid image – 400 error.

        Maybe it's better to use 422 code.
        """
        user, token = self.create_user_with_token()
        for incorrect_content in (b'', b'text content'):
            with self.subTest():
                image_file = SimpleUploadedFile('one.jpeg', incorrect_content, content_type='image/jpeg')
                resp = self.client.post(self.url, {'file': image_file}, HTTP_X_AUTH_TOKEN=token.token)
                self.assertEqual(resp.status_code, 400)
                response = self.load(resp)
                self.assertEqual(response['code'], Response.INVALID_PARAMETER)
                self.assertEqual(response['message'], {'file': ['File probably is not an image']})

    @mock.patch('builtins.open')
    @mock.patch('os.makedirs')
    def test_okay_no_sizes(self, mocked_makedirs, mocked_open) -> None:
        """Okay file, no sizes."""
        user, token = self.create_user_with_token()

        with NamedTemporaryFile(suffix='.jpg') as file:
            image = PillowImage.new('RGB', (100, 100))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile('T-w-o.jpg', file.read(), content_type='image/jpeg')

        resp = self.client.post(self.url, {'file': image_file}, HTTP_X_AUTH_TOKEN=token.token)

        self.assertEqual(resp.status_code, 200)
        response = self.load(resp)
        filename = response['message']['filename']
        self.assertEqual(response['code'], Response.OKAY)
        self.assertEqual(response['message']['sizes'], None)
        self.assertTrue(re.match('^[0-9a-f]{32}.jpeg$', filename))

        self.assertEqual(Image.objects.count(), 1)
        image = Image.objects.get()
        self.assertEqual(image.filename, filename)
        self.assertEqual(image.user, user)
        self.assertEqual(image.original_filename, 'T-w-o.jpg')

    @mock.patch('builtins.open')
    @mock.patch('os.makedirs')
    def test_okay_with_sizes(self, mocked_makedirs, mocked_open) -> None:
        """Okay file with sizes."""
        user, token = self.create_user_with_token()

        with NamedTemporaryFile(suffix='.jpg') as file:
            image = PillowImage.new('RGB', (300, 300))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile('three.jpeg', file.read(), content_type='image/jpeg')

        data = {
            'file': image_file,
            'sizes': '200x200,150x150',
        }
        with mock.patch('PIL.Image.Image.save'):
            resp = self.client.post(self.url, data, HTTP_X_AUTH_TOKEN=token.token)

        self.assertEqual(resp.status_code, 200)
        response = self.load(resp)

        filename = response['message']['filename']
        sizes = response['message']['sizes']
        base_url = env('BASE_URL', '')

        self.assertEqual(response['code'], Response.OKAY)
        self.assertTrue(re.match('^[0-9a-f]{32}.jpeg$', filename))
        self.assertEqual(len(sizes), 2)
        for size in sizes:
            path = f'{base_url}/{user}/{size}/{filename}'
            self.assertEqual(sizes[size], path)

        self.assertEqual(Image.objects.count(), 1)
        db_image = Image.objects.get()
        self.assertEqual(db_image.filename, filename)
        self.assertEqual(db_image.user, user)
        self.assertEqual(db_image.original_filename, 'three.jpeg')

    def test_incorrect_sizes(self) -> None:
        """Okay file, incorrect sizes."""
        user, token = self.create_user_with_token()

        with NamedTemporaryFile(suffix='.jpg') as file:
            image = PillowImage.new('RGB', (120, 120))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile('four.jpeg', file.read(), content_type='image/jpeg')

        data = {
            'file': image_file,
            'sizes': '1a2x3b4,2x2',
        }
        resp = self.client.post(self.url, data, HTTP_X_AUTH_TOKEN=token.token)

        self.assertEqual(resp.status_code, 400)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_PARAMETER)
        self.assertEqual(response['message'], {'sizes': ['Value contains inappropriate symbols']})

    def test_empty_size(self) -> None:
        """Okay file, incorrect sizes (comma at the end)."""
        user, token = self.create_user_with_token()

        with NamedTemporaryFile(suffix='.jpg') as file:
            image = PillowImage.new('RGB', (130, 130))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile('five.jpeg', file.read(), content_type='image/jpeg')

        data = {
            'file': image_file,
            'sizes': '100x200,',
        }
        resp = self.client.post(self.url, data, HTTP_X_AUTH_TOKEN=token.token)

        self.assertEqual(resp.status_code, 400)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_PARAMETER)
        self.assertEqual(response['message'], {'sizes': ['Empty size given']})
