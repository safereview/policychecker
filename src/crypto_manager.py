#TODO:Check integrity before verification

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


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

    result = 'Valid Signature!'
    try:
        verify_key.verify(msg_hex, signature_bytes, encoder=HexEncoder)
    except BadSignatureError:
        result = 'Invalid Signature!'
        pass

    return result


# Compute an ed25519 over the CRP 
def sign_crp(crp):
    signing_key, verify_key = generate_key()
    signed_hex = compute_signature(crp, signing_key)
    return signed_hex.signature.decode("utf-8"), verify_key
