#!/usr/bin/env python3
"""
EyeCheq Kiosk Hardware Test Script (V2 PCB)
Tests I2C buses, GPIO interfaces, and power button configuration.

Usage: sudo python3 eck-hardware-test.py [--monitor] [--fix-config] [--tree]
"""

import subprocess
import sys
import os
import time
import argparse
from pathlib import Path

# ANSI colors and formatting
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
DIM = '\033[2m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Box drawing characters for tree view
TREE_PIPE = '│'
TREE_TEE = '├──'
TREE_ELBOW = '└──'
TREE_BLANK = '   '

# =============================================================================
# EyeCheq Hardware I2C Device Registry (V2 PCB)
# =============================================================================
# Master list of all known I2C devices by address
KNOWN_DEVICES = {
    0x10: {
        'name': 'SparkFun VEML6075 UV Light Sensor',
        'type': 'sensor',
        'description': 'UV-A/UV-B light measurement',
    },
    0x2f: {
        'name': 'CPU Fan Controller',
        'type': 'thermal',
        'description': 'PWM fan speed control',
    },
    0x38: {
        'name': 'Adafruit DHT20 Temperature & Humidity Sensor',
        'type': 'sensor',
        'description': 'Temperature and humidity measurement',
    },
    0x44: {
        'name': 'Sensirion SHT40 Temperature & Humidity Sensor',
        'type': 'sensor',
        'description': 'High-accuracy temperature and humidity',
    },
    0x48: {
        'name': 'ADS1015 Analog to Digital Converter',
        'type': 'adc',
        'description': '12-bit ADC for motor position/current',
    },
    0x53: {
        'name': 'Adafruit LTR390 UV Light Sensor',
        'type': 'sensor',
        'description': 'UV and ambient light measurement',
    },
    0x60: {
        'name': 'PCA9685 PWM Expander (LEDs)',
        'type': 'pwm',
        'description': '16-channel LED brightness control',
    },
    0x68: {
        'name': 'SparkFun ICM-20948 9DoF IMU',
        'type': 'sensor',
        'description': 'Accelerometer, gyroscope, magnetometer',
    },
    0x69: {
        'name': 'Sensirion SEN54 Environmental Sensor',
        'type': 'sensor',
        'description': 'PM, VOC, humidity, temperature',
    },
    0x70: {
        'name': 'PCA9685 PWM Controller (Motors)',
        'type': 'pwm',
        'description': 'Motor speed and direction control',
    },
}

# =============================================================================
# V2 PCB I2C Bus Configuration
# =============================================================================
# GPIO2/GPIO3 - Power button only (no I2C)
# I2C3 - Sensor Board on GPIO4/5
# I2C4 - Motor + LED on GPIO6/7
# I2C5 - CPU Fan on GPIO10/11
# I2C6 - Air Quality on GPIO22/23
# =============================================================================

EXPECTED_I2C_BUSES = {
    3: {
        'name': 'Sensor Board',
        'gpio_sda': 4,
        'gpio_scl': 5,
        'overlay': 'dtoverlay=i2c3,pins_4_5',
        'expected_devices': [0x44, 0x53, 0x68],
        'optional_devices': [0x10, 0x38],  # May not be present on all units
    },
    4: {
        'name': 'Motor + LED Control',
        'gpio_sda': 6,
        'gpio_scl': 7,
        'overlay': 'dtoverlay=i2c4,pins_6_7',
        'expected_devices': [0x48, 0x60, 0x70],
        'optional_devices': [],
    },
    5: {
        'name': 'CPU Fan',
        'gpio_sda': 10,
        'gpio_scl': 11,
        'overlay': 'dtoverlay=i2c5,pins_10_11',
        'expected_devices': [0x2f],
        'optional_devices': [],
    },
    6: {
        'name': 'Air Quality',
        'gpio_sda': 22,
        'gpio_scl': 23,
        'overlay': 'dtoverlay=i2c6,pins_22_23',
        'expected_devices': [0x69],
        'optional_devices': [],
    },
}

