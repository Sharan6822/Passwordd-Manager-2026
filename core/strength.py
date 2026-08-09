import math
import string
from typing import List, Dict, Tuple, Optional
from core import config

LOWER_SET = set(string.ascii_lowercase)
UPPER_SET = set(string.ascii_uppercase)
DIGIT_SET = set(string.digits)

_COMMON_PASSWORDS_CACHE: Optional[set] = None

def load_common_passwords() -> set:
    """Load bundled common passwords into set for O(1) lookup."""
    global _COMMON_PASSWORDS_CACHE
    if _COMMON_PASSWORDS_CACHE is not None:
        return _COMMON_PASSWORDS_CACHE

    passwords = set()
    if config.COMMON_PASSWORDS_FILE.exists():
        try:
            with open(config.COMMON_PASSWORDS_FILE, "r", encoding="utf-8", errors="ignore") as f:
                passwords = set(p.strip().lower() for p in f.read().splitlines() if p.strip())
        except Exception:
            pass
            
    # Fallback built-in list if file missing
    fallback = {"123456", "password", "123456789", "qwerty", "12345678", "12345", "1234567", "welcome", "admin"}
    passwords.update(fallback)
    _COMMON_PASSWORDS_CACHE = passwords
    return passwords

KEYBOARD_PATTERNS = [
    "qwerty", "asdfgh", "zxcvbn", "123456", "234567", "345678",
    "456789", "567890", "qwertyuiop", "asdfghjkl", "zxcvbnm",
    "qwer", "asdf", "zxcv", "1234", "abcd"
]

def calculate_entropy(password: str) -> float:
    """Calculate bits of entropy for a password."""
    if not password:
        return 0.0
        
    pw_set = set(password)
    has_lower = bool(pw_set & LOWER_SET)
    has_upper = bool(pw_set & UPPER_SET)
    has_digits = bool(pw_set & DIGIT_SET)
    has_symbols = bool(pw_set - LOWER_SET - UPPER_SET - DIGIT_SET)
    
    charset_size = (26 if has_lower else 0) + (26 if has_upper else 0) + (10 if has_digits else 0) + (32 if has_symbols else 0)
        
    if charset_size == 0:
        return 0.0
        
    return len(password) * math.log2(charset_size)

def analyze_password(password: str, vault_entries: Optional[List[Dict]] = None, current_entry_id: Optional[str] = None) -> Dict:
    """
    Perform deep offline strength analysis on a password.
    Returns dict containing score, label, color, entropy, and feedback rules.
    """
    if not password:
        return {
            "score": 0,
            "label": "Very Weak",
            "color": "#ff4d4d",
            "entropy": 0.0,
            "feedback": ["Password cannot be empty."]
        }
        
    feedback = []
    penalty = 0
    bonus = 0
    
    # 1. Entropy calculation
    entropy = calculate_entropy(password)
    
    # 2. Length evaluation
    length = len(password)
    if length < 8:
        feedback.append("Too short: minimum 8 characters recommended (14+ ideal).")
        penalty += 35
    elif length < 12:
        feedback.append("Moderate length: consider expanding to 14+ characters.")
        bonus += 10
    elif length >= 14:
        bonus += 25
        
    # 3. Character diversity checks
    pw_set = set(password)
    has_lower = bool(pw_set & LOWER_SET)
    has_upper = bool(pw_set & UPPER_SET)
    has_digits = bool(pw_set & DIGIT_SET)
    has_symbols = bool(pw_set - LOWER_SET - UPPER_SET - DIGIT_SET)
    
    types_count = sum([has_lower, has_upper, has_digits, has_symbols])
    if types_count <= 1:
        feedback.append("Lacks character variety: combine uppercase, lowercase, digits, and symbols.")
        penalty += 25
    elif types_count >= 3:
        bonus += 15
        
    # 4. Common password dictionary check (Offline)
    common_set = load_common_passwords()
    if password.lower() in common_set:
        feedback.append("CRITICAL: Password matches a known leaked dictionary password!")
        penalty += 50
        
    # 5. Keyboard pattern detection
    pw_lower = password.lower()
    for pattern in KEYBOARD_PATTERNS:
        if pattern in pw_lower:
            feedback.append(f"Contains predictable keyboard pattern ('{pattern}').")
            penalty += 20
            break
            
    # 6. Vault duplicate reuse check
    if vault_entries:
        reused_in = []
        for entry in vault_entries:
            if current_entry_id and entry.get("id") == current_entry_id:
                continue
            if entry.get("password") == password:
                reused_in.append(entry.get("site_name", "another entry"))
        if reused_in:
            sites_str = ", ".join(reused_in[:3])
            feedback.append(f"WARNING: Password reused in vault entry ({sites_str}).")
            penalty += 30

    # Calculate final score (0 - 100)
    raw_score = min(100, max(0, int(entropy * 1.1) + bonus - penalty))
    
    # Force low score if dictionary matched or extremely short
    if password.lower() in common_set:
        raw_score = min(20, raw_score)
        
    if raw_score < 35:
        label = "Weak"
        color = "#8a92a3"  # Soft slate
    elif raw_score < 65:
        label = "Fair"
        color = "#adb5c7"  # Muted silver
    elif raw_score < 85:
        label = "Strong"
        color = "#d0d7de"  # Bright silver
    else:
        label = "Very Strong"
        color = "#ffffff"  # Pure white
        
    if not feedback:
        feedback.append("Excellent password strength and entropy.")
        
    return {
        "score": raw_score,
        "label": label,
        "color": color,
        "entropy": round(entropy, 1),
        "feedback": feedback
    }
