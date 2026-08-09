import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("==================================================")
    print(" Password Manager - Non-Admin User Installer ")
    print("==================================================")
    
    appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    install_dir = Path(appdata) / "PasswordManager"
    
    if getattr(sys, 'frozen', False):
        bundle_dir = Path(sys._MEIPASS) / "PasswordManagerApp"
    else:
        bundle_dir = Path(__file__).parent / "dist" / "PasswordManagerApp"
        
    if not bundle_dir.exists():
        print(f"Error: Bundle directory not found at {bundle_dir}")
        input("Press Enter to exit...")
        return
        
    print(f"Installing application to: {install_dir}")
    install_dir.mkdir(parents=True, exist_ok=True)
    
    for item in os.listdir(bundle_dir):
        src = bundle_dir / item
        dst = install_dir / item
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
            
    exe_file = install_dir / "PasswordManager.exe"
    appdata_roaming = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    start_menu = Path(appdata_roaming) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    desktop = Path(os.path.expanduser("~\\Desktop"))
    
    for folder in [start_menu, desktop]:
        if folder.exists():
            link_path = folder / "Password Manager.lnk"
            ps_script = f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{link_path}');$s.TargetPath='{exe_file}';$s.WorkingDirectory='{install_dir}';$s.Save()"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
            
    print("\n[SUCCESS] Password Manager installed successfully!")
    print(f"  Location: {install_dir}")
    print(f"  Shortcuts created on Desktop and Start Menu.")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
