from github import Github
from configs.github_config import *

# TODO
"""
Understand how the data should be printed to the screen

"""

def get_branch(g, user, repo, branch):
	return g.get_repo(f"{user}/{repo}").get_branch(branch)

def signed_commits(branch):
    return branch.get_required_signatures()

def enforce_admin(branch):
    return branch.get_admin_enforcement()



def get_full_branch_protection(g, user, repo, branch):
    pass


def list_all_branch_protections(g, user, repo):
    branches = g.get_repo(f"{user}/{repo}").get_branches()
    print(branches)




if __name__ == '__main__':
    REST = Github(TOKEN)

    dev_branch = get_branch(REST, USER, repo, "dev")
    sign = signed_commits(dev_branch)
    admin_enforce = enforce_admin(dev_branch)

    print(f"dev_branch:{dev_branch}\n")
    print(f"Sign:{sign}\nAdmin_enfore:{admin_enforce}")

    list_all_branch_protections(REST, USER, repo)