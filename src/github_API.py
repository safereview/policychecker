
# $ pip install PyGithub
from github import Github

import json
import requests
import re

# from bs4 import BeautifulSoup as bs
# CODE EXPLAIN: 
# BeautifulSoup is used to potentially grab the preview from the future changes in preview automatically 

from configs.github_config import *
from crypto_manager import *
from constants import *

# NOTE: Headers accept content change
# For latest: https://developer.github.com/changes/2018-02-22-protected-branches-required-signatures/
# ACCEPT = bs(requests.get(HEAD_ACCEPT).text, 'html.parser').find('code').get_text()
# Potentially, This will parse the blog that it gets it from the latest preview.


HEADERS = {
	'Authorization': f"token {TOKEN}",
	"Accept" : "application/vnd.github.zzzax-preview+json"
}

POST_HEADERS = {
	'Authorization': f"token {TOKEN}",
	"Accept" : "application/vnd.github.v3+json"
} # The documentation suggested to use the following accept for POST request

# new_HEADER = {
# 	'Authorization' : f"token {TOKEN}",
# 	"Accept" : f"{ACCEPT}"
# }

# hyper_flex = lambda endpoint, header: requests.get(f"{GITHUB_API}/{endpoint}", headers=header)

# Form a get request
def get_request(endpoint):
	try:
		return requests.get(f"{GITHUB_API}/{endpoint}", headers = HEADERS)
	except Exception:
		pass

# Gets blob content 
def get_blob_content(user, repo, path):
	# :calls: `GET /repos/:owner/:repo/contents/:path <http://developer.github.com/v3/repos/contents>`_
	endpoint = f"{user}/{repo}/contents/{path}"
	response = get_request(endpoint)
	kson = json.loads(response.content)
	return requests.get(kson["download_url"]).content   #--> does the same exact thing as the former get_blob_content
	# Note: that ^it doesn't take in directories very well

###### Invalid and trial code
def store_new_crp_signature(user, repo, signature):
	return 0
	# The followings is potent code that can be used to complete minimizes the usage of PyGithub
    # :calls: `POST /repos/:owner/:repo/statuses/:sha <http://developer.github.com/v3/repos/statuses>`_
	endpoint = f"{user}/{repo}/statuses/{SHA}"
	url = f"{GITHUB_API}/{endpoint}"
	print(url)
	payload = {'state':'success','context':'CODE_REVIEW_POLICY','description':signature}
	payload_tuples = [('state', 'success'),('context', 'CODE_REVIEW_POLICY'),('description',signature)]
	body = dict(state="success",target_url=None,context="CODE_REVIEW_POLICY",description="Good lord waasdkas asdfjk asdkfhsk")
	jdump = json.dumps(payload)
	print(jdump)

	# gets somethings and then full send it in
	return requests.post(url, data=jdump, headers=HEADERS)
	#return requests.post(url, data=json.dumps(payload), headers=POST_HEADERS)
	# yeet = requests.post(url, json=payload, headers=POST_HEADERS)
	#print(yeet)
	#return requests.Request(method="POST", url=url, data=json.dumps(payload), headers=HEADERS) #yeet

# Store the crp signature as review label on the server
def store_crp_signature(user, repo, sha, signature):
    # :calls: `POST /repos/:owner/:repo/statuses/:sha <http://developer.github.com/v3/repos/statuses>`_
	g = Github(TOKEN)
	repo_name = f"{user}/{repo}"
	repo = g.get_repo(repo_name)
	res = repo.get_commit(sha=sha).create_status(
		state = "success",
		#target_url="https://myURL.com",
		context = "CODE_REVIEW_POLICY",
		description = signature
	)
	return res

# Retrive the crp signature from the Github server
def get_crp_signature(user, repo):
	# :calls: `GET /repos/:owner/:repo/statuses/:ref <http://developer.github.com/v3/repos/statuses>`_
	endpoint = f"{user}/{repo}/statuses/{SHA}"
	cnt = get_request(endpoint)
	json_load = json.loads(cnt.content)
	return json_load[0]["description"] # Gets the most recent status check  

# Form the code revivew policy
def form_crp(user, repo, branch_name):

	#Github CRP
	gitattributes = ""
	codeowners = ""
	protection_rules = {}

	try:
		gitattributes = get_blob_content(user, repo, GITATTRIBUTES)
	except Exception:
		# print("error in gitattr")
		pass

	try:
		codeowners = get_blob_content(user, repo, CODEOWNERS)
	except Exception:
		# print("error in codeowners")
		pass

	try:
		protection_rules = get_branch_protection_rules(user, repo, branch_name)
	except Exception:
		# print("error in protections")
		pass

	#TODO:
	#	- Strip all strings
	# 	-DOC: The CRP format is as follows:
	crp = f"[{protection_rules},{codeowners},{gitattributes}]"
	return crp.encode()


# Get branch protection rules
def get_branch_protection_rules(user, repo, branch_name):

	endpoint = f"{user}/{repo}/branches/{branch_name}/protection"
	protection_info = get_request(endpoint)

	try: 
		#TODO: DOC
		result = dict()
		if(protection_info.ok):
			rules_json = json.loads(protection_info.content)

			# Depending on preview version in the HEADER['accept'] you may be able to do this all all of them
			# Imperative to check latest preview for Github Branch API
			result['require_linear_history'] = rules_json["required_linear_history"]['enabled']
			result['allow_force_pushes'] = rules_json["allow_force_pushes"]['enabled']
			result['allow_deletions'] = rules_json["allow_deletions"]['enabled']
			result['include_administrators'] = rules_json['enforce_admins']['enabled']
			result['require_signed_commits'] = rules_json['required_signatures']['enabled']

			#TODO: We try the rules_dump becasue
			try:
				rules_dump = json.dumps(protection_info.json()) 
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

		endpoint = f"{user}/{repo}/branches/{branch_name}"
		branch_info = get_request(endpoint)

		if(branch_info.ok):
			branch_load = json.loads(branch_info.content)
			status_prot = branch_load["protection"]["required_status_checks"]["enforcement_level"]
			# Need to check if it is enabled from a branch requests and then any more info is on protection
			if(status_prot == "off"):
				result['require_status_checks'] = False
			else:
				result['require_status_checks'] = {}
				result['require_status_checks']['enabled'] = True
				result['require_status_checks']['strict'] = json.loads(protection_info.content)['required_status_checks']['strict']

		return result
	except Exception:
		return False

if __name__ == '__main__':
	pass
	# kol = store_crp_signature(USER, REPO, 'HEAD', "asfaskdfjkasdfaksdfkshdfad")
	# print(kol)

	# btu = get_crp_signature(USER, REPO)
	# print(btu)

	# # Get Branch Protection Rules
	# rules = get_branch_protection_rules(USER, REPO, BRANCH)
	# print(rules)

	# # Form the CRP
	# crp = form_crp(USER, REPO, BRANCH)
	# print(crp)

	# # Sign and Store the CRP
	# crp_signature, verify_key = sign_crp(crp)
	# result = store_new_crp_signature(USER, REPO, crp_signature)
	# print(result)

	# # Retrieve and Verify CRP
	# retrieved_signature = get_crp_signature(USER, REPO)
	# result = verify_signature(crp, retrieved_signature, verify_key)
	# print(result)
