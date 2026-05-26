import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet():
    raw_key = getattr(settings, "TOTP_ENCRYPTION_KEY", None) or settings.SECRET_KEY
    derived = hashlib.pbkdf2_hmac("sha256", raw_key.encode(), b"join-totp-encryption", 600_000)
    key = base64.urlsafe_b64encode(derived[:32])
    return Fernet(key)


def encrypt_totp_secret(plain: str) -> str:
    if not plain:
        return ""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_totp_secret(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        return encrypted
