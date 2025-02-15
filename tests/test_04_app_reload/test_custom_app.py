import time
from pathlib import Path, PurePath

import docker
import pytest
import requests

from ..utils import (
    CONTAINER_NAME,
    IMAGE_NAME,
    get_config,
    get_logs,
    remove_previous_container,
)

client = docker.from_env()


def verify_container(container, response_text):
    logs = get_logs(container)
    assert "Checking for script in /app/prestart.sh" in logs
    assert "Running script /app/prestart.sh" in logs
    assert (
        "Running inside /app/prestart.sh, you could add migrations to this file" in logs
    )
    assert "Uvicorn running on http://0.0.0.0:80" in logs
    response = requests.get("http://127.0.0.1:8000")
    assert response.text == response_text


@pytest.mark.parametrize(
    "dockerfile,environment,response_text",
    [
        (
            "python3.6.dockerfile",
            {"MODULE_NAME": "custom_app.custom_main", "VARIABLE_NAME": "custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.6",
        ),
        (
            "python3.7.dockerfile",
            {"MODULE_NAME": "custom_app.custom_main", "VARIABLE_NAME": "custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "latest.dockerfile",
            {"MODULE_NAME": "custom_app.custom_main", "VARIABLE_NAME": "custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "python3.6-alpine3.9.dockerfile",
            {"MODULE_NAME": "custom_app.custom_main", "VARIABLE_NAME": "custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.6",
        ),
        (
            "python3.7-alpine3.9.dockerfile",
            {"MODULE_NAME": "custom_app.custom_main", "VARIABLE_NAME": "custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "python3.6.dockerfile",
            {"APP_MODULE": "custom_app.custom_main:custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.6",
        ),
        (
            "python3.7.dockerfile",
            {"APP_MODULE": "custom_app.custom_main:custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "latest.dockerfile",
            {"APP_MODULE": "custom_app.custom_main:custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "python3.6-alpine3.9.dockerfile",
            {"APP_MODULE": "custom_app.custom_main:custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.6",
        ),
        (
            "python3.7-alpine3.9.dockerfile",
            {"APP_MODULE": "custom_app.custom_main:custom_var"},
            "Test app. From Uvicorn with Gunicorn. Using Python 3.7",
        ),
    ],
)
def test_custom_app(dockerfile, environment, response_text):
    remove_previous_container(client)
    test_path: PurePath = Path(__file__)
    path = test_path.parent / "custom_app"
    client.images.build(path=str(path), dockerfile=dockerfile, tag=IMAGE_NAME)
    container = client.containers.run(
        IMAGE_NAME,
        name=CONTAINER_NAME,
        environment=environment,
        ports={"80": "8000"},
        detach=True,
        command="/start-reload.sh",
    )
    time.sleep(1)
    verify_container(container, response_text)
    container.exec_run(
        "sed -i 's|Uvicorn with Gunicorn|Uvicorn with autoreload|' /app/custom_app/custom_main.py"
    )
    new_response_text = response_text.replace(
        "Uvicorn with Gunicorn", "Uvicorn with autoreload"
    )
    time.sleep(1)
    verify_container(container, new_response_text)
    container.stop()
    container.remove()
