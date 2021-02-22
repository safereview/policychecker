#TODO:Check integrity before verification

from gnupg import GPG
from nacl.encoding import HexEncoder, Base64Encoder
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

from constants import KEYS_DIR, ED25519_KEY
import re

# Load public key info from a local path
def load_local_pub_keys(local_path):
    gpg = GPG(gnupghome = local_path)
    # Get GPG public keys
    public_keys = gpg.list_keys()
    key_info = {'GPG':[], 'Ed25519':[]}

    # Collect key info for GPG keys
    for key in public_keys:
        uids = []
        for uid in key['uids']:
            name, email = re.search(
                '(.*) <(.*)>', uid).groups()

            uids.append({'name': name, 
                'email': email})
        
        key_info['GPG'].append({
            'key_id': key['keyid'],
            'uids': uids})

    # Search for any Ed25519 verify key files
    # and store the created VerifyKey objects
    ed25519_key_path = f"{local_path}/{ED25519_KEY}"
    try:
        with open(ed25519_key_path, 'r') as f:
            content = f.read()
            # Extract the Base64 string
            # representing the serialized verify key
            # and encode it back to bytes
            key_b64 = re.search(
                "-----BEGIN PUBLIC KEY-----\n"
                "(.*)\n-----END PUBLIC KEY-----", 
                content
            ).group(1).encode()

        # Create a verify key object from
        # the Base64 serialized bytes
        key_info['Ed25519'].append(
            VerifyKey(key_b64, encoder=Base64Encoder)
        )
    except:
        pass

    return key_info


# Generate a pair of key
def generate_key():
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    # Store the verify key bytes as
    # a Base64 encoded string
    verify_key_b64 = verify_key.encode(
        encoder=Base64Encoder
        ).decode("utf-8")

    # Prepare a PEM formatted string
    pem_str = (
        "-----BEGIN PUBLIC KEY-----\n"
        f"{verify_key_b64}\n"
        "-----END PUBLIC KEY-----"
    )

    # Save PEM file for future verify key retrieval
    f = open(ED25519_KEY, "w")
    f.write(pem_str)
    f.close()
    
    return signing_key, verify_key



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
    gpg = GPG(gnupghome = KEYS_DIR)
    return gpg.sign(message, detach=True)


# Verify a gpg signature
def gpg_verify_signature(signature_file, message):
    gpg = GPG(gnupghome = KEYS_DIR)
    return gpg.verify_data(signature_file, message)
