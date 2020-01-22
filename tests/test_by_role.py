from unittest import TestCase
from collections import namedtuple
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock
from tox_ansible.filter.by_role import ByRole


class TestByRole(TestCase):
    def test_by_role(self):
        Role = namedtuple('Role', 'name')
        role = Role(name='yes')
        envlist = {
            'yes': Mock(tox_case=Mock(role=role)),
            'no': Mock(spec=[])
        }
        names = ['yes']
        by_role = ByRole(names)
        filtered_roles = by_role.filter(envlist)
        self.assertIn('yes', filtered_roles)
        self.assertNotIn('no', filtered_roles)
