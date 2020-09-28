#TODO: Add requirements to support f strings 

# Install: $ pip install pygerrit2
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from gerrit_config import *


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
