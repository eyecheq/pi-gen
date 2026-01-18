# Config.txt Changelog - 2026-01-17

## Session Summary
Modifications made to `/boot/firmware/config.txt` on Pi CM4 (192.168.2.2) to support V2 PCB I2C bus layout.

## Backup Location
- `/boot/firmware/config.txt.v1-backup-20260117-210451` - Original V1 config

## Changes Made

### 1. Removed I2C1 (GPIO2/3)
```diff
- dtparam=i2c_arm=on
```
**Reason**: Free GPIO3 for dedicated power button use

### 2. Added I2C5 for CPU Fan (GPIO10/11)
```diff
+ dtoverlay=i2c5,pins_10_11
```
**Reason**: V2 PCB moves CPU fan to I2C5

### 3. Updated gpio-shutdown debounce
```diff
- dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=1000
+ dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=100
```
**Reason**: Faster button response

### 4. Cleaned up overlay syntax
```diff
- dtoverlay=i2c3,pins_4_5=1
+ dtoverlay=i2c3,pins_4_5

- dtoverlay=i2c6,pins_22_23=1
+ dtoverlay=i2c6,pins_22_23
```
**Reason**: Cleaner syntax (=1 is redundant)

### 5. Updated comments
- Changed header to "V2 PCB Configuration"
- Updated I2C bus documentation to reflect V2 layout
- Fixed typo "prpocessor" -> "processor"

## Issues Found and Fixed

### Issue: Desktop Environment Not Loading
**Symptom**: After reboot, Debian 12 login screen appeared instead of PIXEL desktop

**Root Cause**: NOT related to config.txt changes. The user's `.profile` was sourcing a non-existent file:
```
/home/eyecheq/.profile:28:. "$HOME/.cargo/env"
```
This caused the X session to exit with code 2 when lightdm tried to start the autologin session.

**Fix Applied**:
```bash
# Changed unconditional sourcing to conditional:
# Before:
. "$HOME/.cargo/env"

# After:
[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
```

**Files Fixed**:
- `/home/eyecheq/.profile` (backup: `.profile.bak`)
- `/home/eyecheq/.bashrc` (backup: `.bashrc.bak`)

**Verification**: After fixing and restarting lightdm, LXDE desktop loads correctly with:
- lxsession running
- openbox running
- lxpanel running
- pcmanfm running

### Issue: Display Layout Reset After Login
**Symptom**: Display configuration was reset after desktop login despite `display-setup-script` in lightdm

**Root Cause**: The LXDE desktop components (lxpanel, pcmanfm) were resetting the display configuration after the lightdm display-setup-script ran.

**Fix Applied**:
1. Created user-level LXDE autostart at `/home/eyecheq/.config/lxsession/LXDE-pi/autostart`
2. Created desktop autostart entry at `/home/eyecheq/.config/autostart/configure-displays.desktop`
3. Updated `/home/eyecheq/bin/configure_displays.sh` with better timing

**Expected Display Layout**:
```
┌─────────────────┬───────────────┬─────────────┐
│    HDMI-1       │    HDMI-2     │    DSI-1    │
│  1920x1080      │   1280x720    │  1024x600   │
│   PRIMARY       │  TOUCHSCREEN  │  Waveshare  │
│   pos 0x0       │  pos 1920x0   │  pos 3200x0 │
└─────────────────┴───────────────┴─────────────┘
```

**Touchscreen Mapping**: `ILITEK ILITEK-TP` → `HDMI-2`

### Issue: Power Button Not Triggering Shutdown
**Symptom**: Pressing power button did not shut down the system despite gpio-shutdown overlay working

**Root Cause 1**: `/etc/systemd/logind.conf` had `HandlePowerKey=ignore` set (intentionally for kiosk mode to prevent accidental shutdowns)

**Fix Applied**:
```bash
# Changed in /etc/systemd/logind.conf:
HandlePowerKey=ignore  →  HandlePowerKey=poweroff
```
Then restarted systemd-logind.

**Root Cause 2**: `/etc/xdg/autostart/pwrkey.desktop` was running `systemd-inhibit --what=handle-power-key gtk-nop` which blocked power key handling even after logind was configured correctly.

**Fix Applied**:
```bash
sudo mv /etc/xdg/autostart/pwrkey.desktop /etc/xdg/autostart/pwrkey.desktop.disabled
kill <inhibitor-pid>
```

## Files Modified
- `/boot/firmware/config.txt` - Main boot configuration
- `/home/eyecheq/.profile` - Fixed cargo env sourcing
- `/home/eyecheq/.bashrc` - Fixed cargo env sourcing
- `/home/eyecheq/bin/configure_displays.sh` - Improved display setup script
- `/home/eyecheq/.config/lxsession/LXDE-pi/autostart` - User autostart (new)
- `/home/eyecheq/.config/autostart/configure-displays.desktop` - Desktop autostart (new)
- `/etc/systemd/logind.conf` - Changed HandlePowerKey from ignore to poweroff
- `/etc/xdg/autostart/pwrkey.desktop` - Renamed to .disabled to allow power button shutdown

## How to Revert
```bash
sudo cp /boot/firmware/config.txt.v1-backup-20260117-210451 /boot/firmware/config.txt
sudo reboot
```

## Test Script Location
- Local: `scripts/eck-hardware-test.py`
- Pi: `/tmp/eck-hardware-test.py` (cleared on reboot)
