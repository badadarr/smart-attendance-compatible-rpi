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
        python src/add_faces_rpi.py

        if [ $? -eq 0 ]; then
            echo "✅ Face registration completed!"
        else
            echo "❌ Face registration failed!"
            exit 1
        fi
    else
        echo "⚠️  Cannot start attendance system without registered faces"
        echo "💡 Run 'python src/add_faces_rpi.py' to register faces"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting Face Recognition Attendance System..."
echo ""
echo "📋 Available options:"
echo "1. Start Attendance Recognition (Keyboard/Mouse)"
echo "2. Start Touchscreen Attendance (No Keyboard Needed)"
echo "3. Start Web Dashboard Only"
echo "4. Start Touchscreen Web Interface"
echo "5. Register New Faces"
echo "6. System Check"
echo "7. Performance Monitor"
echo "8. Backup & Restore"
echo "9. Validate Setup"
echo "10. Troubleshoot"
echo "11. Exit"
echo ""

while true; do
    echo -n "Please select an option (1-11): " choice
    read -r choice

    case $choice in
        1)
            echo "🎯 Starting attendance recognition (keyboard/mouse)..."
            echo "📝 Instructions:"
            echo "   - Press SPACE to record attendance"
            echo "   - Press 'q' to quit"
            echo "   - Ensure good lighting"
            echo ""
            python src/take_attendance_rpi.py
            break
            ;;
        2)
            echo "📱 Starting touchscreen attendance system..."
            echo "📝 Instructions:"
            echo "   - Touch buttons to interact"
            echo "   - No keyboard needed"
            echo "   - Fullscreen touchscreen interface"
            echo ""
            python src/take_attendance_touchscreen.py
            break
            ;;
        3)
            echo "🌐 Starting web dashboard..."
            echo "📱 Access at: http://$(hostname -I | awk '{print $1}'):5000"
            echo "⚠️  Press Ctrl+C to stop"
            echo ""
            python src/app.py
            break
            ;;
        4)
            echo "📱 Starting touchscreen web interface..."
            echo "🌐 Access at: http://$(hostname -I | awk '{print $1}'):5001"
            echo "📝 Perfect for touchscreen displays"
            echo "⚠️  Press Ctrl+C to stop"
            echo ""
            python src/app_touchscreen.py
            break
            ;;
        5)
            echo "👤 Starting face registration..."
            python src/add_faces_rpi.py
            ;;
        6)
            echo "🔍 Running system check..."
            python scripts/maintenance/system_check.py
            echo ""
            ;;
        7)
            echo "⚡ Starting performance monitor..."
            python scripts/maintenance/performance_monitor.py
            echo ""
            ;;
        8)
            echo "💾 Opening backup & restore menu..."
            bash scripts/maintenance/backup_restore.sh
            echo ""
            ;;
        9)
            echo "✅ Running setup validation..."
            python scripts/maintenance/validate_setup.py
            echo ""
            ;;
        10)
            echo "🔧 Running troubleshoot script..."
            bash scripts/troubleshooting/troubleshoot.sh
            echo ""
            ;;
        11)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-11."
            ;;
    esac
done

# Deactivate virtual environment
deactivate
echo ""
echo "✅ Session completed!"
