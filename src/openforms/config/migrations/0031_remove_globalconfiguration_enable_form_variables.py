# Generated by Django 3.2.15 on 2022-08-10 13:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0030_piwik_pro_support"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="globalconfiguration",
            name="enable_form_variables",
        ),
    ]
