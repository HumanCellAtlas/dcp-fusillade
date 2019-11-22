#!/usr/bin/env python
"""
This scripts updates groups, roles, and users deployed to a fusillade instance. Roles will be created or updated if
specified in the configuration. Users will be added or removed from a group if specified in the group. Roles will be
added or removed from a group as needed. Users will be created as needed. If a role does not exist in fusillade and
is not in the configuration, it will not be added to the group.

To use you must have a google service account that has been authorized to create and modify groups and users in
fusillade.
"""
import argparse
import json
from collections import defaultdict

import requests

from dcplib.security import DCPServiceAccountManager

auth_deployments = {
    'dev': "https://auth.dev.data.humancellatlas.org",
    'integration': "https://auth.integration.data.humancellatlas.org",
    'staging': "https://auth.staging.data.humancellatlas.org",
    "testing": "https://auth.testing.data.humancellatlas.org",
    "production": "https://auth.data.humancellatlas.org"
}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('stage',
                    metavar='stage',
                    type=str,
                    help="The stage of fusillade you would like apply the configuration.",
                    choices=[i for i in auth_deployments.keys()])
parser.add_argument('--file',
                    help="A file containing a fusillade configuration.",
                    required=True)
parser.add_argument("--secret",
                    help="secretId of secret stored in AWS Secrets Manager containing google service account "
                         "credentials with permission to modify groups in the fusillade deployment.",
                    type=str,
                    default="deployer_service_account.json",
                    required=False)
parser.add_argument('--dry-run', '-d',
                    help="See the changes without applying them.",
                    action="store_true")
parser.add_argument('--force', '-f',
                    help="Makes the changes without requiring the user to confirm.",
                    action="store_true")
args = parser.parse_args()

auth_url = auth_deployments[args.stage]
secret_id = '/'.join(['dcp', 'fusillade', args.stage, args.secret])
service_account = DCPServiceAccountManager.from_secrets_manager(
    secret_id,
    "https://auth.data.humancellatlas.org/")
headers = {'Content-Type': "application/json"}
headers.update(**service_account.get_authorization_header())


def request_action(path: str, action: str, entity_type: str, entities: list):
    if entities:
        for chunk in [entities[n:n + 10] for n in range(0, len(entities), 10)]:
            resp = requests.put(f"{auth_url}{path}?action={action}", headers=headers, json={entity_type: chunk})
            resp.raise_for_status()


def update_roles(name: str, policy: dict, new: bool):
    if new:
        resp = requests.post(
            f"{auth_url}/v1/role",
            headers=headers,
            json={
                "role_id": name,
                "policy": policy
            }
        )
        resp.raise_for_status()
        message = f"Created role {name}."
    else:
        resp = requests.put(
            f"{auth_url}/v1/role/{name}/policy",
            headers=headers,
            json={"policy": policy}
        )
        resp.raise_for_status()
        message = f"Updated role {name}."


def update_group(name: str, roles: dict, users: dict, new: bool):
    if new:
        resp = requests.post(
            f"{auth_url}/v1/group",
            headers=headers,
            json={"group_id": name}
        )
        resp.raise_for_status()
        message = f"Created group {name}."
    else:
        message = f"Updated group {name}."
    request_action(f'/v1/group/{name}/roles', 'add', 'roles', roles.get('add'))
    request_action(f'/v1/group/{name}/roles', 'remove', 'roles', roles.get('remove'))
    request_action(f'/v1/group/{name}/users', 'add', 'users', users.get('add'))
    request_action(f'/v1/group/{name}/users', 'remove', 'users', users.get('remove'))
    print(message)


def update_user(name, new):
    if new:
        resp = requests.post(
            f"{auth_url}/v1/user",
            headers=headers,
            json={"user_id": name}
        )
        resp.raise_for_status()
        print(f"Created user {name}.")


def paginate(path, key):
    resp = requests.get(f"{auth_url}{path}", headers=headers)
    resp.raise_for_status()
    items = []
    while "Link" in resp.headers:
        items.extend(resp.json()[key])
        next_url = resp.headers['Link'].split(';')[0][1:-1]
        resp = requests.get(next_url, headers=headers)
        resp.raise_for_status()
    else:
        items.extend(resp.json()[key])
    return items


