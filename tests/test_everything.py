from __future__ import print_function

import contextlib
import os
import subprocess

import pytest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


EXPECTED = {
    "tests/fixtures/collection": "\n".join(
        [
            "complex-default",
            "complex-openstack",
            "complex-real_name",
            "lint_all",
            "simple-default",
        ]
    ),
    "tests/fixtures/expand_collection": "\n".join(
        [
            "derp",
            "py27-ansible28-lint_all",
            "py27-ansible28-simple-default",
            "py27-ansible29-lint_all",
            "py27-ansible29-simple-default",
            "py38-ansible28-lint_all",
            "py38-ansible28-simple-default",
            "py38-ansible29-lint_all",
            "py38-ansible29-simple-default",
        ]
    ),
    "tests/fixtures/not_collection": "\n".join(
        [
            "py27",
            "py35",
            "py36",
            "py37",
            "py38",
            "py27-tox20",
            "py27-tox30",
            "py38-tox20",
            "py38-tox30",
            "lint",
            "coverage",
        ]
    ),
}

EXPECTED_ARGS = {
    "default": """complex-default
simple-default""",
    "openstack": "complex-openstack",
    "simple": "simple-default",
}


@contextlib.contextmanager
def cd(directory):
    cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield
    except Exception:
        raise
    finally:
        os.chdir(cwd)


def run_tox(args, capture):
    tox = ["tox"]
    tox.extend(args)
    try:
        subprocess.run(tox)
    except SystemExit as s:
        if s.code != 0:
            raise
    finally:
        outs = capture.readouterr()
        return outs.out.strip()


@pytest.mark.parametrize(
    "directory",
    [
        ("tests/fixtures/collection"),
        ("tests/fixtures/expand_collection"),
        ("tests/fixtures/not_collection"),
    ],
)
def test_run_tox(directory, capfd):
    with cd(directory):
        out = run_tox(["-l"], capfd)
    assert out == EXPECTED[directory]


@pytest.mark.parametrize(
    "target,value",
    [("scenario", "default"), ("driver", "openstack"), ("role", "simple")],
)
def test_run_tox_with_args(target, value, capfd):
    args = ["-l"]
    args.append("--ansible-{}".format(target))
    args.append(value)
    with cd("tests/fixtures/collection"):
        cli = run_tox(args, capfd)
        with patch.dict("os.environ", {"TOX_ANSIBLE_{}".format(target.upper()): value}):
            env = run_tox(["-l"], capfd)
    assert cli == EXPECTED_ARGS[value]
    assert env == EXPECTED_ARGS[value]
