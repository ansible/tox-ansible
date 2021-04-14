from __future__ import print_function

import contextlib
import os
import shutil
import subprocess
from unittest.mock import patch

import pytest

EXPECTED = {
    "tests/fixtures/collection": "\n".join(
        [
            "env",
            "lint_all",
            "one",
            "roles-complex-default",
            "roles-complex-name_mismatch",
            "roles-complex-openstack",
            "roles-simple-default",
            "sanity",
            "shell",
            "two",
        ]
    ),
    "tests/fixtures/expand_collection": "\n".join(
        [
            "derp",
            "env",
            "py27-ansible28-lint_all",
            "py27-ansible28-roles-simple-default",
            "py27-ansible29-lint_all",
            "py27-ansible29-roles-simple-default",
            "py38-ansible28-lint_all",
            "py38-ansible28-roles-simple-default",
            "py38-ansible29-lint_all",
            "py38-ansible29-roles-simple-default",
            "sanity",
            "shell",
        ]
    ),
    "tests/fixtures/not_collection": "\n".join(
        [
            "coverage",
            "lint",
            "lint_all",
            "one",
            "py27",
            "py27-tox20",
            "py27-tox30",
            "py35",
            "py36",
            "py37",
            "py38",
            "py38-tox20",
            "py38-tox30",
            "two",
        ]
    ),
    "tests/fixtures/simplified": "\n".join(
        [
            "default",
            "env",
            "lint_all",
            "myrole",
            "myrole-another",
            "sanity",
            "shell",
            "two",
        ]
    ),
}
EXPECTED["tests/fixtures/expand_collection_comma"] = EXPECTED[
    "tests/fixtures/expand_collection"
]
EXPECTED["tests/fixtures/expand_collection_newlines"] = EXPECTED[
    "tests/fixtures/expand_collection"
]

EXPECTED_ARGS = {
    "default": """roles-complex-default
roles-simple-default""",
    "openstack": "roles-complex-openstack",
    "simple": "roles-simple-default",
}


@contextlib.contextmanager
def cd(directory):
    cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(cwd)


def run_tox(args, capture):
    tox = ["tox"]
    tox.extend(args)
    try:
        subprocess.run(tox, check=True)
    except SystemExit as s:
        if s.code != 0:
            raise
    outs = capture.readouterr()
    return outs.out.strip()


@pytest.mark.parametrize(
    "directory",
    [
        ("tests/fixtures/collection"),
        ("tests/fixtures/expand_collection"),
        ("tests/fixtures/expand_collection_comma"),
        ("tests/fixtures/expand_collection_newlines"),
        ("tests/fixtures/not_collection"),
        ("tests/fixtures/simplified"),
    ],
)
def test_run_tox(directory, capfd):
    with cd(directory):
        out = run_tox(["-l"], capfd)
    assert out == EXPECTED[directory]


def test_tox_ini_deps_preserved(capfd):
    with cd("tests/fixtures/has_deps"):
        lint_out = run_tox(["--showconfig", "-e", "lint_all"], capfd)
        simple_out = run_tox(["--showconfig", "-e", "roles-simple-default"], capfd)
    deps = [m for m in lint_out.split("\n") if m.startswith("deps = ")][0]
    assert "notadep==1" in deps
    deps = [m for m in simple_out.split("\n") if m.startswith("deps = ")][0]
    assert "otherdep" in deps


@pytest.mark.parametrize(
    "target,value",
    [("scenario", "default"), ("driver", "openstack")],
)
def test_run_tox_with_args(target, value, capfd):
    args = ["-l", "--ansible-{}".format(target), value]
    with cd("tests/fixtures/collection"):
        cli = run_tox(args, capfd)
        with patch.dict("os.environ", {"TOX_ANSIBLE_{}".format(target.upper()): value}):
            env = run_tox(["-l"], capfd)
    assert cli == EXPECTED_ARGS[value]
    assert env == EXPECTED_ARGS[value]


def test_run_with_test_command(capfd):
    with cd("tests/fixtures/collection"):
        shutil.rmtree(".tox")
        cli = run_tox(["-e", "roles-simple-default"], capfd)
    assert "tox-ansible is the best" in cli
