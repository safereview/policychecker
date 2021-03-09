from constants import *
from configs.gerrit_config import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from gerrit_API import *
from commit_manager import find_group_membership


# Check if the committer has the direct push permission
def has_push_permission(committer, permissions):
    # Get the project config with an API call
    # This code is for testing purposes only
    ap_head = get_branch_head(ALL_PROJECTS, CONFIG_BRANCH)
    project_config = get_blob_content(ALL_PROJECTS, ap_head, CONFIG_PROJECT)

    committers_groups = find_group_membership(
        committer.name,
        committer.email
    )
    # Extract the 'refs/heads/*' access rights which contains
    # the groups that are allowed to direct push onto ALL branches
    access_rights = re.search("\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config).group()

    # Check each group to see if one has the direct push permission
    for g in committers_groups:
        if f"push = group {g}" in access_rights:
            return True

    return False


# Check if the merger is authorized
def is_authorized_merger(crp, commits):
    access_rights = re.search("\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config
    ).group()

    committer = commits[0].committer
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
                f"submit = group {g}",
                access_rights
            )
            if match:
                return True

        return False


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


# Find the Gerrit's default policy
def get_gerrit_default_policy(crp):
    parsed_crp = gerrit_parse_crp(crp)

    # Extract the default policy from the project config
    default_policy = re.search("function.*\n", 
        parsed_crp[CONFIG_PROJECT]
    ).group()

    return default_policy.split("=")[1].strip()


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


# Check if the default review policy is followed
def is_submittable(crp, review_units):
    #TODO check if rule is met
    # https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/server/rules/DefaultSubmitRule.java#L107
    # https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/entities/LabelFunction.java#L91-#L123

    # Extract the default policy
    default_policy = get_gerrit_default_policy(crp)
    rule = GERRIT_LABELS[default_policy.upper()]

    # TODO: Pass project_config to the function, as it is parsed earlier
    project_config = gerrit_parse_crp(crp)[CONFIG_PROJECT]

    status = "MAY"
    if rule["isRequired"]:
        status = "NEED"

    for item in review_units:
        signature, review = split_review_unit(item)
        comment, score, reviewer = parse_review(review)

        if score == '0':
            continue

        if rule["isBlock"] and is_max_negative(project_config, score):
            if not is_allowed_to_block(crp, reviewer):
                exit("Committer is not allowed to block the change")
            status = "REJECT"
            return status

        if is_max_positive(project_config, score) or not rule["requiresMaxValue"]:
            if not is_allowed_to_approve(crp, reviewer):
                exit("Committer is not allowed to approve the change")
            status = "MAY"

            if rule["isRequired"]:
                status = "OK"

    return status


# Check if there are minimum number of approavals
def check_min_approvals(crp, review_units):
    #TODO
    return True


# Check if there reviews from certain users
def check_required_reviews(crp, review_units):
    #TODO
    return True