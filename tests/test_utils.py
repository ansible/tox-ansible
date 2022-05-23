from tox_ansible.utils import use_docker


def test_docker_present(mocker):
    use_docker.cache_clear()
    rc = mocker.Mock()
    rc.returncode = 0
    mocker.patch("tox_ansible.utils.subprocess.run", return_value=rc)
    assert use_docker()


def test_docker_absent(mocker):
    use_docker.cache_clear()
    mocker.patch("tox_ansible.utils.subprocess.run", side_effect=FileNotFoundError)
    assert not use_docker()
