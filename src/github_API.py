#TODO: Add requirements to support f strings 

# Install: $ pip install PyGithub
from github import Github
from configs.github_config import *
from crypto_manager import *


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

# Get the crp signature from the the status check
def get_crp_signature_remote(status_check):
	return status_check.description

def get_crp_signature_local():
	return crp_signature

# Get Protection Status of that Branch
def get_branch_protection_status(g, user, repo, branch):
	# The Protection Status will either go to True or an Error, must debug for future 
	repo_name = "{}/{}".format(user, repo)
	try:
		branch = g.get_repo(repo_name).get_branch(branch)
		branch_prot = branch.protected
		if( isinstance(branch_prot, bool) ):
			return True
		else:
			return False  
	except:
		return False

	

# See required status checks of branch
def get_required_branch_protection_checks(g, user, repo, branch):
	repo_name = "{}/{}".format(user, repo)
	branch =  g.get_repo(repo_name).get_branch(branch)
	return branch.get_required_status_checks()


# Get file content
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

def store_crp_signature(g, user, repo, sha, crp_sig):
	repo_name = "{}/{}".format(user, repo)
	repo = g.get_repo(repo_name)
	res = repo.get_commit(sha=sha).create_status(
		state = "success",
		context = "CODE_REVIEW_POLICY",
		description = crp_sig,
	)
	return res

# Compare the signatures of the crp
cmp_crp = lambda local_crp, remote_crp: True if local_crp == remote_crp else False


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

	# Get local crp signature from status check
	local_crp_sig = get_crp_signature_local()
	print(local_crp_sig)  

	# Retrieve crp_signature from API
	remote_crp_sig = get_crp_signature_remote(crp_sig)
	print(remote_crp_sig)

	# Retrieve CRP, Sign it, Store the signature in repo
	valid_crp = cmp_crp(local_crp_sig, remote_crp_sig)
	store_crp_signature(REST, USER, repo, 'HEAD', local_crp_sig)


	
	if(valid_crp):
		print("The local hash is equal to the remote hash.")
	else:
		print("Data has been tempered with.")