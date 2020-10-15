#TODO: Add requirements to support f strings 

# Install: $ pip install pygerrit2
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from gerrit_config import *
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

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

# Get a Git blog object
def get_blob_content(project, head, fname):
    endpoint = f"projects/{project}/commits/{head}/files/{fname}"
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


# Create a new code review label
def create_review_label(project, crp_signature):

    label = {
        'commit_message' : 'Code-Review-Policy',
        'values' : { '0' : crp_signature }
    }

    endpoint = f"projects/{project}/labels/Code-Review-Policy"
    return REST.put(endpoint = endpoint, data = label)


def get_signature(project):
    endpoint = f"projects/{project}/labels/Code-Review-Policy"
    review_label = REST.get(endpoint = endpoint)
    return review_label['values'][' 0'].encode()


# Get the code review policy for the project
def get_code_review_policy(project):
    project_bh = get_branch_head(project, CONFIG_BRANCH)
    rules_pl = get_blob_content(project, project_bh, 'rules.pl')
    project_config = get_blob_content(project, project_bh, CONFIG_FILE)
    all_projects_bh = get_branch_head(ALL_PROJECTS, CONFIG_BRANCH)
    groups = get_blob_content(ALL_PROJECTS, all_projects_bh, CONFIG_GROUP)
    crp = rules_pl + project_config + groups
    return crp.encode()

    
if __name__ == '__main__':
    # Gerrit REST API call
    REST = get_rest_api(USER, PASS, url)

    # Prepare pprint
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    # Get a list of groups on the server
    groups = list_groups()
    pp.pprint(groups)

    # Get members in a group
    group = get_group_info('1')
    print(group['members'])

    # Get account info using the username (e.g. 'r1')
    account = get_account_info(get_account_id('r1'))
    print(account)

    # Get head of the branch
    branch_head = get_branch_head(project, CONFIG_BRANCH)
    print(branch_head)

    # Get info about the access rights
    access_rights = get_access_rights(project)
    access_rights = access_rights["All-Projects"]
    # Print out all items in access rights
    for item in access_rights:
        print(item)

    # Print out groups listed in access rights
    pp.pprint(access_rights['groups'])

    # Print out permissions listed in access rights
    pp.pprint(access_rights['local'])

    # Sign the CRP and store the signature in repo
    signing_key = SigningKey.generate()
    crp = get_code_review_policy(project)
    crp_signature = signing_key.sign(crp, encoder=HexEncoder).decode()
    create_review_label(project, crp_signature)

    # Retrieve signature from repo and verify
    verify_key = signing_key.verify_key
    retrieved_signature = get_signature(project)
    try:
        verify_key.verify(retrieved_signature, encoder=HexEncoder)
        print('Verified Signature')
    except BadSignatureError:
        print('Bad Signature')
