#TODO:Add prerequisites
#   - pip install pygerrit2
#   - pip install PyNaCl

from pygerrit2 import GerritRestAPI, HTTPBasicAuth

from configs.gerrit_config import *
from constants import *
from crypto_manager import *
from utils import file_path_trim


# create the REST API call
def get_rest_api(username, password, url):
    return GerritRestAPI(url=url, auth=HTTPBasicAuth(username, password))


# Get access rights in a repository
def get_access_rights(g, project):
    '''
    TODO: Get access rights recursively
    Curreltly we assume the project is inherited from ALL_PROJECTS
    Ideally we get the access rights for the project
    Go back up until the ALL_PROJECTS
    '''
    project = ALL_PROJECTS
    endpoint = f"access/?project={project}"
    return g.get(endpoint = endpoint)


# Get the head
def _get_branch_head(g, project, branch):
    '''
    TODO
    - get the head of refs/meta/config directly by
    - updating the endpoint: f"projects/{project}/branches/{branch}"
    '''
    endpoint = f"projects/{project}/branches"
    result = g.get(endpoint = endpoint)

    head = ''
    for res in result:
        if res['ref'] == branch:
            head = res['revision']

    if head == '':
        from sys import exit
        exit('Could not find the branch')

    return head


# Get a file content
def get_blob_content(g, project, head, fname):
    # Replace / in fname with %2F
    fname = file_path_trim(fname)
    # Form the endpoint
    endpoint = f"projects/{project}/commits/{head}/files/{fname}/content"
    return g.get(endpoint = endpoint)


# List files per commit
def list_files(g, project, head):
    endpoint = f"projects/{project}/commits/{head}/files/"
    return g.get(endpoint = endpoint)


# Find the groups that a committer is in
def find_group_membership(committer_name, committer_email):
    # Get all of the groups in the Gerrit project
    groups = list_groups()
    committers_groups = []

    for g in groups:
        g_id = groups[g]['group_id']
        for member in get_group_info(g_id)['members']:
            if (
                member['name'] == committer_name
                and member['email'] == committer_email
            ):
                committers_groups.append(g)
    
    return committers_groups


# Get a list of groups
def list_groups(g):
    endpoint = f"groups/"
    return g.get(endpoint = endpoint)


# Get info about a specific group
def get_group_info(g, gid):
    endpoint = f"groups/{gid}/detail"
    return g.get(endpoint = endpoint)


# Get account id
def  get_account_id(g, account):
    endpoint = f"/accounts/?q=name:{account}"
    res = g.get(endpoint = endpoint)
    return res[0]['_account_id']


# Get account info
def get_account_info(g, aid):
    endpoint = f"accounts/{aid}"
    return g.get(endpoint = endpoint)


# Store the crp signature as review label on the server
def store_crp_signature(g, project, crp_signature):
    label = {
        'commit_message' : 'Code-Review-Policy',
        'values' : { '0' : crp_signature }
    }

    endpoint = f"projects/{project}/labels/Code-Review-Policy"
    return g.put(endpoint = endpoint, data = label)


# Retrive the crp signature from the Gerrit server
def _get_crp_signature(g, project):
    endpoint = f"projects/{project}/labels/Code-Review-Policy"
    review_label = g.get(endpoint = endpoint)
    return review_label['values'][' 0'].encode()


# Form the code revivew policy
def _form_gerrit_crp(g, project):
    # FIXME: Update the retrieval function
    # Now: Assume that any project inherits the
    # entire code review policy from ALL_PROJECTS
    # Later: Check if a project has its own crp

    #cb_head = _get_branch_head(project, CONFIG_BRANCH)
    ap_head = _get_branch_head(g, ALL_PROJECTS, CONFIG_BRANCH)

    rules_pl = ''
    project_config = ''
    groups = ''
    try:
        # rules.pl is not created by default. It is
        # available only if there is a customized rule.
        rules_pl = get_blob_content(g, ALL_PROJECTS, ap_head, CONFIG_RULES)
        groups = get_blob_content(g, ALL_PROJECTS, ap_head, CONFIG_GROUP)
        project_config = get_blob_content(g, ALL_PROJECTS, ap_head, CONFIG_PROJECT)
    except Exception:
        pass

	#TODO: Add DOC for the CRP format
    crp = (
        f"RULES\n{rules_pl}"
        f"\nPROJECTCONFIG\n{project_config}"
        f"\nGROUPS\n{groups}"
    )
    return crp.encode()


# Validate the GitHub repo's code review policy
def validate_gerrit_crp(repo, branch):
	# Gerrit REST API call
	REST = get_rest_api(USER, PASS, url)

	# Form the CRP
	crp = _form_gerrit_crp(REST, repo)

    # TODO: Remove this part
	# Sign and Store the CRP
	crp_signature, verify_key = ed25519_sign_message(crp)
	store_crp_signature(REST, repo, crp_signature)

	# Retrieve and Verify CRP
	retrieved_signature = _get_crp_signature(REST, repo)
	return crp, verify_signature(crp, retrieved_signature, verify_key)
