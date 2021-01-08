# Install: $ pip install gitpython
from git import Repo
import re
from configs.gerrit_config import *
from constants import *
from gerrit_API import list_groups, get_group_info
from gerrit_API import get_ref_access_rights
from tempfile import NamedTemporaryFile
from review_unit import gpg_verify_data


def has_multiple_parents(commit):
    return len(commit.parents) > 1


def has_direct_push_permission(committer, permissions):
    # Extract all of the groups in the Gerrit repostiory
    groups = list_groups()
    committer_groups = []

    # Find the groups that the committer belongs to
    for g in groups:
        g_id = groups[g]['group_id']
    
        for member in get_group_info(g_id)['members']:
            if (
                member['name'] == committer.name
                and member['email'] == committer.email
            ):
                committer_groups.append(g)

    # Check all of the groups the committer is in to see if
    # any of them have direct push permissions
    access_rights = get_ref_access_rights(project, 'refs/heads/*')
    for c_g in committer_groups:
        if f'push = group {c_g}' in access_rights:
            return True

    return False


# Check if the commit has the first review unit in a chain
def is_first_review(review_units):
    for unit in review_units:
        # Split the unit into the review and signature
        # portions to attempt verification
        signature = PGP_START + unit.split(PGP_START)[1]
        review = unit.split(signature)\
            [0].strip().encode()

        # Create a temporary file containing the 
        # review unit's signature as required by Py-GNUPG
        with NamedTemporaryFile('w+') as sig_file:
            sig_file.write(signature)
            sig_file.flush()

            # If the review is successfully verified by the
            # attached signature, the signature was computed
            # over this review only, proving it is the first 
            # in the chain
            is_verified = gpg_verify_data(
                sig_file.name, review)
            if is_verified:
                return True

    return False


# Extrcact all review units in a commit
def get_review_units(commit):
    return re.findall(f"[\\s\\S]*?[\n]?score.*\
        \n.*\n{PGP_START}[\\s\\S]+?{PGP_END}", 
        commit.message)


# Check if the commit has a review unit
def has_review_units(commit):
    return bool(re.search(f"score .*\n.*\n{PGP_START}\n",
        commit.message))


# Extract PR's commits in a REBASE
def get_rebase_commits(repo, commit):
    merge_commits = []
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
