# Configuration

`tox-ansible` can be configured via `pyproject.toml` (recommended) or a standalone `tox-ansible.ini` file.

## pyproject.toml (recommended)

Add a `[tool.tox-ansible]` section to your collection's `pyproject.toml`:

```toml
# pyproject.toml
[tool.tox-ansible]
skip = [
    "2.16",
    "devel",
]
```

This will skip tests in any environment whose name contains `2.16` or `devel`. The list of strings is used for a simple substring comparison against environment names.

When using `pyproject.toml`, tox also needs a `[tool.tox]` section (even if empty) so it can discover the file as its configuration source:

```toml
# pyproject.toml
[tool.tox]
requires = ["tox>=4.2"]

[tool.tox-ansible]
skip = ["devel"]
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
skip =
    2.16
    devel
```

```bash
tox --ansible --conf tox-ansible.ini
```

Using a separate `tox-ansible.ini` file avoids conflicts with an existing `tox.ini` that may already define `[testenv]` sections for other purposes.

If both `pyproject.toml` and `tox-ansible.ini` contain configuration, `pyproject.toml` takes precedence.

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