# GPIO configuration for V2 PCB
GPIO_CONFIG = {
    3: {
        'name': 'Power Button',
        'expected': 'input with pull-up',
        'function': 'Shutdown trigger + Wake from halt',
        'overlay': 'gpio-shutdown',
    },
    17: {
        'name': 'Safety Bumper Switch',
        'expected': 'input with pull-up',
        'function': 'Safety interlock',
    },
    24: {
        'name': 'Audio Enable',
        'expected': 'output, driven high',
        'function': 'Enable audio amplifier',
    },
}


def run_cmd(cmd, check=False):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return '', 'Command timed out', 1
    except Exception as e:
        return '', str(e), 1


def print_header(text):
    """Print a section header."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")


def print_status(name, status, detail=''):
    """Print a status line with color."""
    if status == 'OK':
        color = GREEN
        symbol = '✓'
    elif status == 'WARN':
        color = YELLOW
        symbol = '!'
    elif status == 'FAIL':
        color = RED
        symbol = '✗'
    elif status == 'MISSING':
        color = RED
        symbol = '✗'
    elif status == 'OPTIONAL':
        color = DIM
        symbol = '○'
    else:
        color = RESET
        symbol = '?'

    detail_str = f" - {detail}" if detail else ''
    print(f"  {color}[{symbol}]{RESET} {name}: {color}{status}{RESET}{detail_str}")


def get_device_info(addr):
    """Get device information by address."""
    return KNOWN_DEVICES.get(addr, {
        'name': f'Unknown device at 0x{addr:02X}',
        'type': 'unknown',
        'description': '',
    })


def check_power_button_config():
    """Check power button configuration for V2 PCB."""
    print_header("POWER BUTTON CONFIGURATION CHECK")

    issues = []
    warnings = []

    # Check if gpio-shutdown overlay loaded successfully
    stdout, stderr, rc = run_cmd("dmesg | grep -i 'gpio.*shutdown\\|gpio_keys' | tail -10")

    print(f"\n{BOLD}Kernel messages for gpio-shutdown:{RESET}")
    if stdout:
        for line in stdout.split('\n'):
            if 'error' in line.lower() or 'cannot claim' in line.lower():
                print(f"  {RED}{line}{RESET}")
                issues.append("gpio-shutdown overlay failed to load")
            elif 'gpio_keys' in line.lower():
                print(f"  {GREEN}{line}{RESET}")
            else:
                print(f"  {DIM}{line}{RESET}")
    else:
        print(f"  {YELLOW}No gpio-shutdown messages found{RESET}")

    # Check GPIO3 current state
    stdout, _, _ = run_cmd("pinctrl get 3")
    print(f"\n{BOLD}GPIO3 current state:{RESET}")
    print(f"  {stdout}")

    if 'a0' in stdout.lower():
        print(f"  {RED}ERROR: GPIO3 is in ALT0 mode (I2C){RESET}")
        print(f"  {YELLOW}For V2 PCB, remove 'dtparam=i2c_arm=on' from config.txt{RESET}")
        issues.append("GPIO3 is configured for I2C instead of power button")
    elif 'ip' in stdout.lower():
        print(f"  {GREEN}GPIO3 is in input mode (correct for power button){RESET}")
    else:
        warnings.append("GPIO3 state unclear")

    # Check if gpio_keys module is loaded
    stdout, _, _ = run_cmd("lsmod | grep gpio_keys")
    print(f"\n{BOLD}gpio_keys module:{RESET}")
    if stdout:
        print(f"  {GREEN}Loaded{RESET}")
    else:
        print(f"  {RED}Not loaded{RESET}")
        issues.append("gpio_keys module not loaded")

    # Check for the shutdown button device
    stdout, _, rc = run_cmd("cat /sys/class/input/*/name 2>/dev/null | grep -i shutdown")
    print(f"\n{BOLD}Shutdown button input device:{RESET}")
    if rc == 0 and stdout:
        print(f"  {GREEN}Found: {stdout}{RESET}")
    else:
        print(f"  {RED}Not found{RESET}")
        issues.append("No shutdown button input device found")

    # Summary
    print(f"\n{BOLD}POWER BUTTON STATUS:{RESET}")
    if not issues:
        print(f"  {GREEN}[✓] Power button is correctly configured{RESET}")
        print(f"      - Button press will trigger shutdown")
        print(f"      - Button press will wake from halt")
        return True
    else:
        print(f"  {RED}[✗] Power button has configuration issues:{RESET}")
        for issue in issues:
            print(f"      - {issue}")
        print(f"\n  {BOLD}To fix for V2 PCB:{RESET}")
        print(f"      1. Remove 'dtparam=i2c_arm=on' from config.txt")
        print(f"      2. Add 'dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=100'")
        print(f"      3. Reboot the system")
        return False


def scan_i2c_bus(bus_num):
    """Scan a single I2C bus and return found devices."""
    stdout, stderr, rc = run_cmd(f"i2cdetect -y {bus_num} 2>&1")

    if rc != 0 or 'Error' in stderr:
        return None, stderr

    devices = []
    for line in stdout.split('\n')[1:]:
        parts = line.split(':')
        if len(parts) < 2:
            continue
        try:
            row_base = int(parts[0], 16)
            for i, val in enumerate(parts[1].split()):
                if val != '--' and val != 'UU':
                    addr = row_base + i
                    devices.append(addr)
        except ValueError:
            pass

    return devices, None


def print_i2c_tree():
    """Print I2C bus configuration as a tree view."""
    print_header("I2C HARDWARE TREE")

    # Get available buses
    stdout, _, _ = run_cmd("ls /dev/i2c-* 2>/dev/null | sed 's|/dev/i2c-||'")
    available_buses = set(int(x) for x in stdout.split('\n') if x.isdigit())

    print(f"\n{BOLD}{CYAN}EyeCheq Kiosk V2 PCB{RESET}")
    print(f"{TREE_PIPE}")

    # Power button (not I2C)
    print(f"{TREE_TEE} {MAGENTA}GPIO2/GPIO3{RESET} ─ {BOLD}Power Button{RESET}")
    stdout, _, _ = run_cmd("pinctrl get 3")
    if 'ip' in stdout.lower() and 'a0' not in stdout.lower():
        print(f"{TREE_PIPE}   {GREEN}└── [✓] gpio-shutdown (wake + shutdown){RESET}")
    else:
        print(f"{TREE_PIPE}   {RED}└── [✗] Not configured correctly{RESET}")

    bus_list = sorted(EXPECTED_I2C_BUSES.keys())
    all_found = []
    all_missing = []
    all_optional_missing = []

    for idx, bus_num in enumerate(bus_list):
        bus_info = EXPECTED_I2C_BUSES[bus_num]
        is_last_bus = (idx == len(bus_list) - 1)
        prefix = TREE_ELBOW if is_last_bus else TREE_TEE
        cont_prefix = TREE_BLANK if is_last_bus else f"{TREE_PIPE}   "

        gpio_str = f"GPIO{bus_info['gpio_sda']}/GPIO{bus_info['gpio_scl']}"
        bus_exists = bus_num in available_buses

        # Print bus header
        if bus_exists:
            status_icon = GREEN + '●' + RESET
        else:
            status_icon = RED + '○' + RESET

        print(f"{TREE_PIPE}")
        print(f"{prefix} {MAGENTA}{gpio_str}{RESET} ─ {BOLD}I2C{bus_num}: {bus_info['name']}{RESET} {status_icon}")

        if not bus_exists:
            print(f"{cont_prefix}   {RED}└── Bus not available! Check config.txt:{RESET}")
            print(f"{cont_prefix}       {DIM}{bus_info['overlay']}{RESET}")
            for addr in bus_info['expected_devices']:
                all_missing.append((bus_num, addr, get_device_info(addr)['name']))
            continue

        # Scan the bus
        devices, error = scan_i2c_bus(bus_num)
        if error:
            print(f"{cont_prefix}   {RED}└── Scan failed: {error}{RESET}")
            continue

        expected = set(bus_info['expected_devices'])
        optional = set(bus_info.get('optional_devices', []))
        found = set(devices)

        # Combine all possible devices for this bus
        all_addrs = sorted(expected | optional | found)

        if not all_addrs:
            print(f"{cont_prefix}   {YELLOW}└── No devices{RESET}")
            continue

        for dev_idx, addr in enumerate(all_addrs):
            is_last_dev = (dev_idx == len(all_addrs) - 1)
            dev_prefix = TREE_ELBOW if is_last_dev else TREE_TEE
            dev_info = get_device_info(addr)

            if addr in found:
                # Device found
                if addr in expected:
                    status = GREEN + '[✓]' + RESET
                    all_found.append((bus_num, addr, dev_info['name']))
                elif addr in optional:
                    status = GREEN + '[✓]' + RESET
                    all_found.append((bus_num, addr, dev_info['name']))
                else:
                    status = YELLOW + '[?]' + RESET  # Unexpected device

                print(f"{cont_prefix}   {dev_prefix} {status} {WHITE}0x{addr:02X}{RESET}: {dev_info['name']}")
                if dev_info['description']:
                    desc_prefix = TREE_BLANK if is_last_dev else f"{TREE_PIPE}   "
                    print(f"{cont_prefix}   {desc_prefix}    {DIM}{dev_info['description']}{RESET}")
            else:
                # Device not found
                if addr in expected:
                    status = RED + '[✗]' + RESET
                    all_missing.append((bus_num, addr, dev_info['name']))
                    print(f"{cont_prefix}   {dev_prefix} {status} {DIM}0x{addr:02X}: {dev_info['name']} (MISSING){RESET}")
                elif addr in optional:
                    status = DIM + '[○]' + RESET
                    all_optional_missing.append((bus_num, addr, dev_info['name']))
                    print(f"{cont_prefix}   {dev_prefix} {status} {DIM}0x{addr:02X}: {dev_info['name']} (optional){RESET}")

    # Print summary
    print(f"\n{BOLD}{'─'*70}{RESET}")
    print(f"{BOLD}DEVICE SUMMARY{RESET}")
    print(f"{BOLD}{'─'*70}{RESET}")

    total_expected = sum(len(b['expected_devices']) for b in EXPECTED_I2C_BUSES.values())

    print(f"\n  {GREEN}Found:{RESET} {len(all_found)}/{total_expected} expected devices")
    if all_found:
        for bus, addr, name in all_found:
            print(f"    {GREEN}✓{RESET} I2C{bus} @ 0x{addr:02X}: {name}")

    if all_missing:
        print(f"\n  {RED}Missing:{RESET} {len(all_missing)} expected devices")
        for bus, addr, name in all_missing:
            print(f"    {RED}✗{RESET} I2C{bus} @ 0x{addr:02X}: {name}")

    if all_optional_missing:
        print(f"\n  {DIM}Optional not present:{RESET} {len(all_optional_missing)}")
        for bus, addr, name in all_optional_missing:
            print(f"    {DIM}○ I2C{bus} @ 0x{addr:02X}: {name}{RESET}")

    return {
        'found': all_found,
        'missing': all_missing,
        'optional_missing': all_optional_missing,
    }


def check_gpio_status():
    """Check status of configured GPIOs."""
    print_header("GPIO STATUS CHECK")

    for gpio, config in sorted(GPIO_CONFIG.items()):
        stdout, _, _ = run_cmd(f"pinctrl get {gpio}")

        print(f"\n{BOLD}GPIO{gpio} - {config['name']}{RESET}")
        print(f"  Function: {config['function']}")
        print(f"  Expected: {config['expected']}")
        print(f"  Current:  {stdout}")

        # Validation
        if gpio == 24:  # Audio enable should be output high
            if 'op' in stdout and 'hi' in stdout:
                print_status("Status", "OK", "Output driving high")
            else:
                print_status("Status", "WARN", "Not configured as expected")
        elif gpio == 17:  # Safety bumper should be input with pull-up
            if 'ip' in stdout and 'pu' in stdout:
                print_status("Status", "OK", "Input with pull-up")
            else:
                print_status("Status", "WARN", "Not configured as expected")
        elif gpio == 3:  # Power button
            if 'a0' in stdout:
                print_status("Status", "FAIL", "In I2C mode - conflicts with power button!")
            elif 'ip' in stdout:
                print_status("Status", "OK", "Input mode (correct for power button)")
            else:
                print_status("Status", "WARN", "Unexpected configuration")

    # Check I2C GPIO pins
    print(f"\n{BOLD}I2C Bus GPIO Status:{RESET}")
    for bus_num, bus_info in sorted(EXPECTED_I2C_BUSES.items()):
        sda = bus_info['gpio_sda']
        scl = bus_info['gpio_scl']

        sda_out, _, _ = run_cmd(f"pinctrl get {sda}")
        scl_out, _, _ = run_cmd(f"pinctrl get {scl}")

        # Check if in alternate function mode (I2C)
        sda_ok = 'a' in sda_out.lower() and 'i2c' in sda_out.lower()
        scl_ok = 'a' in scl_out.lower() and 'i2c' in scl_out.lower()

        if sda_ok and scl_ok:
            status = f"{GREEN}[✓]{RESET}"
        else:
            status = f"{RED}[✗]{RESET}"

        print(f"  {status} I2C{bus_num} ({bus_info['name']}): GPIO{sda}/GPIO{scl}")
        if not (sda_ok and scl_ok):
            print(f"      {DIM}SDA: {sda_out}{RESET}")
            print(f"      {DIM}SCL: {scl_out}{RESET}")


def monitor_all_interfaces(duration=30):
    """Monitor GPIO interfaces for state changes."""
    print_header(f"MONITORING INTERFACES FOR {duration} SECONDS")
    print("Press Ctrl+C to stop\n")

    print(f"{BOLD}Monitoring:{RESET}")
    print("  - GPIO3 (Power Button)")
    print("  - GPIO17 (Safety Bumper)")
    print()

    try:
        start = time.time()
        last_gpio3 = None
        last_gpio17 = None

        while time.time() - start < duration:
            timestamp = time.strftime('%H:%M:%S')

            gpio3, _, _ = run_cmd("gpioget gpiochip0 3")
            gpio17, _, _ = run_cmd("gpioget gpiochip0 17")

            if gpio3 != last_gpio3:
                state = f"{RED}PRESSED (LOW){RESET}" if gpio3 == '0' else f"{GREEN}RELEASED (HIGH){RESET}"
                print(f"  [{timestamp}] GPIO3 (Power Button): {state}")
                last_gpio3 = gpio3

            if gpio17 != last_gpio17:
                state = f"{RED}PRESSED (LOW){RESET}" if gpio17 == '0' else f"{GREEN}RELEASED (HIGH){RESET}"
                print(f"  [{timestamp}] GPIO17 (Safety Bumper): {state}")
                last_gpio17 = gpio17

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n  Monitoring stopped by user")


def show_v2_config():
    """Show recommended config.txt for V2 PCB."""
    print_header("RECOMMENDED CONFIG.TXT FOR V2 PCB")

    print(f"""
{BOLD}Add/modify these lines in /boot/firmware/config.txt:{RESET}

