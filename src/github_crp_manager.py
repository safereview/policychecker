from ast import literal_eval
import re

from constants import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from github_API import *
from commit_manager import get_pr_code_changes
from review_manager import parse_review, split_review_unit

# Parse the GitHub CRP
def _github_parse_crp(crp):
    # Extract the components from the CRP
    protection_rules, codeowners, gitattributes, collaborators = \
        re.search(
            "RULES\n([\s\S]*?)\nCODEOWNERS\n([\s\S]*?)"
            "\nGITATTRIBUTES\n([\s\S]*?)\nCOLLABORATORS\n([\s\S]*)",
            crp.decode()
        ).groups()

    return {
        # Turn protection rules string into a dictionary
        PROTECTION_RULES: literal_eval(protection_rules),
        CODEOWNERS: codeowners,
        GITATTRIBUTES: gitattributes,
        COLLABORATORS: literal_eval(collaborators)
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
    # Get a list of the global codeowners' usernames / emails
    # TODO: Improve this to check the file types / directories
    # of modified files and check that the owners for those patterns
    # have provided reviews instead of the global owners
    global_owners = _parse_codeowners(codeowners)['*']

    for unit in review_units:
        review = parse_review(
            split_review_unit(unit)[1])

        for owner in global_owners:
            # Check if the review was written
            # by a global code owner
            if (
                review['name'] == owner 
                or review['email'] == owner
            ):
                # Remove the owner that has provided
                # a review from the list
                global_owners.remove(owner)
                break

        # Check if the code owners list is
        # empty, which means all owners have provided
        # a review
        if len(global_owners) == 0:
            return True

    return False


# Check if there are minimum number of approavals
def _check_min_approvals(rules, collaborators, review_units):
    #TODO
    # Check outdated approving reviews are dismissed correctly
    # 
    return True


# Parse the codeowners component of the CRP
def _parse_codeowners(codeowners):
    # Get the lines that don't begin with
    # a pound or whitespace. This should be improved
    # to detect lines that don't have a hash
    # as the first character in the line
    rules = re.findall(
        '^[^#\s].*?$', 
        codeowners, 
        re.MULTILINE)

    parsed_codeowners = {}
    for rule in rules:
        # The left hand side of the first whitespace 
        # character is the file type / directory pattern
        pattern = rule.split()[0]

        # Extract all codeowners' usernames 
        # and emails in each line
        owners = re.findall(
            '(?<=@)[\S]+|[\S]+@[\S]+',
            rule)

        parsed_codeowners[pattern] = owners

    return parsed_codeowners


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

    if not _check_min_approvals(rules, collaborators, review_units):
        if not _check_required_reviews(codeowners, review_units):
            return False

        # https://docs.github.com/en/github/administering-a-repository/about-protected-branches
        return False

    return True