# Generated by Django 2.2.16 on 2020-09-25 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0004_auto_20200924_1909"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="bsn",
            field=models.CharField(blank=True, default="", max_length=9),
        ),
    ]