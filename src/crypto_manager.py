#TODO:Check integrity before verification

from gnupg import GPG
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

from constants import GPGHOME


# Generate a pair of key
def generate_key():
    signing_key = SigningKey.generate()
    return signing_key, signing_key.verify_key


# Sign a message using the ed25519 scheme
def compute_signature(msg, signing_key):
    # Generate a hex signature with size of 128 bytes
    # Without using HexEncoder we can have a size of 64 bytes

    # 64-byte signature
    # signed_hex = signing_key.sign(msg, encoder=HexEncoder)
    # signature_bytes = HexEncoder.decode(signed_hex.signature)

    # 128-byte signature
    return signing_key.sign(msg, encoder=HexEncoder)


# Verify an ed25519 signature
def verify_signature(msg, signature, verify_key):
    # Encode the message to hex
    msg_hex = HexEncoder.encode(msg)
    # Decode signature to byte
    signature_bytes = HexEncoder.decode(signature)

    result = True
    try:
        verify_key.verify(msg_hex, signature_bytes, encoder=HexEncoder)
    except BadSignatureError:
        result = False
        pass

    return result


# Compute an ed25519 signature over the CRP
def ed25519_sign_message(crp):
    signing_key, verify_key = generate_key()
    signed_hex = compute_signature(crp, signing_key)
    return signed_hex.signature.decode("utf-8"), verify_key


# Sign a message using the gpg signature
def gpg_sign_message(message):
    gpg = GPG(gnupghome=GPGHOME)
    return gpg.sign(message, detach=True)


# Verify a gpg signature
def gpg_verify_signature(signature_file, message):
    gpg = GPG(gnupghome=GPGHOME)
    return gpg.verify_data(signature_file, message)
