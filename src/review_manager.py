# Install: $ pip install python-gnupg
# TODO: Make a requirements.txt file to add python-gnupg
# Consider the following note as well:
# https://github.com/secure-systems-lab/securesystemslib/blob/master/securesystemslib/gpg/__init__.py
from crypto_manager import gpg_sign_message


class Review:
    def __init__(self, score, comment = None):
        review = f"score {score}"
        if comment:
             review = f"{comment}\n{review}"
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
        return f"{self.review}\
            \n{self.reviewer.name} <{self.reviewer.email}>\
            \n{signature}"


    def _sign_review_unit(self):
        '''
        The data over which the review unit's signature is computed:
            <signature field of the previous review unit>
            <current review information>
            <reviewer name> <reviewer e-mail>

        The first review unit has no previous signature.
        '''
        payload = f"{self.review}\
            \n{self.reviewer.name} <{self.reviewer.email}>"

        # Add previous review unit's signature if there is any
        if self.previous_signature:
            payload = f"{self.previous_signature}\
                \n{payload}"

        return gpg_sign_message(payload)


# Check if the commit has the first review unit in a chain
def is_first_review(review_units):
    for unit in review_units:
        # Split the unit into the review and signature
        # portions to attempt verification
        signature = PGP_START + unit.split(PGP_START)[1]
        review = unit.split(signature)\
            [0].strip().encode()

        # Create a temporary file containing the
        # review unit's signature as required by Py-GNUPG
        with NamedTemporaryFile('w+') as sig_file:
            sig_file.write(signature)
            sig_file.flush()

            # If the review is successfully verified by the
            # attached signature, the signature was computed
            # over this review only, proving it is the first
            # in the chain
            is_verified = gpg_verify_signature(
                sig_file.name, review)
            if is_verified:
                return True

    return False


# Check if the review unit's signature is valid
def validate_reviews_signatures(review_units):
    #TODO
    return True


# Check if the chain of reviews is valid
def validate_review_chain(review_units):
    #TODO
    return True
