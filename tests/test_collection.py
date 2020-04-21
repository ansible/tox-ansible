import os
from unittest import TestCase
from tox_ansible.ansible.collection import Collection
from tox_ansible.ansible.role import Role
from tox_ansible.ansible.scenario import Scenario
from tox_ansible.tox_test_case import ToxTestCase

try:
    from unittest import mock
except ImportError:
    import mock


class TestCollection(TestCase):
    @mock.patch("tox_ansible.ansible.collection.path.isfile")
    def test_collection_works(self, isfile_mock):
        isfile_mock.return_value = True
        c = Collection()
        self.assertEqual(os.path.abspath(os.curdir), c.directory)
        self.assertTrue(c.is_collection())

    @mock.patch("tox_ansible.ansible.collection.path.isdir")
    def test_no_roles_dir(self, isdir_mock):
        isdir_mock.return_value = False
        c = Collection()
        roles = c.get_roles()
        self.assertEqual(len(roles), 0)

    @mock.patch("tox_ansible.ansible.collection.path.isdir")
    @mock.patch("tox_ansible.ansible.collection.listdir")
    @mock.patch.object(Role, "is_role", new_callable=mock.PropertyMock)
    def test_get_roles_back(self, role_mock, listdir_mock, isdir_mock):
        isdir_mock.return_value = True
        dirs = ["one", "two", "three"]
        listdir_mock.return_value = dirs
        role_mock.return_value = True
        c = Collection()
        roles = c.get_roles()
        self.assertEqual(len(roles), len(dirs))
        for d, r in zip(dirs, roles):
            self.assertEqual(d, r.name)

    @mock.patch.object(Scenario, "config")
    @mock.patch.object(Collection, "get_roles")
    @mock.patch.object(Role, "tox_cases", new_callable=mock.PropertyMock)
    def test_get_tox_cases(self, role_mock, collection_mock, scenario_mock):
        s1 = Scenario("s1")
        s2 = Scenario("s2")
        r1 = Role("r1")
        r2 = Role("r2")
        scenario_mock.return_value = {}
        collection_mock.return_value = [r1, r2]
        # Yeah, both roles will pretend they're r1 for this. Big deal
        role_mock.return_value = [ToxTestCase(r1, s1), ToxTestCase(r1, s2)]
        c = Collection()
        cases = c.get_tox_cases()
        self.assertEqual(len(cases), len(role_mock()) * len(collection_mock()))
