from __future__ import print_function
import os
import sys
from py.io import StdCaptureFD
from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


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
        def _assert(out):
            self.assertIn("-simple-default", out)
            self.assertNotIn("lint_all", out)
        os.chdir("tests/fixtures/expand_collection")
        out = self.run_tox(["--ansible-role", "simple", "-l"])
        _assert(out)
        with patch.dict("os.environ", {"TOX_ANSIBLE_ROLE": "simple"}):
            out = self.run_tox(["-l"])
        _assert(out)

    def test_run_tox_scenario_filter(self):
        def _assert(out):
            self.assertIn("complex-default", out)
            self.assertIn("simple-default", out)
            self.assertNotIn("lint_all", out)
            self.assertNotIn("no_tests", out)
            self.assertNotIn("complex-openstack", out)
        os.chdir("tests/fixtures/collection")
        out = self.run_tox(["-l", "--ansible-scenario", "default"])
        _assert(out)
        with patch.dict("os.environ", {"TOX_ANSIBLE_SCENARIO": "default"}):
            out = self.run_tox(["-l"])
        _assert(out)

    def test_run_tox_driver_filter(self):
        def _assert(out):
            self.assertIn("complex-openstack", out)
            self.assertNotIn("default", out)
            self.assertNotIn("simple", out)
            self.assertNotIn("lint_all", out)
        os.chdir("tests/fixtures/collection")
        out = self.run_tox(["-l", "--ansible-driver", "openstack"])
        _assert(out)
        with patch.dict("os.environ", {"TOX_ANSIBLE_DRIVER": "openstack"}):
            out = self.run_tox(["-l"])
        _assert(out)

    def test_run_in_not_ansible(self):
        out = self.run_tox(["-l"])
        self.assertNotIn("-default", out)
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
                raise
        finally:
            return out
