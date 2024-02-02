# BULLSEYE ----------------------------------

pi-gen/stage2 copy/02-net-tweaks/00-packages

- dnsutils
- traceroute

pi-gen/stage2 copy/01-sys-tweaks/00-packages-nr

- python3-picamera2

pi-gen/stage3 copy/00-install-packages/00-packages

- libcamera-tools
- libcamera-apps

pi-gen/stage3 copy/00-install-packages/01-run.sh

# Remove alternative browser

update-alternatives --install /usr/bin/x-www-browser \
 x-www-browser /usr/bin/chromium-browser 86
update-alternatives --install /usr/bin/gnome-www-browser \
 gnome-www-browser /usr/bin/chromium-browser 86

pi-gen/stage4 copy/00-install-packages/00-packages

- python3-pygame
- python3-tk thonny
- python3-pgzero
- python3-serial
- python3-picamera
- debian-reference-en dillo
- python3-pip
- python3-numpy
- pypy
- alacarte rc-gui sense-hat
- geany
- piclone
- python3-twython
- python3-flask
- piwiz
- rp-prefapps
- vlc
- rpi-imager
- rpi-wayland

pi-gen/stage4 copy/00-install-packages/00-packages-nr

- realvnc-vnc-server

# BOOKWORM ----------------------------------

# Skip image creation in stage 2

/home/pi/pi-gen/stage2_eck/SKIP_IMAGES

stage2_eck/02-net-tweaks/00-packages
TODO: Remove wpasupplicant wireless-tools

- dnsutils
- traceroute

pi-gen/stage2_eck/02-net-tweaks/01-run.sh

- # EC : Assign a static IP address to 192.168.2.2
- install -v -m 600 files/static-ethernet.nmconnection "${ROOTFS_DIR}/etc/NetworkManager/system-connections/static-ethernet.nmconnection"

pi-gen/stage2/03-accept-mathematica-eula/00-debconf

- Remove Wolfram-engine which is installed in stage5

pi-gen/stage3_eck/00-install-packages/00-debconf
TODO: Remove rpi-chromium-mods rpi-chromium-mods/adobe note

pi-gen/stage3_eck/00-install-packages/00-packages

- evince
- firefox rpi-firefox-mods
- libcamera-tools
- libcamera-apps
- python3-picamera2

pi-gen/stage3_eck/00-install-packages/00-packages-nr

- xserver-xorg-video-fbdev xserver-xorg xinit xserver-xorg-video-fbturbo

pi-gen/stage3_eck/00-install-packages/01-run.sh

- Remove alternate browser
  update-alternatives --install /usr/bin/x-www-browser \
   x-www-browser /usr/bin/chromium-browser 86
  update-alternatives --install /usr/bin/gnome-www-browser \
   gnome-www-browser /usr/bin/chromium-browser 86

pi-gen/stage4_eck/00-install-packages/00-packages

- python3-pygame
- python3-tk thonny
- python3-pgzero
- python3-serial
- debian-reference-en dillo
- python3-pip
- python3-numpy
- alacarte rc-gui sense-hat
- geany
- piclone
- python3-twython
- python3-flask
- piwiz
- rp-prefapps
- vlc
- rpi-imager

Removed the following files
pi-gen/stage4/00-install-packages/00-packages-nr
pi-gen/stage4/00-install-packages/00-packages-nr
pi-gen/stage4/03-bookshelf
pi-gen/stage4/05-print-support
pi-gen/stage4/06-enable-wayland

Added

- /stage4/SKIP
- /stage4/SKIP_IMAGES
