# Generated by Django 3.2.15 on 2022-09-19 10:51

from django.db import migrations

from openforms.forms.utils import advanced_formio_logic_to_backend_logic


def convert_frontend_advanced_logic(apps, schema_editor):
    FormDefinition = apps.get_model("forms", "FormDefinition")

    form_definitions = FormDefinition.objects.all()
    for form_definition in form_definitions:
        advanced_formio_logic_to_backend_logic(form_definition, apps)


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0002_auto_20210917_1114_squashed_0045_remove_formstep_optional"),
    ]

    operations = [
        migrations.RunPython(
            convert_frontend_advanced_logic, migrations.RunPython.noop
        ),
    ]
