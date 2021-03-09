from constants import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from github_API import *
from review_manager import *


# Parse the GitHub CRP
def github_parse_crp(crp):
    # TODO: Split CRP into an array containing the three components
    return 0


# Check if there are minimum number of approavals
def check_min_approvals(crp, review_units):
    protection_rules = github_parse_crp(crp)[PROTECTION_RULES]
    required_approvals = protection_rules['required_pull_request_reviews']

    if not required_approvals:
        # No approvals are required
        return True
    else:
        approvals = 0
        for unit in review_units:
            review = parse_review(
                split_review_unit(unit)[1])

            if review['score'] == '+1':
                approvals += 1

        return approvals == required_approvals 


# Check if there reviews from certain users
def check_required_reviews(crp, review_units):
    #TODO
    return True


# Check if the review dismissal is followed
def check_review_dismissal(crp, review_units):
    #TODO
    return True
