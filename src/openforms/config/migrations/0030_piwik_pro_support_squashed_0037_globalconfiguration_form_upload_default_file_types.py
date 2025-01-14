# Generated by Django 3.2.15 on 2022-09-16 13:46

import functools

import django.core.validators
import django.db.migrations.operations.special
from django.db import migrations, models

import django_better_admin_arrayfield.models.fields
import tinymce.models

import openforms.config.models
import openforms.emails.validators
import openforms.utils.validators
from openforms.analytics_tools.constants import AnalyticsTools
from openforms.analytics_tools.utils import (
    get_cookies,
    get_csp,
    get_domain_hash,
    update_analytical_cookies,
    update_csp,
)

# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:


def move_analytics_config(apps, _):

    AnalyticsToolsConfiguration = apps.get_model(
        "analytics_tools", "AnalyticsToolsConfiguration"
    )
    GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")

    analytics_config = AnalyticsToolsConfiguration.objects.first()
    config = GlobalConfiguration.objects.first()

    if not (analytics_config and config):
        return

    analytics_config.analytics_cookie_consent_group = (
        config.analytics_cookie_consent_group
    )

    # Google analytics
    analytics_config.gtm_code = config.gtm_code
    analytics_config.ga_code = config.ga_code
    if (
        analytics_config.gtm_code
        and analytics_config.ga_code
        and analytics_config.analytics_cookie_consent_group
    ):
        analytics_config.enable_google_analytics = True
        cookies = get_cookies(AnalyticsTools.google_analytics, [])
        csp = get_csp(AnalyticsTools.google_analytics, [])
        update_analytical_cookies(
            cookies, True, analytics_config.analytics_cookie_consent_group.id
        )
        update_csp(csp, True)

    # Matomo
    analytics_config.matomo_url = config.matomo_url
    analytics_config.matomo_site_id = config.matomo_site_id
    if (
        analytics_config.matomo_url
        and analytics_config.matomo_site_id
        and analytics_config.analytics_cookie_consent_group
    ):
        analytics_config.enable_matomo_site_analytics = True
        string_replacements_list = [
            ("SITE_ID", analytics_config.matomo_site_id),
            ("SITE_URL", analytics_config.matomo_url),
            (
                "DOMAIN_HASH",
                lambda cookie: get_domain_hash(
                    settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                ),
            ),
        ]
        cookies = get_cookies(AnalyticsTools.matomo, string_replacements_list)
        csp = get_csp(AnalyticsTools.matomo, string_replacements_list)
        update_analytical_cookies(
            cookies, True, analytics_config.analytics_cookie_consent_group.id
        )
        update_csp(csp, True)

    # Piwik
    analytics_config.piwik_url = config.piwik_url
    analytics_config.piwik_site_id = config.piwik_site_id
    if (
        analytics_config.piwik_url
        and analytics_config.piwik_site_id
        and analytics_config.analytics_cookie_consent_group
    ):
        analytics_config.enable_piwik_site_analytics = True
        string_replacements_list = [
            ("SITE_ID", analytics_config.piwik_site_id),
            ("SITE_URL", analytics_config.piwik_url),
            (
                "DOMAIN_HASH",
                lambda cookie: get_domain_hash(
                    settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                ),
            ),
        ]
        cookies = get_cookies(AnalyticsTools.piwik, string_replacements_list)
        csp = get_csp(AnalyticsTools.piwik, string_replacements_list)
        update_analytical_cookies(
            cookies, True, analytics_config.analytics_cookie_consent_group.id
        )
        update_csp(csp, True)

    # Piwik Pro
    analytics_config.piwik_pro_url = config.piwik_pro_url
    analytics_config.piwik_pro_site_id = config.piwik_pro_site_id
    if (
        analytics_config.piwik_pro_url
        and analytics_config.piwik_pro_site_id
        and analytics_config.analytics_cookie_consent_group
    ):
        analytics_config.enable_piwik_pro_site_analytics = True
        string_replacements_list = [
            ("SITE_ID", analytics_config.piwik_pro_site_id),
            ("SITE_URL", analytics_config.piwik_pro_url),
            (
                "DOMAIN_HASH",
                lambda cookie: get_domain_hash(
                    settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                ),
            ),
        ]
        cookies = get_cookies(AnalyticsTools.piwik_pro, string_replacements_list)
        csp = get_csp(AnalyticsTools.piwik_pro, string_replacements_list)
        update_analytical_cookies(
            cookies, True, analytics_config.analytics_cookie_consent_group.id
        )
        update_csp(csp, True)

    # SiteImprove
    analytics_config.siteimprove_id = config.siteimprove_id
    if (
        analytics_config.siteimprove_id
        and analytics_config.analytics_cookie_consent_group
    ):
        analytics_config.enable_siteimprove_analytics = True
        cookies = get_cookies(AnalyticsTools.siteimprove, [])
        csp = get_csp(AnalyticsTools.siteimprove, [])
        update_analytical_cookies(
            cookies, True, analytics_config.analytics_cookie_consent_group.id
        )
        update_csp(csp, True)

    analytics_config.save()


