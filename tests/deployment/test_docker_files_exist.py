
import os
import pytest

def test_dockerfile_exists():
    assert os.path.exists("deployment/Dockerfile")

def test_docker_compose_exists():
    assert os.path.exists("deployment/docker-compose.yml")

def test_entrypoint_exists():
    assert os.path.exists("deployment/entrypoint.sh")

def test_healthcheck_exists():
    assert os.path.exists("deployment/healthcheck.sh")

def test_no_hardcoded_secrets_in_dockerfile():
    with open("deployment/Dockerfile", "r") as f:
        content = f.read()
    assert "password" not in content.lower() or "#" in content
    assert "password=" not in content.lower()

def test_docker_compose_no_hardcoded_secrets():
    with open("deployment/docker-compose.yml", "r") as f:
        content = f.read()
    # Should use env_file or ${VAR} not literal passwords
    lines = content.split("\n")
    for line in lines:
        if "password" in line.lower() and "${" not in line and "#" not in line:
            pytest.fail(f"Possible hardcoded secret: {line}")
