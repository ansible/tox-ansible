# Configuration

`tox-ansible` should be configured using a `tox-ansible.ini` file. Using a `tox-ansible.ini` file allows for the introduction of the `tox-ansible` plugin to a repository that may already have an existing `tox` configuration without conflicts. If no configuration overrides are needed, the `tox-ansible.ini` file may be empty but should be present. In addition to all `tox` supported keywords the `ansible` section and `skip` keyword are available:

```ini
# tox-ansible.ini
[ansible]
skip =
    2.9
    devel
```

This will skip tests in any environment that uses Ansible 2.9 or the devel branch. The list of strings is used for a simple string in string comparison of environment names.

### Overriding the configuration

Any configuration in either the `[testenv]` section or am environment section `[testenv:integration-py3.11-{devel,milestone}]` can override some or all of the `tox-ansible` environment configurations.

For example

```ini

[testenv]
commands_pre =
    true

[testenv:integration-py3.11-{devel,milestone}]
commands =
    true
```

will result in:

```ini
# tox-ansible.ini
[testenv:integration-py3.11-devel]
commands_pre = true
commands = true
```

Used without caution, this configuration can result in unexpected behavior, and possible false positive or false negative test results.
