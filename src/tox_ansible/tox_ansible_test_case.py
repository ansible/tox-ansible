import os

from .tox_base_case import ToxBaseCase

DEFAULT_DESCRIPTION = "Auto-generated for: molecule test -s {scenario_name}"


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
            raise RuntimeError(
                "Invalid galaxy.yml content, missing one of "
                f"required keys {', '.join(_galaxy_fields)} but we got {galaxy_config}"
            )

        self.namespace = galaxy_config["namespace"]
        self.collection = galaxy_config["name"]
        self.version = galaxy_config["version"]

        if self.command == "coverage":
            self.args = ["--venv", "--requirements"]

        self._dependencies = [
            # to build collections we want to be sure we use latest version
            # of ansible core, as older versions like 2.9 do not support
            # ignore patterns. Install can be done with older versions.
            "ansible-core>=2.11.3",
        ]
        self._name_parts = name_parts or []
        super().__init__()

    def get_name(self, fmt=""):
        return self.command

    @property
    def description(self):
        return f"Auto-generated for: ansible-test {self.command} {' '.join(self.args)}"

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def working_dir(self):
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
