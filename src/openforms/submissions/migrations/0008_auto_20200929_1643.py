# Generated by Django 2.2.16 on 2020-09-29 14:43

import uuid

from django.db import migrations, models

import openforms.utils.fields
import openforms.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0007_merge_20200925_1630"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="current_step",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="submission",
            name="bsn",
            field=models.CharField(
                blank=True,
                default="",
                max_length=9,
                validators=[openforms.utils.validators.BSNValidator()],
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="uuid",
            field=openforms.utils.fields.StringUUIDField(
                default=uuid.uuid4, unique=True
            ),
        ),
    ]