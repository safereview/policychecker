# Install: $ pip install PyGithub
from github import Github
from configs.github_config import *
from crypto_manager import *
import json
import requests
import re 


# Get a list of branches
def get_branches(g, user, repo):
	repo_name = f"{user}/{repo}"
	repo = g.get_repo(repo_name)	
	return list(repo.get_branches())


# Get info about a branch
def get_branch(g, user, repo, branch):
	repo_name = f"{user}/{repo}"
	return g.get_repo(repo_name).get_branch(branch)


# Get the head of a branch
def get_branch_head(g, user, repo, branch):
	repo_name = f"{user}/{repo}"
	branch = g.get_repo(repo_name).get_branch(branch)
	return branch.commit


# Get Protection Status of that Branch
def get_branch_protection_status(g, user, repo, branch):
	# The Protection Status will either go to True or an Error, must debug for future 
	repo_name = f"{user}/{repo}"
	try:
		branch = g.get_repo(repo_name).get_branch(branch)
		branch_prot = branch.protected
		if( isinstance(branch_prot, bool) ):
			return True
		else:
			return False  
	except Exception as e:
		SystemExit(e)

	
# See required status checks of branch
def get_required_branch_protection_checks(g, user, repo, branch):
	repo_name = f"{user}/{repo}"
	branch =  g.get_repo(repo_name).get_branch(branch)
	return branch.get_protection()


# Get file content
def get_blob_content(g, user, repo, path):
	repo_name = f"{user}/{repo}"
	return g.get_repo(repo_name).get_contents(path).decoded_content


# Create a status check
def create_status_check(g, user, repo, sha, signature):
	repo_name = "{}/{}".format(user, repo)
	repo = g.get_repo(repo_name)
	res = repo.get_commit(sha=sha).create_status(
		state = "success",
		#target_url="https://myURL.com",
		context = "CODE_REVIEW_POLICY",
		description = signature
	)
	return res

# grabs the latest status check 
def grab_status_check_signature(g, user, repo, sha):
	repo_name = f"{user}/{repo}"
	repo = g.get_repo(repo_name)
	stati = repo.get_commit(sha=sha).get_statuses()
	_list = list()
	for obj in stati:
		_list.append(obj)
		return _list[0].description  # get latest status check
		# print(f"{obj}\n\t{type(obj)}")


def get_crp(g, user, repo, branch_name):

	gitattr = ""
	codeowners = ""
	branch_prot_rules = {} 

	try:
		gitattr = get_blob_content(REST, USER, repo, ".git/info/attributes")
	except Exception:
		# print("error in gitattr")
		pass

	try:
		codeowners = get_blob_content(g, user, repo, CODEOWNERS)
	except Exception:
		# print("error in codeowners")
		pass

	try:
		branch_prot_rules = get_full_branch_protection(g, user, repo, branch_name)
	except Exception:
		# print("error in protections")
		pass

	crp = f"[{branch_prot_rules},{codeowners},{gitattr}]"
	return crp.encode() # Needs to be in (bytes) in order to be put into the compute func

