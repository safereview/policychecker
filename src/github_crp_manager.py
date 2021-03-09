from constants import *
from configs.github_config import *
from crypto_manager import ed25519_sign_message
from github_API import *
from ast import literal_eval


# Parse the GitHub CRP
def github_parse_crp(crp):
    # Since the CRP is formed from byte objects
    # coerced into strings, there will be a " b' "
    # delimiter inbetween the components
    # Perhaps this can be changed into more clear
    # delimiters?
    protection_rules, codeowners, gitattributes = \
        re.search(
            "({[\s\S]+?})b['\"]{1}([\s\S]+?)['\"]"
            "{1}b['\"]{1}([\s\S]+?)['\"]{1}",
            crp.decode()
        ).groups()

    return {
        # Turn protection rules string into a dictionary
        PROTECTION_RULES: literal_eval(protection_rules),
        # Turn escaped whitespace characters back into
        # the actual characters
        CODEOWNERS: codeowners.encode('utf-8'
                    ).decode('unicode-escape'),
        GITATTRIBUTES: gitattributes.encode('utf-8'
                    ).decode('unicode-escape')
    }


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
