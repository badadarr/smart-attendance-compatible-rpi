#!/bin/bash
# Troubleshooting and Fix Script for Face Recognition Attendance System
# Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit

echo "🔧 Face Recognition Attendance System - Troubleshooting"
echo "======================================================"

# Function to fix camera permissions
fix_camera_permissions() {
    echo "📹 Fixing camera permissions..."
    
    # Add user to video group
    sudo usermod -a -G video $USER
    
    # Set permissions for video devices
    for device in /dev/video*; do
        if [ -e "$device" ]; then
            sudo chmod 666 "$device"
            echo "✅ Fixed permissions for $device"
        fi
    done
    
    echo "💡 You may need to log out and log back in for group changes to take effect"
}

# Function to enable camera interface
enable_camera() {
    echo "📷 Enabling camera interface..."
    
    # Enable camera using raspi-config
    sudo raspi-config nonint do_camera 0
    
    # Check if camera is enabled in config
    if grep -q "start_x=1" /boot/config.txt; then
        echo "✅ Camera interface is enabled"
    else
        echo "🔧 Adding camera configuration..."
        echo "start_x=1" | sudo tee -a /boot/config.txt
        echo "gpu_mem=128" | sudo tee -a /boot/config.txt
    fi
    
    echo "⚠️  Reboot required for camera changes to take effect"
}

# Function to install missing packages
install_missing_packages() {
    echo "📦 Installing missing system packages..."
    
    sudo apt update
    sudo apt install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        libopencv-dev \
        python3-opencv \
        libatlas-base-dev \
        libjasper-dev \
        libqtgui4 \
        libqt4-test \
        libhdf5-dev \
        libhdf5-serial-dev \
        libharfbuzz0b \
        libwebp6 \
        libtiff5 \
        libjasper1 \
        libilmbase23 \
        libopenexr23 \
        libgstreamer1.0-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libgtk-3-dev \
        espeak \
        espeak-data \
        libespeak1 \
        libespeak-dev \
        ffmpeg
    
    echo "✅ System packages installation completed"
}

# Function to fix Python virtual environment
fix_virtual_environment() {
    echo "🐍 Fixing Python virtual environment..."
    
    # Remove old virtual environment if corrupted
    if [ -d "venv" ]; then
        echo "🗑️  Removing old virtual environment..."
        rm -rf venv
    fi
    
    # Create new virtual environment
    echo "🆕 Creating new virtual environment..."
    python3 -m venv venv
    
    # Activate and upgrade pip
    source venv/bin/activate
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        echo "📚 Installing Python packages..."
        pip install -r requirements.txt
    else
        echo "❌ requirements.txt not found!"
        return 1
    fi
    
    deactivate
    echo "✅ Virtual environment fixed"
}

# Function to fix file permissions
fix_file_permissions() {
    echo "🔐 Fixing file permissions..."
    
    # Make Python scripts executable
    chmod +x *.py 2>/dev/null
    chmod +x *.sh 2>/dev/null
    
    # Create directories if they don't exist
    mkdir -p data Attendance templates static
    
    # Set proper permissions for directories
    chmod 755 data Attendance templates static
    
    # Set permissions for data files
    if [ -f "data/faces_data.pkl" ]; then
        chmod 644 data/faces_data.pkl
    fi
    
    if [ -f "data/names.pkl" ]; then
        chmod 644 data/names.pkl
    fi
    
    echo "✅ File permissions fixed"
}

# Function to clean up temporary files
cleanup_temp_files() {
    echo "🧹 Cleaning up temporary files..."
    
    # Remove Python cache
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    
    # Remove temporary CSV files
    find . -name "temp_*.csv" -delete 2>/dev/null
    
    # Clean log files (keep only recent ones)
    find . -name "*.log" -mtime +7 -delete 2>/dev/null
    
    echo "✅ Temporary files cleaned"
}

# Function to check and fix memory issues
fix_memory_issues() {
    echo "💾 Checking and fixing memory issues..."
    
    # Check available memory
    free_mem=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    echo "📊 Available memory: ${free_mem}MB"
    
    if [ "$free_mem" -lt 100 ]; then
        echo "⚠️  Low memory detected. Attempting to free up memory..."
        
        # Clear system cache
        sudo sync
        sudo sysctl vm.drop_caches=3
        
        # Kill memory-intensive processes (if any)
        sudo pkill -f chromium 2>/dev/null
        sudo pkill -f firefox 2>/dev/null
        
        echo "🔄 Memory cleanup completed"
    else
        echo "✅ Memory levels are adequate"
    fi
    
    # Check swap
    swap_total=$(free -m | awk 'NR==3{print $2}')
    if [ "$swap_total" -eq 0 ]; then
        echo "💡 No swap detected. Consider enabling swap for better performance."
        echo "   Run: sudo dphys-swapfile setup && sudo dphys-swapfile swapon"
    fi
}

