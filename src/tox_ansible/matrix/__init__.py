class Matrix(object):
    def __init__(self):
        self.axes = []

    def add_axis(self, axis):
        """Add an extension axis to this matrix. Axes can be found in the
        axes.py file and are subclasses of the MatrixAxisBase class.

        :param axis: An expansion axis to add to this matrix."""
        self.axes.append(axis)

    def expand(self, cases):
        for axis in self.axes:
            cases = axis.expand(cases)
        return cases


class MatrixAxisBase(object):
    """Expands a list of a particular test case by creating copies with the
    appropriately named factors and replacing the base case.

    ***THIS IS AN ABSTRACT BASE CLASS***"""

    def __init__(self, versions):
        """Initialize a matrix to expand a particular version.

        :param versions: A list of versions to expand this matrix"""
        self.versions = versions

    def expand(self, tox_cases):
        """Expand the list of test cases by multiplying it by this matrix for
        the configured field.

        :param tox_cases: An iterable of the currently existing test cases
        :return: A list of the test cases, copied and expanded by this
        particular matrix factor."""
        results = []
        for tox_case in tox_cases:
            for version in self.versions:
                results.append(self.expand_one(tox_case, version))
        return results

    def expand_one(self, tox_case, version):
        """Do the actual expansion on a particular test case.

        ***MUST BE OVERRIDDEN BY CHILD CLASSES***

        :param: tox_case: the test case to be expanded by this particular
        axis
        :param version: the version of the test case to be expanded in this
        step
        :return: the resultant new version of the test case"""
        raise NotImplementedError
