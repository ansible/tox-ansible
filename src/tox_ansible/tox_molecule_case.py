import os
from functools import lru_cache
from string import Template
from typing import Iterable, List, Optional

from .options import INI_SCENARIO_FORMAT_DEFAULT
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
    "vagrant": ["molecule-vagrant", "python-vagrant"],
}


DEFAULT_DESCRIPTION = "Auto-generated for: {cwd_cmd}molecule test -s {scenario_name}"


class ToxMoleculeCase(ToxBaseCase):
    """Represents a generalized Test Case for an Ansible structure."""

    def __init__(self, scenario, name_parts=None, drivers: Optional[List[str]] = None):
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
        if drivers:
            self._drivers = drivers
        else:
            self._drivers = []
        super().__init__()  # type: ignore

    def get_commands(self, options):
        """Get the commands that this scenario should execute.

        :param options: The options object for this plugin
        :return: the default commands to run to execute this test case, if the
        user does not configure them explicitly"""
        molecule = ["molecule"]
        molecule.extend(options.get_global_opts())

        if options.molecule_config_files:
            for config_file in options.molecule_config_files:
                molecule.extend(["-c", config_file])

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
        for driver in self._drivers:
            if driver in DRIVER_DEPENDENCIES.keys():
                dependencies.extend(DRIVER_DEPENDENCIES[driver])
            elif driver != "delegated":
                dependencies.append("molecule-" + driver)
        # Scenarios can specify a requirements.txt
        if self.scenario.requirements is not None:
            dependencies.append("-r" + self.scenario.requirements)
        return dependencies

    @lru_cache()
    def get_name(self, fmt=""):
        """The name of this test case. The name is made up of various factors
        from the tox world, joined together by hyphens. Some of them are based
        on the role and scenario names. Others are based on factors such as
        the python version or ansible version.

        :return: The tox-friendly name of this test scenario
        """
        scenario_path = self.scenario.directory.split(os.path.sep)
        parts = list(filter(lambda x: x != "molecule" and "." not in x, scenario_path))

        name = parts[-1]

        parent = ""
        path = ""
        if len(parts) >= 3:
            path = "-".join(parts[:-2])
            parent = parts[-2]
        elif len(parts) == 2:
            parent = parts[-2]

        nondefault_name = name if (name != "default" or not parent) else ""

        if not fmt:
            fmt = INI_SCENARIO_FORMAT_DEFAULT

        formatted_name = Template(fmt).safe_substitute(
            path=path, parent=parent, name=name, nondefault_name=nondefault_name
        )
        formatted_name = "-".join(self._name_parts + [formatted_name])

        # remove any leading or trailing dashes
        formatted_name = formatted_name.strip("-")
        # remove double dashes
        while "--" in formatted_name:
            formatted_name = formatted_name.replace("--", "-")

        return formatted_name

    @property
    def description(self):
        cwd_cmd = f"cd {self.scenario.run_dir} && " if self.scenario.run_dir else ""
        return DEFAULT_DESCRIPTION.format(
            scenario_name=self.scenario.name, cwd_cmd=cwd_cmd
        )
