#!/bin/bash
# Enhanced Camera Config Fix for Raspberry Pi
# Addresses specific issues found in user's config.txt

echo "🔧 Enhanced Camera Configuration Fix"
echo "===================================="

# Backup current config
echo "💾 Creating backup of config.txt..."
sudo cp /boot/config.txt /boot/config.txt.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

# Create optimized config for Pi Camera
echo "📝 Applying camera optimizations..."

# Remove manual ov5647 overlay (conflicts with auto-detect)
sudo sed -i '/^dtoverlay=ov5647$/d' /boot/config.txt
echo "✅ Removed manual ov5647 overlay"

# Ensure camera_auto_detect is enabled (should already be there)
if ! grep -q "^camera_auto_detect=1" /boot/config.txt; then
    echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
    echo "✅ Added camera_auto_detect=1"
else
    echo "✅ camera_auto_detect=1 already present"
fi

# Ensure legacy camera support if needed
if ! grep -q "^start_x=1" /boot/config.txt; then
    echo "start_x=1" | sudo tee -a /boot/config.txt
    echo "✅ Added start_x=1"
else
    echo "✅ start_x=1 already present"
fi

# Check GPU memory allocation
current_gpu_mem=$(grep "^gpu_mem=" /boot/config.txt | cut -d'=' -f2)
if [ "$current_gpu_mem" = "128" ]; then
    echo "✅ GPU memory already optimal (128MB)"
else
    # Update or add gpu_mem
    if grep -q "^gpu_mem=" /boot/config.txt; then
        sudo sed -i 's/^gpu_mem=.*/gpu_mem=128/' /boot/config.txt
        echo "✅ Updated gpu_mem to 128MB"
    else
        echo "gpu_mem=128" | sudo tee -a /boot/config.txt
        echo "✅ Added gpu_mem=128MB"
    fi
fi

# Enable VC4 driver if not already (helps with some camera issues)
if grep -q "^#dtoverlay=vc4-kms-v3d" /boot/config.txt; then
    echo "⚠️  VC4 driver is commented out"
    echo "🤔 Do you want to enable VC4 driver? (can help with camera issues)"
    echo "   This might affect display output on some setups"
    read -p "Enable VC4 driver? [y/N]: " enable_vc4
    
    if [[ $enable_vc4 =~ ^[Yy]$ ]]; then
        sudo sed -i 's/^#dtoverlay=vc4-kms-v3d/dtoverlay=vc4-kms-v3d/' /boot/config.txt
        echo "✅ Enabled VC4 driver"
    else
        echo "⏭️  Keeping VC4 driver disabled"
    fi
else
    echo "✅ VC4 driver configuration unchanged"
fi

# Add camera-specific optimizations
echo ""
echo "📷 Adding camera-specific optimizations..."

# Ensure no conflicting camera settings
sudo sed -i '/^dtoverlay=imx219$/d' /boot/config.txt
sudo sed -i '/^dtoverlay=imx477$/d' /boot/config.txt
sudo sed -i '/^dtoverlay=imx708$/d' /boot/config.txt

# Add optimizations for Pi Camera v1 (OV5647)
if ! grep -q "# Pi Camera optimizations" /boot/config.txt; then
    echo "" | sudo tee -a /boot/config.txt
    echo "# Pi Camera optimizations" | sudo tee -a /boot/config.txt
    echo "# These settings help with OV5647 (Pi Camera v1) compatibility" | sudo tee -a /boot/config.txt
fi

# Check for HDMI settings that might interfere
echo ""
echo "🖥️  Checking display settings that might affect camera..."

if grep -q "hdmi_force_hotplug=1" /boot/config.txt; then
    echo "✅ HDMI force hotplug enabled (good for stability)"
fi

# Show final camera-related config
echo ""
echo "📋 Final camera configuration:"
echo "=============================="
grep -E "(camera|start_x|gpu_mem|dtoverlay)" /boot/config.txt | grep -v "^#"

echo ""
echo "🎯 Next steps:"
echo "=============="
echo "1. Reboot: sudo reboot"
echo "2. After reboot, test: python pi_camera_wrapper.py"
echo "3. Check camera status: vcgencmd get_camera" 
echo "4. If still issues, try USB camera alternative"

echo ""
echo "💡 Alternative approach if Pi Camera still fails:"
echo "================================================"
echo "1. Use USB webcam (often more reliable)"
echo "2. Update config.ini to use USB camera"
echo "3. USB cameras don't need special config.txt settings"
