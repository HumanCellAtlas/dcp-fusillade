import os

from dcplib.aws.clients import secretsmanager as sm_client  # type: ignore


def get_seceret(self, secret_id: str):
    """returns secret string from AWS Secrets Manager"""
    return sm_client.get_secret_value(SecretId=secret_id).get('SecretString')

class BaseConfig(object):
    """
    Basic object defining variables that should be turned into Flask configuration variables.

    Eventually this will use an AWS client to fetch secrets from the secrets manager.
    """

     # SSM
    SECRET_STORE = os.getenv('FUS_SECRETS_STORE')
    secret_name = os.getenv('GITLAB_ACCESS_KEY_SECRET_NAME')

    # flask
    FLASK_SECRET_KEY = os.environ["FLASK_SECRET_KEY"]

    # github sensitive info
    # these values should be placed into application.json, but need to find how Zappa packages files.
    GITHUB_OAUTH_CLIENT_ID = os.environ.get("DCP_FUS_GH_CLIENT_ID")
    GITHUB_OAUTH_CLIENT_SECRET = os.environ.get("DCP_FUS_GH_CLIENT_SECRET")
    GITHUB_ORG = "HumanCellAtlas"

    # gitlab sensitive info
    GITLAB_URL = os.environ.get("GITLAB_URL")
    GITLAB_PID = os.environ.get("GITLAB_RPOJECT_ID")
    GITLAB_TOKEN = get_seceret(f"{SECRET_STORE}/{secret_name}")


class DefaultConfig(BaseConfig):
    pass
