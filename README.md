[![CI/CD Builds](https://github.com/ansible-community/tox-ansible/workflows/tox/badge.svg)](https://github.com/ansible-community/tox-ansible/actions)
[![codecov](https://codecov.io/gh/ansible-community/tox-ansible/branch/master/graph/badge.svg)](https://codecov.io/gh/ansible-community/tox-ansible)
[![PyPI version](https://badge.fury.io/py/tox-ansible.svg)](https://badge.fury.io/py/tox-ansible)

tox-ansible
===========

This plugin for tox auto-generates tox environments for running
quality assurance tools like ansible-test or molecule. Optionally, you can
decide to filter the environments down to only a subset of them.
The tool is rather tightly integrated for the official [Molecule](https://github.com/ansible/molecule)
testing tool that integrates with [Ansible](https://github.com/ansible/ansible).

ansible-test
------------

This plugin saves you this trouble by allowing you the freedom to run
these commands tranparently. For example you can run `tox -e sanity` which
will install the collection, change current directory and execute
`ansible-test sanity --python X.Y`. You can even add posargs that endup being
passed to the executed command, like `tox -e sanity -- --help`.

By default tox-ansible will also limit execution of ansible-test to the
current python version used by tox.

```shell
$ tox -va
default environments:
sanity       -> Auto-generated for: ansible-test sanity
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
will not override settings specified directly in the tox.ini for that environment. Thus, if you need to customize
a particular run, then you can do so, but still take advantage of the filtering options and
auto-generation of the environments for other scenarios and options. Dependencies defined in the standard
way in tox.ini for any name collision environments will be augmented with the ones needed for
running Molecule and lint.

Configuration
=============

tox.ini
-------

Any values in the `envlist` will be left in the default envlist by this plugin. So if you want to have
several envs that do things other than run `molecule ...` commands, you can configure those directly
in the tox.ini file.

To add global options to the molecule commands, add the arguments in a line list to the "[ansible]"
section key "molecule\_opts".

To test each scenario with specified versions of either Ansible or Python, you can add version
numbers to the keys `ansible` and `python` under the `[ansible]` section of the ini. These versions
take the same format as the `envlist` version familiar to Python users. So, if you want to test on
Ansible 2.9, 2.10, and 3.0 as well as with Python 2.7 and 3.8 then you can add this snippet (values can
be separated by a mix of commas and newlines):

```ini
[ansible]
ansible = 2.{9,10},3.0
python = 2.7,3.8
# To change how tox env name is build for scanrios, you can use vars like:
# $path - paths under which molecule file is hosted (can be empty string)
# $parent - only the parent folder under which is hosted (can be empty string)
# $name - this is the name of the scenario (folder under molecule/)
# $nondefault_name - same as name but when scenario is named 'default' it becomes empty string
#
# scenario_format = $path-$role-$name

```

If you find the default environment names generated for scenarios too long,
you can configure `scenario_format = $parent-$nondefault_name` which should
produce very short names, regardless if your scenarios are in repository root
or under the roles. That works nicely as long you do not have duplicate
scenario names.

To pass a configuration file to "[ansible-lint](https://github.com/ansible-community/ansible-lint)",
add the option "ansible\_lint\_config". Similarly to pass a config file option to
"[yamllint](https://github.com/adrienverge/yamllint)", set the option "yamllint\_config" in
the "[ansible]" section. Flake8 can be configured per its normal segment in your tox.ini file. All
three of these commands are run as part of the "lint\_all" environment that this plugin creates.

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
    --debug
```

If you use a global molecule configuration file at the project level
(`<project_name>/.config/molecule/config.yml`), it will be detected
automatically and will be the reference in order to determine the default driver
name used for your molecule scenarios.

If you want pass one or multiple base configuration file(s) to
"[molecule](https://github.com/ansible-community/molecule)", add the option
"molecule\_config\_files" to the Ansible section and list them as follows.
```ini
[ansible]
molecule_opts =
    --debug
molecule_config_files =
    {toxinidir}/tests/molecule_one.yml
    {toxinidir}/tests/molecule_two.yml
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
ansible = 2.{7,8,9}
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
python = 2.7,3.8
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
