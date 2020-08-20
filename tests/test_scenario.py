from unittest import TestCase

from testfixtures import TempDirectory

from tox_ansible.ansible.scenario import Scenario


class TestScenarioDefaultName(TestCase):
    scenarios = [
        {"dir": "default", "file": b"driver:\n  name: openstack"},
        {"dir": "other", "file": b"scenario:\n  name: surprise"},
    ]

    def test_scenario_name_introspect(self):
        s = Scenario(self.d.getpath("default"))
        self.assertEqual(s.name, "default")
        self.assertEqual(str(s), "default")

    def test_scenario_driver_correct(self):
        s = Scenario(self.d.getpath("default"))
        self.assertEqual(s.driver, "openstack")

    def test_scenario_name_explicit(self):
        s = Scenario(self.d.getpath("other"))
        self.assertEqual(s.name, "surprise")
        self.assertEqual(str(s), "surprise")

    @classmethod
    def setUp(cls):
        cls.d = TempDirectory()
        for scenario in cls.scenarios:
            cls.d.write((scenario["dir"], "molecule.yml"), scenario["file"])

    @classmethod
    def tearDown(cls):
        cls.d.cleanup()
