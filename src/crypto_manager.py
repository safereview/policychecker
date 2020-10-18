#TODO:Check integrity before verification

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

# Create an ed25519 signature
def compute_signature(msg):
    # Sign the CRP and store the signature in repo
    signing_key = SigningKey.generate()
    return signing_key.verify_key,\
        signing_key.sign(msg, encoder=HexEncoder).decode()


# Verify an ed25519 signature
def verify_signature(msg, verify_key):
    result = 'Valid Signature!'
    try:
        verify_key.verify(msg, encoder=HexEncoder)
        result = 'Invalid Signature!'
    except BadSignatureError:
        pass

    return result
