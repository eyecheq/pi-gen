# EyeCheq Kiosk OS - Pi-Gen Fork

This is a fork of [pi-gen](https://github.com/RPi-Distro/pi-gen) customized to build Debian 12 (Bookworm) images for Raspberry Pi CM4 on a custom host board.

## Project Overview

- **Purpose**: Build a kiosk operating system for EyeCheq devices
- **Target Hardware**: Raspberry Pi Compute Module 4 (CM4) on custom carrier board
- **Architecture**: ARM64 (64-bit)
- **Base OS**: Debian Bookworm
- **Current Version**: ec-kiosk-os-bookworm-0.0.1-alpha

## Build System

### Building Images

```bash
# Docker build (recommended for non-Debian hosts)
./build-docker.sh -c ec-kiosk_config_bookworm

# Resume a failed build
CONTINUE=1 ./build-docker.sh -c ec-kiosk_config_bookworm

# Keep container for incremental builds
PRESERVE_CONTAINER=1 ./build-docker.sh -c ec-kiosk_config_bookworm
```

### Configuration File

Main config: `ec-kiosk_config_bookworm`

Key settings:
- `RELEASE=bookworm` - Debian 12
- `ARCH=arm64` - 64-bit ARM
- `IMG_NAME=ec-kiosk-os-bookworm`
- `TARGET_HOSTNAME=eck-base-0000`
- `FIRST_USER_NAME=eyecheq` / `FIRST_USER_PASS=eyecheq`
- `ENABLE_SSH=1` with public key auth

## Stage System

The build uses custom EyeCheq stages instead of standard pi-gen stages 2-5:

| Stage | Purpose |
|-------|---------|
| `stage0` | Bootstrap - debootstrap, APT, firmware |
| `stage1` | Minimal bootable system - boot files, networking, SSH |
| `stage2_eck` | EyeCheq lite - I2C/GPIO/SPI tools, static IP (192.168.2.2), swap config |
| `stage3_eck` | EyeCheq desktop - GStreamer, Chromium, Qt5, OpenGL |
| `stage4_eck` | EyeCheq standard - Console autologin, compositor, power button disabled |

Build flow: `stage0 → stage1 → stage2_eck → stage3_eck → stage4_eck`

## Key Customizations

### Networking
- Static IP: `192.168.2.2/24`
- Gateway: `192.168.2.1`
- DNS: `192.168.2.1, 8.8.8.8, 8.8.4.4`
- Configuration: `stage2_eck/02-net-tweaks/files/static-ethernet.nmconnection`

### CM4 Hardware Support
- Boot config: `stage1/00-boot-files/files/config.txt`
- OTG mode enabled for USB host
- 64-bit kernel (linux-image-rpi-v8, linux-image-rpi-2712)
- Camera auto-detect enabled

### Kiosk Features
- Auto-login to console as `eyecheq` user
- Power button disabled (HandlePowerKey=ignore)
- Chromium browser as default
- X compositing manager (xcompmgr) enabled

### Hardware Libraries
Installed in stage2_eck:
- i2c-tools, python3-smbus2 (I2C)
- gpiod, python3-libgpiod, python3-gpiozero, pigpio (GPIO)
- python3-spidev (SPI)
- rpicam-apps-lite (camera)
- v4l-utils, mkvtoolnix, ffmpeg (video)

## Directory Structure

```
pi-gen/
├── build.sh                    # Main build script
├── build-docker.sh             # Docker build wrapper
├── ec-kiosk_config_bookworm    # EyeCheq build configuration
├── stage0/                     # Bootstrap (standard)
├── stage1/                     # Minimal system (standard)
├── stage2_eck/                 # EyeCheq lite customizations
│   ├── 01-sys-tweaks/          # Packages, swap, SSH
│   ├── 02-net-tweaks/          # Static IP configuration
│   └── 03-set-timezone/        # UTC timezone
├── stage3_eck/                 # EyeCheq desktop (graphics)
├── stage4_eck/                 # EyeCheq standard (kiosk mode)
│   ├── 01-console-autologin/   # Auto-login setup
│   └── 04-disable-pwr-button/  # Power button disabled
├── export-image/               # Image export scripts
└── scripts/                    # Helper scripts
```

## Output

Built images are placed in `deploy/`:
- `image_YYYY-MM-DD-ec-kiosk-os-bookworm.img.gz`
- `image_YYYY-MM-DD-ec-kiosk-os-bookworm-lite.img.gz` (stage2_eck export)

## Stage Substage Convention

Each stage contains numbered substages that run in order:
- `00-packages` - Package list to install
- `00-packages-nr` - Packages installed without recommends
- `00-run.sh` - Shell script run on host
- `00-run-chroot.sh` - Shell script run inside chroot
- `00-debconf` - Debconf preseed configuration
- `00-patches/` - Patches applied to files
- `files/` - Static files to copy

## Development Notes

- Branch: `arm64_eyecheq_kiosk_os_bookworm`
- Main branch for PRs: `master`
- Build requires root or Docker
- 200MB swap configured for 64-bit desktop with limited RAM
