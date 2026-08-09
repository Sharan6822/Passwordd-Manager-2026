import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from core.config import load_settings
from core.logger import log_activity

BREACH_SERVICES: List[Dict[str, str]] = [
    {
        "name": "Have I Been Pwned",
        "url": "https://haveibeenpwned.com/",
        "description": "Check if your email or password has been compromised in a public data breach."
    },
    {
        "name": "Firefox Monitor",
        "url": "https://monitor.firefox.com/",
        "description": "Mozilla's breach alert service to discover exposed account details."
    },
    {
        "name": "DeHashed",
        "url": "https://dehashed.com/",
        "description": "Deep data breach search engine for security professionals."
    },
    {
        "name": "Cybernews Leak Checker",
        "url": "https://cybernews.com/personal-data-leak-check/",
        "description": "Search across billions of leaked records for personal data exposures."
    },
    {
        "name": "Google Password Checkup",
        "url": "https://passwords.google.com/checkup",
        "description": "Scan saved credentials against known security incidents."
    }
]

def find_edge_executable() -> Optional[str]:
    """
    Locates Microsoft Edge (msedge.exe) on the local Windows machine.
    Checks custom path in settings, standard install directories, and PATH.
    """
    settings = load_settings()
    custom_path = settings.get("edge_path", "").strip()
    if custom_path and os.path.isfile(custom_path):
        return custom_path
        
    # Check standard 64-bit and 32-bit install paths
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        possible_paths.append(os.path.join(local_appdata, r"Microsoft\Edge\Application\msedge.exe"))
        
    for p in possible_paths:
        if os.path.isfile(p):
            return p
            
    # Check PATH
    which_edge = shutil.which("msedge")
    if which_edge and os.path.isfile(which_edge):
        return which_edge
        
    # Fallback to Chrome if Edge not found
    which_chrome = shutil.which("chrome")
    if which_chrome:
        return which_chrome
        
    possible_chrome = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for p in possible_chrome:
        if os.path.isfile(p):
            return p
            
    return None

def launch_browser_url(url: str, in_private: bool = False, custom_edge_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Launches browser URL.
    in_private=False: Opens in normal standard browser window (for saved vault URLs).
    in_private=True: Opens in InPrivate / Incognito mode (for breach checker URLs).
    """
    url = url.strip()
    if url and not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    if not in_private:
        import webbrowser
        try:
            webbrowser.open(url)
            log_activity("BROWSER_LAUNCH_NORMAL", f"Opened URL '{url}' in standard browser window.")
            return True, "Opened URL in standard browser window."
        except Exception as e:
            log_activity("BROWSER_LAUNCH_ERROR", f"Webbrowser error: {str(e)}")

    browser_exe = custom_edge_path if (custom_edge_path and os.path.isfile(custom_edge_path)) else find_edge_executable()
    
    if not browser_exe:
        log_activity("BREACH_LAUNCH_FAILED", f"Browser executable not found for URL: {url}")
        return False, "Microsoft Edge / Chrome executable not found. Please set Edge path in Settings."
        
    try:
        # Determine incognito/inprivate flag
        exe_name = os.path.basename(browser_exe).lower()
        private_flag = "--inprivate" if "edge" in exe_name else "--incognito"
        
        cmd = [browser_exe]
        if in_private:
            cmd.append(private_flag)
        cmd.append(url)

        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        
        mode_str = "InPrivate" if in_private else "Normal"
        log_activity("BREACH_LAUNCH_SUCCESS", f"Launched {mode_str} browser ({exe_name}) for URL '{url}'")
        return True, f"Opened URL in {exe_name} ({mode_str} mode)."
    except Exception as e:
        log_activity("BREACH_LAUNCH_ERROR", f"Subprocess error: {str(e)}")
        return False, f"Error launching browser: {str(e)}"

def launch_breach_check_url(url: str, custom_edge_path: Optional[str] = None) -> Tuple[bool, str]:
    """Shortcut for breach checker URLs launching in InPrivate mode."""
    return launch_browser_url(url, in_private=True, custom_edge_path=custom_edge_path)
