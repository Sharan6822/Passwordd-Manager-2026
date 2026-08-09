import json
import secrets
import string
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from core import config
from core.crypto import encrypt_data, decrypt_data
from core.logger import log_activity

AMBIGUOUS_CHARS = set("l1Io0O|S5B8Z2")

DEFAULT_WORDS = [
    "Falcon", "Cascade", "Summit", "Vanguard", "Horizon",
    "Nebula", "Titan", "Matrix", "Cipher", "Phoenix"
]

# --- Memorable Words Storage ---

def load_memorable_words(key: bytes) -> List[str]:
    """Load and decrypt the 10 memorable words."""
    config.ensure_directories()
    if not config.WORDS_FILE.exists():
        return DEFAULT_WORDS.copy()
    try:
        with open(config.WORDS_FILE, "rb") as f:
            encrypted_data = f.read()
        if not encrypted_data:
            return DEFAULT_WORDS.copy()
        raw_data = decrypt_data(encrypted_data, key)
        words = json.loads(raw_data.decode("utf-8"))
        if isinstance(words, list) and len(words) >= 2:
            return words
        return DEFAULT_WORDS.copy()
    except Exception:
        return DEFAULT_WORDS.copy()

def save_memorable_words(words: List[str], key: bytes):
    """Encrypt and save memorable words list."""
    config.ensure_directories()
    # Filter and clean words
    cleaned_words = [w.strip() for w in words if w.strip()]
    if len(cleaned_words) < 2:
        raise ValueError("Must provide at least 2 non-empty personal words.")
    raw_bytes = json.dumps(cleaned_words).encode("utf-8")
    encrypted_bytes = encrypt_data(raw_bytes, key)
    with open(config.WORDS_FILE, "wb") as f:
        f.write(encrypted_bytes)
    log_activity("MEMORABLE_WORDS_UPDATE", f"Updated {len(cleaned_words)} personal words.")

# --- Password Generators ---

def generate_standard_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = True
) -> str:
    """
    Generate a cryptographically secure random password based on character sets.
    """
    length = max(8, min(64, length))
    
    charset = ""
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    if exclude_ambiguous:
        upper = "".join(c for c in upper if c not in AMBIGUOUS_CHARS)
        lower = "".join(c for c in lower if c not in AMBIGUOUS_CHARS)
        digits = "".join(c for c in digits if c not in AMBIGUOUS_CHARS)
        symbols = "".join(c for c in symbols if c not in AMBIGUOUS_CHARS)
        
    pools = []
    if use_upper and upper:
        pools.append(upper)
    if use_lower and lower:
        pools.append(lower)
    if use_digits and digits:
        pools.append(digits)
    if use_symbols and symbols:
        pools.append(symbols)
        
    if not pools:
        # Fallback to lower + digits if nothing selected
        pools = [lower if lower else string.ascii_lowercase, digits if digits else string.digits]
        
    charset = "".join(pools)
    
    # Guarantee at least one char from each selected pool
    password_chars = [secrets.choice(pool) for pool in pools]
    
    # Fill remainder
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(charset))
        
    # Shuffle cryptographically
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)

def generate_memorable_password(words: List[str]) -> str:
    """
    Generate a memorable word-based password using 2 random words,
    random casing, separator, digits, and symbols.
    Example: Tiger#47-Comet or Dallas@89_Pizza!
    """
    if len(words) < 2:
        words = DEFAULT_WORDS.copy()
        
    # Pick 2 distinct words
    w1, w2 = secrets.SystemRandom().sample(words, 2)
    
    # Apply casing variations
    casing_ops = [
        lambda w: w.capitalize(),
        lambda w: w.upper(),
        lambda w: w.lower(),
        lambda w: w.swapcase()
    ]
    w1_cased = secrets.choice(casing_ops)(w1)
    w2_cased = secrets.choice(casing_ops)(w2)
    
    separators = ["-", "_", "#", ".", "@", "!", "$", "&"]
    sep1 = secrets.choice(separators)
    sep2 = secrets.choice(separators)
    
    number = secrets.randbelow(90) + 10  # 2-digit number (10-99)
    symbol = secrets.choice("!@#$%^&*?")
    
    # Format pattern variations
    patterns = [
        f"{w1_cased}{symbol}{number}{sep1}{w2_cased}",
        f"{w1_cased}{sep1}{number}{sep2}{w2_cased}{symbol}",
        f"{w1_cased}{sep1}{w2_cased}{symbol}{number}",
        f"{symbol}{w1_cased}{sep1}{number}{sep2}{w2_cased}"
    ]
    
    return secrets.choice(patterns)

# --- Generator History Storage ---

def load_generator_history(key: bytes) -> List[Dict]:
    """Load and decrypt generator history from history/generator_history.enc."""
    config.ensure_directories()
    if not config.HISTORY_FILE.exists():
        return []
    try:
        with open(config.HISTORY_FILE, "rb") as f:
            encrypted_data = f.read()
        if not encrypted_data:
            return []
        raw_data = decrypt_data(encrypted_data, key)
        return json.loads(raw_data.decode("utf-8"))
    except Exception:
        return []

def add_generator_history_entry(password: str, mode: str, key: bytes, assigned_to: str = ""):
    """Add a generated password entry to encrypted generator history."""
    config.ensure_directories()
    history = load_generator_history(key)
    new_record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "password": password,
        "mode": mode,  # "standard" or "memorable"
        "assigned_to": assigned_to.strip()
    }
    history.insert(0, new_record)  # Newest first
    # Limit history to 200 entries
    history = history[:200]
    
    raw_bytes = json.dumps(history, indent=2).encode("utf-8")
    encrypted_bytes = encrypt_data(raw_bytes, key)
    with open(config.HISTORY_FILE, "wb") as f:
        f.write(encrypted_bytes)
    log_activity("GENERATOR_HISTORY_ADD", f"Saved generated password ({mode} mode)")

def clear_generator_history(key: bytes):
    """Clear all generator history entries."""
    config.ensure_directories()
    raw_bytes = json.dumps([]).encode("utf-8")
    encrypted_bytes = encrypt_data(raw_bytes, key)
    with open(config.HISTORY_FILE, "wb") as f:
        f.write(encrypted_bytes)
    log_activity("GENERATOR_HISTORY_CLEAR", "Cleared password generator history.")
