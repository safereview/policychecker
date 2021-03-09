# Install: $ pip install python-gnupg
# TODO: Make a requirements.txt file to add python-gnupg
# Consider the following note as well:
# https://github.com/secure-systems-lab/securesystemslib/blob/master/securesystemslib/gpg/__init__.py
from crypto_manager import gpg_sign_message, gpg_verify_signature
from constants import PGP_START
from tempfile import NamedTemporaryFile
import re

class Review:
    def __init__(self, score, comment = None):
        review = f"score {score}"
        if comment:
             review = f"{comment.strip()}\n{review}"
        self.review = review


class Reviewer:
    def __init__(self, name, email):
        self.name = name
        self.email = email


class ReviewUnit:
    def __init__(self, review, reviewer, previous_signature = None):
        self.review = review
        self.reviewer = reviewer
        self.previous_signature = previous_signature
        self.review_unit = self._form_review_unit()


    def _form_review_unit(self):
        '''
        The format of a review unit:
            <current review information>
            <reviewer name> <reviewer e-mail>
            <review unit signature>
        '''
        signature = self._sign_review_unit()
        return (
            f"{self.review}"
            f"\n{self.reviewer.name} <{self.reviewer.email}>"
            f"\n{signature}"
        )


    def _sign_review_unit(self):
        '''
        The data over which the review unit's signature is computed:
            <signature field of the previous review unit>
            <current review information>
            <reviewer name> <reviewer e-mail>

        The first review unit has no previous signature.
        '''
        payload = (
            f"{self.review}"
            f"\n{self.reviewer.name} <{self.reviewer.email}>"
        )

        # Add previous review unit's signature if there is any
        if self.previous_signature:
            payload = f"{self.previous_signature}{payload}"

        return gpg_sign_message(payload)


# Check if a list of review units has the first unit in a chain
def is_first_review(review_units):
    for unit in review_units:
        # If the review is successfully verified by the
        # attached signature, the signature was only computed
        # over this review, proving it is the first
        # in the chain
        if validate_review_signature(unit):
            return True

    return False


# Check if a review unit's signature is valid
def validate_review_signature(review_unit, previous_signature = None):
    signature, review = split_review_unit(review_unit)

    # If there is a previous signature, the current
    # review unit's signature must have been computed
    # over the previous signature and the current review
    if previous_signature:
        review = f"{previous_signature}{review}"
    
    # Create a temporary file containing the
    # review unit's signature as required by Py-GnuPG
    with NamedTemporaryFile('w+') as sig_file:
        sig_file.write(signature)
        sig_file.flush()

        # Attempt to verify the signature against
        # the computed review
        is_verified = gpg_verify_signature(
            sig_file.name, review.encode()
        )

    return is_verified


# Check if the chain of reviews is valid
def validate_review_signatures(review_units):
    previous_signature = ""

    # Iterate through the list in reverse order as
    # the last review unit in the original list
    # should be the first in the chain
    for unit in reversed(review_units):
        # Any unit that is not the first review and
        # whose signature is not verified against the previous unit's
        # signature does not belong in the chain
        if not validate_review_signature(unit, previous_signature):
            return False
        # Update the previous signature as we iterate
        # through the list
        previous_signature = split_review_unit(unit)[0]
    
    return True


# Split a review unit into the review and signature
def split_review_unit(review_unit):
    signature = (
        f"{PGP_START}"
        f"{review_unit.split(PGP_START)[1]}"
    )
    review = review_unit.split(signature)\
        [0].rstrip()

    return [
        signature,
        review
    ]


# Parse a review into the comment, score, reviewer info.
def parse_review(review):
    # Save relevant info. into capture groups
    parsed_review = re.search(
        '([\s\S]+?)\nscore ([+-]?[0-9]+?)\n(.*) <(.*)>', 
        review
    )
    comment, score, reviewer_name, reviewer_email \
        = parsed_review.groups()

    return [
        comment,
        score,
        {
            'name': reviewer_name,
            'email': reviewer_email
        }
    ]