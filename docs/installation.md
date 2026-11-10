# Installation

> Need help or want to discuss the project? See our [Contributor guide](https://ansible.readthedocs.io/projects/tox-ansible/contributor_guide/#talk-to-us) to join the conversation!

Getting started with tox-ansible is as simple as:

```bash
pip install tox-ansible
```

## Dependencies

`tox-ansible` will install additional dependencies if necessary:

- `tox` version 4.0 or greater.
- `pytest`
- `pytest-xdist`
- `pytest-cov` when unit test coverage is enabled
- `pyyaml`

Each generated test environment will also install:

- `ansible-dev-environment` (ade) -- handles collection installation, ansible-core versioning, and Python dependency resolution.
- `ansible-compat` (unit, integration, and molecule environments)
- `tox-ansible` (unit and integration environments) -- registers a pytest plugin that initializes Ansible's collection loader from `ANSIBLE_COLLECTIONS_PATH`

## Migrating from pytest-ansible

Recent tox-ansible releases no longer install `pytest-ansible` or pass `--ansible-unit-inject-only` to pytest. Collection discovery uses `ade install -e` during `commands_pre` and `ANSIBLE_COLLECTIONS_PATH=.` in the generated environment (see the [FAQ](faq.md)).

If your collection still relies on pytest-ansible fixtures, plugins, or CLI options:

- Add `pytest-ansible` to `test-requirements.txt`, `requirements-test.txt`, or another file listed in your collection’s Python dependency discovery, or
- Pin an older tox-ansible release until you finish migrating tests.

Adding `pytest-ansible` to your own requirement files does **not** restore tox-ansible's former generated `--ansible-unit-inject-only` flag. If you still need that pytest-ansible option after installing the package yourself, pass it explicitly, for example:

- in `pyproject.toml`: `[tool.pytest.ini_options]` with `addopts = "--ansible-unit-inject-only"`, or
- when invoking tox: `tox -e unit-py3.12-2.19 --ansible -- --ansible-unit-inject-only`

You do not need pytest-ansible for plain pytest unit or integration tests that only import the collection after `ade install -e`.
