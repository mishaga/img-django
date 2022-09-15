from unittest import mock
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from app.helpers import Size
from app.settings import env
from images.models import Image


class ImageModelTestCase(TestCase):
    """Tests Image model."""

    def setUp(self) -> None:
        """Set up."""
        self.user = User.objects.create_user(username=uuid4().hex, password=uuid4().hex)
        self.image = Image.objects.create(user=self.user, filename=uuid4().hex, original_filename='test.jpeg')

    def test_path_to_original(self) -> None:
        """Tests path_to_original method."""
        self.assertEqual(str(self.image.path_to_original),
                         f'{settings.ORIGINALS_DIR}/{self.user}/{self.image.filename}')
        image = Image()
        self.assertIsNone(image.path_to_original)

    def test_filesize(self) -> None:
        """Tests filesize method."""
        self.assertEqual(self.image.filesize, '–')

        with mock.patch('os.path.getsize') as getsize:
            getsize.return_value = 73 * 1024 * 1024
            self.assertEqual(self.image.filesize, '73.00 Mb')

        with mock.patch('os.path.getsize') as getsize:
            getsize.return_value = 73.91 * 1024 * 1024
            self.assertEqual(self.image.filesize, '73.91 Mb')

    def test_get_url(self) -> None:
        """Tests get_url method."""
        width = 299
        height = 156
        path = self.image.get_url(Size(width, height))
        base_url = env('BASE_URL', '')
        self.assertEqual(path, f'{base_url}/{self.user}/{width}x{height}/{self.image.filename}')
