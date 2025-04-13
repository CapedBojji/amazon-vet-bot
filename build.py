#!/usr/bin/env python3
import os
import sys
import shutil
import platform
import subprocess

def ensure_env_file():
    """Makes sure builtin.env exists, creates it from .env if needed"""
    if not os.path.exists('builtin.env') and os.path.exists('.env'):
        print("Creating builtin.env from .env...")
        shutil.copy('.env', 'builtin.env')
    elif not os.path.exists('builtin.env'):
        print("ERROR: No .env or builtin.env file found. Please create a builtin.env file first.")
        return False
    return True

def clean_previous_builds():
    """Remove previous build artifacts"""
    print("Cleaning previous builds...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    # Clean spec files except our template
    for file in os.listdir('.'):
        if file.endswith('.spec') and file != 'template.spec':
            os.remove(file)
    return True

def generate_spec_file(platform_name):
    """Generate a platform-specific spec file"""
    print(f"Generating spec file for {platform_name}...")
    
    # Determine platform-specific settings
    if platform_name == "Darwin":  # macOS
        exe_name = "AtoZBot_mac"
        icon_path = "None"  # Replace with path to .icns file if you have one
        bundle_section = """
app = BUNDLE(
    exe,
    name='AtoZBot.app',
    icon={icon},
    bundle_identifier=None,
)
""".format(icon=icon_path)
    else:  # Windows/Linux
        exe_name = "AtoZBot_win" if platform_name == "Windows" else "AtoZBot_linux"
        icon_path = "None"  # Replace with path to .ico file for Windows
        bundle_section = ""
    
    # Create the spec file content
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('builtin.env', '.'),
    ],
    hiddenimports=[
        'toml', 
        'selenium', 
        'O365', 
        'dotenv',
        'undetected_chromedriver',
        'datetime',
        'calendar',
        're'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon},
)
{bundle_section}
""".format(exe_name=exe_name, icon=icon_path, bundle_section=bundle_section)
    
    # Write the spec file
    spec_filename = f"AtoZBot_{platform_name.lower()}.spec"
    with open(spec_filename, 'w') as f:
        f.write(spec_content)
    
    return spec_filename

def build_executable(spec_file):
    """Build the executable using PyInstaller"""
    system = platform.system()
    print(f"Building for {system}...")
    
    # Make sure PyInstaller is installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    except subprocess.CalledProcessError:
        print("Failed to install PyInstaller. Please install it manually.")
        return False
    
    # Run PyInstaller
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", spec_file], check=True)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def main():
    """Main build function"""
    system = platform.system()
    print(f"=== AtoZBot Build Script for {system} ===")
    
    # Ensure we have the environment file
    if not ensure_env_file():
        return False
    
    # Clean previous builds
    if not clean_previous_builds():
        return False
    
    # Generate platform-specific spec file
    spec_file = generate_spec_file(system)
    
    # Build the executable
    if not build_executable(spec_file):
        return False
    
    # Output final message
    if system == "Windows":
        print("\nBuild complete! Your executable is at: dist/AtoZBot_win.exe")
    elif system == "Darwin":  # macOS
        print("\nBuild complete! Your application is at: dist/AtoZBot.app")
    else:  # Linux
        print("\nBuild complete! Your executable is at: dist/AtoZBot_linux")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)