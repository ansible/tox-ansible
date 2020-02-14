[![Build Status](https://travis-ci.com/greg-hellings/tox-ansible.svg?branch=master)](https://travis-ci.com/greg-hellings/tox-ansible)
[![Coverage Status](https://coveralls.io/repos/github/greg-hellings/tox-ansible/badge.svg?branch=master)](https://coveralls.io/github/greg-hellings/tox-ansible?branch=master)
[![PyPI version](https://badge.fury.io/py/tox-ansible.svg)](https://badge.fury.io/py/tox-ansible)

tox-ansible-collection
----------------------

This plugin for tox auto-generates tox environments for running Molecule against roles within an Ansible
Collection. Optionally, you can then elect to filter the environments down to only a subset of them.
The tool is rather well integrated for the official [Molecule](https://github.com/ansible/molecule)
testing tool that integrates with [Ansible](https://github.com/ansible/ansible).

The plugin can also be used in the root of a regular role, but this is not its primary function.

More details
============

This plugin is designed to support auto-discovery of roles and their scenarios in an Ansible collection
repository. When it has done so, the plugin will then create a tox environment, if one does not already
exist, that contains two factors matching against the role and scenario names. For example, if you have
two roles named "user" and "group" and the "user" role has a scenario named "default" while the "group"
role has scenaiors named "default" and "fedora", then this will auto-configure tox environments named
['user-default', 'group-default', 'group-fedora'].

Additional configuration options exsit to expand this matrix automatically. For instance, you can have
it auto-generate version with tox factors for different versions of python (e.g.
['py27-user-default', 'py38-user-default']). Additional options can also be added for different versions
of Ansible (e.g. ['ansible27-user-default', 'ansible28-user-default'])

There are also options to filter the list of environment variables executed, after all the generation
matrix has been realized. The execution can be filtered to limit itself to only a particular role,
only a particular scenario, only scenarios that operate on a particular driver, or any combination of
those.

If an environment already exists that matches both the rolename and scenario factors, then this plugin
will not modify their configuration. Thus, if you need to customize a particular run, then you can do
so, but still take advantage of the filtering options and auto-generation of the environments for other
scenarios.

Configuration
-------------

tox.ini
=======

Any values in the `envlist` will be left in the default envlist by this plugin. So if you want to have
several envs that do things other than run `molecule ...` commands, you can configure those directly
in the tox.ini file.

To add global options to the molecule commands, add the arguments in a line list to the "[ansible]"
section key "molecule\_opts".

To test with the latest versions of Ansible 2.7, 2.8, AND 2.9, add a comma-delimited list to the
"[ansible]" section key "ansible".

Examples
--------

## Basic Example

The following Collections structure

```
.
├── galaxy.yml
├── roles
│   ├── my_role
│   │   ├── molecule
│   │   │   ├── otherscenario
│   │   │   │   └── molecule.yml
│   │   │   └── somescenario
│   │   │       └── molecule.yml
│   │   └── tasks
│   │       └── main.yml
│   └── other_role
│       ├── molecule
│       │   ├── basic
│       │   │   └── molecule.yml
│       │   ├── default
│       │   │   └── molecule.yml
│       │   └── somescenario
│       │       └── molecule.yml
│       └── tasks
│           └── main.yml
└── tox.ini
```

With the following tox.ini file:

```ini
[tox]
envlist =
```
Assuming the scenarios are named based on their folder (this plugin will read their
molecule.yml file to determine their actual name), will auto-generat the following
environments:

```bash
$ tox -l
my_role-otherscenario
lint_all
other_role-basic
other_role-default
other_role-somescenario
my_role-somescenario
python
```

Note that the "python" environment is a default behavior of Tox, if there are no
environments specified in the config file. To suppress it, specify at least one element
in the envlist entry within tox.ini

### tox.ini examples
To add arguments to every molecule invocation, add the
following segment to tox.ini. Each argument needs to be on a separate line, which allows
spaces and other special characters to be used without needing shell-style escapes:
```ini
[ansible]
molecule_opts =
    -c
    {toxinidir}/tests/molecule.yml
    --debug
```

To test with ansible versions 2.7.\*, 2.8.\*, and 2.9.\* across every role and scenario:
```ini
[ansible]
ansible = 2.7 2.8 2.9
```

Now the output will look like this:
```bash
$ tox -l
ansible28-other_role-default
ansible28-my_role-otherscenario
ansible27-my_role-otherscenario
ansible29-my_role-somescenario
ansible29-other_role-default
ansible28-lint_all
ansible29-my_role-otherscenario
ansible29-other_role-somescenario
ansible27-other_role-somescenario
ansible28-other_role-somescenario
ansible27-other_role-basic
ansible27-other_role-default
ansible29-other_role-basic
ansible27-my_role-somescenario
ansible28-my_role-somescenario
python
ansible29-lint_all
ansible28-other_role-basic
ansible27-lint_all
```

If you want multiple Python versions, you can also specify that:

```ini
[ansible]
python = 2.7 3.8
```

```bash
$ tox -l
py27-other_role-somescenario
py38-my_role-somescenario
py27-other_role-default
py38-lint_all
py38-other_role-somescenario
py27-other_role-basic
py38-other_role-basic
py38-my_role-otherscenario
py27-my_role-otherscenario
py27-lint_all
py38-other_role-default
py27-my_role-somescenario
python
```

Under the hood
--------------

The plugin will first look for a "galaxy.yml" file in the root of the execution. If it doesn't find this,
then it won't affect your run.

Next, the plugin looks inside of the "roles" directory and finds any subdirectories that contain a file
in the "tasks/main.yml" location. This is, technically, the only file required for an Ansible role.

Inside of every role folder, the plugin then looks for `molecule/*/molecule.yml` files and globs those
together.

It then generates new environments for any discovered (role, scenario) pairs that do not already exist
in the tox environment list (based on a name that includes "{role}-{scenario}")
and adds these to the default execution envlist with a dependency on
Molecule. This list will be expanded by any configured matrix axes with appropriate dependencies and
configurations made. Each one will execute the command "molecule test -s {scenario}" if it passes the
filter step.
