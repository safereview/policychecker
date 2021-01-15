from constants import *
from configs.gerrit_config import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from gerrit_API import *
from github_API import *


# Parse the GitHub CRP
def github_parse_crp(crp):
    return 0


# Check if the merger is authorized
def is_authorized_merger(crp, commits):
    #TODO
    return True


# Check if the committer is authorized
def is_authorized_committer(crp, commits):
    #TODO
    return True


# Check if the committer is allowed to block the change
def is_allowed_to_block(crp, committer):
    #TODO:
    return True


# Check if the committer is allowed to approve the change
def is_allowed_to_approve(crp, committer):
    #TODO:
    return True


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
    #TODO
    return 2


# Find the max negative score
def get_max_negative(project_config):
    #TODO
    return -2


# Check if the score is max positive
def is_max_positive (project_config, score):
    return score == get_max_positive(project_config)


# Check if the score is max negative
def is_max_negative (project_config, score):
    return score == get_max_negative(project_config)


# Parse the Gerrit CRP
def gerrit_parse_crp(crp):
    #TODO: extarct three parts of the crp
    PCONFIG = r"\[label \"Code-Review\"\]\n\
	function = MaxWithBlock\n\
	defaultValue = 0\n"
    return PCONFIG


def gerrit_extract_labels(crp):
    #TODO: Extract config file from crp
    project_config = gerrit_parse_crp(crp)

    # Extract the default policy from the pro
    default_policy = re.search("function.*\n", project_config).group()
    return default_policy.split("=")[1].strip()