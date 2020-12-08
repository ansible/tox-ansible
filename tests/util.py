import os
import shutil
import subprocess
import tempfile
from textwrap import dedent
from unittest import TestCase

from tox_ansible.compat import TOX_PARALLEL_ENV

GALAXY_SAMPLE = """
namespace: example
name: foo
version: 0.0.1
"""


class ToxAnsible_TestCase(TestCase):
    """A TestCase for testing tox configs.

    This class creates a temporary directory, writing the provided contents to
    the tox config file and any scenario files.

    The test case also provides the `.tox_call()` method for calling tox with
    the config, and `.tox_envlist()`, which is useful for testing the expected
    env list.

    Note that the test case doesn't change the working directory or environment

    Attributes:
        ini_contents: contentst of tox.ini
        ini_filename: file to create - defaults to tox.ini
        ini_filepath: Full path to tox.ini - generated during test setup
        roles: A list of tuples. [('rolename', [('scenario1', {...}), ...])]
            Each tuple is (rolename, scenariolist). The scenariolist is a list
            of tuples that is (scenarioname, molecule.yml).
    """

    ini_contents = None
    ini_filename = "tox.ini"
    roles = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        assert (
            cls.ini_contents is not None
        ), "`{cls.__module__}.{cls.__name__}.ini_contents` has not been set".format(
            cls=cls
        )

        # Create a tmpdir so that we aren't working somewhere that matters
        cls._temp_dir = tempfile.mkdtemp()
        cls.ini_filepath = os.path.join(cls._temp_dir, cls.ini_filename)

        # Write out the tox.ini file
        with open(cls.ini_filepath, "w") as ini_file:
            ini_file.write(dedent(cls.ini_contents))

        # Write the galaxy.yml file - blank for now
        with open(os.path.join(cls._temp_dir, "galaxy.yml"), "w") as galaxy_yml:
            galaxy_yml.write(GALAXY_SAMPLE)

        # Create role and scenario dirs
        for role, scenarios in cls.roles:
            tasks = os.path.join(cls._temp_dir, "roles", role, "tasks")
            os.makedirs(tasks)
            # It's not a role if it doesn't have a tasks/main.yml
            with open(os.path.join(tasks, "main.yml"), "w") as tasks:
                tasks.write("")
            # Create the molecule scenarios
            for scenario, molecule in scenarios:
                d = os.path.join(cls._temp_dir, "roles", role, "molecule", scenario)
                os.makedirs(d)
                with open(os.path.join(d, "molecule.yml"), "w") as mol_file:
                    mol_file.write(dedent(molecule))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._temp_dir)
        super().tearDownClass()

    def _tox_call(self, arguments):
        # Remove TOX_PARALLEL_ENV from the subprocess environment variables
        # See: https://github.com/tox-dev/tox/issues/1275
        env = os.environ.copy()
        env.pop(TOX_PARALLEL_ENV, None)

        proc = subprocess.Popen(
            arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        stdout, stderr = proc.communicate()

        return proc.returncode, stdout.decode("utf-8"), stderr.decode("utf-8")

    def tox_call(self, arguments):
        base = ["tox", "-c", self.ini_filepath]
        return self._tox_call(base + arguments)

    def tox_envlist(self, arguments=None):
        arguments = arguments if arguments else []
        returncode, stdout, stderr = self.tox_call(["-l"] + arguments)

        self.assertEqual(returncode, 0, stderr)

        return stdout.strip().splitlines()
