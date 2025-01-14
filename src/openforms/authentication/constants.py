from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

FORM_AUTH_SESSION_KEY = "form_auth"  # pending #957 rework
REGISTRATOR_SUBJECT_SESSION_KEY = "registrator_subject"

CO_SIGN_PARAMETER = "coSignSubmission"


class AuthAttribute(DjangoChoices):
    """
    core identifying attributes retrieved from the authentication plugins
    """

    bsn = ChoiceItem("bsn", _("BSN"))
    kvk = ChoiceItem("kvk", _("KvK number"))
    pseudo = ChoiceItem("pseudo", _("Pseudo ID"))
    employee_id = ChoiceItem("employee_id", _("Employee ID"))


class ModeChoices(DjangoChoices):
    citizen = ChoiceItem("citizen", _("Citizen"))
    company = ChoiceItem("company", _("Company"))
    employee = ChoiceItem("employee", _("Employee"))
