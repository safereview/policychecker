# Step1: Extract the code review policy (CRP)
#   FIXME: Issue with the min number of approvals in GitHub
#       When the Branch protection rules are enabled, but
#       The min is not set.

# Step2: Extract and verify the CRP's signature

# TODO: Step 3: Parse and Interpret the CRP

# TODO: Extract review units (RUs) from the repository
#   - Find the merge policy
#   - Extract merge request commits
#       - FIXME: Two corner cases:
#       -   Rebase vs Squash and Merge
#       -   Rebase vs Direct push
#   - Extract RUs  


# TODO: Validate RUs
#   - Valid commit signature
#   - Valid RU signature
#   - Valid chain of reviews

# TODO: Basic checks for
#   - First commit
#   - Direct push
#   - Authorized merger
#   - Minimum number of approving reviews
#   - Required reviews from specific users
#   - Stale approving reviews are dismissed
#   - etc.

# TODO: Check code reviews against review policies

import argparse
import re
from sys import exit

from code_review_policy import *
from commit_manager import *
from constants import *
from crp_manager import *
from github_API import *
from gerrit_API import *
from review_manager import *


# Check if the reviews created on GitHub are legitimate
def github_validate_reviews(merge_commits, review_units):
    return True


def check_gerrit_labels(crp, review_units):
    #TODO check if rule is met
    # https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/server/rules/DefaultSubmitRule.java#L107
    # https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/entities/LabelFunction.java#L91-#L123

    #extract the default policy
    label = gerrit_extract_labels(crp)
    rule = GERRIT_LABELS[label.upper()]

    project_config = parse_crp(crp)[CONFIG_PROJECT]

    status = "MAY"
    if rule["isRequired"]:
        status = "NEED"

    for item in review_units:
        signature, review = split_review_unit(item)
        comment, score, reviewer = parse_review(review)

        if score == '0':
            continue

        if rule["isBlock"] and is_max_negative(project_config, score):
            if not is_allowed_to_block(crp, reviewer):
                exit("Committer is not allowed to block the change")
            status = "REJECT"
            return status

        if is_max_positive(project_config, score) or not rule["requiresMaxValue"]:
            if not is_allowed_to_approve(crp, reviewer):
                exit("Committer is not allowed to approve the change")
            status = "MAY"

            if rule["isRequired"]:
                status = "OK"

        #check for status
        #https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/server/rules/DefaultSubmitRule.java#L110

    return status


# Check if the reviews created on GitHub are legitimate
def gerrit_validate_reviews(crp, review_units):
    # Check if the basic rules (based on labels) are met
    if not check_gerrit_labels(crp, review_units):
        return False

    # Check if the minimum number of approving reviews is met
    if not check_min_approvals(crp, review_units):
        return False

    # Check if there are required reviews from specific users
    if not check_required_reviews(crp, review_units):
        return False

    # Check if stale approving reviews are dismissed
    if not check_review_dismissal (crp, review_units):
        return False

    return True


# Check if the review units are legitimate
def validate_reviews(server, crp, merge_commit_type, merge_commits, review_units):
    # Check if review units have valid signature
    if not validate_reviews_signatures(review_units):
        return False

    # Check if review chain is valid
    if not validate_review_chain(review_units):
        return False

    # Check for the first commit and direct pushes
    if merge_commit_type == FIRSTCOMMIT:
        return True
    elif merge_commit_type == DIRECTPUSH:
        return check_direct_push(merge_commits)

    # Check if the merger has the permission
    if not is_authorized_merger(crp, merge_commits):
        return False

    #Check if the author of code was authorized
    if not is_authorized_committer(crp, merge_commits):
        return False

    # Check if policy rules are violated
    if server == GITHUB:
        return github_validate_reviews(merge_commits, review_units)
    else:
        return gerrit_validate_reviews(merge_commits, review_units)


# Validate all reviews in a branch
def validate_branch(server, repo, branch):
    valid = True
    if server == GITHUB:
        crp, valid = validate_github_crp(repo, branch)
    elif server == GERRIT:
        crp, valid = validate_gerrit_crp(repo, branch)
    else:
        exit(f"{server} is not supported!")

    # CRP is not valid
    if not valid:
        exit('Code Review Policy is not valid')

    # Get a set of all commits in the repo
    commits = get_branch_commits(repo, branch)

    # Check commit signatures
    for commit in list(commits):
        if not validate_commit_signature(commit):
            return False

    # Get the branch head
    branch_head = get_branch_head(repo, branch)

    ## All commits are not visited
    #visited = [False] * len(commits)

    # Extract the commits in the merge request that
    # corresponds to the current branch head
    while commits:
        merge_commit_type, merge_commits, review_units = extract_review_units(server, repo, branch_head)
        if not validate_reviews(server, crp, merge_commit_type, merge_commits, review_units):
            # TODO: Make it more informative per result
            exit('Review Units are not valid')

        # Remove commits in merge request from the set Commits
        remove_visited_commit(commits, merge_commits)

        # Update the head to the head commit of the branch represented
        # by commits left in the set Commits
        branch_head = get_current_head(commits)

    return True


# Parse the artuments
def create_parser():
    '''
    Create and return configured ArgumentParser instance.
    '''

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
        Policychecker checks if a given set of code reviews matches
        the code review policy.
        ''')

    parser.add_argument('-r', '--repo', type=str, required=True,
        help='the path to the repository', )
        
    parser.add_argument('-b', '--branch', type=str, required=True,
    help='the repository branch', )

    parser.add_argument('-s', '--server', type=str, required=True,
        help='the code review server either GitHub or Gerrit', )

    parser.add_argument('-k', '--key', type=str, required=True,
        help='the path to the public key(s)')

    return parser


# Main function
def main():
    '''
    Parse arguments, load key(s) from disk (if passedd)
    and run the verification procedure.
    '''

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    server = args.server.lower()
    repo = args.repo
    branch = args.branch
    
    # Validate the branch
    validate_branch(server, repo, branch)


if __name__ == "__main__":
    # python src/policy_checker.py -s github -r test-repo -b main -k ~/.gnupg
    main()