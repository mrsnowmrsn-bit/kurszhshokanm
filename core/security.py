"""Парольді хэштеу және тексеру (дерекқорға тәуелсіз)."""
import hashlib
import hmac
import os

from core.config import PBKDF2_ITERATIONS


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def is_modern_hash(stored: str) -> bool:
    return stored.startswith("pbkdf2$")


def verify_password(password: str, stored: str) -> bool:
    if is_modern_hash(stored):
        try:
            _, salt_hex, _ = stored.split("$")
            candidate = hash_password(password, bytes.fromhex(salt_hex))
        except ValueError:
            return False
        return hmac.compare_digest(candidate, stored)
    # Ескі (тұзсыз SHA-256) хэштермен үйлесімділік
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored)
