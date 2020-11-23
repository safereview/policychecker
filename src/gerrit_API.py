#TODO: Add requirements to
#   - Support f strings 
#   - Add prerequisites
#       - pip install pygerrit2
#       - pip install PyNaCl

from pygerrit2 import GerritRestAPI, HTTPBasicAuth

from crypto_manager import *
from configs.gerrit_config import *
from utils import file_path_trim
from constants import *


# create the REST API call
def get_rest_api(username, password, url):
    return GerritRestAPI(url=url, auth=HTTPBasicAuth(username, password))


# Get access rights in a repository
def get_access_rights(project):
    '''
    TODO: Get access rights recursively
    Curreltly we assume the project is inherited from ALL_PROJECTS
    Ideally we get the access rights for the project
    Go back up until the ALL_PROJECTS
    '''
    project = ALL_PROJECTS
    endpoint = f"access/?project={project}"
    return REST.get(endpoint = endpoint)


# Get the head
def get_branch_head(project, branch):
    '''
    TODO
    - get the head of refs/meta/config directly by
    - updating the endpoint: f"projects/{project}/branches/{branch}"
    '''
    endpoint = f"projects/{project}/branches"
    result = REST.get(endpoint = endpoint)

    head = ''
    for res in result:
        if res['ref'] == branch:
            head = res['revision']

    if head == '':
        from sys import exit
        exit('Could not find the branch')

    return head


# Get a file content
def get_blob_content(project, head, fname):
    # Replace / in fname with %2F
    fname = file_path_trim(fname)
    # Form the endpoint
    endpoint = f"projects/{project}/commits/{head}/files/{fname}/content"
    return REST.get(endpoint = endpoint)


# List files per commit
def list_files(project, head):
    endpoint = f"projects/{project}/commits/{head}/files/"
    return REST.get(endpoint = endpoint)


# Get a list of groups
def list_groups():
    endpoint = f"groups/"
    return REST.get(endpoint = endpoint)


# Get info about a specific group
def get_group_info(gid):
    endpoint = f"groups/{gid}/detail"
    return REST.get(endpoint = endpoint)


# Get account id
def  get_account_id(account):
    endpoint = f"/accounts/?q=name:{account}"
    res = REST.get(endpoint = endpoint)
    return res[0]['_account_id']


# Get account info
def get_account_info(aid):
    endpoint = f"accounts/{aid}"
    return REST.get(endpoint = endpoint)


# Store the crp signature as review label on the server
def store_crp_signature(project, crp_signature):
    label = {
        'commit_message' : 'Code-Review-Policy',
        'values' : { '0' : crp_signature }
    }

    endpoint = f"projects/{project}/labels/Code-Review-Policy"
    return REST.put(endpoint = endpoint, data = label)


# Retrive the crp signature from the Gerrit server
def get_crp_signature(project):
    endpoint = f"projects/{project}/labels/Code-Review-Policy"
    review_label = REST.get(endpoint = endpoint)
    return review_label['values'][' 0'].encode()


# Form the code revivew policy
def form_crp(project):
    # TODO: Update the retrieval function
    # Now: Assume that any project inherits the
    # entire code review policy from ALL_PROJECTS
    # Later: Check if a project has its own crp

    #cb_head = get_branch_head(project, CONFIG_BRANCH)
    ap_head = get_branch_head(ALL_PROJECTS, CONFIG_BRANCH)

    rules_pl = ''
    project_config = ''
    groups = ''
    try:
        # rules.pl is not created by default. It is 
        # available only if there is a customized rule.
        rules_pl = get_blob_content(ALL_PROJECTS, ap_head, CONFIG_RULES)
        groups = get_blob_content(ALL_PROJECTS, ap_head, CONFIG_GROUP)
        project_config = get_blob_content(ALL_PROJECTS, ap_head, CONFIG_PROJECT)
    except Exception:
        pass

	#TODO:
	#	- Strip all strings
	# 	-DOC: The CRP format is as follows:
    crp = f"{rules_pl}{project_config}{groups}"
    return crp.encode()


if __name__ == '__main__':
    # Gerrit REST API call
    REST = get_rest_api(USER, PASS, url)

	# Form the CRP
    crp = form_crp(project)
    print(crp)

	# Sign and Store the CRP
    crp_signature, verify_key = sign_crp(crp)
    result = store_crp_signature(project, crp_signature)
    print(result)

    # Retrieve and Verify CRP
    retrieved_signature = get_crp_signature(project)
    result = verify_signature(crp, retrieved_signature, verify_key)
    print(result)