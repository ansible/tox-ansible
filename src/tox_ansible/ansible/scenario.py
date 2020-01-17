from os import path
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class Scenario(object):
    """Knows about scenarios."""
    def __init__(self, directory):
        self.directory = directory
        self.scenario_file = path.join(self.directory, "molecule.yml")
        self._config = self._get_config()
        self.name = self._get_name()
        self.driver = self._get_driver()

    def __str__(self):
        return "{}".format(self.name)

    def _get_config(self):
        """Reads the molecule.yml file. Adds it to the self._config
        field."""
        with open(self.scenario_file, "r") as c:
            return load(c.read(), Loader=Loader)

    def _get_name(self):
        """Determines the name of the scenario, which is not always
        self-evident. By default it is the name of the directory that the
        scenario file lives in, but if there is an entry in the molecule.yml
        definition, it can override that value."""
        if "scenario" in self._config and \
           "name" in self._config["scenario"]:
            return self._config["scenario"]["name"]
        return path.basename(self.directory)

    def _get_driver(self):
        """Reads the driver for this scenario, if one is defined.

        :return: Driver name defined in molecule.yml or None"""
        if "driver" in self._config and \
           "name" in self._config["driver"]:
            return self._config["driver"]["name"]
        return None
