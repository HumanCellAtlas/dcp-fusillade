import os
import boto3
from functools import lru_cache


sm_client = boto3.client("secretsmanager")


def get_secret(secret_id: str):
    """Returns secret string from AWS Secrets Manager"""
    return sm_client.get_secret_value(SecretId=secret_id).get("SecretString")


class BaseConfig(object):
    """
    The base configuration class used by Flask to define its config.
    Base class is used by both tests and live deployments.
    """

    STAGE = os.environ["FUS_DEPLOYMENT_STAGE"]


class TestConfig(object):
    """
    Configuration class used for tests only
    """

    FLASK_SECRET_KEY = "SUPERSECRETFLASKKEYFORTESTING"


class LiveConfig(object):
    """
    Configuration class used for live deployments. This class uses AWS secrets manager
    to retrieve most of the config variables.
    """

    STORE = os.environ["FUS_SECRETS_STORE"]

    # Gitlab things
    GITLAB_PROJECT_ID = os.environ["GITLAB_PROJECT_ID"]
    GITLAB_API_URL = os.environ["GITLAB_URL"]
    GITLAB_API_TOKEN = get_secret(f"{self.STORE}/{self.STAGE}/{os.environ['WEBAPP_STASH_SECRET_NAME']}")

    # Flask and Github things are packed into the WEBAPP_STASH secret
    GITHUB_ORG = os.environ["GITHUB_ORG"]
    WEBAPP_STASH = get_secret(f"{self.STORE}/{self.STAGE}/{os.environ['WEBAPP_STASH_SECRET_NAME']}")
    FLASK_SECRET_KEY = self.WEBAPP_STASH["FLASK_SECRET_KEY"]
    GITHUB_OAUTH_CLIENT_ID = self.WEBAPP_STASH["GITHUB_OAUTH_CLIENT_ID"]
    GITHUB_OAUTH_CLIENT_SECRET = self.WEBAPP_STASH["GITHUB_OAUTH_CLIENT_SECRET"]

