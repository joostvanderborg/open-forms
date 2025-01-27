# Generated by Django 2.2.24 on 2021-08-12 15:16

import uuid

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models

import openforms.utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("submissions", "0001_initial_squashed_0057_alter_submissionvaluevariable_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubmissionPayment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    openforms.utils.fields.StringUUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="UUID"
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "plugin_id",
                    models.CharField(max_length=100, verbose_name="Payment backend"),
                ),
                (
                    "plugin_options",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True,
                        help_text="Copy of payment options at time of initializing payment.",
                        null=True,
                        verbose_name="Payment options",
                    ),
                ),
                ("form_url", models.URLField(max_length=255, verbose_name="Form URL")),
                (
                    "order_id",
                    models.BigIntegerField(
                        help_text="Unique tracking across backend",
                        null=True,
                        unique=True,
                        verbose_name="Order ID",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Total payment amount.",
                        max_digits=8,
                        verbose_name="payment amount",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("started", "Started by user"),
                            ("processing", "Backend is processing"),
                            ("failed", "Cancelled or failed"),
                            ("completed", "Completed by user"),
                            ("registered", "Completed and registered"),
                        ],
                        default="started",
                        help_text="Status of the payment process in the configured backend.",
                        max_length=32,
                        verbose_name="payment status",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="submissions.Submission",
                    ),
                ),
            ],
        ),
    ]
