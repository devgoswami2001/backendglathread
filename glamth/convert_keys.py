import base64
from cryptography.hazmat.primitives import serialization

# Load PEM public key
with open("public.pem", "rb") as f:
    public_pem = f.read()

public_key_obj = serialization.load_pem_public_key(public_pem)

# Convert to uncompressed EC point (raw key)
raw_key = public_key_obj.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Convert to Base64URL (browser format)
vapid_public_key = base64.urlsafe_b64encode(raw_key).rstrip(b"=").decode()

print("VAPID PUBLIC KEY (Base64URL):")
print(vapid_public_key)
