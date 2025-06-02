#!/bin/bash
# Script untuk membuat semua file shell executable
# Gunakan ini setelah mengorganisir ulang project

echo "🔐 Making all shell scripts executable..."

# Core scripts
chmod +x start.sh
echo "✅ start.sh"

# Installation scripts
chmod +x scripts/installation/*.sh
echo "✅ scripts/installation/*.sh"

# Troubleshooting scripts  
chmod +x scripts/troubleshooting/*.sh
echo "✅ scripts/troubleshooting/*.sh"

# Maintenance scripts
chmod +x scripts/maintenance/*.sh
echo "✅ scripts/maintenance/*.sh"

# Testing scripts
chmod +x scripts/testing/*.sh
echo "✅ scripts/testing/*.sh"

# Python scripts
chmod +x *.py
chmod +x scripts/*/*.py
chmod +x tools/*.py
echo "✅ All Python scripts"

echo ""
echo "🎉 All files are now executable!"
echo ""
echo "📋 Quick commands:"
echo "   ./start.sh                                    # Menu utama"
echo "   scripts/installation/install_rpi.sh          # Install"
echo "   scripts/troubleshooting/troubleshoot.sh      # Troubleshoot"
echo "   scripts/maintenance/validate_setup.py        # Validasi"
echo ""
