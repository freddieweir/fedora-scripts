#!/usr/bin/env python3

import os
import subprocess
import shutil
import sys
import pwd
from pathlib import Path

# Capture the original user running the script
ORIGINAL_USER = subprocess.check_output(['logname']).decode().strip()

def is_installed(package):
    """Check if a package is installed via RPM or Flatpak"""
    rpm_check = subprocess.run(['rpm', '-q', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    flatpak_check = subprocess.run(['flatpak', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return rpm_check.returncode == 0 or package in flatpak_check.stdout.decode()

def create_directories():
    """Create required directories if they don't exist"""
    dirs = [
        f"/home/{ORIGINAL_USER}/scripts/",
        f"/home/{ORIGINAL_USER}/git/",
        f"/home/{ORIGINAL_USER}/git/fedora_config/",
        f"/home/{ORIGINAL_USER}/Documents/Obsidian/"
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            print(f"Creating directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
        else:
            print(f"Directory {dir_path} already exists, skipping...")

def install_docker():
    """Install Docker using the official Docker repository"""
    if shutil.which('docker'):
        print("Docker is already installed, skipping Docker installation.")
        
    else:
        print("Installing Docker using the official Docker repository...")
        
        # Remove any old versions
        subprocess.run(['sudo', 'dnf', 'remove', '-y', 'docker', 'docker-client', 'docker-client-latest', 
                       'docker-common', 'docker-latest', 'docker-latest-logrotate', 'docker-logrotate', 'docker-engine'])

        # Set up repository
        subprocess.run(['sudo', 'dnf', '-y', 'install', 'dnf-plugins-core'])
        subprocess.run(['sudo', 'dnf', 'config-manager', '--add-repo', 
                       'https://download.docker.com/linux/fedora/docker-ce.repo'])

        # Install Docker Engine
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io',
                       'docker-buildx-plugin', 'docker-compose-plugin'])

        # Start and enable Docker
        subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
        subprocess.run(['sudo', 'systemctl', 'enable', 'docker'])

    # Add user to docker group if not already in it
    groups = subprocess.check_output(['groups', ORIGINAL_USER]).decode()
    if 'docker' not in groups:
        print(f"Adding user {ORIGINAL_USER} to the docker group...")
        subprocess.run(['sudo', 'usermod', '-aG', 'docker', ORIGINAL_USER])
        print(f"User {ORIGINAL_USER} has been added to the docker group.")
    else:
        print(f"User {ORIGINAL_USER} is already in the docker group, skipping...")

    print("Docker has been installed and configured successfully.")

def install_docker_compose():
    """Install Docker Compose"""
    if shutil.which('docker-compose'):
        print("Docker Compose is already installed, skipping Docker Compose installation.")
        return

    print("Installing Docker Compose...")
    
    # Get latest version
    version_cmd = "curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '\"tag_name\": \"\\K[^\"]+'"
    version = subprocess.check_output(version_cmd, shell=True).decode().strip()
    
    # System info
    system = subprocess.check_output(['uname', '-s']).decode().strip()
    machine = subprocess.check_output(['uname', '-m']).decode().strip()
    
    # Download and install
    url = f"https://github.com/docker/compose/releases/download/{version}/docker-compose-{system}-{machine}"
    subprocess.run(['sudo', 'curl', '-L', url, '-o', '/usr/local/bin/docker-compose'])
    subprocess.run(['sudo', 'chmod', '+x', '/usr/local/bin/docker-compose'])
    
    # Create symlink
    if not os.path.exists('/usr/bin/docker-compose'):
        subprocess.run(['sudo', 'ln', '-s', '/usr/local/bin/docker-compose', '/usr/bin/docker-compose'])

    print(f"Docker Compose version {version} has been installed.")

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

def ensure_flathub_repo():
    """Ensure Flathub repository is added"""
    result = subprocess.run(['flatpak', 'remotes'], stdout=subprocess.PIPE)
    if 'flathub' not in result.stdout.decode():
        print("Flathub repository not found. Adding Flathub repository...")
        subprocess.run(['flatpak', 'remote-add', '--if-not-exists', 'flathub',
                       'https://dl.flathub.org/repo/flathub.flatpakrepo'])
    else:
        print("Flathub repository is already added, skipping...")

def install_1password():
    """Install 1Password"""
    if not is_installed("1password"):
        print("Installing 1Password...")
        subprocess.run(['sudo', 'dnf', 'install', '-y',
                       'https://downloads.1password.com/linux/rpm/stable/x86_64/1password-latest.rpm'])
    else:
        print("1Password is already installed, skipping...")

def install_bitwarden():
    """Install Bitwarden"""
    if not is_installed("com.bitwarden.desktop"):
        ensure_flathub_repo()
        print("Installing Bitwarden...")
        subprocess.run(['flatpak', 'install', '-y', 'flathub', 'com.bitwarden.desktop'])
    else:
        print("Bitwarden is already installed, skipping...")

def install_discord():
    """Install Discord"""
    if not is_installed("com.discordapp.Discord"):
        ensure_flathub_repo()
        print("Installing Discord...")
        subprocess.run(['flatpak', 'install', '-y', 'flathub', 'com.discordapp.Discord'])
    else:
        print("Discord is already installed, skipping...")

def install_mullvad():
    """Install Mullvad VPN"""
    if not is_installed("mullvad-vpn"):
        print("Installing Mullvad VPN...")
        subprocess.run(['sudo', 'dnf', 'config-manager', '--add-repo',
                       'https://repository.mullvad.net/rpm/stable/mullvad.repo'])
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'mullvad-vpn'])
    else:
        print("Mullvad VPN is already installed, skipping...")

def install_obsidian():
    """Install Obsidian"""
    if not is_installed("md.obsidian.Obsidian"):
        ensure_flathub_repo()
        print("Installing Obsidian...")
        subprocess.run(['flatpak', 'install', '-y', 'flathub', 'md.obsidian.Obsidian'])
    else:
        print("Obsidian is already installed, skipping...")

def install_timeshift():
    """Install Timeshift"""
    if not is_installed("timeshift"):
        print("Installing Timeshift...")
        subprocess.run(['sudo', 'dnf', 'update', '-y'])
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'timeshift'])
    else:
        print("Timeshift is already installed, skipping...")

