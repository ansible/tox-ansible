from configparser import ConfigParser
from pathlib import Path

import pytest
import os

from tox_ansible.options import Options, INI_MOLECULE_GLOBAL_OPTS, INI_IGNORE_PATHS, SCENARIO_ENV_NAME, SCENARIO_OPTION_NAME
from tox_ansible.tox_helper import Tox


@pytest.fixture
def good_config(mocker):
    c = mocker.Mock()
    reader = mocker.Mock()
    c.get_reader.return_value = reader
    reader.getlist.return_value = ["2.10", "3.9"]
    reader.getstring.return_value = "auto"
    c.opts = {SCENARIO_OPTION_NAME: ['explicit_scenario,other_scenario']}
    return c


@pytest.fixture
def opts(mocker, good_config):
    opts = Options(good_config)
    return opts


@pytest.fixture
def bad_config(mocker):
    c = mocker.Mock()
    reader = mocker.Mock()
    c.get_reader.return_value = reader
    reader.getlist.return_value = ["2.11"]
    reader.getstring.return_value = "invalid"
    return c


def test_do_filter_scenario(opts):
    opts.role = []
    opts.scenario = ["default"]
    opts.driver = []
    assert opts.do_filter()


def test_do_filter_driver(opts):
    opts.role = []
    opts.scenario = []
    opts.driver = ["openstack"]
    assert opts.do_filter()


def test_do_filter_none_is_false(opts):
    opts.role = []
    opts.scenario = []
    opts.driver = []
    assert not opts.do_filter()


def test_options_expand_matrix(opts, mocker):
    opts.matrix = mocker.Mock()
    opts.expand_matrix([])
    opts.matrix.expand.assert_called_once_with([])


@pytest.mark.parametrize(
    "folder,expected",
    [
        (Path("tests/fixtures/collection"), False),
        (Path("tests/fixtures/expand_collection"), False),
        (Path("tests/fixtures/expand_collection_newlines"), False),
        (Path("tests/fixtures/has_deps"), False),
        (Path("tests/fixtures/not_collection"), False),
        (Path("tests/fixtures/nothing"), True),
    ],
)
def test_disabled(mocker, folder, expected):
    c = ConfigParser()
    c.read(folder / "tox.ini")
    config = mocker.Mock()
    config._cfg = c  # pylint: disable=protected-access
    tox = Tox(config)
    options = Options(tox)
    assert options.disabled == expected


def test_options_are_valid(bad_config):
    with pytest.raises(ValueError):
        o = Options(bad_config)


def test_global_opts(opts):
    assert opts.global_opts == ["2.10", "3.9"]
    opts.reader.getlist.assert_called_with(INI_MOLECULE_GLOBAL_OPTS, sep="\n")
    assert opts.ignore_paths == ["2.10", "3.9"]
    opts.reader.getlist.assert_called_with(INI_IGNORE_PATHS, sep="\n")


def test_environment_cli_set_option(mocker, good_config):
    mocker.patch.dict(os.environ, {SCENARIO_ENV_NAME: "my_test_scenario"})
    # Tests with both env and CLI
    cli_opts = Options(good_config)
    # Tests with only env
    good_config.opts = {}
    env_opts = Options(good_config)
    # CLI options take precedence
    assert cli_opts.scenario == ["explicit_scenario", "other_scenario"]
    # Env options dropback
    assert env_opts.scenario == ["my_test_scenario"]
