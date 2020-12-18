from unittest import TestCase

try:
    from unittest import mock
except ImportError:
    import mock

from tox_ansible.ansible.scenario import Scenario
from tox_ansible.options import Options
from tox_ansible.tox_helper import Tox
from tox_ansible.tox_molecule_case import ToxMoleculeCase

DOCKER_DRIVER = {"driver": {"name": "docker"}}
OPENSTACK_DRIVER = {"driver": {"name": "openstack"}}
BASE_DEPS = [
    "ansible-lint",
    "flake8",
    "pytest",
    "testinfra",
    "yamllint",
    "boto",
    "boto3",
    "molecule",
    "molecule-containers",
    "molecule-docker",
    "molecule-ec2",
    "molecule-openstack",
    "molecule-podman",
    "molecule-vagrant",
    "openstacksdk",
    "os-client-config",
]


@mock.patch.object(Scenario, "config", new_callable=mock.PropertyMock, return_value={})
class TestToxMoleculeCase(TestCase):
    @mock.patch.object(Options, "get_global_opts", return_value=[])
    @mock.patch.object(Tox, "posargs", new_callable=mock.PropertyMock, return_value=[])
    def test_case_is_simple(self, pos_mock, opts_mock, config_mock):
        t = ToxMoleculeCase(self.scenario)
        self.assertEqual(t.get_name(), "my_test")
        self.assertEqual(t.get_working_dir(), "")
        self.assertEqual(sorted(t.get_dependencies()), sorted(BASE_DEPS + ["ansible"]))
        cmds = [["molecule", "test", "-s", self.scenario.name]]
        self.assertEqual(t.get_commands(self.opts), cmds)
        self.assertIsNone(t.get_basepython())

    @mock.patch.object(Options, "get_global_opts", return_value=["-c", "derp"])
    @mock.patch.object(Tox, "posargs", new_callable=mock.PropertyMock, return_value=[])
    def test_case_has_global_opts(self, pos_mock, opts_mock, config_mock):
        t = ToxMoleculeCase(self.scenario)
        cmds = [["molecule", "-c", "derp", "test", "-s", self.scenario.name]]
        self.assertEqual(t.get_commands(self.opts), cmds)

    def test_case_expand_ansible(self, config_mock):
        t = ToxMoleculeCase(self.scenario)
        ts = t.expand_ansible("2.7")
        self.assertEqual(ts.ansible, "2.7")
        self.assertEqual(ts.get_name(), "ansible27-my_test")
        self.assertEqual(
            sorted(ts.get_dependencies()), sorted(BASE_DEPS + ["ansible==2.7.*"])
        )
        self.assertIsNone(ts.get_basepython())

    def test_case_expand_python(self, config_mock):
        t = ToxMoleculeCase(self.scenario)
        ts = t.expand_python("4.1")
        self.assertEqual(ts.python, "4.1")
        self.assertEqual(ts.get_name(), "py41-my_test")
        self.assertEqual(ts.get_basepython(), "python4.1")

    def test_case_expand_twice(self, config_mock):
        t = ToxMoleculeCase(self.scenario)
        t1 = t.expand_python("4.1")
        t2 = t1.expand_ansible("1.0")
        self.assertEqual(t2.get_name(), "ansible10-py41-my_test")

    @mock.patch.object(
        Scenario, "driver", new_callable=mock.PropertyMock, return_value="docker"
    )
    def test_case_includes_docker_deps(self, driver_mock, config_mock):
        s = Scenario("molecule/my_test")
        t = ToxMoleculeCase(s)
        self.assertIn("molecule-docker", t.get_dependencies())

    @mock.patch.object(
        Scenario, "driver", new_callable=mock.PropertyMock, return_value="openstack"
    )
    def test_case_includes_openstack_deps(self, driver_mock, config_mock):
        s = Scenario("molecule/osp_test")
        t = ToxMoleculeCase(s)
        self.assertIn("openstacksdk", t.get_dependencies())

    @classmethod
    def setUp(cls):
        cls.scenario = Scenario("molecule/my_test")
        cls.opts = Options(mock.Mock())
