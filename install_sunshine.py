import os
import subprocess
import sys
import venv
from getpass import getuser

# Capture the original user running the script
ORIGINAL_USER = getuser()

# Function to check if Sunshine is installed and running
def is_sunshine_installed():
    try:
        # Check if the Sunshine binary exists
        sunshine_path = subprocess.check_output(['which', 'sunshine'], stderr=subprocess.STDOUT).strip()
        print(f"Sunshine is installed at: {sunshine_path.decode()}")
        
        # Check if the Sunshine service is running
        service_status = subprocess.check_output(['sudo', 'systemctl', 'is-active', 'sunshine.service'], stderr=subprocess.STDOUT).strip()
        if service_status == b'active':
            print("Sunshine is already running.")
            return True
        else:
            print("Sunshine is installed but not running.")
            return False
    except subprocess.CalledProcessError:
        # Sunshine is not installed or not running
        print("Sunshine is not installed or not running.")
        return False

# Function to create directories if they don't exist
def create_directories():
    dirs = [f"/home/{ORIGINAL_USER}/git/fw/sunshine"]
    for dir in dirs:
        if not os.path.exists(dir):
            print(f"Creating directory: {dir}")
            os.makedirs(dir)
        else:
            print(f"Directory {dir} already exists. Skipping creation.")

# Function to install necessary dependencies
def install_dependencies():
    print("Installing dependencies for Sunshine...")
    try:
        # Run dnf update if necessary
        print("Updating system...")
        subprocess.check_call(["sudo", "dnf", "update", "-y"])

        # Check if development tools are already installed
        dev_tools_installed = subprocess.call(["dnf", "groupinfo", "Development Tools"], stdout=subprocess.DEVNULL) == 0
        if dev_tools_installed:
            print("Development Tools group already installed. Skipping.")
        else:
            print("Installing Development Tools group...")
            subprocess.check_call(["sudo", "dnf", "groupinstall", "-y", "Development Tools"])

        # Check for individual dependencies
        dependencies = [
            "boost-devel", "cmake", "gcc", "gcc-c++", "intel-mediasdk-devel",
            "libappindicator-gtk3-devel", "libcap-devel", "libcurl-devel", "libdrm-devel",
            "libevdev-devel", "libnotify-devel", "libva-devel", "libvdpau-devel", 
            "libX11-devel", "libxcb-devel", "libXcursor-devel", "libXfixes-devel", 
            "libXi-devel", "libXinerama-devel", "libXrandr-devel", "libXtst-devel", 
            "mesa-libGL-devel", "miniupnpc-devel", "npm", "numactl-devel", 
            "openssl-devel", "opus-devel", "pulseaudio-libs-devel", "rpm-build", 
            "wget", "which", "xorg-x11-drv-nvidia", "akmod-nvidia", "vdpauinfo", 
            "libva-vdpau-driver", "libva-utils"
        ]
        installed = subprocess.check_output(['dnf', 'list', 'installed'], stderr=subprocess.STDOUT).decode()
        for dep in dependencies:
            if dep in installed:
                print(f"{dep} is already installed. Skipping.")
            else:
                print(f"Installing {dep}...")
                subprocess.check_call(["sudo", "dnf", "install", "-y", dep])
    except subprocess.CalledProcessError as e:
        print(f"Error during installation of dependencies: {e}")
        sys.exit(1)

# Function to create a virtual environment
def create_virtualenv(env_name, env_path):
    venv_dir = os.path.join(env_path, env_name)
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment: {env_name}")
        venv.create(venv_dir, with_pip=True)
    else:
        print(f"Virtual environment {env_name} already exists. Skipping creation.")
    return venv_dir

# Function to activate the virtual environment
def activate_virtualenv(venv_dir):
    activate_script = os.path.join(venv_dir, "bin", "activate")
    if os.path.exists(activate_script):
        print(f"Activating virtual environment: {venv_dir}")
        subprocess.call(f"source {activate_script}", shell=True, executable="/bin/bash")
    else:
        print(f"Failed to activate virtual environment: {venv_dir}")
        sys.exit(1)

# Function to add user to necessary groups for permissions
def setup_permissions_groups():
    print("Setting up user permissions for GPU and input devices...")
    try:
        # Check if user is already in the video group
        video_group = subprocess.check_output(["groups", ORIGINAL_USER]).decode()
        if "video" in video_group:
            print(f"User {ORIGINAL_USER} is already in 'video' group. Skipping.")
        else:
            subprocess.check_call(["sudo", "usermod", "-aG", "video", ORIGINAL_USER])
            print(f"User {ORIGINAL_USER} added to 'video' group.")

        # Check if user is already in the input group
        input_group = subprocess.check_output(["groups", ORIGINAL_USER]).decode()
        if "input" in input_group:
            print(f"User {ORIGINAL_USER} is already in 'input' group. Skipping.")
        else:
            subprocess.check_call(["sudo", "usermod", "-aG", "input", ORIGINAL_USER])
            print(f"User {ORIGINAL_USER} added to 'input' group.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding user to groups: {e}")
        sys.exit(1)

