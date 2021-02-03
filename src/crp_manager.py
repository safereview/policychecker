from constants import *
from configs.gerrit_config import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from gerrit_API import *
from github_API import *
from commit_manager import find_group_membership

# Parse the GitHub CRP
def github_parse_crp(crp):
    return 0


# Check if the merger is authorized
def is_authorized_merger(crp, commits):
    #TODO
    return True


# Check if the committer is authorized
def is_authorized_committer(crp, commits):
    # Get the access rights to the refs/for/refs/*
    # namespace, which is where changes
    # requesting a code review are pushed to
    access_rights = re.search(
            '\[access "refs\/for\/refs\/\*"\]'
            '[\s\S]+?(?=\[)', crp
    ).group()

    for commit in commits:
        committer = commit.committer
        committers_groups = find_group_membership(
            committer.name,
            committer.email
        )
        
        if not committers_groups:
            return False
        else:
            for g in committers_groups:
                # Check if the committer belongs to a 
                # group that is allowed to push changes
                # for code review
                match = re.search(
                    f"push = group {g}",
                    access_rights
                )
                if not match:
                    return False
    
            return True


# Check if the committer is allowed to block the change
def is_allowed_to_block(crp, reviewer):
    # Note: the groups that a reviewer belongs to
    # are retrieved using the Gerrit API. In the future,
    # the CRP might be extended to include each groups'
    # members instead.
    committers_groups = find_group_membership(
        reviewer['name'],
        reviewer['email']
    )

    # Extract the refs/heads/* access rights
    # which contain the code review permissions that 
    # apply to all branches
    access_rights = re.search(
        "\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", crp
    ).group()

    max_negative = get_max_negative(crp)

    # Check if the committer belongs to a group
    # that is allowed to vote the max negative
    # score and thus block a change
    for g in committers_groups:
        match = re.search(
            "label-Code-Review = "
            f"{max_negative}..[+-]?[0-9]+? group {g}",
            access_rights
        )
        if match:
            return True

    return False


# Check if the committer is allowed to approve the change
def is_allowed_to_approve(crp, reviewer):
    committers_groups = find_group_membership(
        reviewer['name'],
        reviewer['email']
    )

    access_rights = re.search(
        "\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", crp
    ).group()

    max_positive = get_max_positive(crp)

    for g in committers_groups:
        match = re.search(
            "label-Code-Review = "
            f"[+-]?[0-9]+?..{max_positive} group {g}",
            access_rights
        )
        if match:
            return True

    return False


# Check if there are minimum number of approavals
def check_min_approvals(crp, review_units):
    #TODO
    return True


# Check if there reviews from certain users
def check_required_reviews(crp, review_units):
    #TODO
    return True


# Check if the review dismissal is followed
def check_review_dismissal(crp, review_units):
    #TODO
    return True


# Find the max positive score
def get_max_positive(project_config):
    return get_gerrit_scores(project_config)[-1]


# Find the max negative score
def get_max_negative(project_config):
    return get_gerrit_scores(project_config)[0]


# Get a sorted list of all score options
def get_gerrit_scores(project_config):
    # Extract code review settings
    code_review_label = re.search(
        '(?<=\[label "Code-Review"\])[\s\S]+?(?=\[)',
        project_config
    ).group()

    # Retrieve all of the available score
    # options
    scores = re.findall(
        '(?<=value = )[-+]?[0-9]+?', 
        code_review_label
    )
    
    return sorted(scores, key = int)


# Check if the score is max positive
def is_max_positive (project_config, score):
    return score == get_max_positive(project_config)


# Check if the score is max negative
def is_max_negative (project_config, score):
    return score == get_max_negative(project_config)


# Parse the Gerrit CRP
def gerrit_parse_crp(crp):
    # Split CRP into an array containing the three components
    split_crp = re.split('(\[project\]\n|# UUID)', crp)
    rules = split_crp[0]
    # Join the appropriate elements together
    project_config = ''.join(split_crp[1:3]).rstrip()
    groups = ''.join(split_crp[3:])

    return {
        CONFIG_RULES: rules,
        CONFIG_PROJECT: project_config,
        CONFIG_GROUPS: groups
    }


def gerrit_extract_labels(crp):
    parsed_crp = gerrit_parse_crp(crp)

    # Extract the default policy from the pro
    default_policy = re.search("function.*\n", 
        parsed_crp[CONFIG_PROJECT]
    ).group()

    return default_policy.split("=")[1].strip()