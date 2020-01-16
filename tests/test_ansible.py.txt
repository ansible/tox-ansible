from __future__ import print_function
import os
from tox_ansible_collection.ansible import (
    Collection,
    Role,
    Scenario
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


class TestRole(ToxAnsibleTestCase):
    ini_contents = ''
    roles = [('myrole', [('scenario', '')])]

    def test_is_role(self):
        c = Collection(self._temp_dir)
        r = Role(c, self.roles[0][0])
        self.assertTrue(r.is_role())
        fake_role = os.path.join(self._temp_dir, "roles", "fakerole")
        os.makedirs(fake_role)
        fr = Role(c, "fakerole")
        self.assertFalse(fr.is_role())

    def test_gets_scenarios(self):
        c = Collection(self._temp_dir)
        r = Role(c, self.roles[0][0])
        self.assertEqual(len(r.get_scenarios()), len(self.roles[0][1]))


class TestScenario(ToxAnsibleTestCase):
    ini_contents = ''
    roles = [('myrole', [
                ('scenario', ''),
                ('default', '''
                scenario:
                    name: other''')])]

    def test_scenario_name_inferred(self):
        c = Collection(self._temp_dir)
        r = Role(c, "myrole")
        s = Scenario(r, "molecule/scenario")
        self.assertEqual(s.name, "scenario")

    def test_scenario_name_explicit(self):
        c = Collection(self._temp_dir)
        r = Role(c, "myrole")
        s = Scenario(r, "molecule/default")
        self.assertEqual(s.name, "other")
