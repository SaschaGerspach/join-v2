import base64

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet():
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b"\0"))
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
