import pytest
import os

from tox_ansible.ansible import Ansible


@pytest.mark.parametrize("scenarios,expected", [([1], True), ([], False)])
def test_with_scenarios(mocker, scenarios, expected):
    ansible = Ansible()
    ansible._scenarios = scenarios  # pylint: disable=protected-access
    assert ansible.is_ansible == expected
    assert ansible.directory == os.path.realpath(os.curdir)


def test_with_full_path():
    ansible = Ansible("/dev")
    assert ansible.directory == "/dev"


def test_scenarios_correct(mocker):
    ansible = Ansible("tests/fixtures/collection")
    ansible.options = mocker.Mock()
    ansible.options.ignore_paths = []
    assert len(ansible.scenarios) ==  6
