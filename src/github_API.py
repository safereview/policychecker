#TODO: Add requirements to support f strings 

# Install: $ pip install PyGithub
from github import Github
from configs.github_config import *


# Get a list of branches
def get_branches(g, user, repo):
	repo_name = "{}/{}".format(user, repo)
	repo = g.get_repo(repo_name)	
	return list(repo.get_branches())


# Get info about a branch
def get_branch(g, user, repo, branch):
	repo_name = "{}/{}".format(user, repo)
	return g.get_repo(repo_name).get_branch(branch)


# Get the head of a branch
def get_branch_head(g, user, repo, branch):
	repo_name = "{}/{}".format(user, repo)
	branch = g.get_repo(repo_name).get_branch(branch)
	return branch.commit


# Gef file content
def get_blob_content(g, user, repo, path):
	repo_name = "{}/{}".format(user, repo)
	return g.get_repo(repo_name).get_contents(path).decoded_content


# Create a status check
def create_status_check(g, user, repo, sha):
	repo_name = "{}/{}".format(user, repo)
	repo = g.get_repo(repo_name)
	res = repo.get_commit(sha=sha).create_status(
		state = "success",
		#target_url="https://myURL.com",
		context = "CODE_REVIEW_POLICY",
		description = crp_signature
	)
	return res


if __name__ == '__main__':
	# GitHub REST API call
	REST = Github(TOKEN)

	# Try out some APIs
	branches = get_branches (REST, USER, repo)
	branch = get_branch (REST, USER, repo, "master")
	branch_head = get_branch_head(REST, USER, repo, "master")
	crp_sig = create_status_check(REST, USER, repo, 'HEAD')

	# Print out results
	print(branch_head)
	print(branch)
	print(branches)
	print(crp_sig)
