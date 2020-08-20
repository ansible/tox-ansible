from .base_filter import BaseFilter


class ByDriver(BaseFilter):
    """Filters environments based on what Molecule driver is configured to run
    the scenario."""

    def __init__(self, names):
        self.names = names

        def _filter(e):
            if hasattr(e[1], "tox_case") and hasattr(e[1].tox_case, "scenario"):
                return e[1].tox_case.scenario.driver in self.names
            return False

        self._filter = _filter
