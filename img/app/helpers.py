import json
from typing import Any, List, Optional, Tuple

from django.http import HttpResponse


class Size:
    """Class for working with size of an image."""

    def __init__(self, width: int, height: int) -> None:
        """Init method, saves width and height."""
        self.__width = width
        self.__height = height

    def __str__(self) -> str:
        """Represent object as string."""
        return f'{self.__width}x{self.__height}'

    def __repr__(self) -> str:
        """Representation for development."""
        return f'Size({self.__width}, {self.__height})'

    @property
    def width(self) -> int:
        """Return width."""
        return self.__width

    @property
    def height(self) -> int:
        """Return height."""
        return self.__height

    @classmethod
    def from_str(cls, size_str: str):
        """Return object by sting representation."""
        width, height = size_str.split('x')
        return cls(int(width), int(height))

    def as_tuple(self) -> Tuple[int, int]:
        """Return width and height in tuple."""
        return self.__width, self.__height


Sizes = Optional[List[Size]]


class Response:
    """Wrapper class for HttpResponse to simplify responses."""

    OKAY = 1
    UNKNOWN_ERROR = 0
    INVALID_REQUEST = -1
    INVALID_PARAMETER = -2
    SERVER_ERROR = -3

    @staticmethod
    def json(code: int, message: Any, status_code: int = 200) -> HttpResponse:
        """JSON response."""
        return HttpResponse(
            json.dumps({
                'code': code,
                'message': message,
            }),
            content_type='application/json; charset=utf-8',
            status=status_code,
        )

    @staticmethod
    def text(message: str, status_code: int = 200) -> HttpResponse:
        """Plain text response."""
        return HttpResponse(message, content_type='text/plain; charset=utf-8', status=status_code)
