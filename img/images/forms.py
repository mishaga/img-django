import re

from PIL import Image as PillowImage, UnidentifiedImageError
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

from app.helpers import Size, Sizes


class SizesField(forms.Field):
    """Class for validation POST-param sizes."""

    def clean(self, value: str) -> Sizes:
        """Validate."""
        if not value:
            return self.to_python(value)

        for size in value.split(','):
            if not size:
                raise ValidationError('Empty size given', params={'value': size})
            if not re.match(r'^[0-9]+x[0-9]+$', size):
                raise ValidationError('Value contains inappropriate symbols', params={'value': size})

        return self.to_python(value)

    def to_python(self, value: str) -> Sizes:
        """To python."""
        if not value:
            return None

        sizes_list = []
        for size in str(value).split(','):
            sizes_list.append(Size.from_str(size))

        return sizes_list


class ImageFileField(forms.FileField):
    """Class for validation incoming file."""

    def clean(self, data, initial=None) -> PillowImage:
        """Validate."""
        if not data:
            raise ValidationError('File was not received', params={'value': data})

        try:
            img = PillowImage.open(data)
        except UnidentifiedImageError:
            raise ValidationError('File probably is not an image')
        except Exception as e:
            raise ValidationError(str(e))

        return self.to_python(img)

    def to_python(self, value) -> PillowImage:
        """To python."""
        return value


class UploadImageForm(forms.Form):
    """Form for upload."""

    sizes = SizesField(help_text='Comma separated sizes "{WIDTH}x{HEIGHT}". Example: 700x600,1024x768')
    file = ImageFileField(required=True)  # noqa: VNE002


class ResizeImageForm(forms.Form):
    """Form for resize."""

    width = forms.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10000)])
    height = forms.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10000)])
