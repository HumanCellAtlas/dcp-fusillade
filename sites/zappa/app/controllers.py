import bisect
import copy
import urllib
import sys
import os
import json
import requests
from datetime import datetime

from .errors import GitlabError, EnvironmentVariableError, MalformedFusilladeConfigError


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
            try:
                assert group in modified_data.get("groups")
            except AssertionError:
                raise MalformedFusilladeConfigError(f'group "{group}" not found in {modified_data.get("groups")} ')
            group_data = modified_data['groups'][group]
            users_in_current_group = group_data.get('users',[])
            if user not in users_in_current_group:
                bisect.insort(users_in_current_group, user)
        return modified_data

class GitlabController:

    def __init__(self):
        self.access_token = os.getenv('DCP_FUS_GL_TOKEN')
        self.gitlab_api_url  = os.getenv("GITLAB_API_URL")
        self.access_headers = {"PRIVATE-TOKEN": self.access_token}
        self.gitlab_project_id = os.getenv("GITLAB_PROJECT_ID")
        self.ci_branch = self._get_ci_branch()
        self.timestamp = datetime.today().strftime('%Y%m%d-%H%M%S')
        self._new_branch_name = f'{self.ci_branch}-{self.timestamp}'

    def get_file_from_repo(self, file_path: os.PathLike) -> requests.Response:
        """ get a file from a repo, file_path is from root of repository"""
        encoded_file_path = urllib.parse.quote(file_path, safe='')
        gl_file_path = f'/projects/{self.gitlab_project_id}/repository/files/{encoded_file_path}/raw'
        url = f'{self.gitlab_api_url}{gl_file_path}'
        parameters = {"ref": self.ci_branch}
        resp = requests.get(url=url, headers=self.access_headers, params=parameters)
        return resp

    # https://docs.gitlab.com/ee/api/commits.html
    def commit_changes_(self, service_account_name, modified_file: FileController):
        gl_commit_path = f'/projects/{self.gitlab_project_id}/repository/commits'
        commit_message = f'This commit was created from DCP-Fusillade'
        actions = [{'action': 'update',
                    'file_path': modified_file.file_path,
                    'content': json.dumps(modified_file.updated_data, indent=4)}]
        # Note this might be able to be reduced to 1 api call to gitlab.
        # may need to set force to true.
        payload = {'branch': self._new_branch_name,
                   'start_branch': self.ci_branch,
                   'commit_message': commit_message,
                   'force': False,
                   'actions': actions}
        url = f'{self.gitlab_api_url}{gl_commit_path}'
        headers = self.access_headers
        headers['Content-Type']= 'application/json'
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload))
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            msg = "Error calling Gitlab URL to commit propposed changes "
            msg += f"to branch ({self._new_branch_name}): "
            msg += str(err)
            raise GitlabError(msg)
        return r.json()

    def create_merge_request(self):
        gl_merge_path = f"/projects/{self.gitlab_project_id}/merge_requests"
        payload = {"id": self.gitlab_project_id,
                   "source_branch": self._new_branch_name,
                   "target_branch": self.ci_branch,
                   "title": f"Request to add user to groups",
                   "description": "This pull request was opened automatically.",
                   "remove_source_branch": True,
                   "allow_collaboration": True,
                   "squash": True}
        url = f'{self.gitlab_api_url}{gl_merge_path}'
        headers = self.access_headers
        headers['Content-Type'] = 'application/json'
        try:
            r = requests.post(url, headers=headers, data=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            msg = f"Error calling Gitlab URL to commit changes: {url} "
            msg += "Error Message: "
            msg += str(err)
            raise GitlabError(msg)
        return r.json()

    @staticmethod
    def _get_ci_branch():
        stage = os.getenv('FUS_DEPLOYMENT_STAGE')
        return stage if stage != 'dev' else 'master'
