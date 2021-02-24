# Install: $ pip install gitpython
from git import Repo
import re
from tempfile import NamedTemporaryFile

from configs.gerrit_config import *
from constants import *
from crypto_manager import gpg_verify_signature
from gerrit_API import *
from review_manager import is_first_review


# List all commits in a branch
def get_branch_commits(repo, branch):
    branch_commits = []
    commit_ids = repo.git.rev_list(
        branch).split()
    for id in commit_ids:
        branch_commits.append(repo.commit(id))

    # Returns a list of all branch commits
    # in order from newest to oldest
    return branch_commits


# Get the head of a branch
def get_branch_head(repo, branch):
    # The branch head can be obtained by
    # getting the first commit in the branch_commits
    # list, so this might not be needed?
    head_id = repo.git.rev_parse(branch)
    return repo.commit(head_id)


# Remove visited commits
def remove_visited_commit(commits, merge_commits):
    for commit in merge_commits:
        commits.remove(commit)


# Get the head of a set of commits
def get_current_head(commits):
    # Assume the first commit in the list is head
    # TODO: Make sure it works

    # With the branch_commits list in order
    # the head of the commits list should be
    # the current head after the visited 
    # merge commits are removed from the list

    # I found that using the branch_head's first parent
    # would not work for Rebase merge requests
    return commits[0]


# Check if the commits' signature is valid
def validate_commit_signature(repo, commit):
    # res is a string containing a single
    # letter status code for the signature.
    # Can be G, B, or N for good, bad, or no
    # signature to name a few
    res = repo.git.show(commit.hexsha, 
        "--pretty=%G?")
    return res == 'G'


# Check if he commit has multiple parents
def has_multiple_parents(commit):
    return len(commit.parents) > 1


# Find the groups that a committer is in
def find_group_membership(committer_name, committer_email):
    # Get all of the groups in the Gerrit project
    groups = list_groups()
    committers_groups = []

    for g in groups:
        g_id = groups[g]['group_id']
        for member in get_group_info(g_id)['members']:
            if (
                member['name'] == committer_name
                and member['email'] == committer_email
            ):
                committers_groups.append(g)
    
    return committers_groups


# Extrcact all review units in a commit
def get_review_units(commit):
    return re.findall(f"[\s\S]*?[\n]?score.*\n"
        f".*\n{PGP_START}[\s\S]+?{PGP_END}\n", 
        commit.message)


# Check if the commit has a review unit
def has_review_units(commit):
    return bool(re.search(f"score .*\n.*\n{PGP_START}\n",
        commit.message))


# Extract PR's commits in a REBASE
def get_rebase_commits(repo, commit):
    merge_commits = [commit]
    first_review_found = False

    # Traverse all of the ancestors of the initial commit
    for curr in commit.iter_parents():
        if not first_review_found:
            # Add commits until we find the first review unit in the chain
            merge_commits.append(repo.commit(curr))
            review_unit = get_review_units(curr)
            first_review_found = is_first_review(review_unit)
        else:
            # Keep adding commits until we find a commit that
            # either has a review unit or has multiple parents
            if (
                not has_review_units(curr)
                and not has_multiple_parents(curr)
            ):
                merge_commits.append(repo.commit(curr))
            else:
                break

    return merge_commits


# Extract commits in a PR
def get_pr_commits(server, repo, commit):
    merge_commits = [commit]
    parents = commit.parents
    # Get common ancestor of two parents
    common_ancestor = repo.merge_base(parents[0], parents[1])[0]

    # Get commits between the head of PR and CA
    merge_commit_ids = repo.git.rev_list(
        '--ancestry-path',
        f'{common_ancestor.hexsha}..{parents[1].hexsha}'
        ).split()

    for id in merge_commit_ids:
        merge_commits.append(repo.commit(id))

    return merge_commits


# TOTO: Merge Gerrit and GitHub versions
# Extract the GitHub merge requests' commits
def github_extract_merge_request_commits(repo, commit):
    # Get the commit's parents
    parents = commit.parents
    p = len(parents)

    merge_commits = []
    review_units = []
    commit_type = MERGE

    # FIRSTCOMMIT:
    # A commit with no parents
    if p == 0:
        commit_type = FIRSTCOMMIT

    elif p == 1:
        # Add the current commit to merge_commits
        merge_commits.append(commit)

        # Extract the review units embeded in the Commit
        review_units = get_review_units(commit)
        r = len(review_units)

        # DIRECTPUSH
        # Commits with one parent and no review units
        if r == 0:
            commit_type = DIRECTPUSH

        # REBASE or SQUASH:
        # Commits with one parent and at least one review unit
        elif r == 1:
            if not is_first_review(review_units):
                    commit_type = REBASE
                    merge_commits = get_rebase_commits(repo, commit)
            #else
                #FIXME: differentiate between REBASE and SQUASH

        # SQUASH:
        # Commits with one parent and more than one review unit
        else:
            commit_type = SQUASH
    else:
        # MERGE:
        # Commits with two parents
        merge_commits = get_pr_commits(repo, commit)

    return [
        commit_type,
        merge_commits,
        review_units
    ]


# Extract the Gerrit merge requests' commits
def gerrit_extract_merge_request_commits(repo, commit):
    # Get the commit's parents
    parents = commit.parents
    p = len(parents)

    merge_commits = []
    review_units = []
    commit_type = MERGE

    # FIRSTCOMMIT:
    # A commit with no parents
    if p == 0:
       commit_type = FIRSTCOMMIT

    elif p == 1:
        # Add the current commit to merge_commits
        merge_commits.append(commit)

        # Extract the review units embeded in the Commit
        review_units = get_review_units(commit)
        r = len(review_units)

        # DIRECTPUSH
        # Commits with one parent and no review units
        if r == 0:
            commit_type = DIRECTPUSH
        else:
            #FIXME: differentiate between merge policies
            commit_type = ""
    else:
        # MERGE:
        # Commits with two parents
        merge_commits = [commit, parents[1]]

    return [
        commit_type,
        merge_commits,
        review_units
    ]


# Extract the merge requests' commits
def extract_review_units(server, repo, commit):
    if server == GITHUB:
        return github_extract_merge_request_commits (repo, commit)
    else:
        return gerrit_extract_merge_request_commits (repo, commit)