import time

import docker
import pytest
import requests

from ..utils import CONTAINER_NAME, get_config, get_logs, remove_previous_container

client = docker.from_env()


def verify_container(container, response_text):
    config_data = get_config(container)
    assert config_data["workers_per_core"] == 1
    assert config_data["host"] == "0.0.0.0"
    assert config_data["port"] == "80"
    assert config_data["loglevel"] == "info"
    assert config_data["workers"] >= 2
    assert config_data["bind"] == "0.0.0.0:80"
    logs = get_logs(container)
    assert "Checking for script in /app/prestart.sh" in logs
    assert "Running script /app/prestart.sh" in logs
    assert (
        "Running inside /app/prestart.sh, you could add migrations to this file" in logs
    )
    response = requests.get("http://127.0.0.1:8000")
    assert response.text == response_text


@pytest.mark.parametrize(
    "image,response_text",
    [
        (
            "hairychris2/uvicorn-gunicorn:python3.6",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.6",
        ),
        (
            "hairychris2/uvicorn-gunicorn:python3.7",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "hairychris2/uvicorn-gunicorn:latest",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "hairychris2/uvicorn-gunicorn:python3.6-alpine3.9",
            "Hello world! From Uvicorn with Gunicorn in Alpine. Using Python 3.6",
        ),
        (
            "hairychris2/uvicorn-gunicorn:python3.7-alpine3.9",
            "Hello world! From Uvicorn with Gunicorn in Alpine. Using Python 3.7",
        ),
    ],
)
def test_defaults(image, response_text):
    remove_previous_container(client)
    container = client.containers.run(
        image, name=CONTAINER_NAME, ports={"80": "8000"}, detach=True
    )
    time.sleep(1)
    verify_container(container, response_text)
    container.stop()
    # Test that everything works after restarting too
    container.start()
    time.sleep(1)
    verify_container(container, response_text)
    container.stop()
    container.remove()
