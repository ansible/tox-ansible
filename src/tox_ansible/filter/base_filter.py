class BaseFilter(object):
    """A base class that filters a given envlist based on the requirements of
    the given _filter variable. This should be a callable function, but not
    a member method of any baseclasses. That is, you should define it to not
    require the "self" keyword. See one of the existing implementation classes
    that exists herein to see exactly how that happens."""

    def filter(self, envlist):
        """
        Calling this method without properly defining the _filter method will
        cause an error. That function must be defined as something which can
        be passed to the builtin method "filter" and should expect to be handed
        the list of objects we're filtering and their names as a tuple of the
        form ('envname', <envconfig object>) from tox. Any environments that
        were modified or created as part of this plugin should have an extra
        attribute named "scenario" that can be queried.

        :param envlist: A dictionary of the environments and the configs that
        will be filtered
        :return: The list of environments filtered based on the defined
        conditions."""
        # By default we're going to add the list of names we're looking for to
        # the self.names attribute. If that is an empty string, then we should
        # not filter on that value
        if hasattr(self, "names") and len(self.names) == 0:
            return envlist
        return dict(filter(self._filter, envlist.items()))