def make_config(config: dict) -> dict:
    """
    get all roles from the json and see if they all exist.
    log message when a role does not exist
    get all groups and see if they exist.
    log message about what groups will be created and what roles will be assigned to them.
    don't add a user to a group they are already in.

    :return: the configuration to setup groups in fusillade
    """
    config_groups = []
    config_group_roles = []
    config_users = defaultdict(list)
    for name, group in config.get('groups', dict()).items():
        config_groups.append(name)
        if group.get('roles'):
            config_group_roles.extend(group['roles'])
        for user in group.get('users', []):
            config_users[user].append(name)

    # find which roles need to be created
    roles = config.get('roles', dict())
    config_roles = set([name for name in roles.keys()])

    # find which roles don't exist in the directory and wont be created
    existing_roles = set(paginate('/v1/roles', 'roles'))
    update_roles = config_roles & existing_roles
    new_roles = config_roles - update_roles
    missing_roles = set(config_group_roles) - existing_roles - new_roles

    # find what groups need to be created
    current_groups = set(paginate('/v1/groups', 'groups'))
    missing_groups = set(config_groups) - current_groups
    existing_groups = current_groups - set(config_groups)

    # create the role config
    new_roles_config = dict()
    outdated_roles = []
    for name in new_roles:
        new_roles_config[name] = config['roles'][name]
        new_roles_config[name].update(new=True)
    for name in update_roles:
        resp = requests.get(
            f"{auth_url}/v1/role/{name}",
            headers=headers,
        )
        resp.raise_for_status()
        policy = resp.json()['policies'].get('IAMPolicy')
        if config['roles'][name]['policy'] != policy:
            new_roles_config[name] = config['roles'][name]
            new_roles_config[name].update(new=False)
            outdated_roles.append(name)

    # create the group config
    new_groups_config = dict()
    for name, group in config.get('groups', dict()).items():
        for role in missing_roles:
            try:
                group['roles'].remove(role)
            except ValueError:
                pass
        new_groups_config[name] = create_group_changes(name,
                                                       group.get('users', []),
                                                       group.get('roles', []),
                                                       True if name in missing_groups else False)

    # create the user config
    new_user_config = create_user_changes(config_users)

    print(f"The following roles do not exist:", *missing_roles, sep='\n\t- ')
    print(f"The following roles will be created:", *new_roles, sep='\n\t- ')
    print(f"The following roles will be updated:", *outdated_roles, sep='\n\t- ')
    print(f"The following groups will be created:", *missing_groups, sep='\n\t- ')
    print("The following users will be created:",
          *[name for name, user in new_user_config.items() if user['new']],
          sep='\n\t- ')

    new_config = defaultdict(dict, users=new_user_config, groups=new_groups_config, roles=new_roles_config)

    print("The following changes will be made:")
    print(json.dumps(new_config, indent=4, sort_keys=True))
    return new_config


def create_user_changes(config_users):
    new_user_config = dict()
    for user, groups in config_users.items():
        try:
            new_user_config[user] = dict(
                groups=list(set(groups) - set(paginate(f'/v1/user/{user}/groups', 'groups'))),
                new=False
            )
        except requests.HTTPError:
            new_user_config[user] = dict(
                groups=groups,
                new=True
            )
    return new_user_config

def create_group_changes(group_name, users, roles, new):
    user_changes = defaultdict(list)
    role_changes = defaultdict(list)
    if not new:
        if group_name != 'user_default':
            current_users = set(paginate(f'/v1/group/{group_name}/users', 'users'))
            user_changes['add'] = list(set(users) - current_users)
            user_changes['remove'] = list(current_users - set(users))
        else:
            # special case for user_default. Since all users should be in this group, don't remove users.
            user_changes['add'] = []
            user_changes['remove'] = []

        current_roles = set(paginate(f'/v1/group/{group_name}/roles', 'roles'))
        role_changes['add'] = list(set(roles) - current_roles)
        role_changes['remove'] = list(current_roles - set(roles))
    else:
        user_changes['add'] = users
        role_changes['add'] = roles
    return dict(new=new, users=user_changes, roles=role_changes)


def setup_groups():
    with open(args.file, 'r') as fp:
        config = json.load(fp)

    new_config = make_config(config)
    if not args.dry_run:
        if not args.force:
            resp = input("Type 'yes' to confirm these changes: ")
            if resp.lower() != 'yes':
                exit(0)
        for name, params in new_config['roles'].items():
            update_roles(name, **params)
        for name, params in new_config['users'].items():
            update_user(name, params['new'])
        for name, params in new_config['groups'].items():
            update_group(name, **params)
    print("Done!")

if __name__ == "__main__":
    setup_groups()
    exit(0)
