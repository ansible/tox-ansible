from __future__ import print_function
from tox_ansible_collection.ansible import Collection
from .util import ToxAnsibleTestCase


class TestCollection(ToxAnsibleTestCase):
    ini_contents = """
    [tox]
    envlist = py27, py34
    """
    roles = [
        ('role1', [
            ('scenario1', ''),
            ('scenario2', '')]),
        ('role2', [])
    ]

    def test_is_collection(self):
        c = Collection(self._temp_dir)
        self.assertTrue(c.is_collection())
