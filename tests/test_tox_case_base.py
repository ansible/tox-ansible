from unittest import TestCase
try:
    from unittest import mock
except ImportError:
    import mock
from tox_ansible.tox_test_case import ToxTestCase
from tox_ansible.ansible.role import Role
from tox_ansible.ansible.scenario import Scenario
from tox_ansible.options import Options


DOCKER_DRIVER = {"driver": {"name": "docker"}}
OPENSTACK_DRIVER = {"driver": {"name": "openstack"}}


class TestToxTestCase(TestCase):
    @mock.patch.object(Options, "get_global_opts", return_value=[])
    def test_case_is_simple(self, opts_mock):
        t = ToxTestCase(self.role, self.scenario)
        self.assertEqual(t.get_name(), "derp-my_test")
        self.assertEqual(t.get_working_dir(), "roles/derp")
        self.assertEqual(t.get_dependencies(), ["molecule", "ansible"])
        cmds = [["molecule", "test", "-s", self.scenario.name]]
        self.assertEqual(t.get_commands(self.opts), cmds)
        self.assertIsNone(t.get_basepython())

    @mock.patch.object(Options, "get_global_opts", return_value=["-c", "derp"])
    def test_case_has_global_opts(self, opts_mock):
        t = ToxTestCase(self.role, self.scenario)
        cmds = [["molecule", "-c", "derp", "test", "-s", self.scenario.name]]
        self.assertEqual(t.get_commands(self.opts), cmds)

    def test_case_expand_ansible(self):
        t = ToxTestCase(self.role, self.scenario)
        ts = t.expand_ansible("2.7")
        self.assertEqual(ts.ansible, "2.7")
        self.assertEqual(ts.get_name(), "ansible27-derp-my_test")
        self.assertEqual(ts.get_dependencies(), ["molecule", "ansible==2.7.*"])
        self.assertIsNone(ts.get_basepython())

    def test_case_expand_python(self):
        t = ToxTestCase(self.role, self.scenario)
        ts = t.expand_python("4.1")
        self.assertEqual(ts.python, "4.1")
        self.assertEqual(ts.get_name(), "py41-derp-my_test")
        self.assertEqual(ts.get_basepython(), "python4.1")

    @mock.patch.object(Scenario, "_get_config", return_value=DOCKER_DRIVER)
    def test_case_includes_docker_deps(self, config_mock):
        s = Scenario("moelcule/my_test")
        t = ToxTestCase(self.role, s)
        self.assertIn("docker", t.get_dependencies())

    @mock.patch.object(Scenario, "_get_config", return_value=OPENSTACK_DRIVER)
    def test_case_includes_openstack_deps(self, config_mock):
        s = Scenario("molecule/osp_test")
        t = ToxTestCase(self.role, s)
        self.assertIn("openstacksdk", t.get_dependencies())

    @classmethod
    @mock.patch.object(Scenario, "_get_config", return_value={})
    def setUp(cls, config_mock):
        cls.role = Role("roles/derp")
        cls.scenario = Scenario("molecule/my_test")
        cls.opts = Options(mock.Mock())
