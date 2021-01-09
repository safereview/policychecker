from gerrit_API import *
from github_API import *
from constants import *
from configs.gerrit_config import *
from configs.github_config import *



# Compute an ed25519 over the CRP
def sign_crp(crp):
    signing_key, verify_key = generate_key()
    signed_hex = compute_signature(crp, signing_key)
    return signed_hex.signature.decode("utf-8"), verify_key


# Validate the GitHub repo's code review policy
def validate_github_crp(repo, branch):
	# GitHub REST API call
	REST = Github(TOKEN)

	# GitHub HEADERS
	HEADERS = {
		'Authorization': f"token {TOKEN}",
		"Accept" : "application/vnd.github.luke-cage-preview+json"
		}

	# Get Branch Protection Rules
	rules = get_branch_protection_rules(REST, HEADERS, USER, repo, branch)
	print(rules)

	# Form the CRP
	crp = form_github_crp(REST, USER, repo, branch)
	print(crp)

	# Sign and Store the CRP
	crp_signature, verify_key = sign_crp(crp)
	result = store_crp_signature(REST, USER, repo, 'HEAD', crp_signature)
	print(result)

	# Retrieve and Verify CRP
	retrieved_signature = get_crp_signature(REST, USER, repo, 'HEAD')
	return crp, verify_signature(crp, retrieved_signature, verify_key)


# Validate the GitHub repo's code review policy
def validate_gerrit_crp(repo, branch):
	# Gerrit REST API call
	REST = get_rest_api(USER, PASS, url)

	# Form the CRP
	crp = form_gerrit_crp(REST, repo)
	print(crp)

	# Sign and Store the CRP
	crp_signature, verify_key = sign_crp(crp)
	result = store_crp_signature(REST, repo, crp_signature)
	print(result)

	# Retrieve and Verify CRP
	retrieved_signature = get_crp_signature(repo)
	return crp, verify_signature(crp, retrieved_signature, verify_key)
