# For rennamed/moved assert(Count|Item)Equal
import six
from unittest import TestCase
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock
from tox_ansible.filter import Filter
from collections import namedtuple


class TestFilter(TestCase):
    def test_filter(self):
        # Mock struggles with an attribute named "name"
        Scenario = namedtuple('Scenario', 'name')
        Role = namedtuple('Role', 'name')
        opts = Mock(role=['one', 'two'], scenario=['default'])
        role1 = Role(name='one')
        role2 = Role(name='two')
        role3 = Role(name='three')
        default = Scenario(name='default')
        other = Scenario(name='other')
        envlist = {
            'one-default': Mock(tox_case=Mock(scenario=default, role=role1)),
            'one-other': Mock(tox_case=Mock(scenario=other, role=role1)),
            'two-default': Mock(tox_case=Mock(scenario=default, role=role2)),
            'three-default': Mock(tox_case=Mock(scenario=default, role=role3))
        }
        expected = ['one-default', 'two-default']

        f = Filter(opts)
        results = f.filter(envlist)
        six.assertCountEqual(self, results.keys(), expected)

    def test_filter_role_only(self):
        opts = Mock(role=['one'], scenario=[])
        Role = namedtuple('Role', 'name')
        role1 = Role(name='one')
        role2 = Role(name='two')
        envlist = {
            'one-default': Mock(tox_case=Mock(role=role1)),
            'two-default': Mock(tox_case=Mock(role=role2))
        }
        expected = ['one-default']

        f = Filter(opts)
        results = f.filter(envlist)
        six.assertCountEqual(self, results.keys(), expected)
