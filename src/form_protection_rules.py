from github import Github
from configs.github_config import *
import json
import requests as re

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
        Require linear history
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
    response = re.get(f"https://api.github.com/repos/{user}/{repo}/branches/{branch_name}/protection", headers={'Authorization': f"token {TOKEN}"})
    if(response.ok):
        return json.loads(response.content) # Returns the content of the json reply if "ok"

# Functions to get individual branch protections
#============================================================================================================================================

# Protect matching branches
#---------------------------------------------------------------------------

def require_pull_request_reviews(branch):
    return branch.get_required_pull_request_reviews()

    #dev branch and check the branch
    # --> Got got to issue with the require pull request review
    # https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#get-branch-protection
    # We may have an issue and that will be taken care of later

    # count, require_code.., required, status checks, 
    # Filled out in Dictioanry
    # count = branch.get_required_pull_request_reviews().required_approving_review_count
    # print(f"\t\t\tcount:{count}\n")
    try:
        return branch.get_required_pull_request_reviews() # (ret) RequiredPullRequestReviews(url="https://api.github.com/repos/AOrps/rebxlance/branches/dev/protection/required_pull_request_reviews", require_code_owner_reviews=False, dismiss_stale_reviews=False)
    except Exception as e:
        print(e)
        return False



def require_status_checks(branch):
    return branch.get_required_status_checks()
    # try:
    #     # print(branch.get_required_status_checks())
    #     status_checks_enabled = branch.get_required_status_checks()
    # except Exception as e:
    #     print(f"{e}: {type(e)} \t\t {str(e)}")
    #     if( str(e) == '404 {"message": "Required status checks not enabled", "documentation_url": "https://docs.github.com/rest/reference/repos#get-status-checks-protection"}'):
    #         print("cdas")
    #         return False

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


# Driver
#============================================================================================================================================

if __name__ == '__main__':
    REST = Github(TOKEN)

    dev_branch = get_branch(REST, USER, repo, "dev")

    pull_request_review = require_pull_request_reviews(dev_branch)
    require_stat_check = "A" #require_status_checks(dev_branch)
    sign = signed_commits(dev_branch)
    admin_enforce = include_admin(dev_branch)

    print(f"dev_branch:{dev_branch}\n")
    print(f"""\
Require_pull_request_rev:\t{pull_request_review}
Require_status+checks:\t\t{require_stat_check}
Require_signed_commits:\t\t{sign}
Include_Administrators:\t\t{admin_enforce}
"""
        )   # -> Require_signed_commits: True

# When done, update PR and let Hammad know
# Ensure that Hammad is updated with current progress and jazzy stuff issues when needed
    print(allow_force_pushes(USER, repo, branch_name="dev"))


    # list_all_branch_protections(REST, USER, repo)

