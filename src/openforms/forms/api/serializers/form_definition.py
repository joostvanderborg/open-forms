from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from openforms.api.serializers import PublicFieldsSerializerMixin
from openforms.formio.service import update_configuration_for_request
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ...models import Form, FormDefinition
from ...validators import validate_form_definition_is_reusable
from ..validators import FormIOComponentsValidator, validate_template_expressions


class UsedInFormSerializer(serializers.HyperlinkedModelSerializer):
    admin_url = serializers.SerializerMethodField(
        label=_("admin URL"),
        help_text=_("Link to the change/view page in the admin interface"),
    )

    class Meta:
        model = Form
        fields = (
            "url",
            "uuid",
            "name",
            "active",
            "admin_url",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
            "name": {
                "source": "admin_name",
            },
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_admin_url(self, obj: Form) -> str:
        admin_url = reverse("admin:forms_form_change", args=(obj.pk,))
        request = self.context.get("request")
        if not request:
            return admin_url
        return request.build_absolute_uri(admin_url)


class FormDefinitionSerializer(
    PublicFieldsSerializerMixin, serializers.HyperlinkedModelSerializer
):
    translations = ModelTranslationsSerializer(required=False)

    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)
        # set upload urls etc
        # TODO: move this to openforms.formio.dynamic_config
        update_configuration_for_request(
            instance.configuration_wrapper, request=self.context["request"]
        )
        representation["configuration"] = instance.configuration_wrapper.configuration
        return representation

    class Meta:
        model = FormDefinition
        fields = (
            "url",
            "uuid",
            "name",
            "internal_name",
            "slug",
            "configuration",
            "login_required",
            "is_reusable",
            "translations",
        )
        public_fields = (
            "url",
            "uuid",
            "name",
            "internal_name",
            "slug",
            "configuration",
            "login_required",
            "is_reusable",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:formdefinition-detail",
                "lookup_field": "uuid",
            },
            "configuration": {
                "validators": [
                    FormIOComponentsValidator(),
                    validate_template_expressions,
                ],
            },
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance:
            validate_form_definition_is_reusable(
                self.instance, new_value=attrs.get("is_reusable")
            )
        return attrs

    def get_model_class(self):
        return self.Meta.model


class FormDefinitionDetailSerializer(FormDefinitionSerializer):
    used_in = UsedInFormSerializer(
        many=True,
        label=_("Used in forms"),
        help_text=_(
            "The collection of forms making use of this definition. This includes both "
            "active and inactive forms."
        ),
    )

    class Meta(FormDefinitionSerializer.Meta):
        fields = FormDefinitionSerializer.Meta.fields + ("used_in",)
        public_fields = FormDefinitionSerializer.Meta.public_fields + ("used_in",)
