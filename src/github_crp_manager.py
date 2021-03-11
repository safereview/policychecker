from ast import literal_eval

from constants import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from github_API import *
from commit_manager import get_pr_code_changes


# Parse the GitHub CRP
def _github_parse_crp(crp):
    # Since the CRP is formed from byte objects
    # coerced into strings, there will be a " b' "
    # delimiter inbetween the components
    # Perhaps this can be changed into more clear
    # delimiters?
    protection_rules, codeowners, gitattributes = \
        re.search(
            "({[\s\S]+?})b['\"]{1}([\s\S]+?)['\"]"
            "{1}b['\"]{1}([\s\S]+?)['\"]{1}",
            crp.decode()
        ).groups()

    return {
        # Turn protection rules string into a dictionary
        PROTECTION_RULES: literal_eval(protection_rules),
        # Turn escaped whitespace characters back into
        # the actual characters
        CODEOWNERS: codeowners.encode('utf-8'
                    ).decode('unicode-escape'),
        GITATTRIBUTES: gitattributes.encode('utf-8'
                    ).decode('unicode-escape'),
        COLLABORATORS: "" #FIXME
    }


# Check if the merger is authorized to perfomr a merge request
def _is_authorized_merger(collaborators, committer):
    # TODO check if the committer has write permission
    return True


# Check if the PR Creator has read access to repo
def _is_authorized_author(collaborators, merge_commits):
    # Get commits with code changes in a PR
    # FIXME: Double check the following function
    commits = get_pr_code_changes (merge_commits)

    # TODO Check if the code authors have the read access
    return True


# Check if the committer has the direct push permission
def _is_authorized_direct_push(rules, collaborators, committer):
    # TODO: Check if the merger is an administrtor and the code review policy
    # excludes administrtors from following the code review policy
    return True


# Check if there reviews from certain users
def _check_required_reviews(codeowners, review_units):
    #TODO if there are appoving reviews from codeowners
    return True


# Check if there are minimum number of approavals
def _check_min_approvals(rules, collaborators, review_units):
    #TODO
    # Check outdated approving reviews are dismissed correctly
    # 
    return True


# Check if the reviews created on GitHub are legitimate
def github_validate_reviews(crp, merge_commits, review_units):
        # Split CPR into three parts: protection rules, codeowners, gitarrtibutes
    crp = _github_parse_crp(crp)
    project_config = crp[CONFIG_PROJECT]
    collaborators = crp[COLLABORATORS]
    rules = crp[PROTECTION_RULES]
    codeowners = crp[CODEOWNERS]

    # First commit in the merge_commits list is the head of PR
    head = merge_commits[0]

    # Check if the merger has the permission
    if not _is_authorized_merger(collaborators, head.committer):
        return False

    # Check if the author of code was authorized
    if not _is_authorized_author(project_config, merge_commits):
        return False

    # Check for the direct push permissions
    if merge_commit_type == DIRECTPUSH:
        return _is_authorized_direct_push(rules, collaborators, head.committer)

    if not _check_required_reviews(codeowners, review_units):
        return False

    if not _check_min_approvals(rules, collaborators, review_units):
        return False

    return True