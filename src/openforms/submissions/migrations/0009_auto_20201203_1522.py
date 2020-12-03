# Generated by Django 2.2.16 on 2020-12-03 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_form_product"),
        ("submissions", "0008_auto_20200929_1643"),
    ]

    operations = [
        migrations.AddField(
            model_name="submissionstep",
            name="modified",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterUniqueTogether(
            name="submissionstep",
            unique_together={("submission", "form_step")},
        ),
    ]