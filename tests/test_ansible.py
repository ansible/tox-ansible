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
    ansible.options.molecule_config_files = []
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
    ansible.options.molecule_config_files = []
    assert len(ansible.scenarios) == 6


def test_scenarios_with_global_molecule_config(mocker):
    ansible = Ansible("tests/fixtures/not_collection")
    global_config = [os.path.join(ansible.directory, ".config/molecule/config.yml")]
    ansible.options = mocker.Mock()
    ansible.options.ignore_paths = []
    ansible.options.molecule_config_files = []
    assert ansible.molecule_config_files() == global_config


def test_scenarios_with_base_molecule_config(mocker):
    ansible = Ansible("tests/fixtures/collection")
    base_configs = [os.path.join(ansible.directory, "molecule.yml")]
    ansible.options = mocker.Mock()
    ansible.options.ignore_paths = []
    ansible.options.molecule_config_files = base_configs
    assert ansible.molecule_config_files() == base_configs


def test_scenarios_with_multiple_base_molecule_config(mocker):
    ansible = Ansible("tests/fixtures/expand_collection")
    base_configs = [
        os.path.join(ansible.directory, "molecule_one.yml"),
        os.path.join(ansible.directory, "molecule_two.yml"),
    ]
    ansible.options = mocker.Mock()
    ansible.options.ignore_paths = []
    ansible.options.molecule_config_files = base_configs
    assert ansible.molecule_config_files() == base_configs
