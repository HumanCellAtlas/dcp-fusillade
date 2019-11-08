import os
import boto3


sm_client = boto3.client("secretsmanager")


def get_secret(secret_id: str):
    """Returns secret string from AWS Secrets Manager"""
    return sm_client.get_secret_value(SecretId=secret_id).get("SecretString")


class BaseConfig(object):
    """
    The base configuration class used by Flask to define its config.
    Base class is used by both tests and live deployments.
    Parameters in this config class are populated from user's environment.

    These environment variables must be set regardless of the configuration:

    - FUS_DEPLOYMENT_STAGE: fusillade stage to point at
    - GITLAB_API_URL: url for gitlab api
    - GITLAB_PROJECT_ID: project ID for the repo
    - GITHUB_ORG: the name of the Github org whose membership allows access
    """

    STAGE = os.environ["FUS_DEPLOYMENT_STAGE"]

    # Gitlab things
    GITLAB_API_URL = os.environ["GITLAB_API_URL"]
    GITLAB_PROJECT_ID = os.environ["GITLAB_PROJECT_ID"]

    # Github things
    GITHUB_ORG = os.environ["GITHUB_ORG"]



class TestConfig(object):
    """
    Configuration class used for tests only.
    Parameters in this config class are populated from user's environment.
    Enable test mode by passing {"TESTING": True} to create_app().
    """

    FLASK_SECRET_KEY = "SUPERSECRETFLASKKEYFORTESTING"


class LocalConfig(object):
    """
    Configuration class used for running locally.
    Parameters in this config class are populated from user's environment.
    Enable local mode by passing {"LOCAL": True} to create_app().
    """

    GITLAB_API_TOKEN = os.environ['GITLAB_API_TOKEN']
    FLASK_SECRET_KEY = os.environ['FLASK_SECRET_KEY']
    GITHUB_OAUTH_CLIENT_ID = os.environ['GITHUB_OAUTH_CLIENT_ID']
    GITHUB_OAUTH_CLIENT_SECRET = os.environ['GITHUB_OAUTH_CLIENT_SECRET']


class LiveConfig(object):
    """
    Configuration class used for live deployments. 
    Paramters in this config class are populated from the AWS secrets manager.
    """

    STORE = os.environ["FUS_SECRETS_STORE"]

    # Gitlab API token is packed into a secret
    @property
    @lru_cache(maxsize=1)
    def GITLAB_API_TOKEN(self):
        """Retrieve the Gitlab API token from the AWS secrets manager"""
        return get_secret(f"{self.STORE}/{self.STAGE}/{os.environ['GITLAB_API_TOKEN_SECRET_NAME']}")

    # Flask and Github things are packed into the WEBAPP_STASH secret
    @property
    @lru_cache(maxsize=1)
    def WEBAPP_STASH(self):
        """Retrieve the Flask/Github OAuth secrets from the AWS secrets manager"""
        return json.loads(get_secret(f"{self.STORE}/{self.STAGE}/{os.environ['WEBAPP_STASH_SECRET_NAME']}"))

    FLASK_SECRET_KEY = self.WEBAPP_STASH["FLASK_SECRET_KEY"]
    GITHUB_OAUTH_CLIENT_ID = self.WEBAPP_STASH["GITHUB_OAUTH_CLIENT_ID"]
    GITHUB_OAUTH_CLIENT_SECRET = self.WEBAPP_STASH["GITHUB_OAUTH_CLIENT_SECRET"]

