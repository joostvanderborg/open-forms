from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from oidc_generics.models import OpenIDConnectEHerkenningConfig
from openforms.accounts.tests.factories import SuperUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory

default_config = dict(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "kvk"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
    oidc_op_logout_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/logout",
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class eHerkenningOIDCFormAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.user = SuperUserFactory.create(app=self.app)
        self.app.set_user(self.user)

        global_config = GlobalConfiguration.get_solo()
        global_config.enable_react_form = False
        global_config.save()

        def _cleanup():
            GlobalConfiguration.get_solo().delete()

        self.addCleanup(_cleanup)

    def test_eherkenning_oidc_disable_allowed(self):
        # Patching `get_solo()` doesn't seem to work when retrieving the change_form
        config = OpenIDConnectEHerkenningConfig(**default_config)
        config.save()

        FormFactory.create(authentication_backends=["digid_oidc"])

        response = self.app.get(
            reverse("admin:oidc_generics_openidconnecteherkenningconfig_change")
        )

        form = response.form
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(OpenIDConnectEHerkenningConfig.get_solo().enabled)

    def test_eherkenning_oidc_disable_not_allowed(self):
        # Patching `get_solo()` doesn't seem to work when retrieving the change_form
        config = OpenIDConnectEHerkenningConfig(**default_config)
        config.save()

        FormFactory.create(authentication_backends=["eherkenning_oidc"])

        response = self.app.get(
            reverse("admin:oidc_generics_openidconnecteherkenningconfig_change")
        )

        form = response.form
        form["enabled"] = False
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OpenIDConnectEHerkenningConfig.get_solo().enabled)
