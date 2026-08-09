import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from core import config

ITERATIONS = 100_000

def get_or_create_salt() -> bytes:
    """Gets the existing salt from salt.bin or creates a new 32-byte salt."""
    config.ensure_directories()
    if config.SALT_FILE.exists():
        with open(config.SALT_FILE, "rb") as f:
            return f.read()
    else:
        salt = os.urandom(32)
        with open(config.SALT_FILE, "wb") as f:
            f.write(salt)
        return salt

def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte key from master password using PBKDF2-HMAC-SHA256 with >=600,000 iterations.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS
    )
    return kdf.derive(master_password.encode('utf-8'))

def generate_verification_hash(derived_key: bytes) -> bytes:
    """Generate SHA256 verification hash of derived key to check password validity."""
    return hashlib.sha256(derived_key + b"PM_VERIFY_TOKEN_V1").digest()

def setup_master_password(master_password: str) -> bytes:
    """
    First-run setup: Creates unique salt, derives key, saves verification hash,
    and returns derived key.
    """
    config.ensure_directories()
    salt = os.urandom(32)
    with open(config.SALT_FILE, "wb") as f:
        f.write(salt)
    
    key = derive_key(master_password, salt)
    v_hash = generate_verification_hash(key)
    with open(config.VERIFY_FILE, "wb") as f:
        f.write(v_hash)
        
    return key

def verify_master_password(master_password: str) -> Optional[bytes]:
    """
    Verifies master password against stored verification hash.
    Returns derived key if valid, or None if invalid.
    """
    if not is_vault_initialized():
        return None
    try:
        with open(config.SALT_FILE, "rb") as f:
            salt = f.read()
        with open(config.VERIFY_FILE, "rb") as f:
            expected_v_hash = f.read()
            
        key = derive_key(master_password, salt)
        v_hash = generate_verification_hash(key)
        if hashlib.sha256(v_hash).digest() == hashlib.sha256(expected_v_hash).digest():
            return key
        return None
    except Exception:
        return None

def is_vault_initialized() -> bool:
    """Returns True if first-time setup has been completed."""
    return config.SALT_FILE.exists() and config.VERIFY_FILE.exists()

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt raw bytes using Fernet (AES-128-CBC + HMAC)."""
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    return f.encrypt(data)

def decrypt_data(token: bytes, key: bytes) -> bytes:
    """Decrypt Fernet token into raw bytes."""
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    return f.decrypt(token)
