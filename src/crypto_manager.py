#TODO:Check integrity before verification
import ed25519

# Verify an ed25519 signature
def verify_signature(crp, sig):
    return 0


# Create an ed25519 signature
def create_signature(crp):
    '''
    Sources:
    https://github.com/warner/python-ed25519
    https://github.com/pyca/pynacl
    TODO:
    1) Use pynacl instead of ed25519
    from nacl.signing import SigningKey
    # Generate a new random signing key
    signing_key = SigningKey.generate()

    # Sign a message with the signing key
    signed = signing_key.sign(b"Attack at Dawn")

    # Obtain the verify key for a given signing key
    verify_key = signing_key.verify_key

    2) Read key from file
    kSIGKEY = "sigKey"
    keydata = open(SIGKEY).read()
    signing_key = ed25519.SigningKey(keydata)

    #open(SIGKEY,"wb").write(signing_key.to_bytes())
    '''

    signing_key, verifying_key = ed25519.create_keypair()
    return signing_key.sign(crp, encoding='hex')


crp = b'Code-Review-Policy'
signed_crp = sign_crp(crp)
print(signed_crp)
