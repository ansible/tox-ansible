from .tox_base_case import ToxBaseCase
DRIVER_DEPENDENCIES = {
    "docker": ["docker"],
    "openstack": ["openstacksdk", "molecule-openstack", "os-client-config"],
    "ec2": ["molecule-ec2", "boto", "boto3"]
}


class ToxTestCase(ToxBaseCase):
    """Represents a generalized Test Case for an Ansible structure."""
    def __init__(self, role, scenario, name_parts=[]):
        """Create the base test case.

        :param role: The role that this test case lives in
        :param scenario: The scenario that this test case should run"""
        self.role = role
        self.scenario = scenario
        self._dependencies = ["molecule", "ansible-lint", "yamllint", "flake8",
                              "pytest", "testinfra"]
        self._name_parts = name_parts
        super(ToxTestCase, self).__init__()

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
        return '-'.join(self._name_parts +
                        [self.role.name, self.scenario.name])
