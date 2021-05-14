# Generated by Django 2.2.20 on 2021-05-12 11:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0013_merge_20210507_1347"),
    ]

    operations = [
        migrations.AlterField(
            model_name="formstep",
            name="form_definition",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="forms.FormDefinition"
            ),
        ),
    ]