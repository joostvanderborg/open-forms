# Generated by Django 3.2.13 on 2022-06-29 08:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0029_rename_design_tokens"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="piwik_pro_site_id",
            field=models.CharField(
                blank=True,
                help_text="Typically looks like XXX-XXX-XXX-XXX-XXX. The 'idsite' of the website you're tracking in Piwik PRO.",
                max_length=36,
                validators=[
                    django.core.validators.RegexValidator(
                        message="The site ID must be a valid Piwik PRO site ID.",
                        regex="\\w{8}-(\\w{4}-){3}\\w{12}",
                    )
                ],
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
    ]
