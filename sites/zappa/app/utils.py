import json
from .controllers import GitlabController, FileController


gitlab = GitlabController()


def get_groups():
    group_file_path = "config/groups.json"
    resp = gitlab.get_file_from_repo(group_file_path)
    group_data = json.loads(resp.text).get('groups')
    groups_in_file = []
    if group_data is not None:
        groups_in_file = [k for k in group_data if k != "user_default"]
    else:
        raise GitlabError("Error: could not get group info from Gitlab")
    return groups_in_file


def add_user_to_group(service_account:str, groups:list):
    group_file_path = "config/groups.json"
    resp = gitlab.get_file_from_repo(group_file_path)
    groups_file = FileController(resp.text, group_file_path)
    # modify groups.json file thats committed currently
    groups_file.updated_data = groups_file.add_user_to_groups(service_account, groups)
    # create new branch, push changes
    commit_changes_json = gitlab.commit_changes_(service_account,groups_file)
    # create merge request with new branch
    merge_request_json = gitlab.create_merge_request()
    # TODO alerts
