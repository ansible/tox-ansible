from os import path

from tox_ansible._yaml import load_yaml


class Scenario(object):
    """Knows about scenarios."""

    def __init__(self, directory):
        self.directory = directory
        self.scenario_file = path.join(self.directory, "molecule.yml")

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

        :return: Driver name defined in molecule.yml or None"""
        if self.config and "driver" in self.config and "name" in self.config["driver"]:
            return self.config["driver"]["name"]
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
