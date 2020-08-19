from .base_filter import BaseFilter


class ByScenario(BaseFilter):
    """Filters to only scenarios that match a given name."""

    def __init__(self, names):
        """
        :param envlist: The dictionary of tox environment configs per the base
        class argument
        :param names: A list of scenario names to match. Only environments
        from scenarios whose names are in the given list will be returned."""
        self.names = names

        def _filter(e):
            if hasattr(e[1], "tox_case") and hasattr(e[1].tox_case, "scenario"):
                # Can still reference "self" because of nesting
                return e[1].tox_case.scenario.name in self.names
            return False

        self._filter = _filter
