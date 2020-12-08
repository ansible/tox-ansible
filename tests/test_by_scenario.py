from collections import namedtuple
from unittest import TestCase
from unittest.mock import Mock

from tox_ansible.filter.by_scenario import ByScenario


class TestByScenario(TestCase):
    def test_by_scenario(self):
        Scenario = namedtuple("Scenario", "name")
        scenario = Scenario(name="affirmative")
        envlist = {"yes": Mock(tox_case=Mock(scenario=scenario)), "no": Mock(spec=[])}
        scenarios = ["affirmative", "other"]
        by_scenario = ByScenario(scenarios)
        filtered = by_scenario.filter(envlist)
        self.assertIn("yes", filtered)
        self.assertNotIn("no", filtered)