# openforms.config.migrations.0031_move_analytics_tools_data


class Migration(migrations.Migration):

    dependencies = [
        ("analytics_tools", "0001_initial"),
        ("config", "0029_rename_design_tokens"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="piwik_pro_site_id",
            field=models.UUIDField(
                blank=True,
                help_text="The 'idsite' of the website you're tracking in Piwik PRO. https://help.piwik.pro/support/questions/find-website-id/",
                null=True,
                verbose_name="Piwik PRO site ID",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="piwik_pro_url",
            field=models.CharField(
                blank=True,
                help_text="The base URL of your Piwik PRO server, e.g. 'https://your-instance-name.piwik.pro/'.",
                max_length=255,
                verbose_name="Piwik PRO server URL",
            ),
        ),
        migrations.RunPython(
            code=move_analytics_config, reverse_code=migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="analytics_cookie_consent_group",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="ga_code",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="gtm_code",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="matomo_site_id",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="matomo_url",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="piwik_pro_site_id",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="piwik_pro_url",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="piwik_site_id",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="piwik_url",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="siteimprove_id",
        ),
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="enable_form_variables",
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="save_form_email_content",
            field=tinymce.models.HTMLField(
                default=functools.partial(
                    openforms.config.models._render,
                    *("emails/save_form/content.html",),
                    **{}
                ),
                help_text="Content of the save form email message.",
                validators=[
                    openforms.utils.validators.DjangoTemplateValidator(),
                    openforms.emails.validators.URLSanitationValidator(),
                ],
                verbose_name="content",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="save_form_email_subject",
            field=models.CharField(
                default=functools.partial(
                    openforms.config.models._render,
                    *("emails/save_form/subject.txt",),
                    **{}
                ),
                help_text="Subject of the save form email message.",
                max_length=1000,
                validators=[openforms.utils.validators.DjangoTemplateValidator()],
                verbose_name="subject",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="theme_stylesheet_file",
            field=models.FileField(
                blank=True,
                help_text="A stylesheet with theme-specific rules for your organization. This will be included as final stylesheet, overriding previously defined styles. If both a URL to a stylesheet and a stylesheet file have been configured, the uploaded file is included after the stylesheet URL.",
                upload_to="config/themes/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=("css",)
                    )
                ],
                verbose_name="theme stylesheet",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="allow_indexing_form_detail",
            field=models.BooleanField(
                default=True,
                help_text="Whether form detail pages may be indexed and displayed in search engine result lists. Disable this to prevent listing.",
                verbose_name="Allow form page indexing",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_upload_default_file_types",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ("*", "any filetype"),
                        ("image/png", ".png"),
                        ("image/jpeg", ".jpg"),
                        ("application/pdf", ".pdf"),
                        ("application/vnd.ms-excel", ".xls"),
                        (
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            ".xlsx",
                        ),
                        ("text/csv", ".csv"),
                        ("application/msword", ".doc"),
                        (
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            ".docx",
                        ),
                        (
                            "application/vnd.oasis.opendocument.*,application/vnd.stardivision.*,application/vnd.sun.xml.*",
                            "Open Office",
                        ),
                        ("application/zip", ".zip"),
                        ("application/vnd.rar", ".rar"),
                        ("application/x-tar", ".tar"),
                    ],
                    max_length=128,
                ),
                blank=True,
                default=list,
                help_text="Provide a list of default allowed file upload types. If empty, all extensions are allowed.",
                size=None,
                verbose_name="Default allowed file upload types",
            ),
        ),
    ]
