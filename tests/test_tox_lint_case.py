from pathlib import Path
from unittest.mock import Mock

import pytest

from tox_ansible.ansible.scenario import Scenario
from tox_ansible.tox_lint_case import ToxLintCase


@pytest.fixture
def precommit():
    p = Path(__file__).parent
    return p / "fixtures" / "is_precommit"


@pytest.fixture
def no_precommit():
    p = Path(__file__).parent
    return p / "fixtures" / "collection"


def test_names_are_correct(mocker):
    tc = ToxLintCase([])
    deps = set(["ansible-lint", "flake8", "yamllint", "ansible"])
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value="/home",
    )
    assert tc.get_name() == "lint_all"
    assert tc.working_dir == "/home"
    assert tc.dependencies == deps


def test_pre_commit_is_correct(mocker, precommit, no_precommit):
    tc = ToxLintCase([])
    deps = set(["pre-commit"])
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value=precommit,
    )
    assert tc.is_precommit
    assert tc.dependencies == deps
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value=no_precommit,
    )
    assert not tc.is_precommit


def test_expand_python():
    tc = ToxLintCase([])
    out = tc.expand_python("2.7")
    assert out.get_name() == "py27-lint_all"


def test_expand_ansible():
    tc = ToxLintCase([])
    out = tc.expand_ansible("2.10")
    assert out.get_name() == "ansible210-lint_all"


def test_commands_are_correct(mocker, no_precommit, precommit):
    options = Mock()
    options.global_opts = []
    options.ansible_lint = None
    options.yamllint = None
    case1 = Mock(scenario=Scenario("molecule/s1"))
    case2 = Mock(scenario=Scenario("something/roles/r1/molecule/s2"))
    case3 = Mock(scenario=Scenario("roles/r2/molecule/s3"))
    bummer = ToxLintCase([])
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value=no_precommit,
    )
    tc = ToxLintCase([case1, case2, case3, bummer])
    cmds = tc.get_commands(options)
    expected = [["ansible-lint", "-R"], ["flake8", "."]]
    assert expected == cmds
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value=precommit,
    )
    assert tc.get_commands(options) == [["pre-commit", "run", "--all"]]


def test_lint_options_correct(mocker, no_precommit):
    options = mocker.Mock()
    options.global_opts = []
    options.ansible_lint = "some/path"
    options.yamllint = "some/yaml.path"
    bummer = ToxLintCase([])
    mocker.patch(
        "tox_ansible.tox_lint_case.Tox.toxinidir",
        new_callable=mocker.PropertyMock,
        return_value=no_precommit,
    )
    tc = ToxLintCase([bummer])
    cmds = tc.get_commands(options)
    expected = [
        ["ansible-lint", "-R", "-c", "some/path"],
        ["yamllint", "-c", "some/yaml.path", "."],
        ["flake8", "."],
    ]
    assert expected == cmds
