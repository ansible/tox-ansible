from os import path

from tox_ansible._yaml import load_yaml


class Scenario(object):
    """Knows about scenarios."""

    def __init__(self, directory, global_config=None):
        self.directory = directory
        self.scenario_file = path.join(self.directory, "molecule.yml")
        self.global_config = global_config

    def __str__(self):
        return "{}".format(self.name)

    @property
    def run_dir(self):
        """The directory this scenario should be run from"""
        return path.dirname(path.dirname(self.directory))

    @property
    def config(self):
        """Reads the molecule.yml file. Adds it to the self.config
        field."""
        return load_yaml(self.scenario_file)

    @property
    def name(self):
        """Determines the name of the scenario."""
        return path.basename(self.directory)

    @property
    def driver(self):
        """Reads the driver for this scenario, if one is defined.
        If there is a driver found in the scenario configuration and if there
        is a global configuration, the driver coming from the scenario
        will be returned. Otherwise, the global driver.

        :return: Driver name defined in molecule.yml or None
        :raise: A RuntimeError if the driver name is present in multiple
                molecule base configuration files given as options in the
                tox.ini file. Or if no driver configuration has been found.
        """
        if self.config and "driver" in self.config and "name" in self.config["driver"]:
            return self.config["driver"]["name"]

        if self.global_config:
            drivers_found_number = len(
                [i for i, d in enumerate(self.global_config) if "driver" in d]
            )
            if drivers_found_number == 0:
                raise RuntimeError("No driver configuration found.")

            if drivers_found_number == 1:
                return self.global_config[-1].get("driver")["name"]

            if drivers_found_number > 1:
                raise RuntimeError(
                    "Driver configuration is present in multiple "
                    "molecule base configuration files."
                )

        return None

    @property
    def requirements(self):
        """Checks for the existence of a requirements.txt file in the current
        scenario directory, so that a scenario can include custom requirements
        without needing to specify them in tox.ini if it doesn't want to.

        :return: path to requirements.txt, if it exists. None otherwise"""
        requirements_txt = path.join(self.directory, "requirements.txt")
        if path.isfile(requirements_txt):
            return requirements_txt
        return None
