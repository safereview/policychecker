# Install: $ pip install gitpython
from git import Repo

# Extract merge request commits given a GitPython Commit object
def gerrit_extract_merge_request_commits(commit, permissions):
    parents = commit.parents

    if not parents:
        return
    else:
        committer = commit.committer    
        if not has_review_units(commit) and not has_direct_push_permission(committer, permissions):
            return 'A suspicious commit is found!'
        else:
            if len(parents) == 1:
                return commit
            else:
                second_parent = parents[1]
                return [commit, second_parent]


def has_review_units(commit):
    return True


def has_direct_push_permission(committer, permissions):
    return True


# TODO: Extract merge commits for other merge policies such as rebase / fast forward, and squash and merge.
def github_extract_merge_request_commits(repo, commit):
    merge_policy = extract_merge_policy(commit)
    merge_commits = []

    if merge_policy == 'FirstCommit':
        return
    elif merge_policy == 'DirectPush':
        return commit
    elif merge_policy == 'Merge':
        merge_commits.append(commit)
        first_parent = commit.parents[0]
        second_parent = commit.parents[1]
        common_ancestor = repo.merge_base(first_parent, second_parent)[0]
        merge_commit_ids = repo.git.rev_list('--ancestry-path', f'{common_ancestor.hexsha}..{second_parent.hexsha}').split()
        
        for id in merge_commit_ids:
            merge_commits.append(repo.commit(id))

    return merge_commits


def extract_merge_policy(commit):
    parents = commit.parents
    merge_policy = 'Merge'

    if not parents:
        merge_policy = 'FirstCommit'
    else:
        review_units = get_review_units(commit)
        if len(parents) == 1:
            if not review_units:
                merge_policy = 'DirectPush'

    return merge_policy


def get_review_units(commit):
    return []