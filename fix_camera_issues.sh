#!/bin/bash
# Fix Camera Issues on Raspberry Pi
# Addresses: libcamera errors, config conflicts, permissions

echo "🔧 Fixing Camera Issues on Raspberry Pi"
echo "======================================="

# 1. Fix config.txt conflicts
echo "📝 Fixing /boot/config.txt conflicts..."
sudo cp /boot/config.txt /boot/config.txt.backup

# Remove duplicate camera_auto_detect entries
sudo sed -i '/^camera_auto_detect=0$/d' /boot/config.txt

# Ensure proper camera settings
if ! grep -q "camera_auto_detect=1" /boot/config.txt; then
    echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
fi

if ! grep -q "start_x=1" /boot/config.txt; then
    echo "start_x=1" | sudo tee -a /boot/config.txt
fi

if ! grep -q "gpu_mem=128" /boot/config.txt; then
    echo "gpu_mem=128" | sudo tee -a /boot/config.txt
fi

echo "✅ Config.txt updated"

# 2. Add user to video group
echo "👥 Adding user to video group..."
sudo usermod -a -G video $USER
echo "✅ User added to video group"

# 3. Fix libcamera permissions and environment
echo "🔐 Fixing libcamera permissions..."
sudo chmod 666 /dev/video*
sudo chmod 666 /dev/media*

# 4. Update libcamera environment
echo "🌍 Setting libcamera environment..."
echo 'export LIBCAMERA_LOG_LEVELS=*:ERROR' >> ~/.bashrc

# 5. Restart camera services
echo "🔄 Restarting camera services..."
sudo systemctl stop camera
sudo systemctl start camera

# 6. Check camera ribbon connection
echo "📷 Camera Connection Check:"
echo "=========================="
vcgencmd get_camera
echo ""

# 7. Test different video devices
echo "🎥 Testing video devices..."
for device in /dev/video0 /dev/video1 /dev/video2; do
    if [ -e "$device" ]; then
        echo "Testing $device..."
        v4l2-ctl --device=$device --info 2>/dev/null || echo "  Not accessible"
    fi
done

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Reboot Raspberry Pi: sudo reboot"
echo "2. After reboot, test: python pi_camera_wrapper.py"
echo "3. If still issues, check physical connection"
echo "4. Alternative: Use USB camera (more reliable)"

echo ""
echo "💡 USB Camera Alternative:"
echo "========================="
echo "If Pi Camera continues to have issues:"
echo "1. Connect USB webcam"
echo "2. Test: python test_camera.py"
echo "3. USB cameras are often more stable"
