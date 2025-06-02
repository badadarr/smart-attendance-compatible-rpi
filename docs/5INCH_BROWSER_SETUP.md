# 5-Inch Display Browser Setup Guide

This guide provides specific browser configuration instructions for optimal 5-inch HDMI display performance.

## Recommended Browser: Chromium

### Installation
```bash
# Ubuntu/Raspberry Pi OS
sudo apt update
sudo apt install chromium-browser

# Windows
# Download from official Chromium website
```

### Launch Configuration for 5-Inch Displays

#### Fullscreen Kiosk Mode (Recommended)
```bash
chromium-browser \
  --kiosk \
  --no-sandbox \
  --disable-infobars \
  --disable-web-security \
  --disable-features=TranslateUI \
  --disable-ipc-flooding-protection \
  --window-size=800,480 \
  --window-position=0,0 \
  --force-device-scale-factor=1.0 \
  http://localhost:5001
```

#### Windowed Mode for Testing
```bash
chromium-browser \
  --window-size=800,480 \
  --window-position=0,0 \
  --force-device-scale-factor=1.0 \
  --disable-web-security \
  http://localhost:5001
```

### PowerShell (Windows) Configuration
```powershell
# Create shortcut for easy launching
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
& $chromePath --kiosk --window-size=800,480 --force-device-scale-factor=1.0 http://localhost:5001
```

## Browser Settings Optimization

### Disable Automatic Features
- **Auto-updates**: Disable to prevent interruptions
- **Password saving**: Disable for security
- **Sync**: Disable for offline operation
- **Extensions**: Remove all unnecessary extensions

### Touch Optimizations
- **Scroll bars**: Auto-hide enabled
- **Zoom**: Disabled (handled by our CSS)
- **Touch gestures**: Limited to essential only

## System Configuration

### Display Settings
```bash
# Set display resolution (Raspberry Pi)
sudo raspi-config
# Advanced Options > Resolution > DMT Mode 87 800x480 60Hz
```

### Auto-start Configuration
```bash
# Create systemd service for auto-launch
sudo nano /etc/systemd/system/attendance-kiosk.service
```

Service file content:
```ini
[Unit]
Description=Attendance System Kiosk
After=graphical-session.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
ExecStart=/usr/bin/chromium-browser --kiosk --no-sandbox --window-size=800,480 http://localhost:5001
Restart=always

[Install]
WantedBy=graphical-session.target
```

### Enable service:
```bash
sudo systemctl enable attendance-kiosk.service
sudo systemctl start attendance-kiosk.service
```

## Performance Optimization

### Memory Management
```bash
# Increase GPU memory split (Raspberry Pi)
sudo raspi-config
# Advanced Options > Memory Split > 128
```

### Browser Cache
```bash
# Clear cache on startup
chromium-browser --disk-cache-size=1 --media-cache-size=1
```

## Touch Calibration

### xinput calibration (Linux)
```bash
# List touch devices
xinput list

# Calibrate touch (adjust coordinates for your display)
xinput set-prop "TouchDevice" "Coordinate Transformation Matrix" 1 0 0 0 1 0 0 0 1
```

## Troubleshooting

### Common Issues

#### Display Resolution Problems
- Verify HDMI output resolution matches display (800x480)
- Check display scaling settings
- Ensure aspect ratio is maintained

#### Touch Input Issues
- Verify USB touch connection
- Check touch driver installation
- Calibrate touch coordinates if offset

#### Performance Issues
- Close unnecessary background applications
- Increase GPU memory allocation
- Reduce browser cache size
- Disable unnecessary browser features

### Debugging Commands
```bash
# Check display information
xrandr

# Monitor system resources
htop

# Check browser process
ps aux | grep chromium
```

## Security Considerations

### Kiosk Security
- Disable browser developer tools
- Remove access to system settings
- Hide browser UI elements
- Prevent website navigation outside attendance system

### Network Security
- Use local network only if possible
- Implement firewall rules
- Regular security updates

## Testing Checklist

- [ ] Display shows at correct resolution (800x480)
- [ ] Touch response is accurate and responsive
- [ ] All buttons are properly sized and clickable
- [ ] Text is readable at 5-inch size
- [ ] Camera feed displays correctly
- [ ] No scroll bars appear
- [ ] Auto-features are disabled
- [ ] Browser launches automatically on boot
- [ ] System performance is acceptable

## Alternative Browsers

### Firefox (Not Recommended)
Firefox may have scaling issues on 5-inch displays. If using Firefox:
```bash
firefox --width=800 --height=480 --new-instance http://localhost:5001
```

### Microsoft Edge (Windows)
```powershell
msedge --kiosk --window-size=800,480 http://localhost:5001
```

## Hardware Recommendations

### Compatible 5-Inch Displays
- **Waveshare 5inch HDMI LCD**: 800×480 resolution
- **Raspberry Pi Foundation 5" Display**: With HDMI adapter
- **Generic 5" HDMI Monitors**: Ensure 800×480 support

### Performance Requirements
- **Minimum RAM**: 2GB
- **Recommended RAM**: 4GB+
- **GPU Memory**: 128MB minimum
- **Touch Interface**: USB HID compliant
