try:
    from tox.config.parallel import ENV_VAR_KEY_PUBLIC as TOX_PARALLEL_ENV
except ImportError:
    from tox.config.parallel import ENV_VAR_KEY as TOX_PARALLEL_ENV

__all__ = ['TOX_PARALLEL_ENV']
