DRIVER_DEPENDENCIES = {
    "docker": ["docker"],
    "openstack": ["openstacksdk"]
}


class ToxCaseBase(object):
    """Represents a generalized Test Case for an Ansible structure."""
    def __init__(self, role, scenario, name_parts=[]):
        """Create the base test case.

        :param role: The role that this test case lives in
        :param scenario: The scenario that this test case should run"""
        self.role = role
        self.scenario = scenario
        self._dependencies = ["molecule"]
        self._name_parts = name_parts + [role.name, scenario.name]
        # Some of the matrix fields we might care about later. They should be
        # copied in the "expand" method below, if you add any more to this
        # area in the future
        self.python = None
        self.ansible = None

    def get_commands(self, options):
        """Get the commands that this scenario should execute.

        :param options: The options object for this plugin
        :return: the default commands to run to execute this test case, if the
        user does not configure them explicitly"""
        molecule = ['molecule']
        molecule.extend(options.get_global_opts())
        molecule.extend(['test', '-s', self.scenario.name])
        return [molecule]

    def get_working_dir(self):
        """Get the directory where the test should be executed.

        :return: Path where the test case should be executed from"""
        return self.role.directory

    def get_dependencies(self):
        """The dependencies for this particular test case.

        :return: A list of the pip dependencies for this test case"""
        dependencies = self._dependencies
        if self.ansible is not None:
            dependencies.append("ansible=={}.*".format(self.ansible))
        else:
            dependencies.append("ansible")
        # Drivers can have their own dependencies
        if self.scenario.driver is not None \
           and self.scenario.driver in DRIVER_DEPENDENCIES.keys():
            dependencies.extend(DRIVER_DEPENDENCIES[self.scenario.driver])
        return dependencies

    def get_name(self):
        """The name of this test case. The name is made up of various factors
        from the tox world, joined together by hyphens. Some of them are based
        on the role and scenario names. Others are based on factors such as
        the python version or ansible version.

        :return: The tox-friendly name of this test scenario"""
        return '-'.join(self._name_parts)

    def get_basepython(self):
        """The python version that should be used to execute this, if a
        particular one is requested. If not, then leave it up to the system
        default. The name of the executable is arrived at simply by appending
        the configured python Version to the word "python". So if you have
        specified python as "3.9" then this method will yield "python3.9"

        :return: Python executable to execute against, if any, else None"""
        if self.python is None:
            return None
        return "python" + self.python

    def _expand(self, name):
        """Create a copy of this role, expanded with the additional name field
        and other such niceties.

        :param name: An additional field to be added to the name factors
        :return: A copy of this object with the additional name factor"""
        copy = ToxCaseBase(self.role, self.scenario, [name])
        copy.python = self.python
        copy.ansible = self.ansible
        return copy

    def expand_python(self, version):
        """Create a copy of this Test Case, but add a factor to the name to
        reflect a particular version of Python

        :param version: String representation of Python version (e.g. '2.7')
        :return: A copy of this test case expanded to specify the given version
        of python"""
        copy = self._expand('py' + version.replace('.', ''))
        copy.python = version

        return copy

    def expand_ansible(self, version):
        """Create a copy of this Test CAse, but add a factor to the name to
        reflect a particular version of Ansible

        :param version: String representation of Ansible version (e.g. 2.8)
        :return: A copy of this test case expanded to specify the given version
        of Ansible"""
        copy = self._expand('ansible' + version.replace('.', ''))
        copy.ansible = version

        return copy
