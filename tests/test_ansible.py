import pytest

from tox_ansible.ansible import Ansible


@pytest.mark.parametrize("scenarios,expected", [([1], True), ([], False)])
def test_with_scenarios(mocker, scenarios, expected):
    ansible = Ansible()
    ansible._scenarios = scenarios  # pylint: disable=protected-access
    assert ansible.is_ansible == expected
