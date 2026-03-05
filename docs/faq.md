# Frequently asked questions

> Need help or want to discuss the project? See our [Contributor guide](https://ansible.readthedocs.io/projects/tox-ansible/contributor_guide/#talk-to-us) join the conversation!

## How does it work?

`tox` will, by default, create a Python virtual environment for a given environment. `tox-ansible` adds Ansible collection specific build and test logic to tox by delegating collection installation to [ansible-dev-environment](https://github.com/ansible/ansible-dev-environment) (ade).

For each test environment, `tox-ansible` runs `ade install` as a pre-command which:

1. Installs the requested version of `ansible-core` (from PyPI, a GitHub branch, or a URL).
2. Builds and installs the collection from the current directory into the virtual environment's site-packages.
3. Discovers and installs Python dependencies declared by the collection and its transitive dependencies using `ansible-builder introspect`.

`tox-ansible` also installs any Python dependencies from a `test-requirements.txt` (or `requirements-test.txt`) and `requirements.txt` file.

`tox-ansible` sets the `ANSIBLE_COLLECTIONS_PATH` environment variable to `"."` (the current directory). This prevents ansible-core from scanning system and user collection paths and isolates the collection under test. The collection itself is installed into the virtual environment's site-packages via an editable install (`ade install -e`), so Ansible discovers it through Python's import machinery. The `pytest-ansible` plugin injects the `ANSIBLE_COLLECTIONS_PATH` environment variable into the collection loader so ansible-core can locate the collection.

`pytest` is used to run both the `unit` and `integration tests`.
`ansible-test sanity` is used to run the `sanity` tests.

For more details on the architecture and how `tox-ansible` and `ade` work together, see the [Architecture](architecture.md) page.

For full configuration examples for each of the sanity, integration, and unit tests including the commands being run and the environment variables being set and passed, see the following:

- [integration](https://github.com/ansible/tox-ansible/blob/main/docs/integration.ini)
- [sanity](https://github.com/ansible/tox-ansible/blob/main/docs/sanity.ini)
- [unit](https://github.com/ansible/tox-ansible/blob/main/docs/unit.ini)

See the [tox documentation](https://tox.readthedocs.io/en/latest/) for more information on tox.
