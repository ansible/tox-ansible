import subprocess
from functools import lru_cache


@lru_cache()
def use_docker() -> bool:
    """Return true if we should use docker."""
    # docker version command works even if service is not accesible, but
    # info should pass only if we have a running service.
    try:
        result = subprocess.run(
            ["docker", "info"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0
    except FileNotFoundError:
        pass
    return False