{CYAN}# =============================================================================
# I2C Bus Configuration - V2 PCB
# =============================================================================
#
# Bus Layout:
#   GPIO2/3   - Power Button (gpio-shutdown + wake-from-halt)
#   I2C3      - Sensor Board on GPIO4/5
#   I2C4      - Motor + LED Control on GPIO6/7
#   I2C5      - CPU Fan on GPIO10/11
#   I2C6      - Air Quality Sensor on GPIO22/23
# ============================================================================={RESET}

{RED}# REMOVE THIS LINE (conflicts with power button on GPIO3):{RESET}
{DIM}# dtparam=i2c_arm=on{RESET}

{GREEN}# === Power Button on GPIO3 ==={RESET}
dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up,debounce=100

{GREEN}# === I2C3 - Sensor Board (GPIO4/5) ==={RESET}
{GREEN}# Devices: SHT40 (0x44), LTR390 (0x53), ICM-20948 (0x68){RESET}
dtoverlay=i2c3,pins_4_5

{GREEN}# === I2C4 - Motor + LED Control (GPIO6/7) ==={RESET}
{GREEN}# Devices: ADS1015 (0x48), PCA9685 LED (0x60), PCA9685 Motor (0x70){RESET}
dtoverlay=i2c4,pins_6_7

{GREEN}# === I2C5 - CPU Fan (GPIO10/11) ==={RESET}
{GREEN}# Devices: Fan Controller (0x2F){RESET}
dtoverlay=i2c5,pins_10_11

