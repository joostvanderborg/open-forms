# Generated by Django 2.2.24 on 2021-10-22 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="submissionpayment",
            options={
                "verbose_name": "submission payment details",
                "verbose_name_plural": "submission payment details",
            },
        ),
        migrations.AddField(
            model_name="submissionpayment",
            name="public_order_id",
            field=models.CharField(
                blank=True,
                help_text="Status of the payment process in the configured backend.",
                max_length=32,
                verbose_name="payment status",
            ),
        ),
        migrations.AddConstraint(
            model_name="submissionpayment",
            constraint=models.UniqueConstraint(
                condition=models.Q(_negated=True, public_order_id=""),
                fields=("public_order_id",),
                name="unique_public_order_id",
            ),
        ),
    ]