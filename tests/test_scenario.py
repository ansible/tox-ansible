import pytest

from tox_ansible.ansible.scenario import Scenario


@pytest.fixture
def openstack(tmp_path):
    d = tmp_path / "default"
    d.mkdir()
    f = d / "molecule.yml"
    f.write_text("driver:\n  name: openstack")
    return d


@pytest.fixture
def surprise(tmp_path):
    d = tmp_path / "surprise"
    d.mkdir()
    f = d / "molecule.yml"
    f.write_text("driver:\n  name: surprise")
    return d


def test_scenario_name_introspect(openstack):
    s = Scenario(openstack)
    assert s.name == "default"
    assert str(s) == "default"
    assert s.driver == "openstack"


def test_scenario_name_explicit(surprise):
    s = Scenario(surprise)
    assert s.name == "surprise"
    assert str(s) == "surprise"
    assert s.driver == "surprise"
