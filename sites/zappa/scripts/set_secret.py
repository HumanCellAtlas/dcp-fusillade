#!/usr/bin/env python
import os
import sys
import select
import argparse

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from secrets import sm_client, get_secret_prefix

"""
Set a secret in the AWS Secrets Manager, and handle secrets prefix.
This script uses secrets.py in the app/ folder.
"""

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--secret-name", required=True)
parser.add_argument("--stage", required=False, choices=['testing','dev','integration','staging','prod'])
parser.add_argument("--dry-run", required=False, action='store_true')
args = parser.parse_args()

tags = [
    {'Key': 'project', "Value": os.getenv("FUS_PROJECT_TAG", '')},
    {'Key': 'owner', "Value": os.getenv("FUS_OWNER_TAG", '')},
    {'Key': 'env', "Value": os.getenv("FUS_DEPLOYMENT_STAGE")},
    {'Key': 'Name', "Value": args.secret_name},
    {'Key': 'managedBy', "Value": "manual"}
]

if args.stage:
    # Use the user-specified stage
    prefix = get_secret_prefix(stage=args.stage)
else:
    # Uses FUS_DEPLOYMENT_STAGE by default
    if os.environ.get("FUS_DEPLOYMENT_STAGE","") == "":
        raise RuntimeError("Error: source environment file before proceeding, FUS_DEPLOYMENT_STAGE is not set!")
    print(f"No --stage flag was set, using $FUS_DEPLOYMENT_STAGE = {os.environ['FUS_DEPLOYMENT_STAGE']}")
    prefix = get_secret_prefix()

secret_name = args.secret_name.rstrip("/")
secret_id = f"{prefix}/" + secret_name.replace(prefix, "", 1).lstrip("/")

print("Setting", secret_id)

if not select.select([sys.stdin], [], [], 0.0)[0]:
    print(f"No data in stdin, exiting without setting {secret_id}")
    sys.exit()
secret_val = sys.stdin.read()

try:
    resp = sm_client.describe_secret(SecretId=secret_id)
except sm_client.exceptions.ResourceNotFoundException:
    if args.dry_run:
        print('Resource Not Found: Creating {}'.format(secret_id))
    else:
        print(f"Creating {secret_id}")
        resp = sm_client.create_secret(
            Name=secret_id,
            SecretString=secret_val,
            Tags=tags
        )
        print(resp)
else:
    missing_tags = []
    for tag in tags:
        if tag in resp.get('Tags', []):
            pass
        else:
            missing_tags.append(tag)

    if args.dry_run:
        print('Resource Found.')
        print(resp)
        if missing_tags:
            print(f"Missing tags:")
            for tag in missing_tags:
                print(f"\t{tag}")
    else:
        print(f'Resource Found: Updating {secret_id}')
        resp = sm_client.update_secret(
            SecretId=secret_id,
            SecretString=val
        )
        sm_client.tag_resource(
            SecretId=secret_id,
            Tags=missing_tags
        )
