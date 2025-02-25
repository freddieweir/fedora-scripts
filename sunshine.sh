# Repository setup  
sudo dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm  
sudo dnf copr enable -y lizardbyte/sunshine  

# Package installation  
sudo dnf install -y sunshine  

# Service configuration  
mkdir -p ~/.config/systemd/user/  
cat <<EOF > ~/.config/systemd/user/sunshine.service  
[Unit]
Description=Sunshine Game Streaming
After=graphical-session.target
Wants=network-online.target
Requires=dbus.socket

[Service]
ExecStart=/usr/bin/sunshine
Environment=DISPLAY=:0
Restart=on-failure
RestartSec=5
PrivateNetwork=yes

[Install]
WantedBy=graphical-session.target  
EOF

loginctl enable-linger $USER  
systemctl --user daemon-reload  
systemctl --user enable --now sunshine.service  
