# Generated by Django 3.2.15 on 2022-10-11 12:51

from django.db import migrations
from django.db.models import Count


def backfill_attachment_submission_variables_from_form_key(apps, schema_editor):
    SubmissionStep = apps.get_model("submissions", "SubmissionStep")
    SubmissionValueVariable = apps.get_model("submissions", "SubmissionValueVariable")

    qs = SubmissionStep.objects.annotate(Count("attachments")).filter(
        attachments__count__gt=0
    )
    qs = qs.only("id", "submission_id")

    for submission_step in qs.iterator():
        vars_qs = SubmissionValueVariable.objects.filter(
            submission=submission_step.submission_id
        )
        step_variables = {v.key: v for v in vars_qs}
        for attachment in submission_step.attachments.all():
            if attachment.form_key not in step_variables:
                print(
                    f"Data migration issue: cannot match form_key '{attachment.form_key}' of attachment({attachment.id}) of submission({submission_step.submission_id}) to form variables {list(step_variables.keys())}"
                )
                continue
            attachment.submission_variable = step_variables[attachment.form_key]
            attachment.save(update_fields=("submission_variable",))


def reverse_backfill_and_restore_submission_form_key(apps, schema_editor):
    SubmissionFileAttachment = apps.get_model("submissions", "SubmissionFileAttachment")

    qs = SubmissionFileAttachment.objects.all()
    for attachment in qs:
        if attachment.submission_variable is None:
            # not possible
            continue
        attachment.form_key = attachment.submission_variable.key
        attachment.save(update_fields=("form_key",))


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0060_auto_20220812_1439"),
    ]

    operations = [
        migrations.RunPython(
            backfill_attachment_submission_variables_from_form_key,
            # using .noop could lead to data loss during reverse migrations
            reverse_backfill_and_restore_submission_form_key,
        ),
    ]
