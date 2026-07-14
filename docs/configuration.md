# Configuration

`tox-ansible` can be configured via `pyproject.toml` (recommended) or a standalone `tox-ansible.ini` file.

## pyproject.toml (recommended)

Add a `[tool.tox-ansible]` section to your collection's `pyproject.toml`:

```toml
# pyproject.toml
[tool.tox-ansible]
coverage = true
downstream = true
skip = [
    "devel",
]
```

This enables coverage reporting for unit test environments, unions AAP/cert
ansible-core extras onto the upstream matrix (`downstream = true`; see ADR-001),
and skips tests in any environment whose name contains `devel`. The `skip` list
is a simple substring comparison against environment names.

### Molecule configuration

Molecule testing is controlled by the `molecule` option:

```toml
# pyproject.toml
[tool.tox-ansible]
molecule = "auto"  # "auto" (default), "true", or "false"
```

- **`auto`** (default): molecule environments are included only if `extensions/molecule/` contains at least one scenario (a subdirectory with `molecule.yml`).
- **`true`**: always include molecule environments, even if no scenarios are discovered.
- **`false`**: never include molecule environments.

When included, molecule uses the **same Python × ansible-core matrix** as
integration, unit, and sanity.

The default command is `python3 -m molecule test --all`. Add CLI flags with
`molecule_append`, or fully replace the command list with
`molecule_commands` (which ignores the default and `molecule_append`):

```toml
[tool.tox-ansible]
# Append to the default: python3 -m molecule test --all --workers 4
molecule_append = ["--workers", "4"]

# Or fully replace:
# molecule_commands = ["molecule test -s default"]
```

`shared_state`, `prerun`, inventory, and other scenario behavior belong in
`extensions/molecule/config.yml` (Molecule's config), not in tox-ansible.
ansible-creator scaffolds that file; leave `prerun` under collection control.

Molecule `commands_pre` installs collection requirements (via ADE) from, when
present:

- `tests/requirements.yml`
- `tests/integration/requirements.yml` (shared with integration during migration)
- `tests/molecule/requirements.yml` (optional molecule-only deps)

### Integration autodetection

`integration-*` environments are included only when the collection has
integration content:

- a non-empty `tests/integration/targets/` directory (ansible-test style), or
- pytest modules under `tests/integration/` (`test_*.py` / `*_test.py`)

Collections that migrate fully to Molecule scenarios (and remove ansible-test
targets) automatically drop the integration matrix without extra `skip`
entries.

When using `pyproject.toml`, tox also needs a `[tool.tox]` section (even if empty) so it can discover the file as its configuration source:

```toml
# pyproject.toml
[tool.tox]
requires = ["tox>=4.2"]

[tool.tox-ansible]
skip = ["devel"]
molecule = "auto"
molecule_append = ["--workers", "4"]
```

With this in place, no `--conf` flag is needed:

```bash
tox --ansible
```

## tox-ansible.ini (legacy)

Alternatively, `tox-ansible` reads the `[ansible]` section from whatever tox configuration file is loaded. This is typically a `tox-ansible.ini` file passed via `--conf`:

```ini
# tox-ansible.ini
[ansible]
coverage = true
downstream = true
skip =
    devel
molecule = auto
molecule_append =
    --workers
    4
molecule_commands =
```

```bash
tox --ansible --conf tox-ansible.ini
```

Using a separate `tox-ansible.ini` file avoids conflicts with an existing `tox.ini` that may already define `[testenv]` sections for other purposes.

If both `pyproject.toml` and `tox-ansible.ini` contain configuration, `pyproject.toml` takes precedence.

## Downstream matrix (AAP / cert)

By default the environment list follows the community ansible-core support
matrix. Set `downstream = true` to **extend** that list with AAP-supported
cores that community has EOL'd (for example 2.16 and 2.18), while keeping newer
upstream cores for forward-looking content testing.

`downstream = true` means **upstream ∪ extras**, not an AAP-only matrix. Use
`skip` to drop unwanted factors (for example `devel`, `milestone`, or `2.21`).

If `pyproject.toml` contains any `[tool.tox-ansible]` section, it takes
precedence over `[ansible]` in `tox-ansible.ini` for the whole section — put
`downstream` in the TOML file when both configs exist.

## Unit test coverage

Coverage reporting is disabled by default. Enable it persistently with `coverage = true` in either configuration format, or for a single invocation with `--coverage`:

```bash
tox --ansible --coverage -e unit-py3.13-2.19
```

When enabled, tox-ansible installs `pytest-cov`, generates coverage configuration for the collection under tox's work directory, and reports coverage for Python files below the collection's `plugins/` directory. Eligible files that the unit tests do not import appear with 0% coverage. No project-level `.coveragerc` is required.

Raw coverage data is stored inside each tox unit environment. This keeps parallel environments isolated; reports from the Python and ansible-core matrix are independent and are not automatically combined.

Coverage applies only to `unit-*` environments. Integration, sanity, molecule, and galaxy environments remain unchanged. Explicit CLI options take precedence over project configuration, so configured coverage can be disabled temporarily:

```bash
tox --ansible --no-coverage -e unit-py3.13-2.19
```

## Overriding the configuration

Any tox environment configuration can be overridden by the user. The method depends on which configuration file you use.

### With pyproject.toml

Use the native tox TOML format under `[tool.tox]`:

```toml
# pyproject.toml
[tool.tox.env_run_base]
commands_pre = ["true"]

[tool.tox.env.integration-py3_12-devel]
commands = ["true"]
```

### With tox-ansible.ini

Use the standard tox INI sections:

```ini
# tox-ansible.ini
[testenv]
commands_pre =
    true

[testenv:integration-py3.12-{devel,milestone}]
commands =
    true
```

Used without caution, overrides can result in unexpected behavior and possible false positive or false negative test results.
