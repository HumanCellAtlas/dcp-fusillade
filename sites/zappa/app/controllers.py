import bisect
import copy
import urllib
from datetime import datetime
import sys
import os
import json
import os.path
import requests
import boto3
from .errors import GitlabError, EnvironmentVariableError, MalformedFusilladeConfigError

sm_client = boto3.client('secretsmanager')

class FileController:
    def __init__(self, file_data, file_path):
        self.file_data = file_data
        self.file_path = file_path
        self.group_data = json.loads(self.file_data)
        self.updated_data = None

    def add_user_to_groups(self, user: str, groups: list):
        """returns a new group_dictionary with user added into requested groups"""
        modified_data = copy.deepcopy(self.group_data)
        for group in groups:

            # Before we get the group key or the users key, make sure they are present
            try:
                assert group in modified_data.get("groups")
            except AssertionError:
                raise MalformedFusilladeConfigError(
                    f'group "{group}" not found in {modified_data.get("groups")} '
                )
            group_data = modified_data["groups"][group]
            try:
                assert "users" in group_data
            except AssertionError:
                group_data['users'] = []
            users_in_current_group = group_data["users"]

            # Insert the user into the users list
            if user not in users_in_current_group:
                bisect.insort(users_in_current_group, user)

            # Update modified copy
            modified_data["groups"][group]["users"] = users_in_current_group

        return modified_data


class GitlabController:
    def __init__(self, config):
        # Also see config.py for how these are defined
        # Base config
        self.gitlab_api_url = config.GITLAB_API_URL
        self.gitlab_project_id = config.GITLAB_PROJECT_ID
        
        # Local config
        self.access_token = config.GITLAB_API_TOKEN

        # Derived variables
        self.access_headers = {"PRIVATE-TOKEN": self.access_token}
        self.ci_branch = self._get_ci_branch(config)
        self.timestamp = datetime.today().strftime("%Y%m%d-%H%M%S")
        self._new_branch_name = f"{self.ci_branch}-{self.timestamp}"

    def get_file_from_repo(self, file_path: os.PathLike) -> requests.Response:
        """ get a file from a repo, file_path is from root of repository"""
        encoded_file_path = urllib.parse.quote(file_path, safe="")
        gl_file_path = (
            f"/projects/{self.gitlab_project_id}/repository/files/{encoded_file_path}/raw"
        )
        url = f"{self.gitlab_api_url}{gl_file_path}"
        parameters = {"ref": self.ci_branch}
        resp = requests.get(url=url, headers=self.access_headers, params=parameters)
        return resp

    def create_branch(self, service_account_name):
        gl_branch_path = f"/projects/{self.gitlab_project_id}/repository/branches"
        parameters = {"branch": self._new_branch_name, "ref": self.ci_branch}
        url = f"{self.gitlab_api_url}{gl_branch_path}"
        try:
            r = requests.post(url=url, headers=self.access_headers, params=parameters)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            msg = "Error calling Gitlab URL to commit proposed changes "
            msg += f"to branch ({self._new_branch_name}): "
            msg += str(err)
            raise GitlabError(msg)
        return r.json()

    # https://docs.gitlab.com/ee/api/commits.html
    def commit_changes_(self, service_account_name, modified_file: FileController):
        gl_commit_path = f"/projects/{self.gitlab_project_id}/repository/commits"
        commit_message = f"This commit was created automatically by DCP-Fusillade"
        actions = [
            {
                "action": "update",
                "file_path": modified_file.file_path,
                "content": json.dumps(modified_file.updated_data, indent=2),
            }
        ]
        payload = {
            "branch": self._new_branch_name,
            "start_branch": self.ci_branch,
            "commit_message": commit_message,
            "force": False,
            "actions": actions,
        }
        url = f"{self.gitlab_api_url}{gl_commit_path}"
        headers = self.access_headers
        headers["Content-Type"] = "application/json"
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload))
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            msg = "Error calling Gitlab URL to commit proposed changes "
            msg += f"to branch ({self._new_branch_name}): "
            msg += str(err)
            raise GitlabError(msg)
        return r.json()

    def create_merge_request(self):
        gl_merge_path = f"/projects/{self.gitlab_project_id}/merge_requests"
        payload = {
            "id": self.gitlab_project_id,
            "source_branch": self._new_branch_name,
            "target_branch": self.ci_branch,
            "title": f"Request to add user to groups",
            "description": "This pull request was opened automatically.",
            "remove_source_branch": True,
            "allow_collaboration": True,
            "squash": True,
        }
        url = f"{self.gitlab_api_url}{gl_merge_path}"
        headers = self.access_headers
        headers["Content-Type"] = "application/json"
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload))
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            exit(1)
        return r.json()

    @staticmethod
    def _get_ci_branch(config):
        stage = config.FUS_DEPLOYMENT_STAGE
        # Keep it simple:
        # integration (webapp) -> integration (fusillade)
        # staging (webapp) -> staging (fusillade)
        # dev (webapp) -> dev (fusillade)
        # testing (webapp) -> testing (fusillade)
        if stage not in ['integration', 'staging', 'dev', 'testing']:
            raise GitlabError(f"Error: specified target stage {stage} does not exist!")
        return stage

