from unittest import TestCase

from tox_ansible.tox_helper import Tox


class TestTox(TestCase):
    def test_tox_helper_basic_works(self):
        Tox({})
