"""Automated PyInstaller Build Script for NudgeDesk.

Builds a standalone Windows 11 executable with icons, themes, and dependencies.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "app_icon.ico"

def clean_previous_builds(target_name: str = "NudgeDesk"):
    """Removes previous build artifacts."""
    print("==> Cleaning previous build directories...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    
    target_exe = DIST_DIR / f"{target_name}.exe"
    if target_exe.exists():
        try:
            target_exe.unlink()
        except PermissionError:
            print(f"Warning: {target_exe} is currently in use.")
            return False
            
    for spec in BASE_DIR.glob("*.spec"):
        try:
            spec.unlink()
        except Exception:
            pass
    return True

def run_pyinstaller(onefile: bool = True, windowed: bool = True):
    """Executes PyInstaller with all required flags and data collections."""
    target_name = "NudgeDesk"
    cleaned = clean_previous_builds(target_name)
    if not cleaned:
        # If NudgeDesk.exe is locked by a running instance, build as NudgeDesk_Update.exe
        target_name = "NudgeDesk_Update"
        print(f"==> Target '{target_name}.exe' selected because original is running.")
        clean_previous_builds(target_name)

    print(f"==> Building {target_name} (onefile={onefile}, windowed={windowed})...")
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--name={target_name}",
        f"--icon={ICON_PATH}",
        f"--add-data={ASSETS_DIR};assets",
        "--collect-all=customtkinter",
        "--collect-all=winotify",
        "--collect-all=pystray",
        "--collect-all=keyring",
        "--hidden-import=googleapiclient",
        "--hidden-import=google.auth",
        "--hidden-import=google_auth_oauthlib",
        "--clean",
        "--noconfirm",
    ]

    if onefile:
        cmd.append("--onefile")
    if windowed:
        cmd.append("--windowed")

    cmd.append(str(BASE_DIR / "main.py"))

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(result.returncode)

    print("\n==> Build completed successfully!")
    if onefile:
        exe_path = DIST_DIR / f"{target_name}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable output: {exe_path} ({size_mb:.2f} MB)")
    else:
        print(f"Application directory output: {DIST_DIR / target_name}")

if __name__ == "__main__":
    run_pyinstaller(onefile=True, windowed=True)

