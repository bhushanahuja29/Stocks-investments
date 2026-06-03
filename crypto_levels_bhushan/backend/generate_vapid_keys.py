"""Generate VAPID keys for Web Push. Run once and add output to .env"""

import base64

from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
from py_vapid import Vapid

v = Vapid()
v.generate_keys()

raw_pub = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
public_b64 = base64.urlsafe_b64encode(raw_pub).decode("ascii").rstrip("=")

private_pem = v.private_key.private_bytes(
    Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
).decode("ascii")

print("Add these to your environment (backend .env or system env):\n")
print("VAPID_SUBJECT=mailto:your-email@example.com")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print("VAPID_PRIVATE_KEY=<paste PEM below — keep newlines or use \\n>")
print(private_pem)
