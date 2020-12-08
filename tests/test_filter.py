# For rennamed/moved assert(Count|Item)Equal
from collections import namedtuple
from unittest import TestCase
from unittest.mock import Mock

from tox_ansible.filter import Filter


class TestFilter(TestCase):
    def test_filter(self):
        # Mock struggles with an attribute named "name"
        Scenario = namedtuple("Scenario", "name")
        opts = Mock(scenario=["default"], driver=[])
        default = Scenario(name="default")
        other = Scenario(name="other")
        envlist = {
            "one-default": Mock(tox_case=Mock(scenario=default)),
            "one-other": Mock(tox_case=Mock(scenario=other)),
            "two-default": Mock(tox_case=Mock(scenario=default)),
            "three-default": Mock(tox_case=Mock(scenario=default)),
        }
        expected = ["one-default", "two-default", "three-default"]

        f = Filter(opts)
        results = f.filter(envlist)
        self.assertCountEqual(results.keys(), expected)
