from github import Github
from configs.github_config import *
import json
import requests
import re


# Most recent 'Accept' : https://developer.github.com/changes/2018-03-16-protected-branches-required-approving-reviews/
# TODO
"""
## DOCS: https://github.com/PyGithub/PyGithub/blob/master/github/Branch.pyi

Understand how the data should be printed to the screen
    # Get list of branches
    # Get a specific branch
        Get Require Pull request reviews before merging
            --> Required Approving reviews => num
            Dismiss stale pull request approvals when new commits are pushed
            Require review from Code Owners
        #Require Status Checks to pass before merging
            Require branch to be up to date before merging
        # Require Signed Commits
        # Require linear history
        # Include administrators (Enfore admin)
"""

# Helper Functions
#============================================================================================================================================

def get_branches(g, user, repo):
	repo = g.get_repo(f"{user}/{repo}")	
	return list(repo.get_branches())

def get_branch(g, user, repo, branch):
	return g.get_repo(f"{user}/{repo}").get_branch(branch)

# Reusable Boiler Plate Code to get some
def re_boiler(user, repo, branch_name):
    response = requests.get(f"https://api.github.com/repos/{user}/{repo}/branches/{branch_name}/protection", headers={'Authorization': f"token {TOKEN}"})
    if(response.ok):
        return json.loads(response.content) # Returns the content of the json reply if "ok"

# Functions to get individual branch protections
#============================================================================================================================================

# Protect matching branches
#---------------------------------------------------------------------------

def require_pull_request_reviews(user, repo, branch_name):
    try:
        response = requests.get(f"https://api.github.com/repos/{user}/{repo}/branches/{branch_name}/protection", headers={'Authorization': f"token {TOKEN}","Accept" : "application/vnd.github.luke-cage-preview+json"})
        if(response.ok):
            resp_dump = json.dumps(response.json())  # str of the json object
            dismiss_stale = bool(re.search('"dismiss_stale_reviews": true', resp_dump)) 
            require_codeowners = bool(re.search('"require_code_owner_reviews": true', resp_dump))
            review_count = int(re.search('"required_approving_review_count": \d', resp_dump).group()[-1]) # gets the number count

            return "{True, dismiss_stale_pull_requests: %r, require_review_from_codeowners: %r, required_review_count: %d}" % (dismiss_stale, require_codeowners, review_count)
        return True
        
    except KeyError:
        return False


def require_status_checks(g, user, repo, branch_name):
    response = requests.get(f"https://api.github.com/repos/{user}/{repo}/branches/{branch_name}", headers={'Authorization': f"token {TOKEN}"})
    if(response.ok):
        stat_check_prot = json.loads(response.content)["protection"]["required_status_checks"]["enforcement_level"] # requests for branch to determine if it is enabled
        if(stat_check_prot == "off"):
            return False
        else:
            branch = get_branch(g, user, repo, branch_name)
            check_strict = re.search("strict=True",str(branch.get_required_status_checks()))
            if(check_strict == None):
                return "{True, strict: False}"
            return "{True, strict: True}"

def signed_commits(branch):
    return branch.get_required_signatures()

def linear_history(user, repo, branch_name):
    response = re_boiler(user, repo, branch_name)
    return response["required_linear_history"]['enabled']

def include_admin(branch):
    return branch.get_admin_enforcement()

# Rules Applied to everyone including administrators
#---------------------------------------------------------------------------
def allow_force_pushes(user, repo, branch_name):
    response = re_boiler(user, repo, branch_name)
    return response["allow_deletions"]['enabled']

def allow_deletions(user, repo, branch_name):
    response = re_boiler(user, repo, branch_name)
    return response["allow_deletions"]['enabled']


# Functions to get all of the protections
#============================================================================================================================================
def get_full_branch_protection(g, user, repo, branch_name):
    pass


def list_all_branch_protections(g, user, repo):
    branches = g.get_repo(f"{user}/{repo}").get_branches()
    print(branches)


def make_dictionary():
    pass

# Driver
#============================================================================================================================================

if __name__ == '__main__':
    REST = Github(TOKEN)

    branch_name = "dev"

    dev_branch = get_branch(REST, USER, repo, branch_name)

    # Func Calls
    pull_request_review = require_pull_request_reviews(USER, repo, branch_name)
    require_stat_check = require_status_checks(REST, USER, repo, branch_name)      
    sign = signed_commits(dev_branch)
    linear = linear_history(USER, repo,branch_name)
    admin_enforce = include_admin(dev_branch)
    fpush = allow_force_pushes(USER, repo, branch_name)
    deletions = allow_deletions(USER, repo, branch_name)


    # prints
    print(f"dev_branch:{dev_branch}\n")
    print(f"""\
require_pull_request_rev:\t{pull_request_review}
require_status+checks:\t\t{require_stat_check}
require_signed_commits:\t\t{sign}
require_linear_history:\t\t{linear}
include_administrators:\t\t{admin_enforce}
allow_force_pushes:\t\t{fpush}
allow_deletions:\t\t{deletions}
"""
        )   # -> Require_signed_commits: True

# When done, update PR and let Hammad know
# Ensure that Hammad is updated with current progress and jazzy stuff issues when needed


    # list_all_branch_protections(REST, USER, repo)

