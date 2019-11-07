import os
import sys
from unittest import mock
from flask import g
from flask import session

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from app.flask_app import create_app


def test_github_login(client, testapp):
    # test that accessing the root url /
    # redirects to login.html page that 
    # has a "login with github" button
    assert client.get("/").status_code == 200
    response = client.get("/")
    assert b"log in to your Github account" in response.data 

def test_github_logged_in(client, authapp):
    # test that accessing the root url /
    # after correctly mocking app.flask_app.github
    # redirects to the form
    response = client.get("/")
    assert response.status_code == 200
    assert b"Enter the email address for a user" in response.data
    
