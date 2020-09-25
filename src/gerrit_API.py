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


if __name__ == '__main__':
    # Gerrit REST API call
    REST = get_rest_api(USER, PASS, url)

    # Try out some APIs
    access_rights = get_access_rights(project)
    branch_head = get_branch_head(project, CONFIG_BRANCH)

    # Print out results
    print(branch_head)
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(access_rights)