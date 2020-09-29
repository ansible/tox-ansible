from .by_driver import ByDriver
from .by_scenario import ByScenario


class Filter(object):
    """Filters an envlist"""

    def __init__(self, options):
        self._filters = [
            ByScenario(options.scenario),
            ByDriver(options.driver),
        ]

    def filter(self, envlist):
        results = envlist
        for f in self._filters:
            results = f.filter(results)
        return results
