#!/bin/bash
# Quick Start Script for Face Recognition Attendance System
# Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit

echo "🍓 Face Recognition Attendance System - Quick Start"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Please run './install_rpi.sh' first"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if this is first run (no training data)
if [ ! -f "data/faces_data.pkl" ] || [ ! -f "data/names.pkl" ]; then
    echo ""
    echo "👤 No training data found!"
    echo "📝 You need to register faces first."
    echo ""
    echo "Would you like to register faces now? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🎥 Starting face registration..."
        python add_faces_rpi.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Face registration completed!"
        else
            echo "❌ Face registration failed!"
            exit 1
        fi
    else
        echo "⚠️  Cannot start attendance system without registered faces"
        echo "💡 Run 'python add_faces_rpi.py' to register faces"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting Face Recognition Attendance System..."
echo ""
echo "📋 Available options:"
echo "1. Start Attendance Recognition (Recommended)"
echo "2. Start Web Dashboard Only"
echo "3. Register New Faces"
echo "4. System Check"
echo "5. Performance Monitor"
echo "6. Backup & Restore"
echo "7. Validate Setup"
echo "8. Troubleshoot"
echo "9. Exit"
echo ""

while true; do
    echo -n "Please select an option (1-9): " choice
    read -r choice
    
    case $choice in
        1)
            echo "🎯 Starting attendance recognition..."
            echo "📝 Instructions:"
            echo "   - Press SPACE to record attendance"
            echo "   - Press 'q' to quit"
            echo "   - Ensure good lighting"
            echo ""
            python take_attendance_rpi.py
            break
            ;;
        2)
            echo "🌐 Starting web dashboard..."
            echo "📱 Access at: http://$(hostname -I | awk '{print $1}'):5000"
            echo "⚠️  Press Ctrl+C to stop"
            echo ""
            python app.py
            break
            ;;
        3)
            echo "👤 Starting face registration..."
            python add_faces_rpi.py
            ;;
        4)
            echo "🔍 Running system check..."
            python scripts/maintenance/system_check.py
            echo ""
            ;;
        5)
            echo "⚡ Starting performance monitor..."
            python scripts/maintenance/performance_monitor.py
            echo ""
            ;;
        6)
            echo "💾 Opening backup & restore menu..."
            scripts/maintenance/backup_restore.sh
            echo ""
            ;;
        7)
            echo "✅ Running setup validation..."
            python scripts/maintenance/validate_setup.py
            echo ""
            ;;
        8)
            echo "🔧 Running troubleshoot script..."
            scripts/troubleshooting/troubleshoot.sh
            echo ""
            ;;
        9)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-9."
            ;;
    esac
done

# Deactivate virtual environment
deactivate
echo ""
echo "✅ Session completed!"
