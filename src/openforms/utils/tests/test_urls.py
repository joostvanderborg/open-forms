from django.test import RequestFactory, TestCase, override_settings
from django.urls import path, re_path

from openforms.utils.urls import build_absolute_uri, reverse_plus


@override_settings(IS_HTTPS=True, BASE_URL="http://test/")  # IS_HTTPS is ignored
class BuildAbsoluteUriTests(TestCase):
    def test_basic(self):
        url = build_absolute_uri("/aa/bb/?x=1")
        self.assertEqual("http://test/aa/bb/?x=1", url)

        url = build_absolute_uri("/aa/bb?x=1")
        self.assertEqual("http://test/aa/bb?x=1", url)

        url = build_absolute_uri("aa/bb/?x=1")
        self.assertEqual("http://test/aa/bb/?x=1", url)

        url = build_absolute_uri("aa/bb?x=1")
        self.assertEqual("http://test/aa/bb?x=1", url)

    @override_settings(BASE_URL="http://test:8000/")
    def test_basic_with_port(self):
        url = build_absolute_uri("/aa/bb/?x=1")
        self.assertEqual("http://test:8000/aa/bb/?x=1", url)

    def test_basic_with_request(self):
        request = RequestFactory().get("/dummy")

        url = build_absolute_uri("/aa/bb/?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb/?x=1", url)

        url = build_absolute_uri("/aa/bb?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb?x=1", url)

        url = build_absolute_uri("aa/bb/?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb/?x=1", url)

        url = build_absolute_uri("aa/bb?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb?x=1", url)

    def test_base_url_with_path(self):
        with self.settings(BASE_URL="http://test/pre/path/"):
            url = build_absolute_uri("/aa/bb")
            self.assertEqual("http://test/aa/bb", url)

            url = build_absolute_uri("aa/bb")
            self.assertEqual("http://test/aa/bb", url)


urlpatterns = [
    path(
        "foo/bar",
        lambda r: None,
        name="basic",
    ),
    re_path(
        r"foo/args/(\d+)/(\d+)",
        lambda r: None,
        name="args",
    ),
    path(
        "foo/kwargs/<int:aa>/<int:bb>",
        lambda r: None,
        name="kwargs",
    ),
]


@override_settings(
    BASE_URL="http://test/",
    ROOT_URLCONF="openforms.utils.tests.test_urls",
    ALLOWED_HOSTS=["test", "testserver", "fooserver"],
)
class ReversePlusTest(TestCase):
    def test_basic(self):
        url = reverse_plus("basic")
        self.assertEqual("http://test/foo/bar", url)

        url = reverse_plus("args", args=[1, 2])
        self.assertEqual("http://test/foo/args/1/2", url)

        url = reverse_plus("kwargs", kwargs={"aa": 1, "bb": 2})
        self.assertEqual("http://test/foo/kwargs/1/2", url)

    def test_basic_not_absolute(self):
        url = reverse_plus("basic", make_absolute=False)
        self.assertEqual("/foo/bar", url)

    @override_settings(BASE_URL="http://test:8000/")
    def test_basic_with_port(self):
        url = reverse_plus("kwargs", kwargs={"aa": 1, "bb": 2})
        self.assertEqual("http://test:8000/foo/kwargs/1/2", url)

    def test_basic_with_request(self):
        request = RequestFactory().get("/dummy")
        url = reverse_plus("kwargs", request=request, kwargs={"aa": 1, "bb": 2})
        self.assertEqual("http://testserver/foo/kwargs/1/2", url)

    def test_base_url_with_path(self):
        with self.settings(BASE_URL="http://test/pre/path/"):
            url = reverse_plus("basic")
            self.assertEqual("http://test/foo/bar", url)

        with self.settings(BASE_URL="http://test/pre/path/"):
            request = RequestFactory().get("/dummy")
            url = reverse_plus("basic", request=request)
            # request takes prio
            self.assertEqual("http://testserver/foo/bar", url)

    def test_query(self):
        url = reverse_plus("basic", query={"aa": 123})
        self.assertEqual("http://test/foo/bar?aa=123", url)

        url = reverse_plus("basic", query={"aa": 123, "bb": [1, 2]})
        self.assertEqual("http://test/foo/bar?aa=123&bb=1&bb=2", url)

    def test_complex(self):
        request = RequestFactory(SERVER_NAME="fooserver").get("/dummy")
        url = reverse_plus(
            "kwargs",
            request=request,
            kwargs={"aa": 1, "bb": 2},
            query={"aa": 123, "bb": [1, 2]},
        )
        self.assertEqual("http://fooserver/foo/kwargs/1/2?aa=123&bb=1&bb=2", url)
