from constants import *
from configs.gerrit_config import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from gerrit_API import *
from commit_manager import get_pr_code_changes


# Parse the Gerrit CRP
def _gerrit_parse_crp(crp):
    # Extract the components from the CRP
    rules, project_config, groups = \
        re.search(
            "RULES\n([\s\S]*?)\nPROJECTCONFIG\n([\s\S]*?)"
            "\nGROUPS\n([\s\S]*)",
            crp.decode()
        ).groups()

    return {
        CONFIG_RULES: rules,
        CONFIG_PROJECT: project_config,
        CONFIG_GROUPS: groups
    }


# Check if the merger is authorized to perfomr a merge request
def _is_authorized_merger(project_config, committer):
    # Get committer group
    committers_groups = find_group_membership(
        committer.name,
        committer.email
    )
    
    # Extract access rights for the 'refs/heads/*' 
    # and check if the user has the right permission
    access_rights = re.search("\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config
        ).group()

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


# Check if the PR Creator has permission to create a change
def _is_authorized_author(project_config, merge_commits):
    # Get commits with code changes in a PR
    commits = get_pr_code_changes (merge_commits)

    # Extract access rights for the 'refs/for/refs/*' 
    # and check if the user has the right permission
    access_rights = re.search(
            '\[access "refs\/for\/refs\/\*"\]'
            '[\s\S]+?(?=\[)', project_config
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


# Check if the committer has the direct push permission
def _is_authorized_direct_push(project_config, committer):
    # Get committer group
    # NOTE: the groups that a user belongs to are retrieved
    # using the Gerrit API. In the future, the CRP might be 
    # extended to include each groups' members instead.
    committers_groups = find_group_membership(
        committer.name,
        committer.email
    )

    # Extract access rights for the 'refs/heads/*' 
    # and check if the user has the right permission
    access_rights = re.search("\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config
        ).group()

    # TODO: Can we do it more efficiently 
    for g in committers_groups:
        if f"push = group {g}" in access_rights:
            return True

    return False


# Check if the committer is allowed to block the change
def _is_allowed_to_block(project_config, reviewer):
    # Get reviewer group
    committers_groups = find_group_membership(
        reviewer['name'],
        reviewer['email']
    )

    # Extract access rights for the 'refs/heads/*' 
    # and check if the user has the right permission
    access_rights = re.search(
        "\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config
        ).group()

    max_negative = _get_max_negative(project_config)

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
def _is_allowed_to_approve(project_config, reviewer):
    # Get reviewer group
    committers_groups = find_group_membership(
        reviewer['name'],
        reviewer['email']
    )

    # Extract access rights for the 'refs/heads/*' 
    # and check if the user has the right permission
    access_rights = re.search(
        "\[access \"refs/heads/\*\"\]"
        "[\s\S]+?(?=\[)", project_config
    ).group()

    max_positive = _get_max_positive(crp)

    # Check if the committer belongs to a group
    # that is allowed to vote the max positive
    # score and thus approve a change
    for g in committers_groups:
        match = re.search(
            "label-Code-Review = "
            f"[+-]?[0-9]+?..{max_positive} group {g}",
            access_rights
        )
        if match:
            return True

    return False


# Get a sorted list of all score options
def _get_gerrit_scores(project_config):
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


# Find the max positive score
def _get_max_positive(project_config):
    return _get_gerrit_scores(project_config)[-1]


# Find the max negative score
def _get_max_negative(project_config):
    return _get_gerrit_scores(project_config)[0]


# Check if the score is max positive
def _is_max_positive (project_config, score):
    return score == _get_max_positive(project_config)


# Check if the score is max negative
def _is_max_negative (project_config, score):
    return score == _get_max_negative(project_config)


# Find the Gerrit's default policy
def _get_gerrit_default_policy(project_config):

    # Extract the default policy from the project config
    default_policy = re.search("function.*\n", 
        project_config
    ).group()

    return default_policy.split("=")[1].strip()


# Check if the default review policy is followed
def is_submittable(crp, review_units):
    #TODO check if a rule is met
    # https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/server/rules/DefaultSubmitRule.java#L107
    # https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/entities/LabelFunction.java#L91-#L123

    # FIXME: Why we shouldn't use crp[CONFIG_GROUPS]
    
    # Extract the default policy
    project_config = crp[CONFIG_PROJECT]
    default_policy = _get_gerrit_default_policy(project_config)
    rules = GERRIT_LABELS[default_policy.upper()]

    status = "MAY"
    if rules["isRequired"]:
        status = "NEED"

    for item in review_units:
        signature, review = split_review_unit(item)
        comment, score, reviewer = parse_review(review)

        if score == '0':
            continue

        if rules["isBlock"] and _is_max_negative(project_config, score):
            if not _is_allowed_to_block(project_config, reviewer):
                exit("Committer is not allowed to block the change")
            status = "REJECT"
            return status

        if _is_max_positive(project_config, score) or not rules["requiresMaxValue"]:
            if not _is_allowed_to_approve(project_config, reviewer):
                exit("Committer is not allowed to approve the change")
            status = "MAY"

            if rules["isRequired"]:
                status = "OK"

    return status


# Check if the reviews created on GitHub are legitimate
def gerrit_validate_reviews(crp, merge_commits, review_units):
    # Split CPR into three parts: rules.pl, project.config, groups
    crp = _gerrit_parse_crp(crp)

    # First commit in the merge_commits list is the head of PR
    head = merge_commits[0]

    project_config = crp[CONFIG_PROJECT]
    # Check if the merger has the permission
    if not _is_authorized_merger(project_config, head.committer):
        return False

    # Check if the author of code was authorized
    if not _is_authorized_author(project_config, merge_commits):
        return False

    # Check for the direct push permissions
    if merge_commit_type == DIRECTPUSH:
        return _is_authorized_direct_push(project_config, head.committer)

    # Check if there are customized rules
    rules_pl = crp [CONFIG_RULES]
    if rules_pl != '':
        # FIXME:
        exit('Customized rules!')

    # Check if the basic rules (based on labels) are met
    # Make decision based on the status
    #https://github.com/GerritCodeReview/gerrit/blob/master/java/com/google/gerrit/server/rules/DefaultSubmitRule.java#L110
    status = is_submittable(crp, review_units)
    # TODO: Ensure it works for any situations
    if status != "OK":
        return False

    # TODO: Check for other policies if needed
    
    return True
