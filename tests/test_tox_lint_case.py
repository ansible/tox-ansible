from tox_ansible.tox_lint_case import ToxLintCase
from unittest import TestCase


class TestToxLintCase(TestCase):
    def test_names_are_correct(self):
        tc = ToxLintCase([])
        tc.ansible = "2.7"
        self.assertEqual(tc.get_name(), "lint_all")
