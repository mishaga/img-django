from django.conf import settings
from django.db import models


class Token(models.Model):
    """Token model."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, primary_key=True)
    token = models.CharField(max_length=256, unique=True)

    objects = models.Manager()

    class Meta:
        """Meta class."""

        ordering = ['user_id']

    def __str__(self) -> str:
        """Model as string."""
        return f'{self.token}'
