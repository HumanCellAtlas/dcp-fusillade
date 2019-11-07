import os
import sys
import json
from unittest import mock

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from app.flask_app import create_app

def test_create_app():
    """Test create_app without passing test config."""
    assert not create_app().testing

def test_create_testing_config():
    assert create_app({"TESTING": True}).testing

def test_hello(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json == {"message": "pong"}

def test_auth_config(client, authapp):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Enter the email address for a user" in response.data

