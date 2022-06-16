from datetime import datetime

from django.core.management import BaseCommand
from django.db.models import Prefetch, Q
from django.utils import timezone

from openforms.forms.models import Form, FormStep
from openforms.submissions.models import Submission

WINDOW_START = datetime(2022, 6, 13, 16, 0, 0).replace(tzinfo=timezone.utc)
WINDOW_END = datetime(2022, 6, 14, 3, 30, 0).replace(tzinfo=timezone.utc)


class Command(BaseCommand):
    help = "Check if a partial DB restore is needed."

    def handle(self, **options):
        # check which forms are relevant
        affected_forms = []
        form_steps = FormStep.objects.select_related("form_definition")
        for form in Form.objects.prefetch_related(
            Prefetch("formstep_set", queryset=form_steps)
        ):
            for component in form.iter_components(recursive=True):
                if component.get("type") == "file":
                    affected_forms.append(form)
                    break

        # do not filter out affected submissions, as the SDK allowed progressing despite
        # HTTP 400s from submission step endpoint.
        potentially_affected_submissions = (
            Submission.objects.filter(form__in=affected_forms)
            .exclude(completed_on__lt=WINDOW_START)
            .exclude(created_on__gt=WINDOW_END)
            .filter(
                Q(submissionstep__modified__range=(WINDOW_START, WINDOW_END))
                | Q(submissionstep__created_on__range=(WINDOW_START, WINDOW_END))
            )
        )

        if potentially_affected_submissions.exists():
            self.stdout.write(
                "There are potentially affected submissions requiring partial backup restore."
            )
