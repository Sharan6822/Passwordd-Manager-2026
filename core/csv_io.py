import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from core import config
from core.logger import log_activity

def get_export_filepath(filename: str) -> Path:
    """Ensure path lands strictly inside EXPORTS_DIR."""
    config.ensure_directories()
    # Strip path separators to keep filename inside EXPORTS_DIR
    clean_filename = Path(filename).name
    if not clean_filename.endswith(".csv"):
        clean_filename += ".csv"
    return config.EXPORTS_DIR / clean_filename

def export_vault_to_csv(entries: List[Dict], target: str | Path, format_type: str = "chrome") -> Path:
    """
    Export vault entries to a CSV file.
    'target' can be a full Path or a filename string.
    format_type: 'chrome' (Chrome/Edge format) or 'firefox' (Firefox format).
    """
    if isinstance(target, Path):
        filepath = target
    elif "/" in target or "\\" in target or Path(target).is_absolute():
        filepath = Path(target)
    else:
        filepath = get_export_filepath(target)

    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        if format_type.lower() == "firefox":
            fieldnames = [
                "url", "username", "password", "httpRealm",
                "formActionOrigin", "guid", "timeCreated", "timeLastUsed", "timePasswordChanged"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "url": entry.get("url", ""),
                    "username": entry.get("username", ""),
                    "password": entry.get("password", ""),
                    "httpRealm": "",
                    "formActionOrigin": "",
                    "guid": entry.get("id", ""),
                    "timeCreated": entry.get("created_at", ""),
                    "timeLastUsed": entry.get("modified_at", ""),
                    "timePasswordChanged": entry.get("modified_at", "")
                })
        else:
            # Default Chrome / Edge format: name,url,username,password,note
            fieldnames = ["name", "url", "username", "password", "note"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "name": entry.get("site_name", ""),
                    "url": entry.get("url", ""),
                    "username": entry.get("username", ""),
                    "password": entry.get("password", ""),
                    "note": entry.get("notes", "")
                })
                
    log_activity("CSV_EXPORT", f"Exported {len(entries)} entries ({format_type}) to '{filepath.name}'")
    return filepath

def parse_import_csv(filepath: Path) -> Tuple[List[Dict], List[str]]:
    """
    Parse a CSV file and return normalized entry dictionaries and error messages.
    Auto-detects Chrome/Edge, Firefox, or generic CSV structures.
    """
    parsed_entries = []
    errors = []
    
    if not filepath.exists():
        return [], ["File does not exist."]
        
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        if not rows or len(rows) < 2:
            return [], ["CSV file is empty or has no data rows."]
            
        header = [col.strip().lower() for col in rows[0]]
        
        # Map columns based on headers
        name_idx = -1
        url_idx = -1
        user_idx = -1
        pass_idx = -1
        note_idx = -1
        
        for idx, col in enumerate(header):
            if col in ["name", "site", "title", "app", "application"]:
                name_idx = idx
            elif col in ["url", "website", "link", "host", "hostname"]:
                url_idx = idx
            elif col in ["username", "user", "email", "login"]:
                user_idx = idx
            elif col in ["password", "pass", "secret"]:
                pass_idx = idx
            elif col in ["note", "notes", "comment"]:
                note_idx = idx
                
        # If pass_idx not found, try fallback standard indexes
        if pass_idx == -1:
            if len(header) >= 4:
                pass_idx = 3  # Standard position in name,url,username,password
            else:
                return [], ["Could not identify 'password' column in CSV header."]
                
        for row_num, row in enumerate(rows[1:], start=2):
            if not row or not any(field.strip() for field in row):
                continue
                
            def get_col(idx: int) -> str:
                return row[idx].strip() if idx >= 0 and idx < len(row) else ""
                
            site_name = get_col(name_idx)
            url = get_col(url_idx)
            username = get_col(user_idx)
            password = get_col(pass_idx)
            notes = get_col(note_idx)
            
            # Fallback site name from URL if name is empty
            if not site_name and url:
                site_name = url.replace("https://", "").replace("http://", "").split("/")[0]
            if not site_name:
                site_name = f"Imported Entry {row_num}"
                
            if not password:
                errors.append(f"Row {row_num}: Skipped (missing password)")
                continue
                
            parsed_entries.append({
                "site_name": site_name,
                "url": url,
                "username": username,
                "password": password,
                "notes": notes,
                "category": "Imported"
            })
            
    except Exception as e:
        errors.append(f"Failed to parse CSV: {str(e)}")
        
    return parsed_entries, errors

def secure_delete_file(filepath: Path) -> bool:
    """Overwrites file with random bytes before deletion for secure cleanup."""
    try:
        if filepath.exists():
            length = filepath.stat().st_size
            with open(filepath, "wb") as f:
                f.write(os.urandom(length))
            filepath.unlink()
            log_activity("SECURE_DELETE", f"Securely deleted CSV file '{filepath.name}'")
            return True
    except Exception as e:
        log_activity("SECURE_DELETE_ERROR", f"Could not delete '{filepath.name}': {str(e)}")
    return False
