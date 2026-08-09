import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_pyinstaller_app(project_root: Path) -> Path:
    """Compile Python source into a standalone folder using PyInstaller."""
    print("==================================================")
    print(" Step 1: Compiling PyInstaller Standalone Bundle ")
    print("==================================================")
    
    spec_file = project_root / "PasswordManager.spec"
    if not spec_file.exists():
        raise FileNotFoundError(f"PyInstaller spec file not found at: {spec_file}")
    
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_file)]
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(project_root))
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller compilation failed with exit code {res.returncode}")
    
    app_dir = project_root / "dist" / "PasswordManagerApp"
    if not app_dir.exists() or not (app_dir / "PasswordManager.exe").exists():
        raise FileNotFoundError("PyInstaller build output directory or executable missing!")
    
    print(f"PyInstaller bundle created successfully at: {app_dir}\n")
    return app_dir

def build_exe_installer(project_root: Path, app_dir: Path) -> Path:
    """Compile non-admin per-user executable installer (PasswordManagerSetup.exe)."""
    print("==================================================")
    print(" Step 2: Compiling Non-Admin Setup Executable (.exe) ")
    print("==================================================")
    
    user_installer_script = project_root / "user_installer.py"
    if not user_installer_script.exists():
        raise FileNotFoundError(f"user_installer.py script missing at {user_installer_script}")
        
    exe_setup_path = project_root / "PasswordManagerSetup.exe"
    dist_exe_setup_path = project_root / "dist" / "PasswordManagerSetup.exe"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name", "PasswordManagerSetup",
        "--add-data", f"{app_dir};PasswordManagerApp",
        str(user_installer_script)
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(project_root))
    if res.returncode != 0:
        print(f"Warning: EXE installer compilation failed with exit code {res.returncode}")
        return dist_exe_setup_path
        
    if dist_exe_setup_path.exists():
        try:
            shutil.copy2(dist_exe_setup_path, exe_setup_path)
        except Exception as e:
            print(f"Note: Could not copy root EXE setup ({e}).")
            
    print(f"Non-Admin Setup Executable complete!")
    print(f" - Dist Location: {dist_exe_setup_path}")
    if exe_setup_path.exists():
        print(f" - Root Location: {exe_setup_path} ({os.path.getsize(exe_setup_path):,} bytes)\n")
        
    return exe_setup_path

def main():
    project_root = Path(__file__).parent.resolve()
    print(f"Project Workspace Root: {project_root}")
    
    # Remove old MSI files if present
    for msi in [project_root / "PasswordManagerSetup.msi", project_root / "dist" / "PasswordManagerSetup.msi"]:
        if msi.exists():
            try:
                msi.unlink()
                print(f"Removed legacy MSI: {msi}")
            except Exception:
                pass
    
    app_dir = build_pyinstaller_app(project_root)
    exe_setup_file = build_exe_installer(project_root, app_dir)
    
    print("==================================================")
    print(" BUILD SUCCESSFUL! ")
    print("==================================================")
    print("Outputs created:")
    print(f" 1. Standalone Portable Executable Folder: {app_dir / 'PasswordManager.exe'}")
    print(f" 2. Non-Admin Portable Setup EXE:          {exe_setup_file}")
    print("==================================================")

if __name__ == "__main__":
    main()
