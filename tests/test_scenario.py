import pytest

from tox_ansible.ansible.scenario import Scenario


@pytest.fixture
def openstack(tmp_path):
    d = tmp_path / "default"
    d.mkdir()
    f = d / "molecule.yml"
    f.write_text("driver:\n  name: openstack")
    r = d / "requirements.txt"
    r.write_text("")
    return d


@pytest.fixture
def surprise(tmp_path):
    d = tmp_path / "surprise"
    d.mkdir()
    f = d / "molecule.yml"
    f.write_text("driver:\n  name: surprise")
    return d


@pytest.fixture
def no_driver(tmp_path):
    d = tmp_path / "no_driver"
    d.mkdir()
    f = d / "molecule.yml"
    f.write_text("")
    return d


def test_scenario_name_introspect(openstack):
    s = Scenario(openstack)
    assert s.name == "default"
    assert str(s) == "default"
    assert s.driver == "openstack"
    assert s.requirements is not None


def test_scenario_name_explicit(surprise):
    s = Scenario(surprise)
    assert s.name == "surprise"
    assert str(s) == "surprise"
    assert s.driver == "surprise"
    assert s.requirements is None


def test_no_driver(no_driver):
    s = Scenario(no_driver)
    assert s.name == "no_driver"
    assert s.driver is None


def test_driver_with_global_config(surprise):
    global_config = [{"driver": {"name": "podman"}}]
    s = Scenario(surprise, global_config)
    assert s.name == "surprise"
    assert str(s) == "surprise"
    assert s.driver == "surprise"
    assert s.requirements is None


def test_no_driver_with_global_config(no_driver):
    global_config = [{"driver": {"name": "podman"}}]
    s = Scenario(no_driver, global_config)
    assert s.name == "no_driver"
    assert s.driver == "podman"
