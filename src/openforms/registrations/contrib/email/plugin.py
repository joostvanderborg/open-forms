import html
from mimetypes import types_map
from typing import List, NoReturn, Optional, Tuple, TypedDict

from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

from openforms.emails.utils import send_mail_html, strip_tags_plus
from openforms.submissions.exports import create_submission_export
from openforms.submissions.models import Submission
from openforms.submissions.rendering.constants import RenderModes
from openforms.submissions.rendering.renderer import Renderer
from openforms.submissions.tasks.registration import set_submission_reference
from openforms.template import render_from_string

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference
from ...registry import register
from .checks import check_config
from .config import EmailOptionsSerializer
from .constants import AttachmentFormat
from .models import EmailConfig


class EmailOptions(TypedDict):
    to_emails: List[str]
    attachment_formats: List[str]
    payment_emails: List[str]
    attach_files_to_email: Optional[bool]
    email_subject: Optional[str]


@register("email")
class EmailRegistration(BasePlugin):
    verbose_name = _("Email registration")
    configuration_options = EmailOptionsSerializer

    def register_submission(
        self, submission: Submission, options: EmailOptions
    ) -> None:
        config = EmailConfig.get_solo()
        config.apply_defaults_to(options)

        # explicitly get a reference before registering
        set_submission_reference(submission)

        subject_template = options.get("email_subject") or ugettext(
            "[Open Forms] {{ form_name }} - submission {{ submission_reference }}"
        )
        subject = render_from_string(
            subject_template,
            {
                "form_name": submission.form.admin_name,
                "submission_reference": submission.public_registration_reference,
            },
        )

        self.send_registration_email(options["to_emails"], subject, submission, options)

    @staticmethod
    def render_registration_email(submission, extra_context=None):
        if extra_context is None:
            extra_context = {}

        # resolve the base templates
        html_template = get_template("emails/email_registration.html")
        text_template = get_template("emails/email_registration.txt")

        # common kwargs and context
        renderer_kwargs = {
            "submission": submission,
            "mode": RenderModes.registration,
        }
        base_context = {
            "public_reference": submission.public_registration_reference,
            "datetime": timezone.localtime(submission.completed_on).strftime(
                "%H:%M:%S %d-%m-%Y"
            ),
        }

        # HTML mode
        html_renderer = Renderer(as_html=True, **renderer_kwargs)
        html_content = html_template.render(
            {
                **base_context,
                "renderer": html_renderer,
                "rendering_text": False,
                **extra_context,
            }
        )

        # Plain text mode
        text_renderer = Renderer(as_html=False, **renderer_kwargs)
        text_content = text_template.render(
            {
                **base_context,
                "renderer": text_renderer,
                "rendering_text": True,
                **extra_context,
            }
        )
        # post process since the mail template has html markup and django escaped entities
        text_content = strip_tags_plus(text_content, keep_leading_whitespace=True)
        text_content = html.unescape(text_content)

        return html_content, text_content

    def send_registration_email(
        self,
        recipients,
        subject,
        submission: Submission,
        options: EmailOptions,
        extra_context=None,
    ):
        html_content, text_content = self.render_registration_email(
            submission, extra_context=extra_context
        )

        attachments = []

        # per form or global default to attach file uploads to the e-mail directly.
        # NOTE that it's explicitly the responsibility of the form designer to ensure
        # the total attachment size is below the SMTP server limit. We do not perform
        # any checking of that as it'd rely on complex configuration and/or guesswork.
        if options.get("attach_files_to_email"):
            attachments += [
                (
                    file_attachment.get_display_name(),
                    file_attachment.content.read(),
                    file_attachment.content_type,
                )
                for file_attachment in submission.attachments
            ]

        attachment_formats = options.get("attachment_formats", [])
        for attachment_format in attachment_formats:
            mime_type = types_map[f".{attachment_format}"]
            if attachment_format in [AttachmentFormat.csv, AttachmentFormat.xlsx]:
                export_data = create_submission_export(
                    Submission.objects.filter(pk=submission.pk).select_related(
                        "auth_info"
                    )
                ).export(attachment_format)

                attachment = (
                    f"{submission.form.admin_name} - submission.{attachment_format}",
                    export_data,
                    mime_type,
                )
                attachments.append(attachment)
            elif attachment_format == AttachmentFormat.pdf:
                attachment = (
                    f"{submission.report.title}.pdf",
                    submission.report.content.read(),
                    mime_type,
                )
                attachments.append(attachment)

        send_mail_html(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
            attachment_tuples=attachments,
            text_message=text_content,
        )

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("Email plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission", options: dict):
        subject = _(
            "[Open Forms] {form_name} - submission payment received {public_reference}"
        ).format(
            form_name=submission.form.admin_name,
            public_reference=submission.public_registration_reference,
        )
        recipients = options.get("payment_emails")
        if not recipients:
            recipients = options["to_emails"]

        extra_context = {
            # switch in the template
            "payment_received": True,
            # note: it is not a feature (yet) but the model supports multiple payments
            "payment_order_id": ", ".join(
                map(str, submission.payments.get_completed_public_order_ids())
            ),
        }
        self.send_registration_email(
            recipients, subject, submission, options, extra_context
        )

    def check_config(self):
        check_config()

    def get_config_actions(self) -> List[Tuple[str, str]]:
        return [
            (_("Test"), reverse("admin_email_test")),
        ]
