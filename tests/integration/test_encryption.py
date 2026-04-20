"""Simple integration test for encryption without Docker."""
import pytest


@pytest.mark.asyncio
async def test_encryption_roundtrip():
    """Test that password can be encrypted and decrypted."""
    import os
    from cryptography.fernet import Fernet
    
    # Generate a test key
    key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = key
    
    # Import after setting env var
    from src.utils.encryption import encrypt_password, decrypt_password
    
    # Test encryption roundtrip
    original_password = "my_secret_password_123"
    encrypted = encrypt_password(original_password)
    decrypted = decrypt_password(encrypted)
    
    assert encrypted != original_password
    assert decrypted == original_password


@pytest.mark.asyncio
async def test_different_passwords_different_encryption():
    """Test that different passwords produce different encrypted values."""
    import os
    from cryptography.fernet import Fernet
    
    key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = key
    
    from src.utils.encryption import encrypt_password
    
    password1 = "password123"
    password2 = "password456"
    
    encrypted1 = encrypt_password(password1)
    encrypted2 = encrypt_password(password2)
    
    assert encrypted1 != encrypted2