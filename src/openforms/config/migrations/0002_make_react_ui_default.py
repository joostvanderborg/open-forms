# Generated by Django 2.2.24 on 2021-09-07 07:54

from django.conf import settings
from django.db import migrations


def make_react_ui_default(apps, _) -> None:
    GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
    config = GlobalConfiguration.objects.first()  # there's only one max
    # don't mess with dev environments, don't mess with fresh instance where the model
    # default will be updated in a fresh migration after this.
    if config is None or settings.DEBUG is True or config.enable_react_form is True:
        return

    config.enable_react_form = True
    config.save(update_fields=["enable_react_form"])


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0001_initial_squashed_0022_merge_20210903_1228"),
    ]

    operations = [
        migrations.RunPython(make_react_ui_default, migrations.RunPython.noop),
    ]