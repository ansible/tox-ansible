import os

import pytest

from tox_ansible.ansible import Ansible


@pytest.mark.parametrize(
    "folder,expected",
    [
        ("tests/fixtures/collection", True),
        ("tests/fixtures/expand_collection", True),
        ("tests/fixtures/expand_collection_newlines", True),
        ("tests/fixtures/not_collection", True),
        ("tests/fixtures/has_deps", True),
        ("tests/fixtures/nothing", False),
    ],
)
def test_with_scenarios(mocker, folder, expected):
    ansible = Ansible(base=folder)
    ansible.options = mocker.Mock()
    ansible.options.ignore_paths = []
    # ansible._scenarios = scenarios  # pylint: disable=protected-access
    assert ansible.directory == os.path.realpath(folder)
    assert ansible.is_ansible == expected


def test_with_full_path():
    ansible = Ansible("/dev")
    assert ansible.directory == "/dev"


def test_scenarios_correct(mocker):
    ansible = Ansible("tests/fixtures/collection")
    ansible.options = mocker.Mock()
    ansible.options.ignore_paths = []
    assert len(ansible.scenarios) == 6
