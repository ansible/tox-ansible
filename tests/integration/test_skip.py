"""Test the use of skip provided by the user."""

from ..conftest import ToxEnvironment


def test_environment_config(
    skip_environment: ToxEnvironment,
) -> None:
    """Test that the user skip config is used for environment generation.

    :param skip_environment: A dict representing the environment configuration
    """
    assert "py3.7" not in skip_environment.name

    config = skip_environment.config

    if "integration" in skip_environment.name:
        assert not config["commands_pre"]
        assert "ANSIBLE_COLLECTION" not in config["set_env"]
    else:
        assert config["commands_pre"]
        assert "ANSIBLE_COLLECTION" in config["set_env"]
