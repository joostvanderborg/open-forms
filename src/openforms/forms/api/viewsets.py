import inspect
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import parsers, permissions, response, status, views, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response

from openforms.api.pagination import PageNumberPagination
from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.translations.utils import set_language_cookie
from openforms.utils.patches.rest_framework_nested.viewsets import NestedViewSetMixin
from openforms.variables.constants import FormVariableSources

from ..messages import add_success_message
from ..models import Category, Form, FormDefinition, FormStep, FormVersion
from ..tasks import recouple_submission_variables_to_form_variables
from ..utils import export_form, import_form
from .datastructures import FormVariableWrapper
from .documentation import get_admin_fields_markdown
from .filters import FormVariableFilter
from .parsers import (
    FormCamelCaseJSONParser,
    IgnoreConfigurationFieldCamelCaseJSONParser,
    IgnoreConfigurationFieldCamelCaseJSONRenderer,
)
from .permissions import FormAPIPermissions
from .renderers import FormCamelCaseJSONRenderer
from .serializers import (
    CurrentLanguageSerializer,
    FormAdminMessageSerializer,
    FormDefinitionDetailSerializer,
    FormDefinitionSerializer,
    FormImportSerializer,
    FormLogicSerializer,
    FormPriceLogicSerializer,
    FormSerializer,
    FormStepLiteralsSerializer,
    FormStepSerializer,
    FormVariableListSerializer,
    FormVariableSerializer,
    FormVersionSerializer,
)
from .serializers.category import CategorySerializer
from .serializers.logic.form_logic import FormLogicListSerializer
from .serializers.logic.form_logic_price import FormPriceLogicListSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="form_uuid_or_slug",
            location=OpenApiParameter.PATH,
            type=str,
            description=_("Either a UUID4 or a slug identifiying the form."),
        )
    ]
)
@extend_schema_view(
    list=extend_schema(summary=_("List form steps")),
    retrieve=extend_schema(summary=_("Retrieve form step details")),
    create=extend_schema(summary=_("Create a form step")),
    update=extend_schema(summary=_("Update all details of a form step")),
    partial_update=extend_schema(summary=_("Update some details of a form step")),
    destroy=extend_schema(summary=_("Delete a form step")),
)
class FormStepViewSet(
    NestedViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    **Warning: the response data depends on user permissions**

    Non-staff users receive a subset of the documented fields which are used
    for internal form configuration. These fields are:

    {admin_fields}
    """

    serializer_class = FormStepSerializer
    queryset = FormStep.objects.all().order_by("order")
    permission_classes = [FormAPIPermissions]
    lookup_field = "uuid"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["form"] = get_object_or_404(Form, uuid=self.kwargs["form_uuid_or_slug"])
        return context


_FORMSTEP_ADMIN_FIELDS_MARKDOWN = get_admin_fields_markdown(
    FormStepLiteralsSerializer, subpath="literals"
)
FormStepViewSet.__doc__ = inspect.getdoc(FormStepViewSet).format(
    admin_fields=_FORMSTEP_ADMIN_FIELDS_MARKDOWN
)


@extend_schema_view(
    list=extend_schema(
        summary=_("List form step definitions"),
        tags=["forms", "form-definitions"],
    ),
    retrieve=extend_schema(
        summary=_("Retrieve form step definition details"),
        tags=["forms", "form-definitions"],
    ),
    create=extend_schema(
        summary=_("Create a form definition"),
        tags=["forms", "form-definitions"],
    ),
    update=extend_schema(
        summary=_("Update all details of a form definition"),
        tags=["forms", "form-definitions"],
    ),
    partial_update=extend_schema(
        summary=_("Update some details of a form definition"),
        tags=["forms", "form-definitions"],
    ),
    destroy=extend_schema(
        summary=_("Delete a form definition"),
        tags=["forms", "form-definitions"],
    ),
)
class FormDefinitionViewSet(viewsets.ModelViewSet):
    """
    **Warning: the response data depends on user permissions**

    Non-staff users receive a subset of the documented fields which are used
    for internal form configuration. These fields are:

    {admin_fields}
    """

    parser_classes = (IgnoreConfigurationFieldCamelCaseJSONParser,)
    renderer_classes = (IgnoreConfigurationFieldCamelCaseJSONRenderer,)
    queryset = FormDefinition.objects.order_by("slug")
    serializer_class = FormDefinitionSerializer
    pagination_class = PageNumberPagination
    lookup_field = "uuid"
    # anonymous clients must be able to get the form definitions in the browser
    # The DRF settings apply some default throttling to mitigate abuse
    permission_classes = [FormAPIPermissions]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FormDefinitionDetailSerializer
        return super().get_serializer_class()

    @extend_schema(
        summary=_("Retrieve form definition JSON schema"),
        tags=["forms"],
        responses=OpenApiTypes.OBJECT,
    )
    @action(methods=("GET",), detail=True)
    def configuration(self, request: Request, *args, **kwargs):
        """
        Return the raw FormIO.js configuration definition.

        This excludes all the meta-data and just returns the JSON schema blob. In
        theory, this can be fed directly to a FormIO.js renderer, but note that there
        may be custom field types in play.
        """
        definition = self.get_object()
        return Response(data=definition.configuration, status=status.HTTP_200_OK)


_FORMDEFINITION_ADMIN_FIELDS_MARKDOWN = get_admin_fields_markdown(
    FormDefinitionSerializer
)
FormDefinitionViewSet.__doc__ = inspect.getdoc(FormDefinitionViewSet).format(
    admin_fields=_FORMDEFINITION_ADMIN_FIELDS_MARKDOWN
)

UUID_OR_SLUG_PARAMETER = OpenApiParameter(
    name="uuid_or_slug",
    location=OpenApiParameter.PATH,
    type=str,
    description=_("Either a UUID4 or a slug identifiying the form."),
)

_FORM_ADMIN_FIELDS_MARKDOWN = get_admin_fields_markdown(FormSerializer)


@extend_schema_view(
    list=extend_schema(
        summary=_("List forms"),
        description=_(
            "List the active forms, including the pointers to the form steps. "
            "Form steps are included in order as they should appear.\n\n"
            "**Warning: the response data depends on user permissions**\n\n"
            "Non-staff users receive a subset of the documented fields which are used "
            "for internal form configuration. These fields are:\n\n{admin_fields}"
        ).format(admin_fields=_FORM_ADMIN_FIELDS_MARKDOWN),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve form details"),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    create=extend_schema(summary=_("Create form")),
    update=extend_schema(
        summary=_("Update all details of a form"),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    partial_update=extend_schema(
        summary=_("Update given details of a form"),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    destroy=extend_schema(
        summary=_("Mark form as deleted"),
        description=_(
            "Destroying a form leads to a soft-delete to protect related submissions. "
            "These deleted forms are no longer visible in the API endpoints."
        ),
        parameters=[UUID_OR_SLUG_PARAMETER],
    ),
    variables_bulk_update=extend_schema(
        summary=_("Bulk configure form variables"),
        description=_(
            "By sending a list of FormVariables to this endpoint, all the FormVariables related to the form will be "
            "replaced with the data sent to the endpoint."
        ),
        tags=["forms"],
        request=FormVariableListSerializer,
        responses={
            status.HTTP_200_OK: FormVariableListSerializer,
            status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
            status.HTTP_403_FORBIDDEN: ExceptionSerializer,
            status.HTTP_404_NOT_FOUND: ExceptionSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ExceptionSerializer,
        },
    ),
    logic_rules_bulk_update=extend_schema(
        summary=_("Bulk configure logic rules"),
        description=_(
            "By sending a list of LogicRules to this endpoint, all the LogicRules related to the form will be "
            "replaced with the data sent to the endpoint."
        ),
        tags=["logic-rules"],
        request=FormLogicListSerializer,
        responses={
            status.HTTP_200_OK: FormLogicListSerializer,
            status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
            status.HTTP_403_FORBIDDEN: ExceptionSerializer,
            status.HTTP_404_NOT_FOUND: ExceptionSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ExceptionSerializer,
        },
    ),
    price_logic_rules_bulk_update=extend_schema(
        summary=_("Bulk configure price logic rules"),
        description=_(
            "By sending a list of FormPriceLogic to this endpoint, all the FormPriceLogic related to the form will be "
            "replaced with the data sent to the endpoint."
        ),
        tags=["logic-rules"],
        request=FormPriceLogicListSerializer,
        responses={
            status.HTTP_200_OK: FormPriceLogicListSerializer,
            status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
            status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
            status.HTTP_403_FORBIDDEN: ExceptionSerializer,
            status.HTTP_404_NOT_FOUND: ExceptionSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ExceptionSerializer,
        },
    ),
)
class FormViewSet(viewsets.ModelViewSet):
    """
    Manage forms.

    Forms are collections of form steps, where each form step points to a formio.js
    form definition. Multiple definitions are combined in logical steps to build a
    multi-step/page form for end-users to fill out. Form definitions can be (and are)
    re-used among different forms.

    **Warning: the response data depends on user permissions**

    Non-staff users receive a subset of the documented fields which are used
    for internal form configuration. These fields are:

    {admin_fields}
    """

    parser_classes = (FormCamelCaseJSONParser,)
    renderer_classes = (FormCamelCaseJSONRenderer,)
    queryset = Form.objects.all().prefetch_related(
        Prefetch(
            "formstep_set",
            queryset=FormStep.objects.select_related("form_definition").order_by(
                "order"
            ),
        )
    )
    lookup_url_kwarg = "uuid_or_slug"
    # lookup_value_regex = "[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}"
    serializer_class = FormSerializer
    permission_classes = [FormAPIPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # if not staff then only show active
            queryset = queryset.filter(active=True).filter(_is_deleted=False)
        elif self.action == "list":
            # So that the admin can display deleted forms, but the list endpoint doesn't return them
            queryset = queryset.filter(_is_deleted=False)

        # ⚡️ - the prefetches are not required for the variables/logic bulk (update/read)
        # endpoints, so we clear prefetches and select_related calls.
        if self.action in (
            "variables_bulk_update",
            "variables_list",
            "logic_rules_bulk_update",
            "logic_rules_list",
            "price_logic_rules_bulk_update",
            "price_logic_rules_list",
        ):
            queryset = queryset.select_related(None).prefetch_related(None)

        return queryset

    def get_serializer(self, *args, **kwargs):
        # overridden so that drf-spectacular calls this rather than using get_serializer_class,
        # as we need the request in the serializer context
        return super().get_serializer(*args, **kwargs)

    def initialize_request(self, request, *args, **kwargs):
        """
        Method overridden to account for the lookup on uuid OR slug.
        """
        request = super().initialize_request(request, *args, **kwargs)

        if not self.kwargs:
            return request

        # mutate self.kwargs based on the type of the lookup_value
        lookup_value = self.kwargs[self.lookup_url_kwarg]
        try:
            UUID(lookup_value)
            self.lookup_field = "uuid"
        except (TypeError, ValueError, AttributeError):  # not a valid UUID
            self.lookup_field = "slug"

        return request

    @extend_schema(
        summary=_("Copy form"),
        tags=["forms"],
        request=None,
        responses={status.HTTP_201_CREATED: FormSerializer},
        parameters=[
            UUID_OR_SLUG_PARAMETER,
            OpenApiParameter(
                name="Location",
                type=OpenApiTypes.URI,
                location=OpenApiParameter.HEADER,
                description="URL of the created resource",
                response=[status.HTTP_201_CREATED],
            ),
        ],
    )
    @transaction.atomic
    @action(
        detail=True, methods=["post"], authentication_classes=(TokenAuthentication,)
    )
    def copy(self, request, *args, **kwargs):
        """
        Create a copy of a form.

        Copying a form copies the meta-data of the form and the steps included.
        Referenced form definitions inside the form steps are re-used instead of
        new copies being created.
        """
        instance = self.get_object()
        copied_form = instance.copy()
        copied_form.refresh_from_db()  # this clears any prefetch caches
        serializer = self.get_serializer(instance=copied_form)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        summary=_("Export form"),
        tags=["forms"],
        parameters=[UUID_OR_SLUG_PARAMETER],
        request=None,
        responses={
            (
                status.HTTP_200_OK,
                "application/zip",
            ): OpenApiTypes.BINARY
        },
    )
    @action(
        detail=True, methods=["post"], authentication_classes=(TokenAuthentication,)
    )
    def export(self, request, *args, **kwargs):
        """
        Export a form with the related steps and form definitions as a ZIP-file.

        The exported ZIP-file can be used to import complete forms.
        """
        instance = self.get_object()

        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = f"attachment;filename={instance.slug}.zip"

        export_form(instance.id, response=response)

        response["Content-Length"] = len(response.content)
        return response

    @extend_schema(
        summary=_("Activate the default language for a Form"),
        tags=["forms"],
        request=None,
        responses={status.HTTP_200_OK: CurrentLanguageSerializer},
        parameters=[UUID_OR_SLUG_PARAMETER],
    )
    @transaction.atomic
    @action(
        detail=True,
        methods=["post"],
        authentication_classes=(),
        permission_classes=(),
    )
    def activate_default_language(self, request, *args, **kwargs):
        """
        Activate the default language of a form.

        In case translation is not enabled for the Form, the default language is set to
        settings.LANGUAGE_CODE.
        """
        form = self.get_object()
        response = Response(status=status.HTTP_200_OK)
        current_language = translation.get_language()
        if not form.translation_enabled:
            translation.activate(settings.LANGUAGE_CODE)
            current_language = translation.get_language()
            set_language_cookie(response, current_language)

        response.data = CurrentLanguageSerializer(
            instance={"active_language": current_language}
        ).data
        return response

    def perform_destroy(self, instance):
        instance._is_deleted = True
        instance.save()

    @extend_schema(
        summary=_("Prepare form edit admin message"),
        tags=["admin"],
        parameters=[UUID_OR_SLUG_PARAMETER],
        request=FormAdminMessageSerializer,
        responses={
            status.HTTP_201_CREATED: FormAdminMessageSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=(permissions.IsAdminUser,),
        url_path="admin-message",
    )
    def admin_message(self, request, *args, **kwargs):
        """
        Prepare the relevant message to be displayed in the admin.

        On form create/update, a success message is displayed to the end user on
        page reload. This exact message varies with the type of submit action that was
        performed and whether the object was created or updated.

        This endpoint is only available for staff users and prepares messages for display
        in the admin environment.
        """
        form = self.get_object()
        serializer = FormAdminMessageSerializer(
            data=request.data,
            context={"request": request, "form": form},
        )
        serializer.is_valid(raise_exception=True)
        add_success_message(
            request,
            form,
            serializer.validated_data["submit_action"],
            serializer.validated_data["is_create"],
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["put"],
        url_path="variables",
        url_name="variables",
    )
    @transaction.atomic
    def variables_bulk_update(self, request, *args, **kwargs):
        form = self.get_object()
        form_variables = form.formvariable_set.all()
        # We expect that all the variables that should be associated with a form come in the request.
        # So we can delete any existing variables because they will be replaced.
        form_variables.delete()

        serializer = FormVariableSerializer(
            data=request.data,
            many=True,
            context={
                "request": request,
                "form": form,
                # context for :class:`openforms.api.fields.RelatedFieldFromContext` lookups
                "forms": {str(form.uuid): form},
                "form_definitions": {
                    str(fd.uuid): fd
                    for fd in FormDefinition.objects.filter(
                        formstep__form=form
                    ).distinct()
                },
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        recouple_submission_variables_to_form_variables.delay(form.id)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary=_("List form variables"),
        description=_("List all variables defined for a form."),
        tags=["forms"],
        request=FormVariableListSerializer,
        responses={
            status.HTTP_200_OK: FormVariableListSerializer,
            status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
            status.HTTP_403_FORBIDDEN: ExceptionSerializer,
            status.HTTP_404_NOT_FOUND: ExceptionSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ExceptionSerializer,
        },
        parameters=[
            OpenApiParameter(
                name="source",
                description=_("Filter by form variable source"),
                type=str,
                enum=FormVariableSources.values,
            )
        ],
    )
    @variables_bulk_update.mapping.get
    def variables_list(self, request, *args, **kwargs):
        form = self.get_object()
        filterset = FormVariableFilter(
            request.GET,
            queryset=form.formvariable_set.select_related("form", "form_definition"),
        )

        serializer = FormVariableSerializer(
            instance=filterset.qs,
            many=True,
            context={"request": request, "form": form},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["put"],
        url_path="logic-rules",
        url_name="logic-rules",
    )
    @transaction.atomic
    def logic_rules_bulk_update(self, request, *args, **kwargs):
        form = self.get_object()
        logic_rules = form.formlogic_set.all()
        # We expect that all the logic rules associated with a form come in the request.
        # So we can delete any existing rule because they will be replaced.
        logic_rules.delete()

        serializer = FormLogicSerializer(
            data=request.data,
            many=True,
            context={
                "request": request,
                "form": form,
                # context for :class:`openforms.api.fields.RelatedFieldFromContext` lookups
                "forms": {str(form.uuid): form},
                "form_variables": FormVariableWrapper(form),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary=_("List logic rules"),
        description=_("List all logic rules defined for a form."),
        tags=["logic-rules"],
        request=FormLogicListSerializer,
        responses={
            status.HTTP_200_OK: FormLogicListSerializer,
            status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
            status.HTTP_403_FORBIDDEN: ExceptionSerializer,
            status.HTTP_404_NOT_FOUND: ExceptionSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ExceptionSerializer,
        },
    )
    @logic_rules_bulk_update.mapping.get
    def logic_rules_list(self, request, *args, **kwargs):
        form = self.get_object()
        logic_rules = form.formlogic_set.all()

        serializer = FormLogicSerializer(
            instance=logic_rules,
            many=True,
            context={"request": request, "form": form},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["put"],
        url_path="price-logic-rules",
        url_name="price-logic-rules",
    )
    @transaction.atomic
    def price_logic_rules_bulk_update(self, request, *args, **kwargs):
        form = self.get_object()
        price_logic_rules = form.formpricelogic_set.all()
        # We expect that all the price logic rules associated with a form come in the request.
        # So we can delete any existing rule because they will be replaced.
        price_logic_rules.delete()

        serializer = FormPriceLogicSerializer(
            data=request.data,
            many=True,
            context={
                "request": request,
                "form": form,
                # context for :class:`openforms.api.fields.RelatedFieldFromContext` lookups
                "forms": {str(form.uuid): form},
                "form_variables": FormVariableWrapper(form),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary=_("List price logic rules"),
        description=_("List all price logic rules defined for a form."),
        tags=["logic-rules"],
        request=FormPriceLogicListSerializer,
        responses={
            status.HTTP_200_OK: FormPriceLogicListSerializer,
            status.HTTP_401_UNAUTHORIZED: ExceptionSerializer,
            status.HTTP_403_FORBIDDEN: ExceptionSerializer,
            status.HTTP_404_NOT_FOUND: ExceptionSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ExceptionSerializer,
        },
    )
    @price_logic_rules_bulk_update.mapping.get
    def price_logic_rules_list(self, request, *args, **kwargs):
        form = self.get_object()
        price_logic_rules = form.formpricelogic_set.all()

        serializer = FormPriceLogicSerializer(
            instance=price_logic_rules,
            many=True,
            context={"request": request, "form": form},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


FormViewSet.__doc__ = inspect.getdoc(FormViewSet).format(
    admin_fields=_FORM_ADMIN_FIELDS_MARKDOWN
)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="form_uuid_or_slug",
            location=OpenApiParameter.PATH,
            type=str,
            description=_("Either a UUID4 or a slug identifying the form."),
        )
    ]
)
@extend_schema_view(
    create=extend_schema(
        summary=_("Save form version"),
        tags=["forms"],
    ),
    restore=extend_schema(
        summary=_("Restore form version"),
        tags=["forms"],
        parameters=[
            OpenApiParameter(
                name="form_uuid_or_slug",
                location=OpenApiParameter.PATH,
                type=str,
                description=_("Either a UUID4 or a slug identifying the form."),
            ),
            OpenApiParameter(
                name="uuid",
                location=OpenApiParameter.PATH,
                type=str,
                description=_("The UUID of the form version"),
            ),
        ],
        responses={status.HTTP_204_NO_CONTENT: ""},
    ),
    list=extend_schema(
        summary=_("List form versions"),
        tags=["forms"],
        parameters=[
            OpenApiParameter(
                name="form_uuid_or_slug",
                location=OpenApiParameter.PATH,
                type=str,
                description=_("Either a UUID4 or a slug identifying the form."),
            )
        ],
    ),
)
class FormVersionViewSet(NestedViewSetMixin, ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FormVersionSerializer
    queryset = FormVersion.objects.all()
    permission_classes = [FormAPIPermissions]
    lookup_field = "uuid"
    parent_lookup_kwargs = {"form_uuid_or_slug": "form__uuid"}

    def create(self, request, *args, **kwargs):
        """Save the current version of the form so that it can later be retrieved"""

        form = get_object_or_404(Form, uuid=self.kwargs["form_uuid_or_slug"])
        form_version = FormVersion.objects.create_for(
            form=form,
            user=request.user,
        )
        serializer = self.serializer_class(instance=form_version)
        return Response(status=status.HTTP_201_CREATED, data=serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        """Restore a previously saved version of a form."""
        form = get_object_or_404(Form, uuid=self.kwargs["form_uuid_or_slug"])
        form_version = get_object_or_404(FormVersion, uuid=self.kwargs["uuid"])

        form.restore_old_version(form_version.uuid, user=request.user)

        return Response(status=status.HTTP_201_CREATED)


class FormsImportAPIView(views.APIView):
    serializer_class = FormImportSerializer
    parser_classes = (parsers.FileUploadParser,)
    authentication_classes = [TokenAuthentication]
    permission_classes = [FormAPIPermissions]

    @extend_schema(
        summary=_("Import form"),
        tags=["forms"],
        responses={"204": {"description": _("No response body")}},
    )
    def post(self, request, *args, **kwargs):
        """
        Import a Form by uploading a .zip file containing a Form, FormDefinitions
        and FormSteps
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        import_form(serializer.validated_data["file"])

        return response.Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # TODO this permission isn't ideal with its mix of public and write access
    permission_classes = [FormAPIPermissions]
    pagination_class = None
    lookup_field = "uuid"
