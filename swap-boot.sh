#!/bin/bash

# Check for dry run option
dry_run=false
if [ "$1" == "--dry-run" ]; then
    dry_run=true
    echo "Dry run mode activated: No changes will be made."
fi

# Retrieve current OS ID
current_os_id=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

# Retrieve boot numbers based on boot entry names
pop_bootnums=($(efibootmgr | grep "Pop!_OS" | awk '{print substr($1,5,4)}'))
fedora_bootnums=($(efibootmgr | grep "Fedora" | awk '{print substr($1,5,4)}'))
uefi_os_bootnum=$(efibootmgr | grep "UEFI OS" | awk '{print substr($1,5,4)}')
hard_drive_bootnum=$(efibootmgr | grep "Hard Drive" | awk '{print substr($1,5,4)}')

# Join boot numbers into comma-separated strings
pop_bootnums_joined=$(IFS=,; echo "${pop_bootnums[*]}")
fedora_bootnums_joined=$(IFS=,; echo "${fedora_bootnums[*]}")

# Construct the new boot order based on current OS
if [ "$current_os_id" == "fedora" ]; then
    # We're on Fedora, so we want to make Pop!_OS first in the boot order
    boot_order="$pop_bootnums_joined,$fedora_bootnums_joined,$uefi_os_bootnum,$hard_drive_bootnum"
    echo "Detected current OS: Fedora"
    echo "Setting Pop!_OS as the first boot entry."
elif [ "$current_os_id" == "pop" ]; then
    # We're on Pop!_OS, so we want to make Fedora first in the boot order
    boot_order="$fedora_bootnums_joined,$pop_bootnums_joined,$uefi_os_bootnum,$hard_drive_bootnum"
    echo "Detected current OS: Pop!_OS"
    echo "Setting Fedora as the first boot entry."
else
    echo "Unknown OS: $current_os_id"
    exit 1
fi

# Display the new boot order
echo "New boot order will be: $boot_order"

if [ "$dry_run" = false ]; then
    # Change the boot order
    sudo efibootmgr -o $boot_order

    # Reboot the system
    echo "Rebooting the system..."
    sudo reboot
else
    echo "Dry run mode: No changes have been made."
    echo "Dry run mode: System will not reboot."
fi
