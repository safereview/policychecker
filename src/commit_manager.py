# Install: $ pip install gitpython
from git import Repo
import re
from configs.gerrit_config import *
from constants import *
from gerrit_API import list_groups, get_group_info
from gerrit_API import get_branch_head, get_blob_content


def has_multiple_parents(commit):
    return len(commit.parents) > 1


def has_direct_push_permission(committer, permissions):
    # Get the project config with an API call
    # This code is for testing purposes only
    ap_head = get_branch_head(ALL_PROJECTS, CONFIG_BRANCH)
    project_config = get_blob_content(ALL_PROJECTS, ap_head, CONFIG_PROJECT)
    # # #

    committers_groups = find_group_membership(committer)

    # Extract the 'refs/heads/*' access rights which contains
    # the groups that are allowed to direct push onto ALL branches
    access_rights = re.findall("\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config)[0]

    # Check each group to see if one has the direct push permission
    for g in committers_groups:
        if f"push = group {g}" in access_rights:
            return True

    return False


# Find the groups that a committer is in
def find_group_membership(committer):
    # Get all of the groups in the Gerrit project
    groups = list_groups()
    committers_groups = []

    for g in groups:
        g_id = groups[g]['group_id']
        for member in get_group_info(g_id)['members']:
            if (
                member['name'] == committer.name
                and member['email'] == committer.email
            ):
                committers_groups.append(g)
    
    return committers_groups


# Check if the commit has the first review unit in a chain
def is_first_review(review_units):
    # TODO:
    return True


# Extrcact all review units in a commit
def get_review_units(commit):
    # TODO:
    return []


# Check if the commit has a review unit
def has_review_units(commit):
    if re.search(f"score .*\n.*\n{PGP_START}\n", commit.message):
        return True
    else:
        return False


# Extract PR's commits in a REBASE
def get_rebase_commits(repo, parents):
    merge_commits = []

    #TODO:
    # Get commits until we find the first review unit in the chain
    # Then, keep adding commits until we find a commit that
    # either has a review unit or has multiple parents

    return merge_commits


# Extract commits in a PR
def get_pr_commits(server, repo, parents):
    merge_commits = []

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
                    merge_commits = get_rebase_commits(repo, parents)
            #else
                #FIXME: differentiate between REBASE and SQUASH

        # SQUASH:
        # Commits with one parent and more than one review unit
        else:
            commit_type = SQUASH
    else:
        # MERGE:
        # Commits with two parents
        merge_commits = get_pr_commits(repo, parents)

    return {
        commit_type,
        merge_commits,
        review_units
    }


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

    return {
        commit_type,
        merge_commits,
        review_units
    }