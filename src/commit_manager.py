# Install: $ pip install gitpython
from git import Repo
import re

# Extract merge request commits given a GitPython Commit object
def gerrit_extract_merge_request_commits(commit, permissions):
    parents = commit.parents

    if not parents:
        return []
    else:
        committer = commit.committer    
        if not has_review_units(commit) and not has_direct_push_permission(committer, permissions):
            return 'A suspicious commit is found!'
        else:
            if len(parents) == 1:
                return [commit]
            else:
                return [commit, parents[1]]


def has_review_units(commit):
    if re.search('score .*\n.*\n-----BEGIN PGP SIGNATURE-----\n', commit.message):
        return True
    else:
        return False


def has_direct_push_permission(committer, permissions):
    return True


# TODO: Extract merge commits for other merge policies such as rebase / fast forward, and squash and merge.
def github_extract_merge_request_commits(repo, commit):
    parents = commit.parents

    if not parents:
        return ['FirstCommit', []]
    else:
        review_units = get_review_units(commit)
        if len(parents) == 1:
            if not review_units:
                return ['DirectPush', [commit]]
        else:
            merge_policy = extract_merge_policy(commit)
            merge_commits = [merge_policy, [commit]]

            if merge_policy == 'SquashAndMerge':
                return merge_commits

            elif merge_policy == 'Merge':
                common_ancestor = repo.merge_base(parents[0], parents[1])[0]
                merge_commit_ids = repo.git.rev_list('--ancestry-path', f'{common_ancestor.hexsha}..{parents[1].hexsha}').split()
                for id in merge_commit_ids:
                    merge_commits[1].append(repo.commit(id))

            elif merge_policy == 'Rebase':
                pass
                # Keep adding commits to merge_commits until is_first_review == true
                # Then, keep adding commits until a commit has_a_review unit or has_multiple_parents
                
        return merge_commits


def extract_merge_policy(commit):
    review_units = get_review_units(commit)
    merge_policy = 'Merge'

    if len(commit.parents) == 1:
        if len(review_units) == 1:
            if not is_first_review(review_units):
                merge_policy = 'Rebase'
            else:
                merge_policy = 'SquashAndMerge'
        else:
            merge_policy = 'SquashAndMerge'

    return merge_policy


def get_review_units(commit):
    return []


def is_first_review(review_units):
    return True


def has_multiple_parents(commit):
    return len(commit.parents) > 1
