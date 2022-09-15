from tempfile import NamedTemporaryFile
from unittest import mock
from uuid import uuid4

from PIL import Image as PillowImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from app.helpers import Response, Size
from app.settings import env
from images.models import Image
from images.tests.mixins import TestImageViewBase


class ResizeDeleteViewTestCase(TestImageViewBase, TestCase):
    """Tests for resize/delete."""

    @property
    def url(self) -> str:
        """Return url for resize/delete."""
        return reverse('resize-n-delete', args=[self.filename])

    @property
    def upload_url(self) -> str:
        """Return url for upload."""
        return reverse('upload')

    def setUp(self) -> None:
        """Set up."""
        self.user, self.token = self.create_user_with_token()
        self.filename = uuid4().hex
        self.width = 90
        self.height = 90

    def test_no_token(self) -> None:
        """No token – 403 error."""
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 403)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_REQUEST)
        self.assertEqual(response['message'], 'Forbidden')

    def test_unknown_token(self) -> None:
        """Undefined token – 404 error."""
        resp = self.client.delete(self.url, HTTP_X_AUTH_TOKEN=uuid4().hex)
        self.assertEqual(resp.status_code, 404)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_REQUEST)
        self.assertEqual(response['message'], 'User not found')

    def test_forbidden_methods(self) -> None:
        """Tests forbidden HTTP-methods."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.put(self.url)
        self.assertEqual(resp.status_code, 405)

        resp = self.client.patch(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_incorrect_filename(self) -> None:
        """Incorrect filename – 404 error."""
        resp = self.client.delete(self.url, HTTP_X_AUTH_TOKEN=self.token.token)
        self.assertEqual(resp.status_code, 404)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.INVALID_REQUEST)
        self.assertEqual(response['message'], 'Image not found')

    def test_other_user(self) -> None:
        """One user can not delete image of another."""
        Image.objects.create(user=self.user, filename=self.filename, original_filename='Yes.png')
        new_user, new_token = self.create_user_with_token()
        resp = self.client.delete(self.url, HTTP_X_AUTH_TOKEN=new_token.token)
        self.assertEqual(resp.status_code, 404)
        response = self.load(resp)
        self.assertEqual(response['message'], 'Image not found')
        self.assertEqual(response['code'], Response.INVALID_REQUEST)

    def test_delete_okay(self) -> None:
        """If all params are okay, image deletes."""
        token = {'HTTP_X_AUTH_TOKEN': self.token.token}
        url = reverse('upload')

        with NamedTemporaryFile(suffix='.jpg') as file:
            # creating tmp file
            image = PillowImage.new('RGB', (110, 110))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile(f'{uuid4().hex}.jpg', file.read(), content_type='image/jpeg')

            # uploading the file
            with mock.patch('builtins.open'), mock.patch('os.makedirs'):
                resp = self.client.post(url, {'file': image_file}, **token)

            # checking correct creation
            self.assertEqual(resp.status_code, 200)
            db_image = Image.objects.get()
            self.filename = db_image.filename

            # delete image
            resp = self.client.delete(self.url, **token)

        # checking correct deletion
        self.assertEqual(resp.status_code, 200)
        response = self.load(resp)
        self.assertEqual(response['code'], Response.OKAY)
        self.assertEqual(response['message'], 'Deleted')

        db_image = Image.objects.first()
        self.assertIsNone(db_image)

    def test_incorrect_size(self) -> None:
        """Tests incorrect width and height params."""
        headers = {'HTTP_X_AUTH_TOKEN': self.token.token}

        with NamedTemporaryFile(suffix='.jpg') as file:
            # create tmp file
            image = PillowImage.new('RGB', (125, 125))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile(f'{uuid4().hex}.jpg', file.read(), content_type='image/jpeg')

            # upload the file
            with mock.patch('builtins.open'), mock.patch('os.makedirs'):
                resp = self.client.post(self.upload_url, {'file': image_file}, **headers)

            # checking correct creation
            self.assertEqual(resp.status_code, 200)
            db_image = Image.objects.get()
            self.filename = db_image.filename

            # trying to create resized image
            incorrect_sizes = [
                (100, -100),
                (0, 100),
                (100, 0),
                (-100, 100),
                (100, 10001),
                (10001, 100),
            ]
            for size in incorrect_sizes:
                data = {
                    'width': size[0],
                    'height': size[1],
                }
                resp = self.client.post(self.url, data=data, **headers)
                self.assertEqual(resp.status_code, 400)
                response = self.load(resp)
                self.assertEqual(response['code'], Response.INVALID_PARAMETER)

    def test_resize_okay(self) -> None:
        """Tests correct resize of image."""
        headers = {'HTTP_X_AUTH_TOKEN': self.token.token}

        with NamedTemporaryFile(suffix='.jpg') as file:
            # create tmp file
            image = PillowImage.new('RGB', (120, 120))
            image.save(file)
            file.seek(0)
            image_file = SimpleUploadedFile(f'{uuid4().hex}.jpeg', file.read(), content_type='image/jpeg')

            # upload it
            with mock.patch('builtins.open'), mock.patch('os.makedirs'):
                resp = self.client.post(self.upload_url, {'file': image_file}, **headers)

            # checking correct creation
            self.assertEqual(resp.status_code, 200)
            db_image = Image.objects.get()
            self.filename = db_image.filename

            # creating resize
            with mock.patch('builtins.open') as open_, mock.patch('os.makedirs'), mock.patch('PIL.Image.Image.save'):
                open_.return_value = file
                data = {
                    'width': self.width,
                    'height': self.height,
                }
                resp = self.client.post(self.url, data=data, **headers)

        # checking correct resize
        self.assertEqual(resp.status_code, 201)
        response = self.load(resp)
        base_url = env('BASE_URL', '')
        size = Size(self.width, self.height)
        self.assertEqual(response['code'], Response.OKAY)
        self.assertEqual(response['message'], f'{base_url}/{self.user}/{size}/{self.filename}')
