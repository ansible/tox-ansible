import os
from typing import Iterable

from .tox_base_case import ToxBaseCase
from .tox_helper import Tox

DRIVER_DEPENDENCIES = {
    # Because of the close relationship of these two, it's not uncommon to run one
    # scenario using the other driver if your system does not support one or the
    # other. So we'll choose to install only one of them
    "containers": ["molecule-containers"],
    "docker": ["molecule-docker", "molecule-podman"],
    "podman": ["molecule-podman", "molecule-docker"],
    "openstack": ["molecule-openstack", "openstacksdk", "os-client-config"],
    "ec2": ["molecule-ec2", "boto", "boto3"],
    "vagrant": ["molecule-vagrant"],
}


DEFAULT_DESCRIPTION = (
    "Auto-generated environment to run: molecule test -s {scenario_name}"
)


class ToxMoleculeCase(ToxBaseCase):
    """Represents a generalized Test Case for an Ansible structure."""

    def __init__(self, scenario, name_parts=None):
        """Create the base test case.

        :param scenario: The scenario that this test case should run"""
        self.scenario = scenario
        self._dependencies = [
            "molecule",
            "ansible-lint",
            "yamllint",
            "flake8",
            "pytest",
            "testinfra",
        ]
        self._name_parts = name_parts or []
        super().__init__()

    def get_commands(self, options):
        """Get the commands that this scenario should execute.

        :param options: The options object for this plugin
        :return: the default commands to run to execute this test case, if the
        user does not configure them explicitly"""
        molecule = ["molecule"]
        molecule.extend(options.get_global_opts())
        molecule.extend(["test", "-s", self.scenario.name])
        tox = Tox()
        molecule.extend(tox.posargs)
        return [molecule]

    def get_working_dir(self):
        """Get the directory where the test should be executed.

        :return: Path where the test case should be executed from"""
        return os.path.dirname(os.path.dirname(self.scenario.directory))

    def get_dependencies(self) -> Iterable:
        """The dependencies for this particular test case.

        :return: A list of the pip dependencies for this test case"""
        dependencies = self._dependencies
        if self.ansible is not None:
            dependencies.append("ansible=={}.*".format(self.ansible))
        else:
            dependencies.append("ansible")
        # Drivers can have their own dependencies but we preinstall of known
        # ones as the current venv may be shared among multiple scenarios
        # If this proves to become heavy, we should look into finding a way
        # to optimize it by allowing user to enable a slim mode.
        for _, deps in DRIVER_DEPENDENCIES.items():
            for dep in deps:
                if dep not in dependencies:
                    dependencies.append(dep)
        # Scenarios can specify a requirements.txt
        if self.scenario.requirements is not None:
            dependencies.append("-r" + self.scenario.requirements)
        return dependencies

    def get_name(self):
        """The name of this test case. The name is made up of various factors
        from the tox world, joined together by hyphens. Some of them are based
        on the role and scenario names. Others are based on factors such as
        the python version or ansible version.

        :return: The tox-friendly name of this test scenario"""
        scenario_path = self.scenario.directory.split(os.path.sep)
        name_path = list(
            filter(lambda x: x != "molecule" and "." not in x, scenario_path)
        )
        return "-".join(self._name_parts + name_path)

    @property
    def description(self):
        return DEFAULT_DESCRIPTION.format(scenario_name=self.scenario.name)
