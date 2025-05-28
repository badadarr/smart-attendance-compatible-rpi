# Raspberry Pi ARM Installation Troubleshooting Guide

## 🔧 Common Installation Issues on Raspberry Pi

### Issue 1: SciPy Build Failure
**Error:** `× pip subprocess to install build dependencies did not run successfully`

**Cause:** Cross-compilation issues on ARM architecture

**Solutions:**

#### Option A: Use the Fix Script (Recommended)
```bash
chmod +x fix_rpi_installation.sh
./fix_rpi_installation.sh
```

#### Option B: Manual Fix
```bash
# Install build dependencies
sudo apt update && sudo apt install -y \
    build-essential cmake pkg-config python3-dev \
    libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev \
    libjpeg-dev libtiff-dev libpng-dev libavcodec-dev \
    libavformat-dev libswscale-dev libv4l-dev libgtk-3-dev

# Activate virtual environment
source venv/bin/activate

# Install with piwheels (ARM-optimized packages)
pip install --extra-index-url https://www.piwheels.org/simple/ \
    numpy scipy scikit-learn opencv-python-headless flask pandas pillow
```

#### Option C: Use Alternative Requirements
```bash
pip install -r requirements_rpi_minimal.txt
```

### Issue 2: Package Not Available for ARM64
**Error:** `Package 'libqtgui4' has no installation candidate`

**Cause:** Some packages are obsolete or not available for ARM64

**Solution:** Use updated package names
```bash
# Install updated packages
sudo apt install -y \
    libilmbase25 \
    libopenexr25 \
    libwebp7 \
    qt5-default  # instead of libqtgui4
```

### Issue 3: NumPy Cross-Compilation Error
**Error:** `Can not run test applications in this cross environment`

**Solutions:**

#### Option A: Use Pre-compiled Wheels
```bash
pip install --only-binary=:all: "numpy>=1.21.0,<1.25.0"
```

#### Option B: Install System Package
```bash
sudo apt install python3-numpy python3-scipy python3-opencv
```

### Issue 4: Memory Issues During Installation
**Error:** Build process killed or runs out of memory

**Solutions:**

#### Increase Swap Space
```bash
# Increase swap to 2GB temporarily
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### Install One Package at a Time
```bash
pip install numpy
pip install scipy
pip install scikit-learn
pip install opencv-python-headless
pip install flask pandas pillow
```

## 🎯 Quick Fix Commands

### Complete Fix Sequence
```bash
# 1. Run the automated fix
chmod +x fix_rpi_installation.sh
./fix_rpi_installation.sh

# 2. If still failing, try minimal installation
source venv/bin/activate
pip install -r requirements_rpi_minimal.txt

# 3. Test the installation
python -c "import cv2, numpy, sklearn, flask; print('✅ All packages imported successfully!')"

# 4. If OpenCV fails, try system package
sudo apt install python3-opencv
```

### Emergency Minimal Setup
```bash
# Minimal working setup
source venv/bin/activate
pip install opencv-python-headless flask pandas pillow

# For face recognition, you might need to install manually:
sudo apt install python3-opencv python3-numpy python3-scipy
```

## 🧪 Testing Installation

### Test Individual Components
```bash
# Test OpenCV
python -c "import cv2; print('OpenCV version:', cv2.__version__)"

# Test NumPy
python -c "import numpy as np; print('NumPy version:', np.__version__)"

# Test camera
python -c "import cv2; cap=cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error'); cap.release()"

# Test Flask
python -c "import flask; print('Flask version:', flask.__version__)"
```

### Run Validation Script
```bash
python validate_setup.py
```

## 📋 Alternative Approaches

### Approach 1: Use System Python Packages
```bash
# Install system packages instead of pip packages
sudo apt install -y \
    python3-opencv \
    python3-numpy \
    python3-scipy \
    python3-sklearn \
    python3-pandas \
    python3-pil \
    python3-flask

# Create virtual environment with system packages
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install pyttsx3  # Only install what's not available in system
```

### Approach 2: Docker Container (Advanced)
```bash
# Use pre-built ARM Docker image with all dependencies
docker pull python:3.11-slim-bookworm
# ... configure container with pre-installed packages
```

### Approach 3: Conda/Mamba (Alternative Package Manager)
```bash
# Install miniforge for ARM
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh

# Create environment
conda create -n face-attendance python=3.11
conda activate face-attendance
conda install opencv numpy scipy scikit-learn flask pandas pillow
```

## ⚡ Performance Optimization for Pi

### Reduce Memory Usage
```bash
# Limit OpenCV to essential modules only
pip uninstall opencv-python
pip install opencv-python-headless

# Use lighter alternatives
pip install "scikit-learn<1.2.0"  # Older version uses less memory
```

### GPU Memory Allocation
```bash
# Add to /boot/config.txt
echo "gpu_mem=64" | sudo tee -a /boot/config.txt
echo "gpu_mem_256=128" | sudo tee -a /boot/config.txt
echo "gpu_mem_512=256" | sudo tee -a /boot/config.txt
```

## 🆘 When All Else Fails

### Last Resort Options

1. **Use pre-built system packages only:**
   ```bash
   sudo apt install python3-opencv python3-flask python3-pandas python3-pil
   # Skip scikit-learn if not essential
   ```

2. **Simplify face recognition:**
   ```bash
   # Use basic OpenCV face detection instead of ML models
   # Modify code to use Haar cascades only
   ```

3. **Remote processing:**
   ```bash
   # Send images to a more powerful machine for processing
   # Pi only handles camera capture and display
   ```

## 📞 Getting Help

If you're still having issues:

1. **Check the logs:**
   ```bash
   journalctl -f  # Real-time system logs
   dmesg | tail   # Kernel messages
   ```

2. **System information:**
   ```bash
   uname -a       # Kernel info
   free -h        # Memory usage
   df -h          # Disk space
   vcgencmd measure_temp  # Temperature
   ```

3. **Create issue report:**
   - Include system info from above
   - Include full error messages
   - Include steps you've already tried

## 🔄 Starting Over

If you need to completely start over:

```bash
# Remove virtual environment
rm -rf venv

# Clean pip cache
pip cache purge

# Clean apt cache
sudo apt clean

# Restart installation
./install_rpi.sh
```

---

**Remember:** ARM architecture can be challenging for Python package compilation. The key is to use pre-compiled wheels whenever possible and fall back to system packages when needed.
