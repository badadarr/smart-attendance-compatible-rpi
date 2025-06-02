#!/bin/bash
# Make all scripts executable

echo "🔐 Making all scripts executable..."

# Main scripts
chmod +x start.sh

# Installation scripts
chmod +x scripts/installation/*.sh

# Troubleshooting scripts  
chmod +x scripts/troubleshooting/*.sh

# Maintenance scripts
chmod +x scripts/maintenance/*.sh

# Testing scripts
chmod +x scripts/testing/*.sh

# Python scripts
chmod +x *.py
chmod +x scripts/*/*.py
chmod +x tools/*.py

echo "✅ All scripts are now executable!"
echo ""
echo "🚀 You can now run:"
echo "   ./start.sh                    # Main menu"
echo "   scripts/installation/install_rpi.sh    # Install system"  
echo "   scripts/troubleshooting/troubleshoot.sh # Fix problems"
