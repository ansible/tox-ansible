from copy import copy
from unittest import TestCase

from tox_ansible.matrix import Matrix, MatrixAxisBase
from tox_ansible.matrix.axes import AnsibleAxis, PythonAxis
from tox_ansible.tox_lint_case import ToxLintCase
from tox_ansible.tox_molecule_case import ToxMoleculeCase

try:
    from unittest import mock
except ImportError:
    import mock


class TestMatrix(TestCase):
    def test_empty_matrix(self):
        cases = [ToxMoleculeCase(mock.Mock()), ToxLintCase([])]
        original = copy(cases)
        matrix = Matrix()
        after_cases = matrix.expand(cases)
        self.assertEqual(after_cases, original)

    def test_python_axis(self):
        axis = PythonAxis(["2.7"])
        case = mock.Mock()
        axis.expand([case])
        case.expand_python.assert_called_once_with("2.7")

    def test_ansible_axis(self):
        axis = AnsibleAxis(["2.10"])
        case = mock.Mock()
        axis.expand([case])
        case.expand_ansible.assert_called_once_with("2.10")

    def test_matrix_calls_axis(self):
        matrix = Matrix()
        axis = mock.Mock()
        matrix.add_axis(axis)
        cases = [mock.Mock()]
        matrix.expand(cases)
        axis.expand.assert_called_once_with(cases)

    def test_base_has_abstract_method(self):
        base = MatrixAxisBase([])
        with self.assertRaises(NotImplementedError):
            base.expand_one(0, 0)

    def test_matrix_leaves_out_bare_lint_all(self):
        matrix = Matrix()
        matrix.add_axis(PythonAxis(["2.7", "3.8"]))
        cases = [ToxLintCase([])]
        expanded = matrix.expand(cases)
        self.assertEqual(2, len(expanded))

    def test_matrix_both_axes(self):
        matrix = Matrix()
        matrix.add_axis(PythonAxis(["2.7"]))
        matrix.add_axis(AnsibleAxis(["2.8"]))
        case = mock.Mock()
        case.expand_python.return_value = case
        case.expand_ansible.return_value = case
        matrix.expand([case])
        self.assertEqual(2, len(matrix.axes))
        case.expand_python.assert_called_once_with("2.7")
        case.expand_ansible.assert_called_once_with("2.8")
