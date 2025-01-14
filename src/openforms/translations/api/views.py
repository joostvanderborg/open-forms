from django.conf import settings
from django.utils.translation import get_language, get_language_info, gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.translations.utils import set_language_cookie

from .serializers import LanguageCodeSerializer, LanguageInfoSerializer


class LanguageInfoView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_serializer(self, *args, **kwargs):
        return LanguageInfoSerializer(
            *args,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    @extend_schema(
        summary=_("List available languages and the currently active one."),
        tags=["translations"],
        examples=[
            OpenApiExample(
                "Selected Dutch",
                value={
                    "languages": [
                        {"code": "en", "name": "English"},
                        {"code": "nl", "name": "Nederlands"},
                        # FIXME: code is validated against the enum list, and at the
                        # moment we only support en/nl
                        # {"code": "fy", "name": "frysk"},
                    ],
                    "current": "nl",
                },
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        codes = (lang[0] for lang in settings.LANGUAGES)
        languages = [
            {"code": code, "name": get_language_info(code)["name_local"]}
            for code in codes
        ]
        current = get_language()
        serializer = self.get_serializer(
            instance={"languages": languages, "current": current}
        )
        return Response(serializer.data)


class SetLanguageView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_serializer(self, *args, **kwargs):
        return LanguageCodeSerializer(
            *args, context={"request": self.request, "view": self}, **kwargs
        )

    @extend_schema(
        summary=_("Set the desired language"),
        tags=["translations"],
        responses={
            "204": None,
            "400": ValidationErrorSerializer,
            "5XX": ExceptionSerializer,
        },
    )
    def put(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_language_cookie(response, serializer.data["code"])
        return response
