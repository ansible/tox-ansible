import os
import sys

from .tox_base_case import ToxBaseCase

DEFAULT_DESCRIPTION = (
    "Auto-generated environment to run: molecule test -s {scenario_name}"
)


# pylint: disable=too-many-instance-attributes
class ToxAnsibleTestCase(ToxBaseCase):
    def __init__(self, command, name_parts=None, args=None, galaxy_config=None):
        """Create the base test case.

        :param scenario: The scenario that this test case should run"""
        _galaxy_fields = ("name", "namespace", "version")
        self._cases = []
        self.command = command
        self.args = args or []
        self.galaxy_config = galaxy_config or {}
        if not galaxy_config or any(k not in galaxy_config for k in _galaxy_fields):
            print(
                "Invalid galaxy.yml content, missing one of "
                "required keys %s but we got %s"
                % (", ".join(_galaxy_fields), galaxy_config),
                file=sys.stderr,
            )
            sys.exit(102)

        self.namespace = galaxy_config["namespace"]
        self.collection = galaxy_config["name"]
        self.version = galaxy_config["version"]

        if self.command == "coverage":
            self.args = ["--venv", "--requirements"]

        self._dependencies = [
            # to build collections we want to be sure we use latest version
            # of ansible-base, as older versions like 2.9 do not support
            # ignore patterns. Install can be done with older versions.
            "ansible-base>=2.10.3",
            # ansible-test is missing to install them on py39:
            "pylint",
            "pytest",
            "pytest-xdist",
        ]
        self._name_parts = name_parts or []
        super().__init__()

    def get_name(self):
        return self.command

    @property
    def description(self):
        return f"Auto-generated environment to run: ansible-test {self.command}"

    def get_dependencies(self):
        return self._dependencies

    def get_working_dir(self):
        """Get the directory where the test should be executed.

        :return: Path where the test case should be executed from"""

        return os.path.expanduser(
            "~/.ansible/collections/ansible_collections/"
            f"{self.namespace}/{self.collection}"
        )

    def get_commands(self, options):
        if self.command != "coverage":
            commands = [
                ["ansible-test", self.command, *self.args],
            ]
        else:
            commands = [
                # avoid ansible-test failure to erase missing location...
                ["mkdir", "-p", "tests/output/coverage"],
                ["ansible-test", self.command, "erase", *self.args],
                ["ansible-test", "units", "--coverage", *self.args],
                ["ansible-test", "integration", "--coverage", *self.args],
                ["ansible-test", self.command, "report", *self.args],
            ]

        return [
            [
                "bash",
                "-c",
                (
                    f"cd {self._config.toxinidir} && "
                    "ansible-galaxy collection build -v -f --output-path dist/ && "
                    "ansible-galaxy collection install -f "
                    f"dist/{self.namespace}-{self.collection}-{self.version}.tar.gz"
                ),
            ],
            *commands,
        ]