# Function to test camera functionality
test_camera() {
    echo "📸 Testing camera functionality..."
    
    # Test with vcgencmd (Pi Camera)
    if command -v vcgencmd &> /dev/null; then
        cam_status=$(vcgencmd get_camera)
        echo "🎥 Camera status: $cam_status"
        
        if [[ "$cam_status" == *"detected=1"* ]]; then
            echo "✅ Pi Camera detected"
        else
            echo "❌ Pi Camera not detected"
        fi
    fi
    
    # Test video devices
    echo "🔍 Checking video devices..."
    for i in {0..4}; do
        if [ -e "/dev/video$i" ]; then
            echo "✅ Found /dev/video$i"
            
            # Quick test with Python
            python3 -c "
import cv2
cap = cv2.VideoCapture($i)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print('✅ Video device $i is working')
    else:
        print('❌ Video device $i cannot capture frames')
    cap.release()
else:
    print('❌ Cannot open video device $i')
" 2>/dev/null
        fi
    done
}

# Function to update system
update_system() {
    echo "⬆️  Updating system..."
    
    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y
    sudo apt autoclean
    
    echo "✅ System updated"
}

# Function to check temperature and throttling
check_temperature() {
    echo "🌡️  Checking system temperature..."
    
    if command -v vcgencmd &> /dev/null; then
        temp=$(vcgencmd measure_temp)
        echo "🔥 CPU Temperature: $temp"
        
        # Check throttling
        throttled=$(vcgencmd get_throttled)
        if [ "$throttled" = "throttled=0x0" ]; then
            echo "✅ No throttling detected"
        else
            echo "⚠️  Throttling detected: $throttled"
            echo "💡 Consider adding cooling or reducing system load"
        fi
    else
        echo "💻 Temperature check not available (non-Pi system)"
    fi
}

# Function to fix ARM-specific installation issues
fix_arm_installation() {
    echo "🔧 Fixing ARM architecture specific issues..."
    
    # Check architecture
    ARCH=$(uname -m)
    echo "📋 Detected architecture: $ARCH"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please run installation first."
        return 1
    fi
    
    # Install build dependencies
    echo "📦 Installing build dependencies for ARM..."
    sudo apt update && sudo apt install -y \
        build-essential \
        cmake \
        pkg-config \
        python3-dev \
        libatlas-base-dev \
        gfortran \
        libhdf5-dev \
        libhdf5-serial-dev \
        python3-h5py \
        libjpeg-dev \
        libtiff-dev \
        libpng-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libgtk-3-dev
    
    # Try installing with piwheels (ARM-optimized repository)
    echo "🎯 Installing packages with ARM optimization..."
    pip install --extra-index-url https://www.piwheels.org/simple/ \
        numpy scipy scikit-learn opencv-python-headless flask pandas pillow
    
    # If still failing, try minimal versions
    if [ $? -ne 0 ]; then
        echo "⚠️  Standard installation failed, trying minimal versions..."
        pip install -r requirements_rpi_minimal.txt
    fi
    
    echo "✅ ARM installation fix completed"
}

# Function to fix SciPy build issues
fix_scipy_build() {
    echo "🧮 Fixing SciPy build issues..."
    
    # Install BLAS/LAPACK libraries
    sudo apt install -y libopenblas-dev liblapack-dev
    
    # Set environment variables for cross-compilation
    export NPY_NUM_BUILD_JOBS=1
    export SCIPY_USE_PROPACK=0
    
    # Try installing scipy with specific flags
    pip install --no-use-pep517 scipy==1.7.3
    
    echo "✅ SciPy build fix attempted"
}

# Main menu
show_menu() {
    echo ""
    echo "🛠️  Troubleshooting Options:"
    echo "1. Fix camera permissions and enable camera"
    echo "2. Install missing system packages"
    echo "3. Fix Python virtual environment"
    echo "4. Fix file permissions"
    echo "5. Clean up temporary files"
    echo "6. Fix memory issues"
    echo "7. Test camera functionality"
    echo "8. Update system"
    echo "9. Check temperature and throttling"
    echo "10. Run all fixes (recommended)"
    echo "11. Exit"
    echo ""
}

# Execute fix based on user choice
execute_fix() {
    case $1 in
        1)
            fix_camera_permissions
            enable_camera
            ;;
        2)
            install_missing_packages
            ;;
        3)
            fix_virtual_environment
            ;;
        4)
            fix_file_permissions
            ;;
        5)
            cleanup_temp_files
            ;;
        6)
            fix_memory_issues
            ;;
        7)
            test_camera
            ;;
        8)
            update_system
            ;;
        9)
            check_temperature
            ;;
        10)
            echo "🔧 Running all fixes..."
            cleanup_temp_files
            fix_file_permissions
            install_missing_packages
            fix_camera_permissions
            enable_camera
            fix_virtual_environment
            fix_memory_issues
            test_camera
            check_temperature
            echo "✅ All fixes completed!"
            ;;
        11)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            ;;
    esac
}

# Main loop
while true; do
    show_menu
    echo -n "Select an option (1-11): "
    read -r choice
    execute_fix $choice
    echo ""
    echo "Press Enter to continue..."
    read -r
done
