from unittest import TestCase

from tox_ansible.tox_lint_case import ToxLintCase

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class TestToxLintCase(TestCase):
    def test_names_are_correct(self):
        tc = ToxLintCase([])
        deps = set(["molecule", "ansible-lint", "flake8", "yamllint"])
        self.assertEqual(tc.get_name(), "lint_all")
        self.assertEqual(tc.get_working_dir(), "{toxinidir}")
        self.assertEqual(tc.get_dependencies(), deps)

    def test_expand_python(self):
        tc = ToxLintCase([])
        out = tc.expand_python("2.7")
        self.assertEqual(out.get_name(), "py27-lint_all")

    def test_expand_ansible(self):
        tc = ToxLintCase([])
        out = tc.expand_ansible("2.10")
        self.assertEqual(out.get_name(), "ansible210-lint_all")

    def test_commands_are_correct(self):
        options = Mock()
        options.get_global_opts.return_value = []
        case1 = Mock(role=Mock(directory="/foo"), scenario=Mock(name="s1"))
        case2 = Mock(role=Mock(directory="/bar"), scenario=Mock(name="s1"))
        case3 = Mock(role=Mock(directory="/bar"), scenario=Mock(name="s2"))
        bummer = ToxLintCase([])
        tc = ToxLintCase([case1, case2, case3, bummer])
        cmds = tc.get_commands(options)
        expected = [
            [
                "bash",
                "-c",
                "cd {} && molecule  lint -s {}".format(
                    case1.role.directory, case1.scenario.name
                ),
            ],
            [
                "bash",
                "-c",
                "cd {} && molecule  lint -s {}".format(
                    case2.role.directory, case2.scenario.name
                ),
            ],
            [
                "bash",
                "-c",
                "cd {} && molecule  lint -s {}".format(
                    case3.role.directory, case3.scenario.name
                ),
            ],
        ]
        self.assertEqual(expected, cmds)
