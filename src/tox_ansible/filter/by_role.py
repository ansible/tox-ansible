from .base_filter import BaseFilter


class ByRole(BaseFilter):
    """Filters down to only those environments that are in the list of defined
    role names."""
    def __init__(self, names):
        """
        :param envlist: The dictionary of tox environment configs as per the
        base class
        :param role_name: A list of role names to filter on. Only scenarios
        matching a name in that list will be returned."""
        self.names = names

        def _filter(e):
            if hasattr(e[1], 'tox_case'):
                # Can still reference "self" because of nesting
                return e[1].tox_case.role.name in self.names
            return False
        self._filter = _filter
