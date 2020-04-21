from os import path
from .collection import Collection
from .role import Role
from ..tox_lint_case import ToxLintCase


class Ansible(object):
    """A generalized class that handles interactions between the plugin and
    Ansible structures. It will determine if we are in an Ansible folder
    structure, what kind, and fetch the relevant information back from the
    filesystem for the caller."""
    def __init__(self, base=""):
        """Create an Ansible object to introspect on whether the given
        directory is an Ansible structure or not. Currently aware of a
        collection and a role.

        :param base: Path to the folder. Defaluts to being relative to
        os.path.curdir, but can be absolute"""
        self.directory = path.abspath(path.join(path.curdir, base))
        self.collection = Collection(self.directory)
        self.role = Role(self.directory)

    def is_ansible(self):
        """Determine if the specified directory is an Ansible structure or not

        :return: True if this is an Ansible structure. False, otherwise."""
        return self.collection.is_collection() or self.role.is_role

    def get_tox_cases(self):
        """Returns a list of TestCase objects that can be queried to create
        the structure of a test environment.

        :return: List of TestCase objects"""
        tox_cases = []
        if self.collection.is_collection():
            tox_cases.extend(self.collection.get_tox_cases())
        elif self.role.is_role:
            tox_cases.extend(self.role.tox_cases)
        tox_cases.append(ToxLintCase(tox_cases))
        return tox_cases
