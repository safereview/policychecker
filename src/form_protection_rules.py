from github import Github
from configs.github_config import *

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
def get_branches(g, user, repo):
	repo = g.get_repo(f"{user}/{repo}")	
	return list(repo.get_branches())

def get_branch(g, user, repo, branch):
	return g.get_repo(f"{user}/{repo}").get_branch(branch)


def require_pull_request_reviews(branch):
    count = branch.get_required_pull_request_reviews().required_approving_review_count
    print(f"\t\t\tcount:{count}\n")
    return branch.get_required_pull_request_reviews() # (ret) RequiredPullRequestReviews(url="https://api.github.com/repos/AOrps/rebxlance/branches/dev/protection/required_pull_request_reviews", require_code_owner_reviews=False, dismiss_stale_reviews=False)

def require_status_checks(branch):
    status_checks_enabled = ""
    try:
        status_checks_enabled = branch.get_required_status_checks()
    except Exception:
        status_checks_enabled = "False"
        return False

    return status_checks_enabled

def signed_commits(branch):
    return branch.get_required_signatures()

def include_admin(branch):
    return branch.get_admin_enforcement()


def get_full_branch_protection(g, user, repo, branch):
    pass


def list_all_branch_protections(g, user, repo):
    branches = g.get_repo(f"{user}/{repo}").get_branches()
    print(branches)




if __name__ == '__main__':
    REST = Github(TOKEN)

    dev_branch = get_branch(REST, USER, repo, "dev")

    pull_request_review = require_pull_request_reviews(dev_branch)
    require_stat_check = require_status_checks(dev_branch)
    sign = signed_commits(dev_branch)
    admin_enforce = include_admin(dev_branch)

    print(f"dev_branch:{dev_branch}\n")
    print(f"""\
Require pull request rev:\t{pull_request_review}
Require status checks:\t{require_stat_check}
Require signed commits:\t{sign}
Include Administrators:\t{admin_enforce}"""
        )

    # list_all_branch_protections(REST, USER, repo)

