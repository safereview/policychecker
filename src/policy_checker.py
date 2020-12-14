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
from sys import exit

from code_review_policy import *


def validate_reviews(merge_policy, merge_commits, review_units):
    print(merge_policy, merge_commits, review_units)


def validate_branch(server, repo, merge_policy, branch):
    print (server, repo, merge_policy, branch)


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

    valid = True
    if server == GITHUB:
        crp, valid = validate_github_crp(repo, branch)
    elif server == GERRIT:
        print(server)
        crp, valid = validate_gerrit_crp(repo, branch)
    else:
        exit(f"{server} is not supported!")

    # CRP is not valid
    if not valid:
        exit('Code Review Policy is not valid')
    
    
    validate_branch(server, args.repo, crp, args.branch)


if __name__ == "__main__":
    # python src/policy_checker.py -s github -r test-repo -b main -k ~/.gnupg
    main()