from tox_ansible.tox_lint_case import ToxLintCase
from unittest import TestCase


class TestToxLintCase(TestCase):
    def test_names_are_correct(self):
        tc = ToxLintCase([])
        self.assertEqual(tc.get_name(), "lint_all")

    def test_expand_python(self):
        tc = ToxLintCase([])
        out = tc.expand_python("2.7")
        self.assertEqual(out.get_name(), "py27-lint_all")

    def test_expand_ansible(self):
        tc = ToxLintCase([])
        out = tc.expand_ansible("2.10")
        self.assertEqual(out.get_name(), "ansible210-lint_all")
