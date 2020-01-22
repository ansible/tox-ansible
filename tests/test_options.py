from unittest import TestCase
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock
from tox_ansible.options import Options


class TestOptions(TestCase):
    def test_do_filter_role(self):
        opts = Options(Mock())
        opts.role = ['one']
        opts.scenario = []
        opts.driver = []
        self.assertTrue(opts.do_filter())

    def test_do_filter_scenario(self):
        opts = Options(Mock())
        opts.role = []
        opts.scenario = ['default']
        opts.driver = []
        self.assertTrue(opts.do_filter())

    def test_do_filter_driver(self):
        opts = Options(Mock())
        opts.role = []
        opts.scenario = []
        opts.driver = ['openstack']
        self.assertTrue(opts.do_filter())

    def test_do_filter_none_is_false(self):
        opts = Options(Mock())
        opts.role = []
        opts.scenario = []
        opts.driver = []
        self.assertFalse(opts.do_filter())
