from .by_role import ByRole
from .by_scenario import ByScenario


class Filter(object):
    """Filters an envlist"""
    def __init__(self, options):
        self._filters = [
            ByRole(options.role),
            ByScenario(options.scenario)
        ]

    def filter(self, envlist):
        results = envlist
        for f in self._filters:
            results = f.filter(results)
        return results
