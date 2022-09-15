import json

from django.test import TestCase

from app.helpers import Response, Size


class SizeTestCase(TestCase):
    """Test for Size helper."""

    def test_methods(self) -> None:
        """Тестирует методы __str__, as_tuple, width и height."""
        width = 199
        height = 56
        size = Size(width, height)
        self.assertEqual(f'{width}x{height}', str(size))
        self.assertEqual((width, height), size.as_tuple())
        self.assertEqual(width, size.width)
        self.assertEqual(height, size.height)


class ResponseTestCase(TestCase):
    """Tests for Response helper."""

    def test_json(self) -> None:
        """Method for application/json responses."""
        okay_response = Response.json(Response.OKAY, 'my very text', 201)
        self.assertEqual(
            okay_response.content.decode('utf-8'),
            json.dumps({'code': Response.OKAY, 'message': 'my very text'}),
        )
        self.assertEqual(okay_response.status_code, 201)

        error_response = Response.json(Response.INVALID_PARAMETER, 'Error...', 401)
        self.assertEqual(
            error_response.content.decode('utf-8'),
            json.dumps({'code': Response.INVALID_PARAMETER, 'message': 'Error...'}),
        )
        self.assertEqual(error_response.status_code, 401)

    def test_text(self) -> None:
        """Method for text/plain responses."""
        okay_response = Response.text('my very text', 201)
        self.assertEqual(okay_response.content.decode('utf-8'), 'my very text')
        self.assertEqual(okay_response.status_code, 201)

        error_response = Response.text('Error...', 401)
        self.assertEqual(error_response.content.decode('utf-8'), 'Error...')
        self.assertEqual(error_response.status_code, 401)
