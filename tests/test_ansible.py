from __future__ import print_function
import os
from tox_ansible_collection.ansible import (
    Collection,
    Role
)
from .util import ToxAnsibleTestCase


class TestCollection(ToxAnsibleTestCase):
    ini_contents = """
    [tox]
    envlist = py27, py34
    """
    roles = [('role', [])]

    def test_is_collection(self):
        c = Collection(self._temp_dir)
        self.assertTrue(c.is_collection())

    def test_roles_list(self):
        c = Collection(self._temp_dir)
        roles = c.get_roles()
        self.assertEqual(len(roles), len(self.roles))


class TestRoles(ToxAnsibleTestCase):
    ini_contents = ''
    roles = [('myrole', [])]

    def test_is_role(self):
        c = Collection(self._temp_dir)
        r = Role(c, "myrole")
        self.assertTrue(r.is_role())
        fake_role = os.path.join(self._temp_dir, "roles", "fakerole")
        os.makedirs(fake_role, exist_ok=True)
        fr = Role(c, "fakerole")
        self.assertFalse(fr.is_role())
