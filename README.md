# tox-ansible-collection
This plugin for tox auto-generates tox environments for running Molecule against roles within an Ansible
Collection. Optionally, you can then elect to filter the environments down to only a subset of them.
The tool is rather well integrated for the official [Molecule](https://github.com/ansible/molecule)
testing tool that integrates with [Ansible](https://github.com/ansible/ansible).

## More details
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

## Under the hood
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
