"""Encryption utilities for secure password storage."""
from cryptography.fernet import Fernet
from src.models.config import settings


def get_fernet() -> Fernet:
    """Get Fernet instance with encryption key."""
    # Ensure key is properly formatted (32 bytes base64-encoded)
    key = settings.encryption_key
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_password(password: str) -> str:
    """Encrypt password string."""
    f = get_fernet()
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password string."""
    f = get_fernet()
    decrypted = f.decrypt(encrypted_password.encode())
    return decrypted.decode()