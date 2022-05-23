import pytest

# pylint: disable=import-error
from tox_ansible.ansible.scenario import Scenario
from tox_ansible.options import Options
from tox_ansible.tox_helper import Tox
from tox_ansible.tox_molecule_case import ToxMoleculeCase


@pytest.fixture
def config(mocker):
    return mocker.PropertyMock(return_value={})


@pytest.fixture
def scenario(mocker):
    s = Scenario("molecule/my_test")
    return s


@pytest.fixture
def long_scenario(mocker):
    s = Scenario("roles/somedir/subdir/molecule/foo")
    return s


@pytest.fixture
def odd_scenario(mocker):
    s = Scenario("somedir/molecule/scenario")
    return s


@pytest.fixture
def opts(mocker):
    config = mocker.Mock()
    reader = mocker.Mock()
    config.get_reader.return_value = reader
    reader.getlist.return_value = ["2.10", "3.9"]
    reader.getstring.return_value = "auto"
    return Options(config)


def test_case_is_simple(config, opts, scenario, mocker):
    mocker.patch.object(
        Options, "global_opts", new_callable=mocker.PropertyMock, return_value=[]
    )
    mocker.patch.object(
        Tox, "posargs", new_callable=mocker.PropertyMock, return_value=[]
    )
    t = ToxMoleculeCase(scenario)
    opts.molecule_config_files = []
    assert t.get_name() == "my_test"
    assert t.working_dir == ""
    cmds = [["molecule", "test", "-s", scenario.name]]
    assert t.get_commands(opts) == cmds
    assert t.basepython is None


def test_case_is_simple_with_config_files(config, opts, scenario, mocker):
    base_configs = [
        "/home/jdoe/my_ansible_collections/tests/molecule_one.yml",
        "/home/jdoe/my_ansible_collections/tests/molecule_one.yml",
    ]
    mocker.patch.object(
        Options, "global_opts", new_callable=mocker.PropertyMock, return_value=[]
    )
    mocker.patch.object(
        Tox, "posargs", new_callable=mocker.PropertyMock, return_value=[]
    )
    t = ToxMoleculeCase(scenario)
    opts.molecule_config_files = base_configs
    assert t.get_name() == "my_test"
    assert t.working_dir == ""
    cmds = [
        [
            "molecule",
            "-c",
            base_configs[0],
            "-c",
            base_configs[-1],
            "test",
            "-s",
            scenario.name,
        ]
    ]
    assert t.get_commands(opts) == cmds
    assert t.basepython is None


def test_case_has_global_opts(mocker, scenario, opts, config):
    mocker.patch.object(
        Options,
        "global_opts",
        new_callable=mocker.PropertyMock,
        return_value=["-c", "derp"],
    )
    mocker.patch.object(
        Tox, "posargs", new_callable=mocker.PropertyMock, return_value=[]
    )
    t = ToxMoleculeCase(scenario)
    opts.molecule_config_files = []
    cmds = [["molecule", "-c", "derp", "test", "-s", scenario.name]]
    assert t.get_commands(opts) == cmds


def test_case_expand_ansible(scenario):
    # pylint: disable=misplaced-comparison-constant
    t = ToxMoleculeCase(scenario)
    ts = t.expand_ansible("2.7")
    assert ts.ansible == "2.7"
    assert ts.get_name() == "ansible27-my_test"
    assert "ansible==2.7.*" in ts.dependencies
    assert ts.basepython is None
    assert "Auto-generated for: molecule test -s my_test" == ts.description


def test_case_expand_python(scenario):
    t = ToxMoleculeCase(scenario)
    ts = t.expand_python("4.1")
    assert ts.python == "4.1"
    assert ts.get_name() == "py41-my_test"
    assert ts.basepython == "python4.1"


def test_case_expand_twice(scenario):
    t = ToxMoleculeCase(scenario)
    t1 = t.expand_python("4.1")
    t2 = t1.expand_ansible("1.0")
    assert t2.get_name() == "ansible10-py41-my_test"


def test_case_includes_docker_deps(scenario):
    t = ToxMoleculeCase(scenario, drivers=["docker"])
    assert "molecule-docker" in t.dependencies
    assert "molecule-podman" in t.dependencies


def test_case_includes_openstack_deps(scenario):
    t = ToxMoleculeCase(scenario, drivers=["openstack"])
    assert "openstacksdk" in t.dependencies
    assert "moelcule-podman" not in t.dependencies


def test_case_ignores_delegated_driver(scenario):
    t = ToxMoleculeCase(scenario, drivers=["delegated"])
    assert "molecule-delegated" not in t.dependencies


def test_case_handles_unknown_driver(scenario):
    t = ToxMoleculeCase(scenario, drivers=["derpy"])
    assert "molecule-derpy" in t.dependencies


def test_case_for_multiple_drivers(scenario):
    t = ToxMoleculeCase(scenario, drivers=["docker", "podman", "vagrant"])
    assert "molecule-docker" in t.dependencies
    assert "molecule-podman" in t.dependencies
    assert "molecule-vagrant" in t.dependencies
    assert len(list(filter(lambda r: "-r" in r, t.dependencies))) == 0


def test_case_handles_requirements(mocker, scenario):
    t = ToxMoleculeCase(scenario, drivers=["derp"])
    mocker.patch(
        "tox_ansible.ansible.scenario.Scenario.requirements",
        new_callable=mocker.PropertyMock,
        return_value="some_reqs.txt",
    )
    print(t.dependencies)
    assert "-rsome_reqs.txt" in t.dependencies


def test_long_name(long_scenario):
    t = ToxMoleculeCase(long_scenario, drivers=["empty"])
    assert t.get_name() == "roles-somedir-subdir-foo"


def test_odd_name(odd_scenario):
    t = ToxMoleculeCase(odd_scenario, drivers=[])
    assert t.get_name() == "somedir-scenario"