def install_syncthingy():
    """Install SyncThingy"""
    if not is_installed("com.github.zocker_160.SyncThingy"):
        ensure_flathub_repo()
        print("Installing SyncThingy...")
        subprocess.run(['flatpak', 'install', '-y', 'flathub', 'com.github.zocker_160.SyncThingy'])
    else:
        print("SyncThingy is already installed, skipping...")

def install_vesktop():
    """Install Vesktop"""
    if not is_installed("dev.vencord.Vesktop"):
        print("Installing Vesktop from Flathub...")
        subprocess.run(['flatpak', 'install', '-y', 'flathub', 'dev.vencord.Vesktop'])
    else:
        print("Vesktop is already installed, skipping...")

def install_vscodium():
    """Install VSCodium"""
    if not is_installed("com.vscodium.codium"):
        ensure_flathub_repo()
        print("Installing VSCodium...")
        subprocess.run(['flatpak', 'install', '-y', 'flathub', 'com.vscodium.codium'])
    else:
        print("VSCodium is already installed, skipping...")

def install_gh_cli():
    """Install GitHub CLI"""
    if not is_installed("gh"):
        print("Installing GitHub CLI...")
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'gh'])
    else:
        print("GitHub CLI is already installed, skipping...")

def install_nvidia_drivers():
    """Install NVIDIA Drivers"""
    if not is_installed("akmod-nvidia"):
        print("Enabling RPM Fusion repositories for NVIDIA drivers...")
        fedora_version = subprocess.check_output(['rpm', '-E', '%fedora']).decode().strip()
        
        subprocess.run(['sudo', 'dnf', 'install', '-y',
                       f'https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-{fedora_version}.noarch.rpm',
                       f'https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-{fedora_version}.noarch.rpm'])

        print("Installing NVIDIA drivers...")
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'akmod-nvidia'])
    else:
        print("NVIDIA drivers are already installed, skipping...")

def resolve_nvidia_toolkit_conflicts():
    """Resolve NVIDIA Container Toolkit conflicts"""
    if is_installed("golang-github-nvidia-container-toolkit"):
        print("Removing conflicting Fedora package: golang-github-nvidia-container-toolkit...")
        subprocess.run(['sudo', 'dnf', 'remove', '-y', 'golang-github-nvidia-container-toolkit'])

def install_nvidia_container_toolkit():
    """Install NVIDIA Container Toolkit"""
    resolve_nvidia_toolkit_conflicts()

    if not is_installed("nvidia-container-toolkit"):
        print("Adding NVIDIA Container Toolkit repository...")
        fedora_version = subprocess.check_output(['rpm', '-E', '%fedora']).decode().strip()
        
        subprocess.run(['sudo', 'dnf', 'config-manager', '--add-repo',
                       f'https://developer.download.nvidia.com/compute/cuda/repos/fedora{fedora_version}/x86_64/cuda-fedora{fedora_version}.repo'])

        print("Installing NVIDIA Container Toolkit...")
        subprocess.run(['sudo', 'dnf', 'install', '-y', 'nvidia-container-toolkit'])

        print("Restarting Docker to apply NVIDIA Container Toolkit...")
        subprocess.run(['sudo', 'systemctl', 'restart', 'docker'])
    else:
        print("NVIDIA Container Toolkit is already installed, skipping...")

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
    """Main function to run all installations"""
    create_directories()
    ensure_flathub_repo()
    install_1password()
    install_bitwarden()
    install_discord()
    install_docker()
    install_docker_compose()
    install_mullvad()
    install_obsidian()
    install_timeshift()
    install_syncthingy()
    install_vscodium()
    install_gh_cli()
    install_vesktop()

    # Install NVIDIA components
    install_nvidia_drivers()
    install_nvidia_container_toolkit()

    print("All selected applications, directories, and configurations have been processed.")
    print("Please log out and log back in for group changes to take effect.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root (with sudo)")
        sys.exit(1)
    main()