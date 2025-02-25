#!/usr/bin/env python3

import os
import subprocess
import shutil
import sys
import pwd
from pathlib import Path

# Capture the original user running the script
ORIGINAL_USER = subprocess.check_output(['logname']).decode().strip()

def set_default_shell_to_zsh():
    """Set Zsh as the default shell"""
    if not shutil.which('zsh'):
        print("Zsh is not installed. Installing Zsh...")
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'zsh'])

    # Check current shell
    current_shell = pwd.getpwnam(ORIGINAL_USER).pw_shell
    zsh_path = shutil.which('zsh')
    
    if current_shell != zsh_path:
        print(f"Setting Zsh as the default shell for {ORIGINAL_USER}...")
        subprocess.run(['sudo', 'chsh', '-s', zsh_path, ORIGINAL_USER])
        print(f"Zsh has been set as the default shell for {ORIGINAL_USER}.")
    else:
        print(f"Zsh is already the default shell for {ORIGINAL_USER}.")

    # Configure .zshrc
    zshrc_path = Path(f"/home/{ORIGINAL_USER}/.zshrc")
    if zshrc_path.exists():
        with open(zshrc_path, 'r') as f:
            content = f.read()
        if 'newgrp docker' not in content:
            with open(zshrc_path, 'a') as f:
                f.write('\nif ! groups | grep -q "\\bdocker\\b"; then exec newgrp docker; fi\n')
            print("Configured Zsh to automatically switch to the docker group.")

def install_powerlevel10k():
    """Install Powerlevel10k theme for Zsh"""
    p10k_dir = Path(f"/home/{ORIGINAL_USER}/git/fedora_config/powerlevel10k")
    zshrc_path = Path(f"/home/{ORIGINAL_USER}/.zshrc")

    if p10k_dir.exists() and zshrc_path.exists():
        with open(zshrc_path, 'r') as f:
            if 'powerlevel10k' in f.read():
                print("Powerlevel10k is already installed and configured, skipping...")
                return

    print("Installing Powerlevel10k...")
    if p10k_dir.exists():
        shutil.rmtree(p10k_dir)
    
    subprocess.run(['sudo', '-u', ORIGINAL_USER, 'git', 'clone', '--depth=1',
                   'https://github.com/romkatv/powerlevel10k.git', str(p10k_dir)])
    
    with open(zshrc_path, 'a') as f:
        f.write('\nsource ~/git/fedora_config/powerlevel10k/powerlevel10k.zsh-theme\n')
    
    print("Powerlevel10k has been installed and added to your Zsh configuration.")

def check_and_install_oh_my_zsh():
    """Check and install Oh My Zsh"""
    if not shutil.which('zsh'):
        print("Zsh is not installed. You can install it using:")
        print("sudo dnf install -y zsh")
        return

    omz_dir = Path(f"/home/{ORIGINAL_USER}/.oh-my-zsh")
    if not omz_dir.exists():
        print("Oh My Zsh is not installed. Installing Oh My Zsh...")
        install_cmd = 'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
        subprocess.run(['sudo', '-u', ORIGINAL_USER, 'sh', '-c', install_cmd])
    else:
        print("Oh My Zsh is already installed, skipping...")

def main():
    """Main function to configure shell environment"""
    check_and_install_oh_my_zsh()
    set_default_shell_to_zsh()
    install_powerlevel10k()
    
    print("Shell configuration completed.")
    print("Please log out and log back in for changes to take effect.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root (with sudo)")
        sys.exit(1)
    main() 