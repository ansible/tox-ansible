from unittest import TestCase
try:
    from unittest import mock
except ImportError:
    import mock
from tox_ansible.ansible.role import Role
from tox_ansible.ansible.scenario import Scenario


class TestRole(TestCase):
    def test_role_name(self):
        """Testing that the role reads its default name from the name of the
        directory that it lives in."""
        r = Role("some/directory")
        self.assertEqual(r.name, "directory")
        self.assertEqual(str(r), "directory")

    @mock.patch("tox_ansible.ansible.role.path.isdir")
    @mock.patch("tox_ansible.ansible.role.path.isfile")
    def test_role_is_valid(self, isfile_mock, isdir_mock):
        """Role should only know that it actually is a role when it is in a
        directory that contains a file at the subpath "tasks/main.yml".
        Anything else is not a role."""
        isfile_mock.return_value = True
        isdir_mock.return_value = True
        r = Role("roles/dummy")
        self.assertTrue(r.is_role())

    def test_role_is_invalid(self):
        """This is not a role, since that path doesn't actually exist"""
        r = Role("roles/nope")
        self.assertFalse(r.is_role())

    @mock.patch.object(Scenario, "_get_config")
    @mock.patch("tox_ansible.ansible.role.walk")
    def test_role_finds_scenarios(self, walk_mock, scenario_mock):
        """Tests that the role properly walks its subdirectories and finds all
        of the ones that are scenarios and not any that don't contain a
        scenario"""
        # The _get_config method tries to read the non-existent filesystem
        scenario_mock.return_value = {}
        # Creates a directory structure that one might find in the role,
        # including both folders we won't care about, and some that we will
        walk_mock.return_value = [
            ("/home/derp/defaults", [], ["main.yml"]),
            ("/home/derp/templates", ["derp"], ["molecule.yml"]),
            ("/home/derp/templates/derp", [], ["molecule.yml"]),
            ("/home/derp/molecule", ["one", "two", "shared"], []),
            ("/home/derp/molecule/one", [], ["molecule.yml"]),
            ("/home/derp/molecule/two", [], ["molecule.yml", "playbook.yml"]),
            ("/home/derp/molecule/shared", [], ["requirements.yml"])
        ]
        r = Role("roles/has_scenarios")
        scenarios = r.get_scenarios()
        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0].name, "one")
        self.assertEqual(scenarios[1].name, "two")
        tox_cases = r.get_tox_cases()
        self.assertEqual(len(tox_cases), 2)