# Function to export Wayland environment variable if needed
def export_wayland_display():
    if os.environ.get('WAYLAND_DISPLAY') is None:
        os.environ['WAYLAND_DISPLAY'] = 'wayland-0'
        print("Set WAYLAND_DISPLAY to wayland-0.")
    else:
        print("WAYLAND_DISPLAY is already set. Skipping.")

# Function to clone and build Sunshine
def build_sunshine():
    print("Cloning and building Sunshine...")
    sunshine_repo_path = f"/home/{ORIGINAL_USER}/git/fw/sunshine/Sunshine"
    if not os.path.exists(sunshine_repo_path):
        try:
            # Clone the Sunshine repository
            subprocess.check_call([
                "git", "clone", "https://github.com/LizardByte/Sunshine.git", 
                sunshine_repo_path
            ])
        except subprocess.CalledProcessError as e:
            print(f"Error during Sunshine clone: {e}")
            sys.exit(1)
    else:
        print(f"Sunshine repository already exists at {sunshine_repo_path}. Skipping clone.")

    try:
        os.chdir(sunshine_repo_path)
        
        # Checkout the specific version
        subprocess.check_call([
            "git", "checkout", "v2024.1011.4829"
        ])
        
        # Create a build directory and compile
        os.makedirs("build", exist_ok=True)
        os.chdir("build")
        subprocess.check_call(["cmake", ".."])
        subprocess.check_call(["make"])
        subprocess.check_call(["sudo", "make", "install"])
    except subprocess.CalledProcessError as e:
        print(f"Error during Sunshine build: {e}")
        sys.exit(1)

# Function to setup permissions for KMS display capture
def setup_permissions():
    print("Setting up KMS display capture permissions...")
    try:
        sunshine_binary = subprocess.check_output(['which', 'sunshine']).strip().decode()
        setcap_output = subprocess.check_output(['sudo', 'getcap', sunshine_binary])
        if "cap_sys_admin" in setcap_output.decode():
            print(f"KMS permissions already set for {sunshine_binary}. Skipping.")
        else:
            subprocess.check_call([
                "sudo", "setcap", "cap_sys_admin+p", sunshine_binary
            ])
            print(f"KMS permissions set for {sunshine_binary}.")
    except subprocess.CalledProcessError as e:
        print(f"Error during permission setup: {e}")
        sys.exit(1)

# Function to setup autostart with systemd
def setup_autostart_service():
    service_file_path = f"/etc/systemd/system/sunshine.service"
    if os.path.exists(service_file_path):
        print(f"Systemd service already exists at {service_file_path}. Skipping creation.")
    else:
        print(f"Creating systemd service at {service_file_path}")
        service_content = f"""
[Unit]
Description=Sunshine Game Streaming Service
After=network.target

[Service]
ExecStart=/usr/local/bin/sunshine
Restart=on-failure
User={ORIGINAL_USER}
Group={ORIGINAL_USER}

[Install]
WantedBy=multi-user.target
        """
        try:
            with open(service_file_path, "w") as service_file:
                service_file.write(service_content)

            # Enable and start the service
            subprocess.check_call(["sudo", "systemctl", "daemon-reload"])
            subprocess.check_call(["sudo", "systemctl", "enable", "sunshine.service"])
            subprocess.check_call(["sudo", "systemctl", "start", "sunshine.service"])
            subprocess.check_call(["sudo", "systemctl", "status", "sunshine.service"])
        except Exception as e:
            print(f"Error setting up systemd service: {e}")
            sys.exit(1)

def main():
    # Check if Sunshine is already installed and running
    if is_sunshine_installed():
        print("Sunshine is already installed and running. Skipping installation.")
        return

    # Create necessary directories
    create_directories()

    # Install dependencies
    install_dependencies()

    # Setup user permissions
    setup_permissions_groups()

    # Set Wayland display environment variable
    export_wayland_display()

    # Create and activate virtual environment
    venv_name = "sunshine-venv"
    venv_path = f"/home/{ORIGINAL_USER}/git/fw/sunshine"
    venv_dir = create_virtualenv(venv_name, venv_path)
    activate_virtualenv(venv_dir)

    # Build Sunshine
    build_sunshine()

    # Set up KMS permissions
    setup_permissions()

    # Setup autostart systemd service
    setup_autostart_service()

if __name__ == "__main__":
    main()
