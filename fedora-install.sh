#!/bin/bash

# Capture the original user running the script
ORIGINAL_USER=$(logname)
# Function to check if a package is installed

is_installed() {
  rpm -q $1 &> /dev/null || flatpak list | grep -q $1
}

# Function to create directories if they don't exist
create_directories() {
  local DIRS=(
    "/home/$ORIGINAL_USER/scripts/"
    "/home/$ORIGINAL_USER/git/"
    "/home/$ORIGINAL_USER/git/fedora_config/"
    "/home/$ORIGINAL_USER/Documents/Obsidian/"
  )
  
  for DIR in "${DIRS[@]}"; do
    if [ ! -d "$DIR" ]; then
      echo "Creating directory: $DIR"
      mkdir -p "$DIR"
    else
      echo "Directory $DIR already exists, skipping..."
    fi
  done
}

# Install Docker using the official Docker repository
install_docker() {
  if command -v docker &> /dev/null; then
    echo "Docker is already installed, skipping Docker installation."
  else
    echo "Installing Docker using the official Docker repository..."

    # Remove any old versions
    sudo dnf remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

    # Set up the repository
    sudo dnf -y install dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

    # Install Docker Engine
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
  fi

  # Add the original user to the docker group if not already part of it
  if ! groups $ORIGINAL_USER | grep -q "\bdocker\b"; then
    echo "Adding user $ORIGINAL_USER to the docker group..."
    sudo usermod -aG docker $ORIGINAL_USER
    echo "User $ORIGINAL_USER has been added to the docker group."
  else
    echo "User $ORIGINAL_USER is already in the docker group, skipping..."
  fi

  echo "Docker has been installed and configured successfully."
}

