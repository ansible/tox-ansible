import pytest

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


@pytest.fixture
def config(mocker):
    return mocker.PropertyMock(return_value={})


@pytest.fixture
def scenario():
    return Scenario("molecule/my_test")


@pytest.fixture
def opts(mocker):
    config = mocker.Mock()
    reader = mocker.Mock()
    config.get_reader.return_value = reader
    reader.getlist.return_value = ["2.10", "3.9"]
    return Options(config)


def test_case_is_simple(config, opts, scenario, mocker):
    mocker.patch.object(Options, "get_global_opts", return_value=[])
    mocker.patch.object(
        Tox, "posargs", new_callable=mocker.PropertyMock, return_value=[]
    )
    t = ToxMoleculeCase(scenario)
    assert t.get_name() == "my_test"
    assert t.get_working_dir() == ""
    assert sorted(t.get_dependencies()) == sorted(BASE_DEPS + ["ansible"])
    cmds = [["molecule", "test", "-s", scenario.name]]
    assert t.get_commands(opts) == cmds
    assert t.get_basepython() is None


def test_case_has_global_opts(mocker, scenario, opts, config):
    mocker.patch.object(Options, "get_global_opts", return_value=["-c", "derp"])
    mocker.patch.object(
        Tox, "posargs", new_callable=mocker.PropertyMock, return_value=[]
    )
    t = ToxMoleculeCase(scenario)
    cmds = [["molecule", "-c", "derp", "test", "-s", scenario.name]]
    assert t.get_commands(opts) == cmds


def test_case_expand_ansible(scenario):
    # pylint: disable=misplaced-comparison-constant
    t = ToxMoleculeCase(scenario)
    ts = t.expand_ansible("2.7")
    assert ts.ansible == "2.7"
    assert ts.get_name() == "ansible27-my_test"
    assert sorted(ts.get_dependencies()) == sorted(BASE_DEPS + ["ansible==2.7.*"])
    assert ts.get_basepython() is None
    assert "Auto-generated for: molecule test -s my_test" == ts.description


def test_case_expand_python(scenario):
    t = ToxMoleculeCase(scenario)
    ts = t.expand_python("4.1")
    assert ts.python == "4.1"
    assert ts.get_name() == "py41-my_test"
    assert ts.get_basepython() == "python4.1"


def test_case_expand_twice(scenario):
    t = ToxMoleculeCase(scenario)
    t1 = t.expand_python("4.1")
    t2 = t1.expand_ansible("1.0")
    assert t2.get_name() == "ansible10-py41-my_test"


def test_case_includes_docker_deps(mocker):
    mocker.patch.object(
        Scenario, "driver", new_callable=mocker.PropertyMock, return_value="docker"
    )
    s = Scenario("molecule/my_test")
    t = ToxMoleculeCase(s)
    assert "molecule-docker" in t.get_dependencies()


def test_case_includes_openstack_deps(mocker):
    mocker.patch.object(
        Scenario, "driver", new_callable=mocker.PropertyMock, return_value="openstack"
    )
    s = Scenario("molecule/osp_test")
    t = ToxMoleculeCase(s)
    assert "openstacksdk" in t.get_dependencies()
