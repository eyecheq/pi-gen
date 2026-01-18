# Config.txt Changes for V2 PCB

## Summary of Changes

The V2 PCB changes the I2C bus GPIO assignments to free GPIO2/GPIO3 for the power button.

### GPIO Assignments

| Function | Old PCB (V1) | New PCB (V2) |
|----------|--------------|--------------|
| Power Button | GPIO3 (conflicted with I2C1) | GPIO3 (dedicated) |
| I2C1 (Main) | GPIO2/3 | **Removed** |
| I2C3 (Sensors) | GPIO4/5 | GPIO4/5 (unchanged) |
| I2C4 (Motor+LED) | GPIO6/7 | GPIO6/7 (unchanged) |
| I2C5 (CPU Fan) | N/A | **GPIO10/11 (new)** |
| I2C6 (Air Quality) | GPIO22/23 | GPIO22/23 (unchanged) |

## Recommended config.txt Changes

### Remove These Lines

```
# REMOVE - This conflicts with gpio-shutdown on GPIO3
dtparam=i2c_arm=on
```

### Modify These Lines

```diff
# I2C Bus Configuration for V2 PCB
# =================================

# === Power Button on GPIO3 ===
# With I2C1 removed, GPIO3 is now available for gpio-shutdown
# Momentary button from GPIO3 to GND triggers shutdown and wake-from-halt
- dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=1000
+ dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=100

# === I2C3 - Sensor Board (GPIO4/5) ===
# No change needed
dtoverlay=i2c3,pins_4_5

# === I2C4 - Motor + LED Control (GPIO6/7) ===
- dtoverlay=i2c4,pins_6_7
+ dtoverlay=i2c4,pins_6_7

# === I2C5 - CPU Fan (GPIO10/11) - NEW ===
+ dtoverlay=i2c5,pins_10_11

# === I2C6 - Air Quality (GPIO22/23) ===
- dtoverlay=i2c6,pins_22_23=1
+ dtoverlay=i2c6,pins_22_23
```

## Complete I2C Section for V2 PCB

Replace the I2C configuration section in `/boot/firmware/config.txt` with:

```
# =============================================================================
# I2C Bus Configuration - V2 PCB
# =============================================================================
#
# Bus Layout:
#   GPIO2/3   - Power Button (gpio-shutdown + wake-from-halt)
#   I2C3      - Sensor Board on GPIO4 (SDA) / GPIO5 (SCL)
#   I2C4      - Motor + LED Control on GPIO6 (SDA) / GPIO7 (SCL)
#   I2C5      - CPU Fan on GPIO10 (SDA) / GPIO11 (SCL)
#   I2C6      - Air Quality Sensor on GPIO22 (SDA) / GPIO23 (SCL)
#
# Device Addresses:
#   I2C3: 0x44 (SHT40), 0x53 (LTR390), 0x68 (ICM-20948)
#   I2C4: 0x48 (ADS1015), 0x60 (PCA9685 LED), 0x70 (PCA9685 Motor)
#   I2C5: 0x2F (CPU Fan)
#   I2C6: 0x69 (SEN54)
# =============================================================================

# === Power Button on GPIO3 ===
# Momentary button from GPIO3 to GND.
# - Press while running: initiates shutdown
# - Press while halted: wakes system (hardware feature of GPIO3)
dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=100

# === I2C3 - Sensor Board (GPIO4/5) ===
# Devices: SHT40 (0x44), LTR390 (0x53), ICM-20948 (0x68)
dtoverlay=i2c3,pins_4_5

# === I2C4 - Motor + LED Control (GPIO6/7) ===
# Devices: ADS1015 (0x48), PCA9685 LED (0x60), PCA9685 Motor (0x70)
dtoverlay=i2c4,pins_6_7

# === I2C5 - CPU Fan (GPIO10/11) ===
# Devices: Fan Controller (0x2F)
dtoverlay=i2c5,pins_10_11

# === I2C6 - Air Quality (GPIO22/23) ===
# Devices: SEN54 (0x69)
dtoverlay=i2c6,pins_22_23
```

## Verification

After making these changes and rebooting, verify with:

```bash
# Check I2C buses exist
ls /dev/i2c-*
# Expected: /dev/i2c-3 /dev/i2c-4 /dev/i2c-5 /dev/i2c-6

# Check gpio-shutdown loaded
dmesg | grep -i gpio.*shutdown
# Should NOT show errors

# Check for shutdown button input device
cat /sys/class/input/*/name | grep -i shutdown
# Should show: gpio_keys

# Scan each bus
i2cdetect -y 3  # Sensor Board: 0x44, 0x53, 0x68
i2cdetect -y 4  # Motor+LED: 0x48, 0x60, 0x70
i2cdetect -y 5  # CPU Fan: 0x2F
i2cdetect -y 6  # Air Quality: 0x69
```

## Migration Notes

1. **No I2C1**: The new PCB does not use I2C1 (GPIO2/3). Any code referencing `/dev/i2c-1` must be updated.

2. **New I2C5**: CPU Fan has moved from I2C1 to I2C5. Update fan control code to use `/dev/i2c-5`.

3. **Power Button Works**: The gpio-shutdown overlay will now load successfully since GPIO3 is not claimed by I2C.

4. **Debounce Reduced**: Changed debounce from 1000ms to 100ms for more responsive button presses.
