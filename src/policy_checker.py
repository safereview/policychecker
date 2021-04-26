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

import os
import argparse
import re
from sys import exit

from commit_manager import *
from constants import *
from github_API import *
from gerrit_API import *
from github_crp_manager import *
from gerrit_crp_manager import *
from review_manager import *


# Check if the review units are legitimate
def validate_reviews(server, crp, review_info):
    merge_method, merge_commits, review_units = review_info
    # Check if code reviews have valid signature 
    # and the chain of code reviews is valid.
    if not validate_review_signatures(review_units):
        return False

    # Check for the first commit and the direct push
    if merge_method == FIRSTCOMMIT:
        return True

    # Check if policy rules are violated
    if server == GITHUB:
        return github_validate_reviews(crp, merge_commits, review_units)
    else:
        return gerrit_validate_reviews(crp, merge_commits, review_units)


# Validate all reviews in a branch
def validate_branch(server, repo_path, branch):
    try:
        # Create the local Repo object
        repo = Repo(repo_path)
    except Exception:
        exit(f"{repo_path} is not a valid Git repository path")

    # Extract the repo name from the repo path
    # e.g., 'd1/d2/f1' returns 'f1'
    repo_name = os.path.basename(repo_path)

    # Validate the CRP signature
    valid = True
    if server == GITHUB:
        crp, valid = validate_github_crp(repo_name, branch)
    elif server == GERRIT:
        crp, valid = validate_gerrit_crp(repo_name, branch)
    else:
        exit(f"{server} is not supported!")

    # CRP is not valid
    if not valid:
        exit('Code Review Policy is not valid')

    # Get a set of all commits in the repo
    commits = get_branch_commits(repo, branch)

    # Check commit signatures
    for commit in list(commits):
        if not validate_commit_signature(repo, commit):
            return False

    # Get the branch head
    branch_head = get_branch_head(repo, branch)

    ## All commits are not visited
    #visited = [False] * len(commits)

    # Extract the commits in the merge request that
    # corresponds to the current branch head
    while commits:
        # review_info = [merge_method, merge_commits, review_units]
        review_info = extract_review_units(server, repo, branch_head)
        if not validate_reviews(server, crp, review_info):
            # TODO: Make it more informative per result
            exit('Review Units are not valid')

        # Remove commits in merge request from the set Commits
        # merge_commits: review_info [1]
        remove_visited_commit(commits, review_info[1])

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
    branch = args.branch
    repo_path = args.repo.rstrip('/')
    
    # Validate the branch
    validate_branch(server, repo_path, branch)


if __name__ == "__main__":
    # python src/policy_checker.py -s github -r test-repo -b main -k ~/.gnupg
    main()
