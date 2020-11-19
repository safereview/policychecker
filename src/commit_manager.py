# Install: $ pip install gitpython
from git import Repo
import re
from configs.gerrit_config import *
from constants import *


def has_multiple_parents(commit):
    return len(commit.parents) > 1


def has_direct_push_permission(committer, permissions):
    return True


def get_review_units(commit):
    return []


def is_first_review(review_units):
    return True


def has_review_units(commit):
    if re.search(f"score .*\n.*\n{PGP_START}\n", commit.message):
        return True
    else:
        return False


# Find GitHub merge policy
def github_extract_merge_policy(commit):
    review_units = get_review_units(commit)
    merge_policy = MERGE

    if len(commit.parents) == 1:
        if len(review_units) == 1:
            if not is_first_review(review_units):
                merge_policy = REBASE
            else:
                merge_policy = SQUASH
        else:
            merge_policy = SQUASH

    return merge_policy


# Extract merge requests' commits for GitHub
# TODO: Support all merge policies including rebase and squash and merge.
def github_extract_merge_request_commits(repo, commit):
    parents = commit.parents

    if not parents:
        return [FIRSTCOMMIT, []]
    else:
        review_units = get_review_units(commit)
        if len(parents) == 1:
            if not review_units:
                return [DIRECTPUSH, [commit]]
        else:
            merge_policy = github_extract_merge_policy(commit)
            merge_commits = [merge_policy, [commit]]

            if merge_policy == SQUASH:
                return merge_commits

            elif merge_policy == MERGE:
                common_ancestor = repo.merge_base(parents[0], parents[1])[0]
                merge_commit_ids = repo.git.rev_list('--ancestry-path', 
                f'{common_ancestor.hexsha}..{parents[1].hexsha}').split()

                for id in merge_commit_ids:
                    merge_commits[1].append(repo.commit(id))

            elif merge_policy == REBASE:
                pass
                # Get commits until we find the first review unit in the chain
                # Then, keep adding commits until we find a commit that
                # either has a review unit or has multiple parents
                
        return merge_commits


# Extract merge requests' commits for Gerrit
def gerrit_extract_merge_request_commits(commit, permissions):
    parents = commit.parents

    if not parents:
        return []
    else:
        committer = commit.committer
        if (
            not has_review_units(commit)
            and not has_direct_push_permission(committer, permissions)
        ):
            return 'A suspicious commit is found!'
        else:
            if len(parents) == 1:
                return [commit]
            else:
                return [commit, parents[1]]
