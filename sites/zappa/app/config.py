import os

class BaseConfig(object):
    """
    Basic object defining variables that should be turned into Flask configuration variables.

    Eventually this will use an AWS client to fetch secrets from the secrets manager.
    """

    # flask
    FLASK_SECRET_KEY = os.environ["FLASK_SECRET_KEY"]

    # github sensitive info
    GITHUB_OAUTH_CLIENT_ID = os.environ.get("DCP_FUS_GH_CLIENT_ID")
    GITHUB_OAUTH_CLIENT_SECRET = os.environ.get("DCP_FUS_GH_CLIENT_SECRET")
    GITHUB_ORG = "HumanCellAtlas"
    
    # gitlab sensitive info
    GITLAB_URL = os.environ.get("GITLAB_URL")
    GITLAB_PID = os.environ.get("GITLAB_RPOJECT_ID")
    GITLAB_TOKEN = os.environ.get("DCP_FUS_GL_TOKEN")

class DefaultConfig(BaseConfig):
    pass
