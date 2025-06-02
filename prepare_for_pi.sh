#!/bin/bash
# Script untuk menyiapkan project untuk transfer ke Raspberry Pi

echo "📦 Preparing project for Raspberry Pi transfer..."

# Buat direktori temporary untuk packaging
mkdir -p package_for_pi

# Copy semua file yang diperlukan
echo "📄 Copying essential files..."

# Core applications
cp *.py package_for_pi/
cp *.sh package_for_pi/
cp *.md package_for_pi/
cp *.ini package_for_pi/
cp *.txt package_for_pi/
cp *.png package_for_pi/
cp *.service package_for_pi/

# Copy directories
cp -r scripts/ package_for_pi/
cp -r docs/ package_for_pi/
cp -r tools/ package_for_pi/
cp -r templates/ package_for_pi/
cp -r data/ package_for_pi/

# Create empty directories that might be needed
mkdir -p package_for_pi/Attendance
mkdir -p package_for_pi/static

# Make scripts executable in the package
find package_for_pi/ -name "*.sh" -exec chmod +x {} \;
find package_for_pi/ -name "*.py" -exec chmod +x {} \;

echo "✅ Project packaged in 'package_for_pi/' directory"
echo ""
echo "📋 Transfer instructions:"
echo "1. Compress the package:"
echo "   tar -czf face-attendance-system.tar.gz package_for_pi/"
echo ""
echo "2. Transfer to Raspberry Pi:"
echo "   scp face-attendance-system.tar.gz pi@your-pi-ip:~/"
echo ""
echo "3. On Raspberry Pi, extract and run:"
echo "   tar -xzf face-attendance-system.tar.gz"
echo "   cd package_for_pi/"
echo "   ./make_all_executable.sh"
echo "   scripts/installation/install_rpi.sh"
echo ""
echo "4. Start using:"
echo "   ./start.sh"
echo ""
