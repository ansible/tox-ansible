from os import path, listdir
from .role import Role


class Collection(object):
    """Knows things about an Ansible collection. Can help traversing the folder
    structure and discovering paths within it."""
    def __init__(self, base=""):
        """Initializes the object with where the directory lives

        :param base: Path to the directory where a collection might live"""
        self.directory = path.abspath(path.join(path.curdir, base))
        self.roles_dir = path.join(self.directory, "roles")
        self.galaxy_file = path.join(self.directory, "galaxy.yml")

    def is_collection(self):
        """Tells you if this folder is an Ansible collection or not."""
        return path.isfile(self.galaxy_file)

    def get_roles(self):
        """Retrieve every role that is contained inside of this collection

        :return: List of Role objects representing roles"""
        # No roles to be found
        if not path.isdir(self.roles_dir):
            return []

        # Not all folders in the "roles" directory are necessarily roles
        roles = [Role(path.join(self.directory, "roles", d))
                 for d in listdir(self.roles_dir)]
        roles = list(filter(lambda r: r.is_role(), roles))

        return roles

    def get_tox_cases(self):
        """Finds any potential test cases in the collection and returns any
        test cases that could be configured.

        :return: List of test case objects to be turned into test env
        configs"""
        tox_cases = []
        for role in self.get_roles():
            tox_cases.extend(role.get_tox_cases())
        return tox_cases
