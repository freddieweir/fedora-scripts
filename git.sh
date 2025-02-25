#!/bin/bash
set -eo pipefail

# Configuration variables
RED='\033[0;91m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
NC='\033[0m'
SSH_KEY_PATH="$HOME/.ssh/id_ed25519"

# Initialization banner
echo -e "${GREEN}"
cat << "EOF"
  ____ _ _   _   _       _   _           _    
 / ___(_) |_| | | |_   _| |_| |__   ___ | | __
| |  _| | __| |_| | | | | __| '_ \ / _ \| |/ /
| |_| | | |_|  _  | |_| | |_| | | | (_) |   < 
 \____|_|\__|_| |_|\__, |\__|_| |_|\___/|_|\_\
                   |___/                      
EOF
echo -e "${NC}"

# Dependency checks
check_architecture() {
    if [ "$(uname -m)" != "x86_64" ]; then
        echo -e "${RED}Error: Unsupported architecture $(uname -m)${NC}" >&2
        exit 1
    fi
}

install_git() {
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}Installing Git...${NC}"
        sudo dnf update -yq && sudo dnf install -yq git
        echo -e "${GREEN}Git $(git --version | awk '{print $3}') installed successfully${NC}[5]"
    else
        echo -e "${GREEN}Git already installed: $(git --version)${NC}"
    fi
}

install_gh_cli() {
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}Installing GitHub CLI...${NC}"
        sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        sudo dnf install -yq gh
        echo -e "${GREEN}GitHub CLI $(gh --version | head -n1 | awk '{print $3}') installed${NC}[7]"
    else
        echo -e "${GREEN}GitHub CLI already installed: $(gh --version | head -n1)${NC}"
    fi
}

configure_git() {
    echo -e "\n${YELLOW}Git Configuration${NC}"
    while true; do
        read -p "Enter your Git user name: " git_name
        [ -n "$git_name" ] && break
        echo -e "${RED}Name cannot be empty!${NC}"
    done

    while true; do
        read -p "Enter your Git email: " git_email
        [[ "$git_email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]] && break
        echo -e "${RED}Invalid email format!${NC}"
    done

    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
    git config --global pull.rebase true
    git config --global fetch.prune true
    git config --global init.defaultBranch main
    git config --global core.editor "nano"
    echo -e "${GREEN}Git configuration completed successfully${NC}[6]"
}

setup_ssh() {
    echo -e "\n${YELLOW}SSH Key Setup${NC}"
    if [ ! -f "$SSH_KEY_PATH" ]; then
        mkdir -p ~/.ssh
        ssh-keygen -t ed25519 -N "" -f "$SSH_KEY_PATH"
        echo -e "${GREEN}Generated new ED25519 SSH key${NC}[1]"
    fi
    
    echo -e "${YELLOW}Add this public key to GitHub:${NC}"
    cat "${SSH_KEY_PATH}.pub"
    echo -e "\n${YELLOW}Press Enter to continue after adding the key to GitHub...${NC}"
    read -r
}

github_login() {
    echo -e "\n${YELLOW}GitHub Authentication${NC}"
    gh auth login --hostname github.com --web --scopes "repo,read:org,gist" || {
        echo -e "${RED}Web authentication failed. Using token fallback...${NC}"
        read -s -p "Enter GitHub Personal Access Token: " gh_token
        echo
        gh auth login --with-token <<< "$gh_token" || {
            echo -e "${RED}GitHub authentication failed!${NC}"
            exit 1
        }
    }
    echo -e "${GREEN}Authenticated as: $(gh api user --jq '.login')${NC}[7]"
}

clone_repo() {
    echo -e "\n${YELLOW}Repository Setup${NC}"
    read -p "Enter GitHub repository URL (SSH or HTTPS): " repo_url
    read -p "Enter clone directory [default: current]: " clone_dir
    clone_dir="${clone_dir:-.}"
    
    if git clone "$repo_url" "$clone_dir"; then
        echo -e "${GREEN}Repository cloned successfully to ${clone_dir}${NC}[4]"
    else
        echo -e "${RED}Clone failed! Verify:${NC}"
        echo "- URL correctness"
        echo "- Repository permissions"
        echo "- Network connectivity"
        exit 1
    fi
}

# Main execution flow
check_architecture
install_git
install_gh_cli
configure_git
setup_ssh
github_login
clone_repo

# Post-install verification
echo -e "\n${GREEN}Verification:${NC}"
git config --global --list | grep -E 'user.name|user.email'
gh auth status
ssh -T git@github.com

echo -e "\n${GREEN}Setup completed successfully!${NC}"
