import os
import boto3

WEBAPP_SECRETS_PREFIX = "webapps/groupsusers"
sm_client = boto3.client("secretsmanager")


def get_secret_prefix(stage=None):
    """Returns the prefix for secrets in the AWS Secrets Manager"""
    store = os.environ["FUS_SECRETS_STORE"]
    webapp_prefix = WEBAPP_SECRETS_PREFIX
    if stage is None:
        stage = os.environ["FUS_DEPLOYMENT_STAGE"]
    prefix = f"{store}/{webapp_prefix}/{stage}"
    return prefix


def get_secret(secret_name: str):
    """Given a secret name, add the secret store prefix and retrieve the secret string from AWS Secrets Manager"""
    prefix = get_secret_prefix()
    secret_name = secret_name.rstrip("/")
    # If prefix is present in the front, remove it. Then prepend prefix.
    secret_id = f"{prefix}/" + secret_name.replace(prefix, "", 1).lstrip("/")
    return sm_client.get_secret_value(SecretId=secret_id).get("SecretString")
