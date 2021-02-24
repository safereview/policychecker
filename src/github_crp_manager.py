from constants import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from github_API import *


# Parse the GitHub CRP
def github_parse_crp(crp):
    # TODO: Split CRP into an array containing the three components
    return 0

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
