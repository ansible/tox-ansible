from configparser import ConfigParser
from pathlib import Path

import pytest

from tox_ansible.options import Options
from tox_ansible.tox_helper import Tox


@pytest.fixture
def opts(mocker):
    c = mocker.Mock()
    reader = mocker.Mock()
    c.get_reader.return_value = reader
    reader.getlist.return_value = ["2.10", "3.9"]
    opts = Options(c)
    return opts


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
