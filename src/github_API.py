#TODO:Add prerequisites
# 	- pip install PyGithub
from github import Github
import json
import requests
import re 

from configs.github_config import *
from constants import *
from crypto_manager import *
from collections import defaultdict


HEADERS = {
	'Authorization': f"token {TOKEN}",
	"Accept" : "application/vnd.github.zzzax-preview+json"
}

POST_HEADERS = {
	'Authorization': f"token {TOKEN}",
	"Accept" : "application/vnd.github.v3+json"
}

PRT_HEADERS = {
	'Authorization': f"token {TOKEN}",
	"Accept" : "application/vnd.github.luke-cage-preview+json"
}

# Form a get request
def get_request(endpoint, headers = HEADERS):
	try:
		return requests.get(f"{GITHUB_API}/{endpoint}", headers = headers)
	except Exception:
		pass


# Get info about one branch
def get_branch(g, user, repo, branch):
	repo_name = f"{user}/{repo}"
	return g.get_repo(repo_name).get_branch(branch)


# Get file content
def get_blob_content(g, user, repo, path):
	endpoint = f"{user}/{repo}/contents/{path}"
	response = get_request(endpoint)
	response = json.loads(response.content)
	return requests.get(response["download_url"]).content


# Store the crp signature as review label on the server
def store_crp_signature(g, user, repo, sha, signature):
	repo_name = "{}/{}".format(user, repo)
	repo = g.get_repo(repo_name)
	res = repo.get_commit(sha=sha).create_status(
		state = "success",
		#target_url="https://myURL.com",
		context = "CODE_REVIEW_POLICY",
		description = signature
	)
	return res


# Retrive the crp signature from the Gerrit server
def get_crp_signature(g, user, repo, sha):
	endpoint = f"{user}/{repo}/statuses/{sha}"
	response = get_request(endpoint)
	json_load = json.loads(response.content)
	return json_load[0]["description"]


# Get branch protection rules
def get_branch_protection_rules(g, user, repo, branch_name):
	# NOTE: The branch protection API is in a preview period
	# During this period, we use different ACCEPT HEADERS per use case
	# See details @ 
	# https://docs.github.com/en/rest/reference/repos#get-branch-protection
	# https://docs.github.com/en/rest/reference/repos#update-branch-protection-preview-notices

	# Check if 'Require pull request reviews before merging' is enabled
	# If so, then
	# - Get the minimum number of approvals
	# - Check if 'Dismiss stale pull request' is enabled
	# - Check if 'Require review from Code Owners' is enabled
	# - Check for additional rules:
	# 		- if commits must br signed
	# 		- if admins must follow the CRP

	endpoint = f"{user}/{repo}/branches/{branch_name}/protection"
	try:
		response = get_request(endpoint, PRT_HEADERS)
	except Exception:
		exit(f"{branch_name} branch has no protection rules!")

	result = dict()
	if(response.ok):
		rules = json.loads(response.content)
		# Check if 'required_pull_request_reviews' is enabled
		if GITHUB_REQURIED_REVIEWS not in rules.keys():
			result[GITHUB_REQURIED_REVIEWS] = False
		else:
			result[GITHUB_REQURIED_REVIEWS] = True

			# Get the min number of required approving reviews
			result[GITHUB_MIN_APPROALS] = \
				rules[GITHUB_REQURIED_REVIEWS][GITHUB_MIN_APPROALS]

			# Check if stale reviews must be dissmissed
			result[GITHUB_DISMISS_STALE_REVIEWS] = \
				rules[GITHUB_REQURIED_REVIEWS][GITHUB_DISMISS_STALE_REVIEWS]

			# Check if reviews from the code owner is required
			result[GITHUB_CODE_OWNER_REVIEWS] = \
				rules[GITHUB_REQURIED_REVIEWS][GITHUB_CODE_OWNER_REVIEWS]

		# Check for additional rules:
		# 1) require_signed_commits: 
		# 		- We must use another HEADER to get the information
		# 		- However, we ignore this check since 
		# 			PolicyChecker assumes all commists are signed
		# 2) include_administrators
		#result['require_signed_commits'] = rules['required_signatures']['enabled']
		result[GITHUB_ENFORCE_ADMIN] = rules[GITHUB_ENFORCE_ADMIN]['enabled']

	return result


	# Form the code revivew policy
def form_github_crp(g, user, repo, branch_name):

	#Github CRP
	gitattributes = ""
	codeowners = ""
	protection_rules = {}

	try:
		#TODO: Check if we need to capture the entire gitattributes
		gitattributes = get_blob_content(g, user, repo, GITATTRIBUTES)
	except Exception:
		#print("error in gitattr")
		pass

	try:
		codeowners = get_blob_content(g, user, repo, CODEOWNERS)
	except Exception:
		#print("error in codeowners")
		pass

	try:
		protection_rules = get_branch_protection_rules(g, user, repo, branch_name)
	except Exception:
		#print("error in protections")
		pass

	#TODO: Add DOC for the CRP format
	crp = f"{protection_rules}{codeowners}{gitattributes}"
	return crp.encode()


# Validate the GitHub repo's code review policy
def validate_github_crp(repo, branch):
	# GitHub REST API call
	REST = Github(TOKEN)

	# Form the CRP
	crp = form_github_crp(REST, USER, repo, branch)
	print(crp)

    # TODO: Remove this part
	# Sign and Store the CRP
	crp_signature, verify_key = ed25519_sign_message(crp)
	store_crp_signature(REST, USER, repo, 'HEAD', crp_signature)

	# Retrieve and Verify CRP
	retrieved_signature = get_crp_signature(REST, USER, repo, 'HEAD')
	return crp, verify_signature(crp, retrieved_signature, verify_key)


if __name__ == "__main__":
	REST = Github(TOKEN)
	validate_github_crp('test-repo', 'main')