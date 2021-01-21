[![CI/CD Builds](https://github.com/ansible-community/tox-ansible/workflows/tox/badge.svg)](https://github.com/greg-hellings/tox-ansible/actions?query=workflow%3A%22CI%2FCD+Builds%22)
[![codecov](https://codecov.io/gh/ansible-community/tox-ansible/branch/master/graph/badge.svg)](https://codecov.io/gh/greg-hellings/tox-ansible)
[![PyPI version](https://badge.fury.io/py/tox-ansible.svg)](https://badge.fury.io/py/tox-ansible)

tox-ansible-collection
======================

This plugin for tox auto-generates tox environments for running Ansible
quality assurance tools like ansible-test or molecule. Optionally, you can
then elect to filter the environments down to only a subset of them.
The tool is rather tightly integrated for the official [Molecule](https://github.com/ansible/molecule)
testing tool that integrates with [Ansible](https://github.com/ansible/ansible).

ansible-test
------------

As you probably already know, ansible-test cannot be just run on a cloned
repository because it requires the current collection to be already installed
and the current directory is already the installed location.

This plugin saves you this trouble by allowing you the freedom to run
these commands tranparently. For example you can run `tox -e sanity` which
will install the collection, change current directory and execute
`ansible-test sanity`. You can even add posargs that endup being passed to
the executed command, like `tox -e sanity -- --help`.

To see all dynamically generated environments, just run `tox -va`, the
description field will tell you what they do:

```shell
$ tox -va
default environments:
sanity       -> Auto-generated environment to run: ansible-test sanity
```

Only those enviroments that are detected will be listed. At least sanity will
always be visible as it does not require adding new files.

More details
------------

This plugin is designed to support auto-discovery of Molecule scenarios. When it has done so, the plugin
will then create a tox environment, if one does not already
exist, that contains factors matching against the scenario path. For example, if you have scenarios
that live at `molecule/scenario`, `roles/somerole/molecule/default`, and `roles/otherrole/molecule/default`,
then tox environments will be named `["scenario", "roles-somerole-default", "roles-otherrole-default"]`.

Additional configuration options exist to expand this matrix automatically. For instance, you can have
it auto-generate version with tox factors for different versions of python (e.g.
['py27-user-default', 'py38-user-default']). Additional options can also be added for different versions
of Ansible (e.g. ['ansible27-user-default', 'ansible28-user-default'])

There are also options to filter the list of environments executed. The execution can be filtered to
limit itself to only scenarios with a particular name, to only certain Molecule drivers, or a combination
of the two options. Of course, tox can still be used to execute only one environment by passing the
name directly via e.g. `tox -e roles-myrole-scenario`.

If an environment already exists that matches the generated environment name, then this plugin
will not settings specified directly in the tox.ini for that environment. Thus, if you need to customize
a particular run, then you can do so, but still take advantage of the filtering options and
auto-generation of the environments for other scenarios and options.

Configuration
=============

tox.ini
-------

Any values in the `envlist` will be left in the default envlist by this plugin. So if you want to have
several envs that do things other than run `molecule ...` commands, you can configure those directly
in the tox.ini file.

To add global options to the molecule commands, add the arguments in a line list to the "[ansible]"
section key "molecule\_opts".

To test with the latest versions of Ansible 2.7, 2.8, AND 2.9, add a comma-delimited list to the
"[ansible]" section key "ansible".

requirements.txt
----------------

If a particular scenario requires a select set of Python packages to be installed in the virtualenv with
molecule and the like, you can add a "requirements.txt" file to the molecule scenario directory, and that
will be appended to the list of built-in scenario requirements.

Examples
========

## Basic Example

The following Collections structure

<pre><font color="#3465A4"><b>.</b></font>
├── galaxy.yml
├── <font color="#3465A4"><b>molecule</b></font>
│   ├── <font color="#3465A4"><b>one</b></font>
│   │   └── molecule.yml
│   └── <font color="#3465A4"><b>two</b></font>
│       └── molecule.yml
├── <font color="#3465A4"><b>roles</b></font>
│   ├── <font color="#3465A4"><b>my_role</b></font>
│   │   └── <font color="#3465A4"><b>molecule</b></font>
│   │       ├── <font color="#3465A4"><b>otherscenario</b></font>
│   │       │   └── molecule.yml
│   │       └── <font color="#3465A4"><b>somescenario</b></font>
│   │           └── molecule.yml
│   └── <font color="#3465A4"><b>other_role</b></font>
│       └── <font color="#3465A4"><b>molecule</b></font>
│           ├── <font color="#3465A4"><b>basic</b></font>
│           │   └── molecule.yml
│           ├── <font color="#3465A4"><b>default</b></font>
│           │   └── molecule.yml
│           └── <font color="#3465A4"><b>somescenario</b></font>
│               └── molecule.yml
└── tox.ini
</pre>

With the following tox.ini file:

```ini
[tox]
envlist =
```
Tox-ansible will auto-generate the following environments:

```bash
$ tox -l
lint_all
one
python
roles-my_role-otherscenario
roles-my_role-somescenario
roles-other_role-basic
roles-other_role-default
roles-other_role-somescenario
two
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

Sometimes there are paths you will want to ignore running tests in. Particularly if you
install other roles or collections underneath of your source tree. You can ignore these paths
with the following tox.ini bit:
```ini
[ansible]
ignore_path =
    dist
    generated_paths_to_ignore
```
This field is very simple, and should list folder names, anywhere in the tree, to ignore.
It does not do specialized glob matching or sub-path matching at this time. Anything living under
any folder whose name appears in this list will be ignored.

To test with ansible versions 2.7.\*, 2.8.\*, and 2.9.\* across every role and scenario:
```ini
[ansible]
ansible = 2.7 2.8 2.9
```

Now the output will look like this:
```bash
$ tox -l
ansible27-lint_all
ansible27-one
ansible27-roles-my_role-otherscenario
ansible27-roles-my_role-somescenario
ansible27-roles-other_role-basic
ansible27-roles-other_role-default
ansible27-roles-other_role-somescenario
ansible27-two
ansible28-lint_all
ansible28-one
ansible28-roles-my_role-otherscenario
ansible28-roles-my_role-somescenario
ansible28-roles-other_role-basic
ansible28-roles-other_role-default
ansible28-roles-other_role-somescenario
ansible28-two
ansible29-lint_all
ansible29-one
ansible29-roles-my_role-otherscenario
ansible29-roles-my_role-somescenario
ansible29-roles-other_role-basic
ansible29-roles-other_role-default
ansible29-roles-other_role-somescenario
ansible29-two
python
```

If you want multiple Python versions, you can also specify that:

```ini
[ansible]
python = 2.7 3.8
```

```bash
$ tox -l
py27-lint_all
py27-one
py27-roles-my_role-otherscenario
py27-roles-my_role-somescenario
py27-roles-other_role-basic
py27-roles-other_role-default
py27-roles-other_role-somescenario
py27-two
py38-lint_all
py38-one
py38-roles-my_role-otherscenario
py38-roles-my_role-somescenario
py38-roles-other_role-basic
py38-roles-other_role-default
py38-roles-other_role-somescenario
py38-two
python
```

Under the hood
--------------

The plugin will glob the current directory and look for any files matching the glob pattern
`molecule/*/molecule.yml` and make the assumption that these represent Molecule scenarios.

It then generates new environments for any discovered scenarios that do not already exist
in the tox environment list. These names will include the full path to the scenario folder
with the exception of the `molecule` directory name. So a scenario rooted at `roles/foo/molecule/bar`
will be named `roles-foo-bar`. Similarly one that lives at `molecule/bar` will be named just `bar`.

Generated environments are added to the default execution envlist with a dependency on
Molecule. This list will be expanded by any configured matrix axes with appropriate dependencies and
configurations made. Each one will execute the command "molecule test -s {scenario}" if it passes the
filter step.

Environments are configured with the following values, by default, unless they are explicitly specified
in the tox.ini file:
* dependencies
* commands
* working directory
* basepython (if specified in the `[ansible]` expand matrix)
By use of the defined factors in a name, some values can be given in the general tox environment config
section, but the above values will be explicitly specified. So do not rely on setting those values
through the use of factor expansion in a generic section.
