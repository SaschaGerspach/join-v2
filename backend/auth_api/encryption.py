import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)
_warned_fallback = False


def _get_fernet():
    global _warned_fallback
    raw_key = getattr(settings, "TOTP_ENCRYPTION_KEY", None)
    if not raw_key:
        raw_key = settings.SECRET_KEY
        if not settings.DEBUG and not _warned_fallback:
            logger.warning("TOTP_ENCRYPTION_KEY not set — falling back to SECRET_KEY. Set a dedicated key in production.")
            _warned_fallback = True
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
