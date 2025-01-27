# Generated by Django 3.2.15 on 2022-09-16 13:39
import colorsys
import functools
import re

import django.contrib.postgres.fields.jsonb
import django.core.validators
import django.db.migrations.operations.special
from django.db import migrations, models

import colorfield.fields
import tinymce.models

import openforms.config.models
import openforms.emails.validators
import openforms.payments.validators
import openforms.utils.translations
import openforms.utils.validators

# default colors from CKEditor source code (in CSS HSL format)
# via https://github.com/ckeditor/ckeditor5/blob/master/packages/ckeditor5-font/src/fontcolor/fontcolorediting.js
default_cke_values = [
    {"color": "hsl(0, 0%, 0%)", "label": "Black"},
    {"color": "hsl(0, 0%, 30%)", "label": "Dim grey"},
    {"color": "hsl(0, 0%, 60%)", "label": "Grey"},
    {"color": "hsl(0, 0%, 90%)", "label": "Light grey"},
    {
        "color": "hsl(0, 0%, 100%)",
        "label": "White",
    },
    {"color": "hsl(0, 75%, 60%)", "label": "Red"},
    {"color": "hsl(30, 75%, 60%)", "label": "Orange"},
    {"color": "hsl(60, 75%, 60%)", "label": "Yellow"},
    {"color": "hsl(90, 75%, 60%)", "label": "Light green"},
    {"color": "hsl(120, 75%, 60%)", "label": "Green"},
    {"color": "hsl(150, 75%, 60%)", "label": "Aquamarine"},
    {"color": "hsl(180, 75%, 60%)", "label": "Turquoise"},
    {"color": "hsl(210, 75%, 60%)", "label": "Light blue"},
    {"color": "hsl(240, 75%, 60%)", "label": "Blue"},
    {"color": "hsl(270, 75%, 60%)", "label": "Purple"},
]


def hsl_to_rgbhex(hsl_css_color):
    exp = "^hsl\((\d+), (\d+)%, (\d+)%\)$"
    m = re.match(exp, hsl_css_color)
    if m:
        h = int(m.group(1))
        s = int(m.group(2))
        l = int(m.group(3))

        # conversion algorithm via https://stackoverflow.com/questions/41403936/converting-hsl-to-hex-in-python3
        rgb = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
        hex = "#%02x%02x%02x" % (
            round(rgb[0] * 255),
            round(rgb[1] * 255),
            round(rgb[2] * 255),
        )
        return hex


def add_colors(apps, schema_editor):
    RichTextColor = apps.get_model("config", "RichTextColor")

    for elem in default_cke_values:
        hex_color = hsl_to_rgbhex(elem["color"])
        if not hex_color:
            continue
        RichTextColor.objects.create(label=elem["label"], color=hex_color)


