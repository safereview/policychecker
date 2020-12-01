# Install: $ pip install PyGithub
from github import Github
import json
import requests
import re 

from configs.github_config import *
from crypto_manager import *
from constants import *

# Form a get request
def get_request(endpoint):
	try:
		return requests.get(f"{GITHUB_API}/{endpoint}", headers = HEADERS)
	except Exception:
		return False

# Get info about one branch
def get_branch(g, user, repo, branch):
	repo_name = f"{user}/{repo}"
	return g.get_repo(repo_name).get_branch(branch)


# Get file content
def get_blob_content(g, user, repo, path):
	repo_name = f"{user}/{repo}"
	return g.get_repo(repo_name).get_contents(path).decoded_content


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
	repo_name = f"{user}/{repo}"
	repo = g.get_repo(repo_name)
	stati = repo.get_commit(sha=sha).get_statuses()
	_list = list()
	for obj in stati:
		_list.append(obj)
		return _list[0].description  # get latest status check
		# print(f"{obj}\n\t{type(obj)}")


# Form the code revivew policy
def form_crp(g, user, repo, branch_name):

	#Github CRP
	gitattr = ""
	codeowners = ""
	protection_rules = {}

	try:
		gitattributes = get_blob_content(REST, USER, repo, GITATTRIBUTES)
	except Exception:
		# print("error in gitattr")
		pass

	try:
		codeowners = get_blob_content(g, user, repo, CODEOWNERS)
	except Exception:
		# print("error in codeowners")
		pass

	try:
		protection_rules = get_branch_protection_rules(g, user, repo, branch_name)
	except Exception:
		# print("error in protections")
		pass

	#TODO:
	#	- Strip all strings
	# 	-DOC: The CRP format is as follows:
	crp = f"[{protection_rules},{codeowners},{gitattr}]"
	return crp.encode()


# Get branch protection rules
def get_branch_protection_rules(g, user, repo, branch_name):
	endpoint = f"{user}/{repo}/branches/{branch_name}/protection"
	rules = get_request(endpoint)

	try:
		#TODO: DOC
		result = dict()
		if(rules.ok):
			rules_json = json.loads(rules.content)
			result['require_linear_history'] = rules_json["required_linear_history"]['enabled']
			result['allow_force_pushes'] = rules_json["allow_force_pushes"]['enabled']
			result['allow_deletions'] = rules_json["allow_deletions"]['enabled']

			#TODO: We try the rules_dump becasue
			try:
				rules_dump = json.dumps(rules.json())
				dismiss_stale = bool(re.search('"dismiss_stale_reviews": true', rules_dump))
				require_codeowners = bool(re.search('"require_code_owner_reviews": true', rules_dump))
				# get the minimum number of approvals: count
				review_count = int(re.search('"required_approving_review_count": \d', rules_dump).group()[-1])
				result['require_pull_request_review'] = {}
				result['require_pull_request_review']['enabled'] = True
				result['require_pull_request_review']['approving_reviews_count'] = review_count
				result['require_pull_request_review']['dismiss_stale_pull_request'] = dismiss_stale
				result['require_pull_request_review']['require_review_from_code_owners'] = require_codeowners
			except Exception:
				result['require_pull_request_review'] = False


		#TODO: DOC
		endpoint = f"{user}/{repo}/branches/{branch_name}"
		branch_info = get_request(endpoint)

		if(branch_info.ok):
			branch_load = json.loads(branch_info.content)
			status_prot = branch_load["protection"]["required_status_checks"]["enforcement_level"]
			if(status_prot == "off"):
				result['require_status_checks'] = False
			else:
				branch = get_branch(g, user, repo, branch_name)
				check_strict = bool(re.search("strict=True",str(branch.get_required_status_checks())))
				result['require_status_checks'] = {}
				result['require_status_checks']['enabled'] = True
				result['require_status_checks']['strict'] = check_strict

		#TODO: Get other rules using a new API call, why?
		# Get additional rules
		branch_info = get_branch(g, user, repo, branch_name)
		result['require_signed_commits'] = branch_info.get_required_signatures()
		result['include_administrators'] = branch_info.get_admin_enforcement()

		return result
	except Exception:
		return False


if __name__ == '__main__':
	# GitHub REST API call
	REST = Github(TOKEN)

	# GitHub HEADERS
	HEADERS = {
		'Authorization': f"token {TOKEN}",
		"Accept" : "application/vnd.github.luke-cage-preview+json"
		}

	# Get Branch Protection Rules
	rules = get_branch_protection_rules(REST, USER, REPO, BRANCH)
	# print(rules)

	# Form the CRP
	crp = form_crp(REST, USER, REPO, BRANCH)
	print(crp)

	# Sign and Store the CRP
	crp_signature, verify_key = sign_crp(crp)
	result = store_crp_signature(REST, USER, REPO, 'HEAD', crp_signature)
	print(result)

	# Retrieve and Verify CRP
	retrieved_signature = get_crp_signature(REST, USER, REPO, 'HEAD')
	result = verify_signature(crp, retrieved_signature, verify_key)
	print(result)
