from unittest import TestCase

try:
    from unittest import mock
except ImportError:
    import mock
from tox_ansible.ansible import Ansible
from tox_ansible.ansible.collection import Collection
from tox_ansible.ansible.role import Role


class TestAnsible(TestCase):
    @mock.patch.object(Role, "tox_cases", new_callable=mock.PropertyMock)
    @mock.patch.object(Role, "is_role", new_callable=mock.PropertyMock)
    @mock.patch.object(Collection, "is_collection")
    def test_collection_when_role(self, c_mock, r_mock, tc_mock):
        c_mock.return_value = False
        r_mock.return_value = True
        tcs = [1, 2, 3]
        tc_mock.return_value = tcs
        ansible = Ansible()
        self.assertTrue(ansible.is_ansible())
        self.assertEqual(ansible.get_tox_cases()[:-1], tcs)

    @mock.patch.object(Collection, "get_tox_cases")
    @mock.patch.object(Role, "is_role", new_callable=mock.PropertyMock)
    @mock.patch.object(Collection, "is_collection")
    def test_collection_when_collection(self, c_mock, r_mock, tc_mock):
        c_mock.return_value = True
        r_mock.return_value = False
        tcs = ["a", "b"]
        tc_mock.return_value = tcs
        ansible = Ansible()
        self.assertTrue(ansible.is_ansible())
        self.assertEqual(ansible.get_tox_cases()[:-1], tcs)

    @mock.patch.object(Role, "is_role", new_callable=mock.PropertyMock)
    @mock.patch.object(Collection, "is_collection")
    def test_collection_when_is_collection(self, c_mock, r_mock):
        c_mock.return_value = False
        r_mock.return_value = False
        ansible = Ansible()
        self.assertFalse(ansible.is_ansible())
        self.assertEqual(len(ansible.get_tox_cases()), 1)
