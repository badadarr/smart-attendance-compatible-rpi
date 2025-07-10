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
echo "🚀 Starting Smart Attendance System..."
echo ""
echo "📋 Available options:"
echo "1. Register New Faces"
echo "2. Start Touchscreen Attendance (Touch Interface)"
echo "3. Start Web Dashboard"
echo "4. Exit"
echo ""

while true; do
    echo -n "Select option (1-4): "
    read -r choice

    case $choice in
        1)
            echo "👤 Starting face registration..."
            python src/add_faces_rpi.py
            ;;
        2)
            echo "📱 Starting touchscreen attendance system..."
            echo "📝 Instructions: Touch buttons to interact, no keyboard needed"
            python src/take_attendance_touchscreen.py
            break
            ;;
        3)
            echo "🌐 Starting web dashboard..."
            echo "📱 Access at: http://$(hostname -I | awk '{print $1}'):5000"
            echo "⚠️  Press Ctrl+C to stop"
            python src/app.py
            break
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
echo "✅ Session completed!"
