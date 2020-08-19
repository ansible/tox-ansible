from . import MatrixAxisBase


class AnsibleAxis(MatrixAxisBase):
    """See documentation on the Matrix base class"""

    def expand_one(self, tox_case, version):
        return tox_case.expand_ansible(version)


class PythonAxis(MatrixAxisBase):
    """See documentation on the Matrix base class"""

    def expand_one(self, tox_case, version):
        return tox_case.expand_python(version)
