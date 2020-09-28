# Install: $ pip install python-gnupg
# TODO: Make a requirements.txt file to add python-gnupg
# Consider the following note as well:
# https://github.com/secure-systems-lab/securesystemslib/blob/master/securesystemslib/gpg/__init__.py


def gpg_sign(message):
    from gnupg import GPG
    # TODO: Make it work for any condition in particular
    # when there is no existing keys at ~/.gnupg/
    GPGHOME = '/home/hmd/.gnupg'
    gpg = GPG(gnupghome=GPGHOME)
    return gpg.sign(message)


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
            \n{self.reviewer.name}\ <{self.reviewer.email}>\
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
            \n{self.reviewer.name}\ <{self.reviewer.email}"

        # Add previous review unit's signature if there is any
        if self.previous_signature:
            payload = f"{self.previous_signature}\
                \n{payload}"

        return gpg_sign(payload)


if __name__ == '__main__':
    # Create a simple signed review unit
    review = Review("+1")
    reviewer = Reviewer('Nick Simon', 'nick@example.com')
    ru = ReviewUnit(review.review, reviewer)
    print(ru.review_unit)