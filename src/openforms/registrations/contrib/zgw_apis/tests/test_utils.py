from django.test import TestCase

from openforms.registrations.contrib.zgw_apis.utils import restructure_names_to_zgw


class ZGWUtilTests(TestCase):
    def test_name_split(self):
        tests = [
            (
                ("Foo", "Bar"),
                ("F", "", "Bar"),
            ),
            (
                ("Foo", "von Bar"),
                ("F", "von", "Bar"),
            ),
            (
                ("foO", "VoN bAr"),
                ("F", "von", "Bar"),
            ),
            (
                ("Foo", "von der Bar"),
                ("F", "von der", "Bar"),
            ),
            (
                ("Foo", "Bar Bar Bar"),
                # incorrect but as expected
                ("F", "bar bar", "Bar"),
            ),
        ]

        for (first_name, last_name), expected in tests:
            actual = restructure_names_to_zgw(first_name, last_name)
            self.assertEqual(actual, expected)
