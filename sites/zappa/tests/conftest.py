"""
Define fixtures, which can be passed as arguments to pytest functions.
"""
import os
import sys

import pytest
from unittest import mock

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from app.flask_app import create_app

"""
Pytest fixtures can bootstrap upon one another - once a fixture is defined,
it can be used in the definition of other fixtures. testapp is the first fixture,
and can be used by subsequent fixtures.
"""

@pytest.fixture
def testapp():
    """Create and configure a new app instance for each test."""
    testapp = create_app({"TESTING": True})
    yield testapp

@pytest.fixture
def client(testapp):
    return testapp.test_client()

@pytest.fixture
def authapp(testapp):
    # re combining with and yield: https://stackoverflow.com/a/41881820
    with mock.patch("app.flask_app.github") as gh:
        gh.authorized = mock.MagicMock(return_value=True)
        class OkResp:
            def __init__(self, *args, **kwargs):
                self.ok = True
            def json(self):
                return [{"login": testapp.config["GITHUB_ORG"]}]
        gh.get = mock.MagicMock(side_effect=[OkResp()])
        yield testapp
