"""A collection of classes that know how to traverse an Ansible Galaxy
folder structure"""
from __future__ import print_function
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from os import path, listdir, walk


class Collection(object):
    """Knows things about an Ansible collection. Can help traversing the folder
    structure and discovering paths within it."""
    def __init__(self, base=""):
        """'base' is the path to the folder. Defaults to CWD"""
        self.base = path.abspath(path.join(path.curdir, base))
        self.roles_dir = path.join(self.base, "roles")
        self.galaxy_file = path.join(self.base, "galaxy.yml")

    def is_collection(self):
        """Tells you if this folder is an Ansible collection or not."""
        return path.isfile(self.galaxy_file)

    def get_roles(self):
        """Return an array of Role objects for every role discovered in this
        collection."""
        # No roles to be found
        if not path.isdir(self.roles_dir):
            return []

        roles = [Role(self, d) for d in listdir(self.roles_dir)]
        roles = [r for r in roles if r.is_role()]
        print(len(roles))

        return roles


class Role(object):
    """Knows things about an Ansible role and how it is stored."""
    def __init__(self, collection, folder):
        """'base' is the path to this role."""
        self.collection = collection
        self.folder = folder
        self.path = path.join(self.collection.roles_dir, self.folder)

    def is_role(self):
        """Tells you if this folder is actually a role."""
        return path.isdir(self.path) and \
            path.isfile(path.join(self.path, "tasks", "main.yml"))

    def get_scenarios(self):
        scenarios = []
        for folder, dirs, files in walk(self.path):
            if 'molecule.yml' in files:
                scenarios.append(Scenario(self, path.join(self.path, folder)))
        return scenarios


class Scenario(object):
    """Knows about scenarios."""
    def __init__(self, role, scenario_dir):
        self.role = role
        self.scenario_dir = scenario_dir
        self.scenario_file = path.join(self.role.path,
                                       scenario_dir,
                                       "molecule.yml")
        self.name = self._get_name()

    def _get_name(self):
        """Determines the name of the scenario, which is not always
        self-evident"""
        name = path.basename(self.scenario_dir)
        print(self.scenario_file)
        with open(self.scenario_file, 'r') as c:
            self.config = load(c.read(), Loader=Loader)
        if self.config and \
           'scenario' in self.config and \
           'name' in self.config['scenario']:
            name = self.config['scenario']['name']
        return name

    def get_environment(self):
        pass
