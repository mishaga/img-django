from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from images.admin import ImageInline
from tokens.models import Token


class TokenInline(admin.StackedInline):
    """Inline with user's token."""

    model = Token
    can_delete = False


class UserAdmin(BaseUserAdmin):
    """Redefine user admin to include inlines with token and images."""

    list_display = ('username', 'is_staff', 'images_count')
    inlines = (TokenInline, ImageInline)

    def images_count(self, obj) -> int:
        """Return count of images of the user."""
        return obj.images.count()


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
