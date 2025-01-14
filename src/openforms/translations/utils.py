from typing import Union

from django.conf import settings
from django.http.response import HttpResponseBase

from rest_framework.response import Response

ResponseType = Union[HttpResponseBase, Response]


def set_language_cookie(response: ResponseType, language_code: str) -> None:
    response.set_cookie(
        key=settings.LANGUAGE_COOKIE_NAME,
        value=language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        path=settings.LANGUAGE_COOKIE_PATH,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        secure=settings.LANGUAGE_COOKIE_SECURE,
    )
