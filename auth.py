"""
Voyager — Auth Utilities
PBKDF2 password hashing · Secure tokens · OTP generation
"""
import hashlib, hmac, secrets, string
from datetime import datetime, timezone, timedelta


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 260_000)
    return f"{salt}:{h.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        check = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 260_000)
        return hmac.compare_digest(check.hex(), h)
    except Exception:
        return False


def gen_token() -> str:
    return secrets.token_urlsafe(48)


def gen_otp(n=6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(n))


def expires_session() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%S")


def expires_otp() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")
