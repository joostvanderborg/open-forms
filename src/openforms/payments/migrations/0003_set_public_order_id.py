# Generated by Django 2.2.24 on 2021-10-22 14:44

from django.db import migrations
from django.db.models import F


def set_public_order_id(apps, _):
    SubmissionPayment = apps.get_model("payments", "SubmissionPayment")
    qs = SubmissionPayment.objects.filter(public_order_id="", order_id__isnull=False)

    # the old order IDs before these public_order_ids are included have the
    # year prefix already. We do not need to calculate it (again).
    qs.update(public_order_id=F("order_id"))


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_submissionpayment_public_order_id"),
    ]

    operations = [
        migrations.RunPython(set_public_order_id, migrations.RunPython.noop),
    ]