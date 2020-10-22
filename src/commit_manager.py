# Install: $ pip install pygit2
from pygit2 import Repository

# Extract merge request commits given a PyGit2 repository object and the commit's hash
def extract_merge_request_commits(repo, commit_id): #takes in pygit repo object and commit hash
    commit = repo.get(commit_id)
    parents = commit.parent_ids

    if len(parents) == 0:
        return
    elif len(parents) == 1:
        return commit
    else:
        second_parent = repo.get(parents[1])
        return (commit, second_parent)