def remove_colors(apps, schema_editor):
    RichTextColor = apps.get_model("config", "RichTextColor")
    RichTextColor.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0001_initial_squashed_0022_merge_20210903_1228"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="ask_privacy_consent",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, the user will have to agree to the privacy policy before submitting a form.",
                verbose_name="ask privacy consent",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="privacy_policy_label",
            field=tinymce.models.HTMLField(
                blank=True,
                default="Ja, ik heb kennis genomen van het {% privacy_policy %} en geef uitdrukkelijk toestemming voor het verwerken van de door mij opgegeven gegevens.",
                help_text="The label of the checkbox that prompts the user to agree to the privacy policy.",
                verbose_name="privacy policy label",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="privacy_policy_url",
            field=models.URLField(
                blank=True,
                help_text="URL to the privacy policy",
                verbose_name="privacy policy URL",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="payment_order_id_prefix",
            field=models.CharField(
                blank=True,
                default="{year}",
                help_text="Prefix to apply to generated numerical order IDs. Alpha-numerical only, supports placeholder {year}.",
                max_length=16,
                validators=[
                    openforms.payments.validators.validate_payment_order_id_prefix
                ],
                verbose_name="Payment Order ID prefix",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="confirmation_email_content",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models._render,
                    *("emails/confirmation/content.html",),
                    **{}
                ),
                help_text="Content of the confirmation email message. Can be overridden on the form level",
                validators=[openforms.utils.validators.DjangoTemplateValidator()],
                verbose_name="content",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="confirmation_email_subject",
            field=models.CharField(
                default=functools.partial(
                    openforms.config.models._render,
                    *("emails/confirmation/subject.txt",),
                    **{}
                ),
                help_text="Subject of the confirmation email message. Can be overridden on the form level",
                max_length=1000,
                validators=[openforms.utils.validators.DjangoTemplateValidator()],
                verbose_name="subject",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="submission_confirmation_template",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.utils.translations.get_default,
                    *("Thank you for submitting this form.",),
                    **{}
                ),
                help_text="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data.",
                verbose_name="submission confirmation template",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_session_timeout",
            field=models.PositiveIntegerField(
                default=15,
                help_text="Amount of time in minutes a user filling in a form can be inactive for before being logged out",
                validators=[
                    django.core.validators.MinValueValidator(5),
                    django.core.validators.MaxValueValidator(
                        15,
                        message="Due to DigiD requirements this value has to be less than or equal to %(limit_value)s minutes.",
                    ),
                ],
                verbose_name="form session timeout",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="confirmation_email_content",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models._render,
                    *("emails/confirmation/content.html",),
                    **{}
                ),
                help_text="Content of the confirmation email message. Can be overridden on the form level",
                validators=[
                    openforms.utils.validators.DjangoTemplateValidator(
                        required_template_tags=[
                            "appointment_information",
                            "payment_information",
                        ]
                    ),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="content",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="submission_confirmation_template",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.utils.translations.get_default,
                    *("Thank you for submitting this form.",),
                    **{}
                ),
                help_text="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data.",
                validators=[openforms.utils.validators.DjangoTemplateValidator()],
                verbose_name="submission confirmation template",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="design_token_values",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Values of various style parameters, such as border radii, background colors... Note that this is advanced usage. Any available but un-specified values will use fallback default values. See https://open-forms.readthedocs.io/en/latest/installation/form_hosting.html#run-time-configuration for documentation.",
                verbose_name="design token values",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="plugin_configuration",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Configuration of plugins for authentication, payments, prefill, registrations and validation",
                verbose_name="plugin configuration",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_display_required_with_asterisk",
            field=models.BooleanField(
                default=True,
                help_text="If checked, required fields are marked with an asterisk and optional fields are unmarked. If unchecked, optional fields will be marked with '(optional)' and required fields are unmarked.",
                verbose_name="Mark required fields with asterisks",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_fields_required_default",
            field=models.BooleanField(
                default=False,
                help_text="Whether the checkbox 'required' on form fields should be checked by default.",
                verbose_name="Mark form fields 'required' by default",
            ),
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="enable_react_form",
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="registration_attempt_limit",
            field=models.PositiveIntegerField(
                default=5,
                help_text="How often we attempt to register the submission at the registration backend before giving up",
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="default registration backend attempt limit",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="enable_form_variables",
            field=models.BooleanField(
                default=False,
                help_text="Whether to enable form variables in the form builder.",
                verbose_name="enable form variables",
            ),
        ),
        migrations.CreateModel(
            name="RichTextColor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "color",
                    colorfield.fields.ColorField(
                        default="#FFFFFF",
                        help_text="Color in RGB hex format (#RRGGBB)",
                        image_field=None,
                        max_length=18,
                        samples=None,
                        verbose_name="color",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="Human readable label for reference",
                        max_length=64,
                        verbose_name="label",
                    ),
                ),
            ],
            options={
                "verbose_name": "text editor color preset",
                "verbose_name_plural": "text editor color presets",
                "ordering": ("label",),
            },
        ),
        migrations.RunPython(code=add_colors, reverse_code=remove_colors),
        migrations.CreateModel(
            name="CSPSetting",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "directive",
                    models.CharField(
                        choices=[
                            ("default-src", "default-src"),
                            ("script-src", "script-src"),
                            ("script-src-attr", "script-src-attr"),
                            ("script-src-elem", "script-src-elem"),
                            ("img-src", "img-src"),
                            ("object-src", "object-src"),
                            ("prefetch-src", "prefetch-src"),
                            ("media-src", "media-src"),
                            ("frame-src", "frame-src"),
                            ("font-src", "font-src"),
                            ("connect-src", "connect-src"),
                            ("style-src", "style-src"),
                            ("style-src-attr", "style-src-attr"),
                            ("style-src-elem", "style-src-elem"),
                            ("base-uri", "base-uri"),
                            ("child-src", "child-src"),
                            ("frame-ancestors", "frame-ancestors"),
                            ("navigate-to", "navigate-to"),
                            ("form-action", "form-action"),
                            ("sandbox", "sandbox"),
                            ("report-uri", "report-uri"),
                            ("report-to", "report-to"),
                            ("manifest-src", "manifest-src"),
                            ("worker-src", "worker-src"),
                            ("plugin-types", "plugin-types"),
                            ("require-sri-for", "require-sri-for"),
                        ],
                        help_text="CSP header directive",
                        max_length=64,
                        verbose_name="directive",
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        help_text="CSP header value",
                        max_length=128,
                        verbose_name="value",
                    ),
                ),
            ],
            options={
                "ordering": ("directive", "value"),
            },
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="theme_classname",
            field=models.SlugField(
                blank=True,
                help_text="If provided, this class name will be set on the <html> element.",
                verbose_name="theme CSS class name",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="theme_stylesheet",
            field=models.URLField(
                blank=True,
                help_text="The URL stylesheet with theme-specific rules for your organization. This will be included as final stylesheet, overriding previously defined styles. Note that you also have to include the host to the `style-src` CSP directive. Example value: https://unpkg.com/@utrecht/design-tokens@1.0.0-alpha.20/dist/index.css.",
                max_length=1000,
                validators=[
                    django.core.validators.RegexValidator(
                        message="The URL must point to a CSS resource (.css extension).",
                        regex="\\.css$",
                    )
                ],
                verbose_name="theme stylesheet URL",
            ),
        ),
    ]
