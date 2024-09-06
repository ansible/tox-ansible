# Frequently asked questions

> Need help or want to discuss the project? See our [Contributor guide](https://ansible.readthedocs.io/projects/tox-ansible/contributor_guide/#talk-to-us) join the conversation!

## How does it work?

`tox` will, by default, create a Python virtual environment for a given environment. `tox-ansible` adds Ansible collection specific build and test logic to tox. The collection is copied into the virtual environment created by tox, built, and installed into the virtual environment. The installation of the collection will include the collection's collection dependencies. `tox-ansible` will also install any Python dependencies from a `test-requirements.txt` (or `requirements-test.txt`) and `requirements.txt` file. The virtual environment's temporary directory is used, so the copy, build and install steps are performed with each test run ensuring the current collection code is used.

`tox-ansible` also sets the `ANSIBLE_COLLECTIONS_PATH` environment variable to point to the virtual environment's temporary directory. This ensures that the collection under test is used when running tests. The `pytest-ansible-units` pytest plugin injects the `ANSIBLE_COLLECTIONS_PATH` environment variable into the collection loader so ansible-core can locate the collection.

`pytest` is used to run both the `unit` and `integration tests`.
`ansible-test sanity` is used to run the `sanity` tests.

For full configuration examples for each of the sanity, integration, and unit tests including the commands being run and the environment variables being set and passed, see the following:

- [integration](https://github.com/ansible/tox-ansible/blob/main/docs/integration.ini)
- [sanity](https://github.com/ansible/tox-ansible/blob/main/docs/sanity.ini)
- [unit](https://github.com/ansible/tox-ansible/blob/main/docs/unit.ini)

See the [tox documentation](https://tox.readthedocs.io/en/latest/) for more information on tox.
