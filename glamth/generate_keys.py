from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# generate EC P-256 private key
private_key = ec.generate_private_key(ec.SECP256R1())

# raw private numbers
priv_num = private_key.private_numbers().private_value

# convert private key → base64url (VAPID format)
private_key_b64 = base64.urlsafe_b64encode(
    priv_num.to_bytes(32, "big")
).rstrip(b'=').decode("utf-8")

# raw public key point (X,Y)
public_key = private_key.public_key()
pub_numbers = public_key.public_numbers()

x = pub_numbers.x.to_bytes(32, "big")
y = pub_numbers.y.to_bytes(32, "big")

# uncompressed EC point: 0x04 || X || Y
uncompressed = b"\x04" + x + y

# convert to base64url (VAPID format)
public_key_b64 = base64.urlsafe_b64encode(
    uncompressed
).rstrip(b'=').decode("utf-8")

print("PUBLIC KEY:", public_key_b64)
print("PRIVATE KEY:", private_key_b64)
