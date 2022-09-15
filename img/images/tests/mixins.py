import json
from typing import Dict, Tuple
from uuid import uuid4

from django.contrib.auth.models import User

from tokens.models import Token


class TestImageViewBase:
    """Base class for testing views."""

    @property
    def url(self) -> str:
        """Return url for certain page."""
        raise NotImplementedError()

    def create_user_with_token(self) -> Tuple[User, Token]:
        """Create user and token for it."""
        user = User.objects.create_user(username=uuid4().hex, password=uuid4().hex)
        token = Token.objects.create(user=user, token=uuid4().hex)
        return user, token

    def load(self, resp) -> Dict:
        """Return dict from API response."""
        return json.loads(resp.content.decode('utf-8'))