# Install Docker Compose
install_docker_compose() {
  if command -v docker-compose &> /dev/null; then
    echo "Docker Compose is already installed, skipping Docker Compose installation."
  else
    echo "Installing Docker Compose..."

    # Download the latest version of Docker Compose
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K[^\"]+')
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

    # Apply executable permissions to the binary
    sudo chmod +x /usr/local/bin/docker-compose

    # Create a symbolic link to /usr/bin
    sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

    echo "Docker Compose version ${DOCKER_COMPOSE_VERSION} has been installed."
  fi
}

# Install Portainer
# install_portainer() {
#   # Check if Docker is installed
#   if ! command -v docker &> /dev/null; then
#     echo "Docker is not installed. Please install Docker first."
#     return
#   fi

#   # Check if Portainer container exists
#   if docker ps -a --format '{{.Names}}' | grep -wq portainer; then
#     echo "Portainer is already installed."

#     # Check if it's running
#     if ! docker ps --format '{{.Names}}' | grep -wq portainer; then
#       echo "Starting Portainer container..."
#       docker start portainer
#       echo "Portainer has been started."
#     else
#       echo "Portainer is already running."
#     fi
#   else
#     echo "Installing Portainer..."

#     # Create the volume if it doesn't exist
#     if ! docker volume ls | grep -wq portainer_data; then
#       docker volume create portainer_data
#     fi

#     # Run the Portainer container
#     docker run -d -p 8000:8000 -p 9443:9443 \
#       --name portainer \
#       --restart=always \
#       -v /var/run/docker.sock:/var/run/docker.sock \
#       -v portainer_data:/data \
#       portainer/portainer-ce:latest

#     echo "Portainer has been installed and started."
#   fi
# }

# Set Zsh as the default shell if not already set
set_default_shell_to_zsh() {
  # Check if Zsh is installed
  if ! command -v zsh &> /dev/null; then
    echo "Zsh is not installed. Installing Zsh..."
    sudo dnf install -y zsh
  fi

  # Check if the current shell is Zsh, if not, set it as the default
  USER_SHELL=$(getent passwd $ORIGINAL_USER | cut -d: -f7)
  if [ "$USER_SHELL" != "$(which zsh)" ]; then
    echo "Setting Zsh as the default shell for $ORIGINAL_USER..."
    sudo chsh -s $(which zsh) $ORIGINAL_USER
    echo "Zsh has been set as the default shell for $ORIGINAL_USER."
  else
    echo "Zsh is already the default shell for $ORIGINAL_USER."
  fi

  # Ensure that Zsh switches to the docker group and reloads settings
  if ! grep -q "newgrp docker" /home/$ORIGINAL_USER/.zshrc; then
    echo 'if ! groups | grep -q "\bdocker\b"; then exec newgrp docker; fi' >> /home/$ORIGINAL_USER/.zshrc
    echo "Configured Zsh to automatically switch to the docker group."
  fi
}

# Install Powerlevel10k theme for Zsh
install_powerlevel10k() {
  local POWERLEVEL10K_DIR="/home/$ORIGINAL_USER/git/fedora_config/powerlevel10k"

  # Check if Powerlevel10k is already installed in .zshrc and installed directory
  if grep -q "powerlevel10k" /home/$ORIGINAL_USER/.zshrc && [ -d "$POWERLEVEL10K_DIR" ]; then
    echo "Powerlevel10k is already installed and configured, skipping..."
  else
    echo "Installing Powerlevel10k..."
    # Ensure the directory exists and clone if necessary
    rm -rf "$POWERLEVEL10K_DIR"  # Remove any potentially broken installation
    sudo -u $ORIGINAL_USER git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$POWERLEVEL10K_DIR"
    
    # Ensure it is sourced in the .zshrc file
    echo 'source ~/git/fedora_config/powerlevel10k/powerlevel10k.zsh-theme' >> /home/$ORIGINAL_USER/.zshrc
    echo "Powerlevel10k has been installed and added to your Zsh configuration."
  fi
}

# Check if Flathub is added, and if not, add it
ensure_flathub_repo() {
  if ! flatpak remotes | grep -q "flathub"; then
    echo "Flathub repository not found. Adding Flathub repository..."
    flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  else
    echo "Flathub repository is already added, skipping..."
  fi
}

# Install 1Password (RPM)
install_1password() {
  if ! is_installed "1password"; then
    echo "Installing 1Password..."
    sudo dnf install -y https://downloads.1password.com/linux/rpm/stable/x86_64/1password-latest.rpm
  else
    echo "1Password is already installed, skipping..."
  fi
}

# Install Bitwarden (Flatpak)
install_bitwarden() {
  if ! is_installed "com.bitwarden.desktop"; then
    ensure_flathub_repo
    echo "Installing Bitwarden..."
    flatpak install -y flathub com.bitwarden.desktop
  else
    echo "Bitwarden is already installed, skipping..."
  fi
}

# Install Discord (Flatpak)
install_discord() {
  if ! is_installed "com.discordapp.Discord"; then
    ensure_flathub_repo
    echo "Installing Discord..."
    flatpak install -y flathub com.discordapp.Discord
  else
    echo "Discord is already installed, skipping..."
  fi
}

# Install Mullvad (using the repository)
install_mullvad() {
  if ! is_installed "mullvad-vpn"; then
    echo "Installing Mullvad VPN..."
    sudo dnf config-manager --add-repo https://repository.mullvad.net/rpm/stable/mullvad.repo
    sudo dnf install -y mullvad-vpn
  else
    echo "Mullvad VPN is already installed, skipping..."
  fi
}

# Install Obsidian (Flatpak)
install_obsidian() {
  if ! is_installed "md.obsidian.Obsidian"; then
    ensure_flathub_repo
    echo "Installing Obsidian..."
    flatpak install -y flathub md.obsidian.Obsidian
  else
    echo "Obsidian is already installed, skipping..."
  fi
}

# Install Timeshift (from Fedora repositories)
install_timeshift() {
  if ! is_installed "timeshift"; then
    echo "Installing Timeshift..."
    sudo dnf update -y
    sudo dnf install -y timeshift
  else
    echo "Timeshift is already installed, skipping..."
  fi
}

# Install SyncThingy (Flatpak)
install_syncthingy() {
  if ! is_installed "com.github.zocker_160.SyncThingy"; then
    ensure_flathub_repo
    echo "Installing SyncThingy..."
    flatpak install -y flathub com.github.zocker_160.SyncThingy
  else
    echo "SyncThingy is already installed, skipping..."
  fi
}

# Install Vesktop (dev.vencord.Vesktop) from Flathub
install_vesktop() {
  if ! is_installed "dev.vencord.Vesktop"; then
    echo "Installing Vesktop from Flathub..."
    flatpak install -y flathub dev.vencord.Vesktop
  else
    echo "Vesktop is already installed, skipping..."
  fi
}

# Install VSCodium (Flatpak)
install_vscodium() {
  if ! is_installed "com.vscodium.codium"; then
    ensure_flathub_repo
    echo "Installing VSCodium..."
    flatpak install -y flathub com.vscodium.codium
  else
    echo "VSCodium is already installed, skipping..."
  fi
}

# Install GitHub CLI (gh)
install_gh_cli() {
  if ! is_installed "gh"; then
    echo "Installing GitHub CLI..."
    sudo dnf install -y gh
  else
    echo "GitHub CLI is already installed, skipping..."
  fi
}

# Install NVIDIA Drivers
install_nvidia_drivers() {
  if ! is_installed "akmod-nvidia"; then
    echo "Enabling RPM Fusion repositories for NVIDIA drivers..."
    sudo dnf install -y \
      https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
      https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

    echo "Installing NVIDIA drivers..."
    sudo dnf install -y akmod-nvidia
  else
    echo "NVIDIA drivers are already installed, skipping..."
  fi
}

# Resolve package conflicts before installing the NVIDIA Container Toolkit
resolve_nvidia_toolkit_conflicts() {
  if is_installed "golang-github-nvidia-container-toolkit"; then
    echo "Removing conflicting Fedora package: golang-github-nvidia-container-toolkit..."
    sudo dnf remove -y golang-github-nvidia-container-toolkit
  fi
}

# Install NVIDIA Container Toolkit with the new repo
install_nvidia_container_toolkit() {
  # Resolve any potential package conflicts first
  resolve_nvidia_toolkit_conflicts

  if ! is_installed "nvidia-container-toolkit"; then
    echo "Adding NVIDIA Container Toolkit repository..."
    # Adjust the repository to match your Fedora version
    FEDORA_VERSION=$(rpm -E %fedora)
    sudo dnf config-manager --add-repo=https://developer.download.nvidia.com/compute/cuda/repos/fedora${FEDORA_VERSION}/x86_64/cuda-fedora${FEDORA_VERSION}.repo

    echo "Installing NVIDIA Container Toolkit..."
    sudo dnf install -y nvidia-container-toolkit

    echo "Restarting Docker to apply NVIDIA Container Toolkit..."
    sudo systemctl restart docker
  else
    echo "NVIDIA Container Toolkit is already installed, skipping..."
  fi
}

# Check if Zsh and Oh My Zsh are installed, and install Oh My Zsh if not
check_and_install_oh_my_zsh() {
  if ! command -v zsh &> /dev/null; then
    echo "Zsh is not installed. You can install it using:"
    echo "sudo dnf install -y zsh"
    return
  fi

  if [ ! -d "/home/$ORIGINAL_USER/.oh-my-zsh" ]; then
    echo "Oh My Zsh is not installed. Installing Oh My Zsh..."
    sudo -u $ORIGINAL_USER sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
  else
    echo "Oh My Zsh is already installed, skipping..."
  fi
}

# Run installation functions and create directories
create_directories
ensure_flathub_repo
install_1password
install_bitwarden
install_discord
install_docker
install_docker_compose
# install_portainer
install_mullvad
install_obsidian
install_timeshift
install_syncthingy
install_vscodium
install_gh_cli
install_powerlevel10k
install_vesktop

# Install NVIDIA drivers and NVIDIA Container Toolkit
install_nvidia_drivers
install_nvidia_container_toolkit

# Check for Zsh and Oh My Zsh, install if necessary
check_and_install_oh_my_zsh
set_default_shell_to_zsh


echo "All selected applications, directories, and configurations have been processed."
echo "Please log out and log back in for group changes to take effect."