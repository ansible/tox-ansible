try:
    # Current name
    from tox.config import PARALLEL_ENV_VAR_KEY_PUBLIC as TOX_PARALLEL_ENV
except ImportError:
    try:
        # Old name
        from tox.config import PARALLEL_ENV_VAR_KEY as TOX_PARALLEL_ENV
    except ImportError:
        TOX_PARALLEL_ENV = "TOX_ANSIBLE_PARALLEL_NOT_SUPPORTED"

__all__ = ["TOX_PARALLEL_ENV"]
