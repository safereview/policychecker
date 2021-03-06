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


# Headers for different requests
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
	return requests.get(f"{GITHUB_API}/{endpoint}", headers = headers)


# Form a post request
def post_request(endpoint, data, headers = HEADERS):
	return requests.post(f"{GITHUB_API}/{endpoint}", data = data, headers = headers)


# Get branch info
def get_branch(user, repo, branch):
	endpoint = f"{user}/{repo}/branches/{branch}"
	response = get_request(endpoint)
	if response.status_code == 404:
		exit(f"{branch} branch not found in the specified repository")

	return  json.loads(response.content)


# Get the file content
def get_blob_content(user, repo, path):
	endpoint = f"{user}/{repo}/contents/{path}"
	response = get_request(endpoint)
	response = json.loads(response.content)
	return requests.get(response["download_url"]).content


# Create a status check
def _create_status(user, repo, sha, status, context, description):
	endpoint = f"{user}/{repo}/statuses/{sha}"
	data = {
		'state': status,
		'context': context,
		'description': description
		}
	data = json.dumps(data)

	return post_request(endpoint, data, POST_HEADERS)


# Retrieve the crp signature from the Gerrit server
def _get_crp_signature(user, repo, sha):
	endpoint = f"{user}/{repo}/statuses/{sha}"
	response = get_request(endpoint)
	json_load = json.loads(response.content)
	return json_load[0]["description"]


# Get branch protection rules
def get_branch_protection_rules(user, repo, branch_name):
	# NOTE: The branch protection API is in a preview period
	# During this period, we use different ACCEPT HEADERS per use case
	# See details @ 
	# https://docs.github.com/en/rest/reference/repos#get-branch-protection
	# https://docs.github.com/en/rest/reference/repos#update-branch-protection-preview-notices

	# Extract certain users specified for a rule
	def find_users(rule):
		result = []
		users = rule['users']
		for user in users:
			result.append(user['login'])
		return result

	# Call the API endpoint to extract protection tules
	endpoint = f"{user}/{repo}/branches/{branch_name}/protection"
	try:
		response = get_request(endpoint, PRT_HEADERS)
	except Exception:
		exit(f"{branch_name} branch has no protection rules!")

	result = dict()
	if(response.ok):
		rules = json.loads(response.content)

		# Check if push permission is narrowed to specific users
		if GITHUB_PUSH_RESTRICTIONS not in rules.keys():
			result[GITHUB_PUSH_RESTRICTIONS] = False
		else:
			result[GITHUB_PUSH_RESTRICTIONS] = True
			result[GITHUB_AUTHORIZED_PUSH] = \
				find_users(rules[GITHUB_PUSH_RESTRICTIONS])

		# Check if 'required_pull_request_reviews' is enabled
		if GITHUB_REQURIED_REVIEWS not in rules.keys():
			result[GITHUB_REQURIED_REVIEWS] = False
		else:
			result[GITHUB_REQURIED_REVIEWS] = True
			review_rules = rules[GITHUB_REQURIED_REVIEWS]

			# Get the min number of required approving reviews
			result[GITHUB_MIN_APPROALS] = \
				review_rules[GITHUB_MIN_APPROALS]

			# Check if stale reviews must be dissmissed
			result[GITHUB_DISMISS_STALE_REVIEWS] = \
				review_rules[GITHUB_DISMISS_STALE_REVIEWS]

			# Check if reviews from the code owner is required
			result[GITHUB_CODE_OWNER_REVIEWS] = \
				review_rules[GITHUB_CODE_OWNER_REVIEWS]

			# Check which users are allowsed to dismiss reviews.
			if GITHUB_DISMISSAL_RESTRICTION not in review_rules:
				result[GITHUB_DISMISSAL_RESTRICTION] = False
			else:
				result[GITHUB_DISMISSAL_RESTRICTION] = True
				result[GITHUB_AUTHORIZED_DISMISS] = \
					find_users(review_rules[GITHUB_DISMISSAL_RESTRICTION])

		# Check for additional rules.
		# 1) required signed commits:
		# We must use another HEADER to get the information. However,
		# we ignore this check since we assumes all commists are signed.
		#result[] = rules['required_signatures']['enabled']

		# 2) include_administrators:
		result[GITHUB_ENFORCE_ADMIN] = rules[GITHUB_ENFORCE_ADMIN]['enabled']

		# 3) enforce the linear history:
		# The merge strategy must be 'Squash and merge' or 'Rebase and merge'
		if GITHUB_LINEAR_HISTORY not in rules.keys():
			result[GITHUB_LINEAR_HISTORY] = False
		else:
			result[GITHUB_LINEAR_HISTORY] = True

	return result


# Get collaborators for a GitHub repo
def _get_collaborators(user, repo):
	endpoint = f"{user}/{repo}/collaborators"
	response = get_request(endpoint)
	content = json.loads(response.content)

	collaborators = {}

	for user_info in content:
		# Create an entry for each user
		# containing their repo permissions
		collaborators[user_info['login']] = \
			user_info['permissions']

	return collaborators


	# Form the code revivew policy
def form_github_crp(user, repo, branch_name):

	#Github CRP
	gitattributes = ""
	codeowners = ""
	protection_rules = {}
	collaborators = {}

	try:
		#TODO: Check if we need to capture the entire gitattributes
		gitattributes = get_blob_content(user, repo, GITATTRIBUTES).decode()
	except Exception:
		#print("error in gitattr")
		pass

	# Check each possible location for codeowners files
	for location in CODEOWNERS_LOCATIONS:
		try:
			# Collect found codeowners contents into a single string
			# NOTE: We're assuming that each codeowners file will have
			# non-conflicting unique entries
			codeowners += get_blob_content(user, repo, location).decode()
		except Exception:
			#print("error in codeowners")
			pass

	try:
		protection_rules = get_branch_protection_rules(user, repo, branch_name)
	except Exception:
		#print("error in protections")
		pass

	try:
		collaborators = _get_collaborators(user, repo)
	except Exception:
		#print("error in protections")
		pass

	#TODO: Add DOC for the CRP format
	crp = (
		f"RULES\n{protection_rules}"
		f"\nCODEOWNERS\n{codeowners}"
		f"\nGITATTRIBUTES\n{gitattributes}"
		f"\nCOLLABORATORS\n{collaborators}"
	)
	return crp.encode()


# Validate the GitHub repo's code review policy
def validate_github_crp(repo, branch):
	# Form the CRP
	crp = form_github_crp(USER, repo, branch)

    # FIXME: Remove this part
	# Sign and Store the CRP as a status check
	crp_signature, verify_key = ed25519_sign_message(crp)
	branch = get_branch(USER, repo, branch)
	sha = branch['commit']['sha']

	_create_status(
		USER, repo, sha,
		'success', 'CODE_REVIEW_POLICY', crp_signature
		)

	# Retrieve and Verify CRP
	retrieved_signature = _get_crp_signature(USER, repo, sha)
	return crp, verify_signature(crp, retrieved_signature, verify_key)
