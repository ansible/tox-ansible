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

## Scoped testing with impact_file

The `impact_file` option enables scoped testing by consuming an ImpactReport JSON artifact from [content-plugin-finder](https://github.com/ansible/content-plugin-finder). This solves the problem of CI pipelines running the full test matrix even when only a small subset of content was changed.

### Configuration

Configure `impact_file` via CLI, INI, or TOML (TOML takes precedence over INI, CLI takes precedence over both):

```bash
# CLI
tox --ansible --impact-file impact.json
```

```toml
# pyproject.toml
[tool.tox-ansible]
impact_file = "impact.json"
```

```ini
# tox-ansible.ini
[ansible]
impact_file = impact.json
```

### Behavior

When an impact file is configured:

- **Molecule environments**: If `molecule_scenarios` is empty or absent, all `molecule-*` environments are omitted from the matrix. When scenarios are listed, molecule commands are scoped to run only those specific scenarios.
- **Integration environments**: If `integration_targets` is empty or absent, all `integration-*` environments are omitted. When targets are listed, integration commands use `ansible-test integration` with only those specific targets. If a listed target does not exist as an ansible-test style target (under `tests/integration/targets/<name>`), a warning is logged and the target is skipped. If no valid ansible-test targets remain, the command falls back to the default pytest-based integration tests with a warning.
- **Unit, sanity, and galaxy environments**: Unaffected by the impact file.

When no `impact_file` is configured, existing behavior is fully preserved.

### ImpactReport JSON schema

The impact file is a JSON object produced by `content-plugin-finder --impact`:

```json
{
  "collection": "namespace.collection",
  "changed_files": ["plugins/module_utils/util.py"],
  "affected_plugins": ["namespace.collection.my_module"],
  "molecule_scenarios": ["extensions/molecule/default"],
  "integration_targets": ["tests/integration/targets/my_module"],
  "reasons": {
    "tests/integration/targets/my_module": ["plugin:namespace.collection.my_module via plugins/module_utils/util.py"]
  }
}
```

### Validation

tox-ansible validates the impact file:

- JSON must be valid and contain an object
- `collection` field is required and must match the collection's `namespace.name` from `galaxy.yml`
- All paths must be relative (no absolute paths or path traversal)
- List fields must contain only strings

Invalid or malformed files cause tox to exit with an actionable error message.

### CI workflow example

A typical CI workflow using content-plugin-finder:

```yaml
- name: Generate impact report
  run: |
    git diff --name-only HEAD~1 | content-plugin-finder --impact . --from-stdin --format json > impact.json

- name: Run scoped tests
  run: tox --ansible --impact-file impact.json
```

This runs only the molecule scenarios and integration targets affected by the changed files.

## Job bucketing

Large integration suites can be split across CI jobs by estimated runtime. `matrix_jobs` is the maximum number of jobs for integration targets and, separately, for molecule scenarios. `matrix_max_parallel` is copied into the matrix for a workflow `strategy.max-parallel` setting. Tox does not start or limit runners.

Set both values in either config file. TOML wins over INI. CLI wins over both. `0` in a config file leaves `max_parallel` out of the matrix. `--matrix-max-parallel` must be a positive integer.

```bash
tox --ansible --impact-file impact.json --matrix-jobs 24 --matrix-max-parallel 8 --gh-matrix-jobs
```

```toml
# pyproject.toml
[tool.tox-ansible]
impact_file = "impact.json"
matrix_jobs = 24
matrix_max_parallel = 8
```

```ini
# tox-ansible.ini
[ansible]
impact_file = impact.json
matrix_jobs = 24
matrix_max_parallel = 8
```

`--gh-matrix-jobs` prints a matrix and exits. Every selected scenario appears in exactly one job. Empty jobs are omitted. Integration targets and molecule scenarios are packed separately, so job ids look like `integration-1` and `molecule-1`.

```json
{
  "jobs": ["integration-1", "integration-2"],
  "scenarios": {
    "integration-1": "slow_target",
    "integration-2": "fast_target"
  },
  "max_parallel": 8
}
```

On GitHub Actions the same object is appended to `GITHUB_OUTPUT` as `jobs`, `scenarios`, and, when set, `max_parallel`.

Estimated seconds come from `tests/integration/targets/<name>/aliases`:

- `time=45s`, `time=2m`, or `time=45`
- `slow` uses 3000 seconds when no `time=` alias is present
- otherwise 180 seconds

Molecule scenarios use 180 seconds. Scenarios with the same estimate are ordered by name. The packer follows `ansible_test_splitter`: each job gets about an equal share of the total, and a scenario that fits nowhere else goes in the first job.

Run one job with the same `matrix_jobs` value. `--matrix-job` recomputes the buckets and runs only that job's scenarios. The job fails if an assigned integration target directory is missing:

```bash
tox --ansible --impact-file impact.json --matrix-jobs 24 --matrix-job integration-1 -e integration-py3.12-2.19
```

`--matrix-job` requires an impact file. A molecule environment does not run integration scenarios, and an integration environment does not run molecule scenarios. `molecule_commands` cannot be combined with `--matrix-job`; remove it so the selected scenarios run.

Molecule jobs keep the impact-report path as the scenario id, so two scenarios named `default` in different directories stay distinct. Integration jobs still use the target directory name. Those ids are space-separated, so a path that contains whitespace is rejected.

Collection scenarios run with `molecule test -s` and the path under `extensions/molecule/` as the scenario name. Every other scenario runs from the directory that contains `molecule/`, because Molecule has no project-directory option.

`--gh-matrix` and `--gh-matrix-jobs` are separate. The first lists tox environments. The second lists scenario jobs.

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
