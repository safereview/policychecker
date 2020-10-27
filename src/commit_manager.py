# Install: $ pip install pygit2
from pygit2 import Repository

# Extract merge request commits given a PyGit2 repository object and the commit's hash
def extract_merge_request_commits(repo, commit_id, permissions):
    commit = repo.get(commit_id)
    parents = commit.parent_ids

    if len(parents) == 0:
        return
    else:
        committer = commit.committer.name
        
        if not has_review_units(commit) and not has_direct_push_permission(committer, permissions):
            return 'A suspicious commit is found!'
        else:
            if len(parents) == 1:
                return commit
            else:
                second_parent = repo.get(parents[1])
                return (commit, second_parent)


def has_review_units(commit):
    return True


def has_direct_push_permission(committer, permissions):
    return True
