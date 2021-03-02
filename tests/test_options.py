import pytest

from tox_ansible.options import Options


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
