# Usage of tox-ansible

> Need help or want to discuss the project? See our [Contributor guide](https://ansible.readthedocs.io/projects/tox-ansible/contributor_guide/#talk-to-us) to learn how to join the conversation!

## Getting started

From the root of your collection, add a `[tool.tox-ansible]` section to your `pyproject.toml` (the section can be empty if no skip filters are needed):

```toml
# pyproject.toml
[tool.tox]
requires = ["tox>=4.2"]

[tool.tox-ansible]
```

Then list the available environments:

```bash
tox list --ansible
```

A list of dynamically generated Ansible environments will be displayed:

```

default environments:
...
integration-py3.11-2.14      -> Integration tests for ansible.scm using ansible-core 2.14 and python 3.11
integration-py3.12-devel     -> Integration tests for ansible.scm using ansible-core devel and python 3.11
...
sanity-py3.11-2.14           -> Sanity tests for ansible.scm using ansible-core 2.14 and python 3.11
sanity-py3.12-devel          -> Sanity tests for ansible.scm using ansible-core devel and python 3.11
...
unit-py3.11-2.14             -> Unit tests for ansible.scm using ansible-core 2.14 and python 3.11
unit-py3.12-devel            -> Unit tests for ansible.scm using ansible-core devel and python 3.11
```

These represent the available testing environments. Each denotes the type of tests that will be run, the Python interpreter used to run the tests, and the Ansible version used to run the tests.

To run tests with a single environment, simply run the following command:

```bash
tox -e sanity-py3.11-2.14 --ansible
```

To run tests with multiple environments, simply add the environment names to the command:

```bash
tox -e sanity-py3.11-2.14,unit-py3.11-2.14 --ansible
```

To run all tests of a specific type in all available environments, use the factor `-f` flag:

```bash
tox -f unit --ansible -p auto
```

To run all tests across all available environments:

```bash
tox --ansible -p auto
```

Note: The `-p auto` flag will run multiple tests in parallel.
Note: The specific Python interpreter will need to be pre-installed on your system, e.g.:

```bash
sudo dnf install python3.9
```

To review the specific commands and configuration for each of the integration, sanity, and unit factors:

```bash
tox config --ansible
```

Limit test execution to a specific scope with `--matrix-scope`:

```bash
tox --ansible --matrix-scope unit
```

The same option limits GitHub Actions matrix output when used with `--gh-matrix`:

```bash
tox --ansible --gh-matrix --matrix-scope unit
```

A list of dynamically generated Ansible environments will be displayed specifically for unit tests:

```
[
  {
    "description": "Unit tests using ansible 2.9 and python 3.8",
    "factors": [
      "unit",
      "py3.8",
      "2.9"
    ],
    "name": "unit-py3.8-2.9",
    "python": "3.8"
  },
  ...
  {
    "description": "Unit tests using ansible-core milestone and python 3.12",
    "factors": [
      "unit",
      "py3.12",
      "milestone"
    ],
    "name": "unit-py3.12-milestone",
    "python": "3.12"
  }
]
```

!!! note "Using tox-ansible.ini"
    If your project uses `tox-ansible.ini` instead of `pyproject.toml`, add `--conf tox-ansible.ini` to every tox command:

    ```bash
    tox list --ansible --conf tox-ansible.ini
    tox -e unit-py3.13-2.19 --ansible --conf tox-ansible.ini
    ```

    See the [Configuration](configuration.md) page for details on both approaches.

## Passing command line arguments to ansible-test / pytest

The behavior of the `ansible-test` (for `sanity-*` environments) or `pytest` (for `unit-*` and `integration-*` environments) commands can be customized by passing further command line arguments to it, e.g., by invoking `tox` like this:

```bash
tox -f sanity --ansible -- --test validate-modules -vvv
```

The arguments after the `--` will be passed to the `ansible-test` command. Thus in this example, only the `validate-modules` sanity test will run, but with an increased verbosity.

Same can be done to pass arguments to the `pytest` commands for the `unit-*` and `integration-*` environments:

```bash
tox -e unit-py3.13-2.19 --ansible -- --junit-xml=tests/output/junit/unit.xml
```

## Unit test coverage

Use `--coverage` to generate a coverage report for Python files in the collection's `plugins/` directory while running unit tests:

```bash
tox -e unit-py3.13-2.19 --ansible --coverage
```

tox-ansible installs `pytest-cov` and generates the required path mappings automatically, including the collection-specific installation path created by Ansible Dev Environment. Eligible Python files below `plugins/` that the unit tests do not import appear with 0% coverage. The collection does not need a `.coveragerc` or a custom unit test command.

Each unit environment stores its raw coverage data in its own tox environment directory. Parallel environments therefore produce independent reports; tox-ansible does not automatically combine results across the Python and ansible-core matrix.

Coverage can also be enabled persistently with `coverage = true` in `[tool.tox-ansible]` in `pyproject.toml` or `[ansible]` in `tox-ansible.ini`. See the [Configuration](configuration.md#unit-test-coverage) page for examples and precedence rules.

Additional pytest-cov options can be passed after `--`, for example:

```bash
tox -e unit-py3.13-2.19 --ansible --coverage -- --cov-report=xml
```

## Usage in a CI/CD pipeline

A GitHub Actions matrix is dynamically created by `tox-ansible` using the `--gh-matrix` and `--ansible` flags. The list of environments is converted to a list of entries in json format which is stored under the `envlist` key in the file specified by the `GITHUB_OUTPUT` environment variable.

Below shows relevant snippets from a GitHub Action workflow which:

1. Uses the `--gh-matrix` flag to generate a list of environments.
2. Creates individual jobs for each environment using a [matrix strategy](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations).

!!! note

    This is not a production ready GitHub Action workflow. It is missing key steps for readability purposes. You will need to set up Python and install `tox-ansible` in your GitHub Action workflow.

```yaml
# .github/workflows/tox-ansible.yml
name: Tox Ansible
# ...
jobs:
  generate-matrix:
    # ...
    outputs:
      envlist: ${{ steps.matrix.outputs.envlist }}
    steps:
      # ...
      - name: Generate matrix
        id: matrix
        run: |
          tox --ansible --conf tox-ansible.ini --gh-matrix

  tox-ansible:
    needs: generate-matrix
    # ...
    strategy:
      fail-fast: false
      matrix:
        env: ${{ fromJSON(needs.generate-matrix.outputs.envlist) }}
    steps:
      # ...
      - name: Run tox environment ${{ matrix.env.name }}
        run: |
          tox --ansible --conf tox-ansible.ini -e ${{ matrix.env.name }}
```

## Skip functionality

Circumstances may require certain tests to be skipped. `tox-ansible` supports skipping tests via `skip` in `[tool.tox-ansible]` (pyproject.toml) or `[ansible]` (tox-ansible.ini).

To include AAP/cert ansible-core versions that extend the upstream community
matrix (for example 2.16 and 2.18), set `downstream = true`. That unions
extras onto the upstream list; it does **not** replace newer community cores.
Combine with `skip` if you need a tighter set. See
[Configuration](configuration.md#downstream-matrix-aap--cert).

Example for `pyproject.toml`:

```toml
# pyproject.toml
[tool.tox-ansible]
downstream = true
skip = ["sanity-py3.13"]
```

Example for `tox-ansible.ini`:

```ini
# tox-ansible.ini
[ansible]
downstream = true
skip =
    sanity-py3.13
```

## Testing molecule scenarios

Molecule is a first-class test type in `tox-ansible`. When molecule scenarios are detected in your collection, a `molecule-*` environment is automatically added to the test matrix.

### How it works

`tox-ansible` looks for molecule scenarios under `extensions/molecule/` in your collection root. Each subdirectory containing a `molecule.yml` file is treated as a scenario. When at least one scenario is found, a `molecule-py3.14-2.20` environment is added to the matrix (using the latest stable Python and ansible-core versions).

The `molecule` package is automatically installed as a dependency. Additional molecule plugins (e.g., `molecule-plugins[docker]`) can be added via your collection's `requirements.txt` or `test-requirements.txt`.

### Collection directory structure

```bash
namespace.name
├── extensions
│   └── molecule
│       ├── default
│       │   ├── converge.yml
│       │   ├── molecule.yml
│       │   └── verify.yml
│       └── another_scenario
│           ├── converge.yml
│           ├── molecule.yml
│           └── verify.yml
├── plugins
│   └── modules
│       └── my_module.py
├── tests
│   └── integration
│       └── ...
├── pyproject.toml
└── galaxy.yml
```

### Running molecule tests

To run molecule tests:

```bash
tox -f molecule --ansible
```

To filter the GitHub Actions matrix to only molecule:

```bash
tox --ansible --gh-matrix --matrix-scope molecule
```

### Configuration

By default, molecule environments are auto-discovered (`molecule = "auto"`). You can override this in your configuration:

```toml
# pyproject.toml
[tool.tox-ansible]
molecule = "auto"  # "auto", "true", or "false"
```

To provide custom commands instead of the default `pytest --molecule` invocation:

```toml
[tool.tox-ansible]
molecule_commands = [
    "molecule test -s default",
]
```

See the [Configuration](configuration.md) page for full details.
