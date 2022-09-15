from typing import Optional

from django.contrib import admin
from django.utils.safestring import mark_safe

from images.models import Image


class SizesMixin:
    """Mixin for resizes of images."""

    def sizes(self, obj: Optional[Image]) -> str:
        """Return all resizes of the image."""
        if not obj:
            return '-'
        resizes_data = obj.resizes_data
        if not resizes_data:
            return '-'
        lst = []
        for data in resizes_data:
            lst.append(f'<a href="{data[2]}" target="_blank">{data[0]}</a>')
        return mark_safe('<br />'.join(lst))


class ReadOnlyMixin:
    """Makes model read only."""

    def has_add_permission(self, request, obj=None) -> bool:
        """Add permission."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Edit permission."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Delete permission."""
        return False


@admin.register(Image)
class ImageAdmin(ReadOnlyMixin, SizesMixin, admin.ModelAdmin):
    """Images admin."""

    list_display = ('filename', 'original_filename', 'user', 'upload_date', 'filesize', 'sizes')
    readonly_fields = ('filename', 'original_filename', 'user', 'upload_date', 'filesize', 'sizes')


class ImageInline(ReadOnlyMixin, SizesMixin, admin.TabularInline):
    """Imline with users images."""

    readonly_fields = ('filename', 'original_filename', 'upload_date', 'filesize', 'sizes')
    model = Image
    extra = 0
