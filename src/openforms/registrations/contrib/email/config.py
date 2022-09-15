from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import DjangoTemplateValidator

from .constants import AttachmentFormat


class EmailOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        label=_("The email addresses to which the submission details will be sent"),
        required=True,
    )
    attachment_formats = serializers.ListField(
        child=serializers.ChoiceField(choices=AttachmentFormat),
        label=_("The format(s) of the attachment(s) containing the submission details"),
        required=False,
    )
    payment_emails = serializers.ListField(
        child=serializers.EmailField(),
        label=_(
            "The email addresses to which the payment status update will be sent "
            "(defaults to general registration addresses)"
        ),
        required=False,
    )
    attach_files_to_email = serializers.BooleanField(
        label=_("attach files to email"),
        allow_null=True,
        default=None,  # falls back to the global default
        help_text=_(
            "Enable to attach file uploads to the registration email. If set, this "
            "overrides the global default. Form designers should take special care to "
            "ensure that the total file upload sizes do not exceed the email size limit."
        ),
    )
    email_subject = serializers.CharField(
        label=_("Email subject"),
        help_text=_(
            "Subject of the email sent to the registration backend. You can use "
            "the expressions '{{ form_name }}' and '{{ submission_reference }}' "
            "to include the form name and the reference number to the submission "
            "in the subject. Additionally, all the form variables are available with "
            "the 'vars' prefix, e.g.: '{{ vars.environment }}'."
        ),
        required=False,
        validators=[DjangoTemplateValidator()],
    )
