#!/bin/bash
# filepath: d:\Documents\Projek Ceces\smart-attendance-compatible-rpi\touchscreen_start.sh
# Quick Touchscreen Attendance Launcher
# No keyboard required - perfect for HDMI touchscreen displays

echo "🖥️ Touchscreen Attendance System Launcher"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Please run './install_rpi.sh' first"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if training data exists
if [ ! -f "data/faces_data.pkl" ] || [ ! -f "data/names.pkl" ]; then
    echo ""
    echo "👤 No training data found!"
    echo "📝 You need to register faces first."
    echo ""
    echo "Starting face registration..."
    python add_faces_rpi.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Face registration failed!"
        exit 1
    fi
fi

echo ""
echo "🖥️ Touchscreen Interface Options:"
echo "================================="
echo "1. Desktop Touchscreen App (Fullscreen, Touch Buttons)"
echo "2. Web Touchscreen Interface (Browser-based)"
echo "3. Register New Faces"
echo "4. Exit"
echo ""

while true; do
    echo -n "Select touchscreen interface (1-4): "
    read -r choice
    
    case $choice in
        1)
            echo ""
            echo "🎯 Starting Desktop Touchscreen Attendance..."
            echo "📱 Features:"
            echo "   - Fullscreen touch interface"
            echo "   - Large touch buttons (RECORD, AUTO, EXIT)"
            echo "   - Auto-record mode available"
            echo "   - Visual feedback"
            echo ""
            python take_attendance_touchscreen.py
            break
            ;;
        2)
            echo ""
            echo "🌐 Starting Web Touchscreen Interface..."
            echo "📱 Access via browser at: http://$(hostname -I | awk '{print $1}'):5001"
            echo "🎯 Features:"
            echo "   - Browser-based interface"
            echo "   - Multi-device access"
            echo "   - Real-time video streaming"
            echo "   - Touch-friendly controls"
            echo ""
            echo "⚠️  Press Ctrl+C to stop the web server"
            echo ""
            python app_touchscreen.py
            break
            ;;
        3)
            echo ""
            echo "👤 Starting face registration..."
            echo "📝 Register new faces for the system"
            python add_faces_rpi.py
            echo ""
            ;;
        4)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-4."
            ;;
    esac
done

# Deactivate virtual environment
deactivate
echo ""
echo "✅ Touchscreen session completed!"
