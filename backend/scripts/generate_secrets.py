"""Generate RS256 key material and refresh the local ``.env`` secrets.

Creates ``infra/keys/jwt-private.pem`` / ``infra/keys/jwt-public.pem`` for
production (K8s Secret injection), and rotates ``INTERNAL_TOKEN`` in ``.env``
for local Compose runs.

Run with the backend venv::

    backend/.venv/bin/python backend/scripts/generate_secrets.py
"""

from __future__ import annotations

import re
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[2]
KEYS_DIR = ROOT / "infra" / "keys"


def generate_keypair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def upsert_env(token: str) -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        example = ROOT / ".env.example"
        env_path.write_text(example.read_text() if example.exists() else "", encoding="utf-8")

    content = env_path.read_text(encoding="utf-8")
    if "INTERNAL_TOKEN=" in content:
        content = re.sub(r"^INTERNAL_TOKEN=.*$", f"INTERNAL_TOKEN={token}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip("\n") + f"\nINTERNAL_TOKEN={token}\n"
    env_path.write_text(content, encoding="utf-8")


def main() -> None:
    private_pem, public_pem = generate_keypair()
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    (KEYS_DIR / "jwt-private.pem").write_text(private_pem, encoding="utf-8")
    (KEYS_DIR / "jwt-public.pem").write_text(public_pem, encoding="utf-8")

    token = secrets.token_hex(32)
    upsert_env(token)

    print(f"Wrote {KEYS_DIR / 'jwt-private.pem'}")
    print(f"Wrote {KEYS_DIR / 'jwt-public.pem'}")
    print(f"Rotated INTERNAL_TOKEN in {ROOT / '.env'}")
    print("For production, inject the PEM files via K8s Secrets (JWT_PRIVATE_KEY / JWT_PUBLIC_KEY).")


if __name__ == "__main__":
    main()