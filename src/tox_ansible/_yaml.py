from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:  # pragma: no cover
    from yaml import Loader  # type: ignore


def load_yaml(filename: str):
    with open(filename, "r") as c:
        return load(c.read(), Loader=Loader)
