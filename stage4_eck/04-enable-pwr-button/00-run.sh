#!/bin/bash -e

# V2 PCB: Enable power button handling for GPIO3 shutdown button
# The gpio-shutdown overlay in config.txt creates a KEY_POWER event on button press
# systemd-logind must be configured to handle this event

sed -i 's/^.*HandlePowerKey=.*$/HandlePowerKey=poweroff/' "${ROOTFS_DIR}/etc/systemd/logind.conf"

# Disable the pwrkey.desktop inhibitor that blocks power key handling
# This file runs systemd-inhibit to block power key events in the desktop session
if [ -f "${ROOTFS_DIR}/etc/xdg/autostart/pwrkey.desktop" ]; then
    mv "${ROOTFS_DIR}/etc/xdg/autostart/pwrkey.desktop" \
       "${ROOTFS_DIR}/etc/xdg/autostart/pwrkey.desktop.disabled"
fi
