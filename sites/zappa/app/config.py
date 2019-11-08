import os
from functools import lru_cache
from .utils import get_secret
import json


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

    These variables will be available via the webapp configuration:
    - FUS_DEPLOYMENT_STAGE
    - GITLAB_API_URL
    - GITLAB_PROJECT_ID
    - GITHUB_ORG
    """
    def __init__(self):
        self.FUS_DEPLOYMENT_STAGE = os.environ["FUS_DEPLOYMENT_STAGE"]

        # Gitlab things
        self.GITLAB_API_URL = os.environ["GITLAB_API_URL"]
        self.GITLAB_PROJECT_ID = os.environ["GITLAB_PROJECT_ID"]

        # Github things
        self.GITHUB_ORG = os.environ["GITHUB_ORG"]


class TestConfig(BaseConfig):
    """
    Configuration class used for tests only.
    Parameters in this config class are populated from user's environment.
    Enable test mode by passing {"TESTING": True} to create_app().
    See `tests` directory.
    """
    def __init__(self):
        super().__init__()
        self.FLASK_SECRET_KEY = "SUPERSECRETFLASKKEYFORTESTING"


class LocalConfig(BaseConfig):
    """
    Configuration class used for running locally.
    Parameters in this config class are populated from user's environment.
    Enable local mode by passing {"LOCAL": True} to create_app().

    Example: run_local.py

    ```
    from app import create_app
    local_app = create_app({"LOCAL": True})
    if __name__=="__main__":
        local_app.run()
    ```

    These environment variables must be set if using a local configuration:

    - GITLAB_API_TOKEN: the access token for opening merge requests in gitlab
    - FLASK_SECRET_KEY: a random string used to establish sessions
    - GITHUB_OAUTH_CLIENT_ID: the client id of the github oauth app checking group membership
    - GITHUB_OAUTH_CLIENT_SECRET: the client secret of the github oauth app checking group membership

    These variables will also be available in the Flask app configuration.
    """
    def __init__(self):
        super().__init__()
        self.GITLAB_API_TOKEN = os.environ['GITLAB_API_TOKEN']
        self.FLASK_SECRET_KEY = os.environ['FLASK_SECRET_KEY']
        self.GITHUB_OAUTH_CLIENT_ID = os.environ['GITHUB_OAUTH_CLIENT_ID']
        self.GITHUB_OAUTH_CLIENT_SECRET = os.environ['GITHUB_OAUTH_CLIENT_SECRET']


class LiveConfig(BaseConfig):
    """
    Configuration class used for live deployments. 
    Paramters in this config class are populated from the AWS secrets manager.

    These environment variables must be set if using a live configuration:

    - FUS_SECRETS_STORE: the secrets store (prefix) for retrieving secrets for the 
      webapp cofiguration.
    - GITLAB_API_TOKEN_SECRET_NAME: name of secret storing gitlab api token
    - WEBAPP_SECRET_STASH_NAME: name of secret storing webapp secret stash

    The following variables will be AUTOMATICALLY set in the Flask app configuration
    using contents of AWS secrets:

    - GITLAB_API_TOKEN: the access token for opening merge requests in gitlab
    - FLASK_SECRET_KEY: a random string used to establish sessions
    - GITHUB_OAUTH_CLIENT_ID: the client id of the github oauth app checking group membership
    - GITHUB_OAUTH_CLIENT_SECRET: the client secret of the github oauth app checking group membership
    """
    def __init__(self):
        super().__init__()

        # Live configuration is based on the AWS secrets manager
        self.STORE = os.environ["FUS_SECRETS_STORE"]
        # TODO: Add a secrets prefix specific to the webapp
        # self.STORE += "/webapps/usersgroups"

        # This allows using http locally
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "true"

    @property
    @lru_cache(maxsize=1)
    def GITLAB_API_TOKEN(self):
        """Retrieve the Gitlab access token from AWS secrets manager (cached)"""
        token_sec_name = os.environ['GITLAB_API_TOKEN_SECRET_NAME']
        secret_name = f"{self.STORE}/{self.FUS_DEPLOYMENT_STAGE}/{token_sec_name}"
        return get_secret(secret_name)

    # Flask and Github things are packed into the WEBAPP_STASH secret
    @property
    @lru_cache(maxsize=1)
    def WEBAPP_STASH(self):
        """Retrieves the Flask/Github OAuth secrets from the AWS secrets manager (cached)"""
        stash_sec_name = os.environ['WEBAPP_SECRET_STASH_NAME']
        secret_name = f"{self.STORE}/{self.FUS_DEPLOYMENT_STAGE}/{stash_sec_name}"
        return json.loads(get_secret(secret_name))

    @property
    def FLASK_SECRET_KEY(self):
        return self.WEBAPP_STASH["FLASK_SECRET_KEY"]

    @property
    def GITHUB_OAUTH_CLIENT_ID(self):
        return self.WEBAPP_STASH["GITHUB_OAUTH_CLIENT_ID"]

    @property
    def GITHUB_OAUTH_CLIENT_SECRET(self):
        return self.WEBAPP_STASH["GITHUB_OAUTH_CLIENT_SECRET"]
