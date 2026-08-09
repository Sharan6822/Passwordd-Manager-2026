import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from core import config
from core.crypto import encrypt_data, decrypt_data
from core.logger import log_activity

DEFAULT_CATEGORIES = ["General", "Work", "Personal", "Financial", "Social"]

def create_empty_vault(key: bytes):
    """Initializes an empty encrypted vault file."""
    save_vault([], key)

def load_vault(key: bytes) -> List[Dict]:
    """Load and decrypt vault entries from data/vault.enc."""
    config.ensure_directories()
    if not config.VAULT_FILE.exists():
        return []
    try:
        with open(config.VAULT_FILE, "rb") as f:
            encrypted_data = f.read()
        if not encrypted_data:
            return []
        raw_data = decrypt_data(encrypted_data, key)
        entries = json.loads(raw_data.decode("utf-8"))
        return entries
    except Exception as e:
        log_activity("VAULT_LOAD_ERROR", f"Failed to decrypt vault: {str(e)}")
        raise ValueError("Could not decrypt vault data. Key may be invalid or file corrupted.")

def save_vault(entries: List[Dict], key: bytes):
    """Encrypt and save vault entries to data/vault.enc."""
    config.ensure_directories()
    raw_bytes = json.dumps(entries, indent=2).encode("utf-8")
    encrypted_bytes = encrypt_data(raw_bytes, key)
    with open(config.VAULT_FILE, "wb") as f:
        f.write(encrypted_bytes)

def add_entry(entries: List[Dict], entry_data: Dict, key: bytes) -> Dict:
    """Add a new password entry to the vault and save."""
    now = datetime.now().isoformat(timespec='seconds')
    new_entry = {
        "id": str(uuid.uuid4()),
        "site_name": entry_data.get("site_name", "").strip(),
        "url": entry_data.get("url", "").strip(),
        "username": entry_data.get("username", "").strip(),
        "password": entry_data.get("password", ""),
        "notes": entry_data.get("notes", "").strip(),
        "category": entry_data.get("category", "General").strip() or "General",
        "created_at": now,
        "modified_at": now
    }
    entries.append(new_entry)
    save_vault(entries, key)
    log_activity("VAULT_ADD_ENTRY", f"Added entry for '{new_entry['site_name']}'")
    return new_entry

def update_entry(entries: List[Dict], entry_id: str, updated_data: Dict, key: bytes) -> bool:
    """Update an existing vault entry by ID and save."""
    for entry in entries:
        if entry["id"] == entry_id:
            entry["site_name"] = updated_data.get("site_name", entry["site_name"]).strip()
            entry["url"] = updated_data.get("url", entry["url"]).strip()
            entry["username"] = updated_data.get("username", entry["username"]).strip()
            entry["password"] = updated_data.get("password", entry["password"])
            entry["notes"] = updated_data.get("notes", entry["notes"]).strip()
            entry["category"] = updated_data.get("category", entry["category"]).strip() or "General"
            entry["modified_at"] = datetime.now().isoformat(timespec='seconds')
            save_vault(entries, key)
            log_activity("VAULT_UPDATE_ENTRY", f"Updated entry for '{entry['site_name']}'")
            return True
    return False

def delete_entry(entries: List[Dict], entry_id: str, key: bytes) -> bool:
    """Delete a vault entry by ID and save."""
    for idx, entry in enumerate(entries):
        if entry["id"] == entry_id:
            deleted_name = entry.get("site_name", "Unknown")
            entries.pop(idx)
            save_vault(entries, key)
            log_activity("VAULT_DELETE_ENTRY", f"Deleted entry for '{deleted_name}'")
            return True
    return False

def filter_entries(entries: List[Dict], query: str = "", category: str = "All") -> List[Dict]:
    """Search and filter entries by search query and category."""
    results = []
    q = query.strip().lower()
    for entry in entries:
        matches_cat = (category == "All") or (entry.get("category", "General").lower() == category.lower())
        if not matches_cat:
            continue
        
        if not q:
            results.append(entry)
        else:
            in_site = q in entry.get("site_name", "").lower()
            in_url = q in entry.get("url", "").lower()
            in_user = q in entry.get("username", "").lower()
            in_notes = q in entry.get("notes", "").lower()
            if in_site or in_url or in_user or in_notes:
                results.append(entry)
    return results

def check_duplicate_passwords(entries: List[Dict], target_password: str, current_entry_id: Optional[str] = None) -> List[Dict]:
    """
    Returns list of vault entries that share the exact same password,
    excluding current_entry_id if specified.
    """
    duplicates = []
    if not target_password:
        return duplicates
    for entry in entries:
        if current_entry_id and entry["id"] == current_entry_id:
            continue
        if entry.get("password") == target_password:
            duplicates.append(entry)
    return duplicates

def get_categories(entries: List[Dict]) -> List[str]:
    """Returns sorted list of all unique categories in vault plus defaults."""
    cats = set(DEFAULT_CATEGORIES)
    for entry in entries:
        if entry.get("category"):
            cats.add(entry["category"].capitalize())
    return sorted(list(cats))