# ==========================================================================================
def get_full_branch_protection(g, user, repo, branch_name):
    ret_dict = dict()    # ret_dict is just the return dictionary that will have the status of each branch
    prot_resp = requests.get(f"https://api.github.com/repos/{user}/{repo}/branches/{branch_name}/protection", headers={'Authorization': f"token {TOKEN}", "Accept" : "application/vnd.github.luke-cage-preview+json" })
    branch_resp = requests.get(f"https://api.github.com/repos/{user}/{repo}/branches/{branch_name}", headers={'Authorization': f"token {TOKEN}", "Accept" : "application/vnd.github.luke-cage-preview+json" })

    pygithub_branch_object = get_branch(g, user, repo, branch_name) 

    ret_dict['require_signed_commits'] = pygithub_branch_object.get_required_signatures()
    ret_dict['include_administrators'] = pygithub_branch_object.get_admin_enforcement() 


    if(prot_resp.ok):
        prot_load = json.loads(prot_resp.content)
        ret_dict['require_linear_history'] = prot_load["required_linear_history"]['enabled']
        ret_dict['allow_force_pushes'] = prot_load["allow_force_pushes"]['enabled']
        ret_dict['allow_deletions'] = prot_load["allow_deletions"]['enabled']

        try:
            resp_dump = json.dumps(prot_resp.json())
            dismiss_stale = bool(re.search('"dismiss_stale_reviews": true', resp_dump)) 
            require_codeowners = bool(re.search('"require_code_owner_reviews": true', resp_dump))
            review_count = int(re.search('"required_approving_review_count": \d', resp_dump).group()[-1]) # gets the number count
            ret_dict['require_pull_request_review'] = {}
            ret_dict['require_pull_request_review']['enabled'] = True
            ret_dict['require_pull_request_review']['approving_reviews_count'] = review_count
            ret_dict['require_pull_request_review']['dismiss_stale_pull_request'] = dismiss_stale
            ret_dict['require_pull_request_review']['require_review_from_code_owners'] = require_codeowners
        except Exception:
            ret_dict['require_pull_request_review'] = False


    if(branch_resp.ok):
        branch_load = json.loads(branch_resp.content)
        status_prot = branch_load["protection"]["required_status_checks"]["enforcement_level"]
        if(status_prot == "off"):
            ret_dict['require_status_checks'] = False
        else:
            branch = get_branch(g, user, repo, branch_name)
            check_strict = bool(re.search("strict=True",str(branch.get_required_status_checks())))
            ret_dict['require_status_checks'] = {}
            ret_dict['require_status_checks']['enabled'] = True
            ret_dict['require_status_checks']['strict'] = check_strict

    return ret_dict


def project_full_branch_protections(g, user, repo):
    full_prot_dict = {}
    branches = g.get_repo(f"{user}/{repo}").get_branches()
    for branch in branches:
        full_prot_dict[branch.name] = {}
        full_prot_dict[branch.name] = get_full_branch_protection(g, user, repo, branch.name)

    return full_prot_dict
# ==========================================================================================


if __name__ == '__main__':
	# GitHub REST API call
	REST = Github(TOKEN)

	branch_name = "dev"

	"""
	# Try out some APIs
	branches = get_branches (REST, USER, repo)
	branch = get_branch (REST, USER, repo, "master")
	branch_head = get_branch_head(REST, USER, repo, "master")
	crp_sig = create_status_check(REST, USER, repo, 'HEAD', crp_signature)   # how you store the crp_signature

	# Print out results
	print(f"{branch_head},\n\t {type(branch_head)}")
	print(f"{branch},\n\t {type(branch)}")
	print(f"{branches},\n\t {type(branches)}")
	print(f"{crp_sig},\n\t {type(crp_sig)}")
	# print("\n")
	"""
	# Get Branch Protections
	branch_prot = get_full_branch_protection(REST, USER, repo,branch_name)
	#print(branch_prot)
	print(branch_prot)

	# Retrieve CRP, Sign It and Store  
	crp = get_crp(REST, USER, repo, branch_name)
	verify_key, crp_sign = compute_signature(crp)
	stored = create_status_check(REST, USER, repo, 'HEAD', crp_sign[:140]) 

    # Retrieve CRP signature, Verify it
	retrieved_signature = grab_status_check_signature(REST, USER, repo, 'HEAD')
	res = verify_signature(retrieved_signature, verify_key)
	#print(res)

	print(f"\nVerify:{verify_key}\n\ncrp_signature:{crp_sign}")
	#print(f"\n{crp_sign[:140]}\n")
	#print(retrieved_signature)
	# print(get_full_branch_protection(REST, USER, repo, "dev"))
	#print(get_branches(REST, USER, repo))
