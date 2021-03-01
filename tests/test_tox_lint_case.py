from unittest.mock import Mock

from tox_ansible.ansible.scenario import Scenario
from tox_ansible.tox_lint_case import ToxLintCase


def test_names_are_correct(mocker):
    tc = ToxLintCase([])
    deps = set(["ansible-lint", "flake8", "yamllint", "ansible"])
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value="/home",
    )
    assert tc.get_name() == "lint_all"
    assert tc.get_working_dir() == "/home"
    assert tc.get_dependencies() == deps


def test_expand_python():
    tc = ToxLintCase([])
    out = tc.expand_python("2.7")
    assert out.get_name() == "py27-lint_all"


def test_expand_ansible():
    tc = ToxLintCase([])
    out = tc.expand_ansible("2.10")
    assert out.get_name() == "ansible210-lint_all"


def test_commands_are_correct(mocker):
    options = Mock()
    options.get_global_opts.return_value = []
    options.ansible_lint = None
    options.yamllint = None
    case1 = Mock(scenario=Scenario("molecule/s1"))
    case2 = Mock(scenario=Scenario("something/roles/r1/molecule/s2"))
    case3 = Mock(scenario=Scenario("roles/r2/molecule/s3"))
    bummer = ToxLintCase([])
    mocker.patch("tox_ansible.tox_lint_case.Tox.toxinidir", "")
    tc = ToxLintCase([case1, case2, case3, bummer])
    cmds = tc.get_commands(options)
    expected = [["ansible-lint", "-R"], ["yamllint", "."], ["flake8", "."]]
    assert expected == cmds


def test_lint_options_correct(mocker):
    options = mocker.Mock()
    options.get_global_opts.return_value = []
    options.ansible_lint = "some/path"
    options.yamllint = "some/yaml.path"
    bummer = ToxLintCase([])
    mocker.patch("tox_ansible.tox_lint_case.Tox.toxinidir", "")
    tc = ToxLintCase([bummer])
    cmds = tc.get_commands(options)
    expected = [
        ["ansible-lint", "-R", "-c", "some/path"],
        ["yamllint", "-c", "some/yaml.path", "."],
        ["flake8", "."],
    ]
    assert expected == cmds
