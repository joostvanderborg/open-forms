from django.contrib import auth
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form
from openforms.utils.urls import reverse_plus

from ...base import BasePlugin
from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from ...registry import register


@register("org-oidc")
class OIDCAuthentication(BasePlugin):
    """
    Authentication plugin using the global mozilla-django-oidc-db (as used for the admin)
    """

    verbose_name = _("Organization via OpenID Connect")
    provides_auth = AuthAttribute.employee_id

    def start_login(self, request: HttpRequest, form: Form, form_url: str):
        auth_return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query={
                "next": form_url,
            },
        )
        redirect_url = reverse_plus(
            "org-oidc:init",
            request=request,
            query={
                "next": auth_return_url,
            },
        )
        if request.user.is_authenticated:
            # logout user if logged in with other account
            # this is relevant when staff users are already logged in, the OIDC state/redirects get confused,
            #   and could send the user back to the admin instead of the form.
            # this is likely because it picks a .success_url instead of session data
            auth.logout(request)
        return HttpResponseRedirect(redirect_url)

    def handle_return(self, request, form):
        """
        Redirect to form URL.
        """
        assert request.user.is_authenticated

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        request.session[FORM_AUTH_SESSION_KEY] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": request.user.username,
        }

        # we could render here but let's redirect
        return HttpResponseRedirect(
            self.get_registrator_subject_url(request, form, form_url)
        )

    def logout(self, request: HttpRequest):
        for key in (
            "oidc_id_token",
            "oidc_login_next",
            "oidc_states",
        ):
            if key in request.session:
                del request.session[key]

        if request.user.is_authenticated:
            auth.logout(request)
            assert not request.user.is_authenticated

    def get_label(self):
        return _("OpenID Connect")

    def get_logo(self, request: HttpRequest):
        return {
            "image_src": request.build_absolute_uri(static("img/openid.png")),
            "href": "https://openid.net/",
        }
