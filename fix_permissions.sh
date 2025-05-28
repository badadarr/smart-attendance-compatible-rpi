#!/bin/bash
# Fix permissions for all shell scripts

echo "🔐 Fixing file permissions..."

# Make shell scripts executable
chmod +x start.sh
chmod +x troubleshoot.sh
chmod +x backup_restore.sh
chmod +x fix_rpi_installation.sh
chmod +x emergency_fix.sh
chmod +x install_rpi.sh

# Make Python scripts executable
chmod +x *.py

echo "✅ All permissions fixed!"
echo ""
echo "📋 Now executable:"
echo "   ✓ start.sh"
echo "   ✓ troubleshoot.sh" 
echo "   ✓ backup_restore.sh"
echo "   ✓ All Python scripts"