{GREEN}# === I2C6 - Air Quality (GPIO22/23) ==={RESET}
{GREEN}# Devices: SEN54 (0x69){RESET}
dtoverlay=i2c6,pins_22_23

{BOLD}After editing, reboot with:{RESET} sudo reboot
""")


def main():
    parser = argparse.ArgumentParser(
        description='EyeCheq Kiosk Hardware Test (V2 PCB)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 eck-hardware-test.py              # Run all tests
  sudo python3 eck-hardware-test.py --tree       # Show I2C device tree only
  sudo python3 eck-hardware-test.py --monitor    # Monitor GPIO inputs
  sudo python3 eck-hardware-test.py --v2-config  # Show V2 PCB config.txt
"""
    )
    parser.add_argument('--monitor', action='store_true',
                        help='Monitor GPIO inputs for state changes')
    parser.add_argument('--monitor-duration', type=int, default=30,
                        help='Monitoring duration in seconds (default: 30)')
    parser.add_argument('--tree', action='store_true',
                        help='Show I2C device tree only')
    parser.add_argument('--v2-config', action='store_true',
                        help='Show recommended config.txt for V2 PCB')
    args = parser.parse_args()

    print(f"{BOLD}{BLUE}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           EyeCheq Kiosk Hardware Test Script (V2 PCB)                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    # Check if running as root
    if os.geteuid() != 0:
        print(f"{YELLOW}Warning: Not running as root. Some tests may fail.{RESET}")
        print(f"Run with: sudo python3 {sys.argv[0]}\n")

    if args.v2_config:
        show_v2_config()
        return

    if args.tree:
        print_i2c_tree()
        return

    # Run all tests
    power_ok = check_power_button_config()
    result = print_i2c_tree()
    check_gpio_status()

    if args.monitor:
        monitor_all_interfaces(args.monitor_duration)

    # Final summary
    print_header("FINAL SUMMARY")

    found_count = len(result['found'])
    missing_count = len(result['missing'])
    total_expected = sum(len(b['expected_devices']) for b in EXPECTED_I2C_BUSES.values())

    if power_ok and missing_count == 0:
        print(f"\n  {GREEN}{BOLD}[✓] ALL SYSTEMS OPERATIONAL{RESET}")
        print(f"      Power button: Working")
        print(f"      I2C devices: {found_count}/{total_expected} found")
    else:
        print(f"\n  {YELLOW}{BOLD}[!] ISSUES DETECTED{RESET}")
        if not power_ok:
            print(f"      {RED}Power button: Not working{RESET}")
        if missing_count > 0:
            print(f"      {RED}Missing devices: {missing_count}{RESET}")

        print(f"\n  {BOLD}Run with --v2-config to see recommended configuration{RESET}")


if __name__ == '__main__':
    main()
