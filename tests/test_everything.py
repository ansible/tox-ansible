import os
import sys
from py.io import StdCaptureFD
from unittest import TestCase


class TestEverything(TestCase):
    def setUp(self):
        self.cwd = os.getcwd()

    def test_run_tox(self):
        os.chdir("tests/fixtures/collection")
        out = self.run_tox(["-l"])
        self.assertIn("complex-default", out)
        self.assertIn("complex-openstack", out)
        self.assertIn("complex-real_name", out)
        self.assertIn("simple-default", out)
        self.assertIn("lint_all", out)
        self.assertNotIn("no_tests", out)
        self.assertNotIn("not_a_role", out)

    def test_run_tox_expansion(self):
        os.chdir("tests/fixtures/expand_collection")
        out = self.run_tox(["-l"])
        self.assertIn("py27-ansible28-simple-default", out)
        self.assertIn("py27-ansible29-simple-default", out)
        self.assertIn("py38-ansible28-simple-default", out)
        self.assertIn("py38-ansible29-simple-default", out)
        self.assertIn("py27-ansible28-lint_all", out)
        self.assertIn("py27-ansible29-lint_all", out)
        self.assertIn("py38-ansible28-lint_all", out)
        self.assertIn("py38-ansible29-lint_all", out)

    def test_run_tox_expansion_role_filter(self):
        os.chdir("tests/fixtures/expand_collection")
        out = self.run_tox(["--ansible-role", "simple", "-l"])
        self.assertIn("-simple-default", out)
        self.assertNotIn("lint_all", out)

    def tearDown(self):
        os.chdir(self.cwd)

    def run_tox(self, args):
        out, err = '', ''
        try:
            self.capture = StdCaptureFD()
            from tox import cmdline
            cmdline(args)
        except SystemExit as s:
            out, err = self.capture.reset()
            if s.code != 0:
                print(err, file=sys.stderr)
                raise s
        finally:
            return out
