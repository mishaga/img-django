import os
from contextlib import suppress
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from uuid import uuid4

from PIL import Image as PillowImage
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from app.helpers import Size, Sizes
from app.settings import env


class Image(models.Model):
    """Image model."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='images')
    filename = models.CharField(max_length=50)
    original_filename = models.CharField(max_length=256)
    upload_date = models.DateTimeField(blank=False, default=timezone.now)

    objects = models.Manager()

    class Meta:
        """Meta class."""

        unique_together = [('user', 'filename')]
        ordering = ['-upload_date']

    def __str__(self) -> str:
        """Model as string."""
        return f'Image {self.user}/{self.filename}'

    @cached_property
    def __walk_resizes_dir(self) -> List:
        """Walk all resizes dir for the user."""
        path = Path(settings.RESIZES_DIR) / str(self.user)
        walk = list(os.walk(path))
        return walk[1:]

    @property
    def resizes_data(self) -> List[Tuple[Size, str, str]]:
        """Return list of tuples containing all data of resized images.

        Each tuple contains:
        1. Size of the image,
        2. path to local file,
        3. url to resized image.
        """
        result = []
        for data in self.__walk_resizes_dir:
            if self.filename in data[2]:
                path = Path(data[0])
                size = Size.from_str(path.name)
                result.append((
                    size,
                    str(path / str(self.filename)),
                    self.get_url(size),
                ))
        return sorted(result, key=lambda x: x[0].as_tuple())

    @cached_property
    def path_to_original(self) -> Optional[Path]:
        """Path to original image file."""
        if not self.filename:
            return None
        return Path(settings.ORIGINALS_DIR) / str(self.user) / str(self.filename)

    @property
    def filesize(self) -> str:
        """File size in Mb (for admin)."""
        if not self.path_to_original:
            return '–'
        try:
            size = os.path.getsize(self.path_to_original) / 1024 / 1024
            return '{:.2f} Mb'.format(size)
        except FileNotFoundError:
            return '–'

    @staticmethod
    def upload(
        img: PillowImage,
        sizes: Sizes,
        uploaded_file: InMemoryUploadedFile,
        user: settings.AUTH_USER_MODEL
    ) -> Dict:
        """Create files in FS and creates record in DB."""
        # save original file
        ext = img.format.lower()
        filename = f'{uuid4().hex}.{ext}'
        originals_path = Path(settings.ORIGINALS_DIR) / str(user)
        os.makedirs(originals_path, exist_ok=True)
        with open(originals_path / filename, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # save info in DB
        db_image: Image = Image.objects.create(user=user, filename=filename, original_filename=uploaded_file.name)

        # creating resizes
        sizes_urls = {}
        if sizes:
            for size in sizes:
                size_str = str(size)
                try:
                    sizes_urls[size_str] = db_image.resize(size, img)
                except OSError as e:
                    sizes_urls[size_str] = str(e)

        return {
            'filename': filename,
            'sizes': sizes_urls if sizes_urls else None,
        }

    def get_url(self, size: Size) -> str:
        """Return absolute URL to resized image."""
        base_url = env('BASE_URL', '')
        return urljoin(base_url, f'{self.user}/{size}/{self.filename}')

    def resize(self, size: Size, image=None) -> str:
        """Resize original image to certain size."""
        size_path = Path(settings.RESIZES_DIR) / str(self.user) / str(size)
        os.makedirs(size_path, exist_ok=True)
        if not image:
            img = PillowImage.open(self.path_to_original)
        else:
            img = image.copy()
        img.thumbnail(size.as_tuple())
        img.save(str(size_path / str(self.filename)), img.format)
        return self.get_url(size)

    def delete(self, using=None, keep_parents: bool = False):
        """Delete image from FS and DB."""
        with suppress(FileNotFoundError):
            # deleting original file
            os.remove(self.path_to_original)
            # deleting resized images
            for data in self.resizes_data:
                os.remove(data[1])

        # after that delete record in DB
        return super().delete(using, keep_parents)
