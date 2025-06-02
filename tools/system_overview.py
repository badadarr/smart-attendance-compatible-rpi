#!/usr/bin/env python3
"""
System Tools Overview
Ringkasan semua tools yang tersedia untuk sistem clock in/clock out
"""

import os
from pathlib import Path
from datetime import datetime


def display_header():
    """Display header information"""
    print("🚀 CLOCK IN/CLOCK OUT SYSTEM - TOOLS OVERVIEW")
    print("=" * 60)
    print(
        "Sistem absensi pintar dengan face recognition dan automatic work hours calculation"
    )
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def check_file_exists(filename):
    """Check if file exists and return status icon"""
    return "✅" if Path(filename).exists() else "❌"


def display_tools_overview():
    """Display overview of all available tools"""

    tools = [
        {
            "category": "🔧 SETUP & PREPARATION",
            "tools": [
                {
                    "file": "setup_manager.py",
                    "name": "Setup Manager (RECOMMENDED)",
                    "description": "All-in-one setup manager dengan menu interaktif untuk semua langkah setup",
                    "usage": "python3 setup_manager.py",
                    "features": [
                        "Menu interaktif untuk semua langkah",
                        "Complete setup (otomatis semua steps)",
                        "Individual step execution",
                        "Setup logging dan monitoring",
                    ],
                },
                {
                    "file": "setup_fresh_system.py",
                    "name": "Fresh System Setup",
                    "description": "Bersihkan data lama dan persiapkan sistem untuk pengumpulan data fresh",
                    "usage": "python3 setup_fresh_system.py",
                    "features": [
                        "Backup data existing otomatis",
                        "Clean old data (faces, attendance, models)",
                        "Setup directory structure",
                        "Generate setup guide",
                    ],
                },
                {
                    "file": "validate_system_readiness.py",
                    "name": "System Readiness Validator",
                    "description": "Validasi kesiapan sistem sebelum pengumpulan data",
                    "usage": "python3 validate_system_readiness.py",
                    "features": [
                        "Camera access validation",
                        "Dependencies checking",
                        "Directory structure verification",
                        "Face detection capability test",
                    ],
                },
            ],
        },
        {
            "category": "📸 DATA COLLECTION",
            "tools": [
                {
                    "file": "collect_face_data.py",
                    "name": "Enhanced Face Data Collection (RECOMMENDED)",
                    "description": "Pengumpulan data wajah dengan quality assessment dan panduan real-time",
                    "usage": 'python3 collect_face_data.py --people "Name1,Name2,Name3"',
                    "features": [
                        "Real-time quality assessment",
                        "Auto-capture dengan interval optimal",
                        "Blur dan brightness detection",
                        "Multiple people support",
                        "Progress tracking",
                    ],
                },
                {
                    "file": "take_pics.py",
                    "name": "Traditional Face Data Collection",
                    "description": "Pengumpulan data wajah cara tradisional (manual)",
                    "usage": "python3 take_pics.py",
                    "features": [
                        "Manual photo capture",
                        "Simple interface",
                        "One person at a time",
                    ],
                },
            ],
        },
        {
            "category": "🎓 MODEL TRAINING",
            "tools": [
                {
                    "file": "train_faces.py",
                    "name": "Face Recognition Model Training",
                    "description": "Training model face recognition dari data yang dikumpulkan",
                    "usage": "python3 train_faces.py",
                    "features": [
                        "LBPH face recognizer training",
                        "Automatic data loading",
                        "Model validation",
                        "Export ke trainer.yml",
                    ],
                }
            ],
        },
        {
            "category": "⏰ ATTENDANCE SYSTEM",
            "tools": [
                {
                    "file": "take_attendance_touchscreen.py",
                    "name": "Main Attendance System",
                    "description": "Sistem absensi utama dengan clock in/clock out otomatis",
                    "usage": "python3 take_attendance_touchscreen.py",
                    "features": [
                        "Automatic clock in/out detection",
                        "Real-time work hours calculation",
                        "Multiple sessions support",
                        "CSV attendance logging",
                        "Live camera interface",
                    ],
                }
            ],
        },
        {
            "category": "📊 REPORTING & ANALYSIS",
            "tools": [
                {
                    "file": "attendance_reports.py",
                    "name": "Attendance Reports Generator",
                    "description": "Generate laporan attendance harian dan mingguan",
                    "usage": "python3 attendance_reports.py",
                    "features": [
                        "Daily attendance reports",
                        "Weekly work hours summary",
                        "Employee work patterns analysis",
                        "Export ke different formats",
                    ],
                }
            ],
        },
        {
            "category": "🧪 TESTING & VALIDATION",
            "tools": [
                {
                    "file": "test_clock_system.py",
                    "name": "Comprehensive Test Suite",
                    "description": "Test lengkap semua fungsi clock in/clock out",
                    "usage": "python3 test_clock_system.py",
                    "features": [
                        "Status determination testing",
                        "Work hours calculation validation",
                        "CSV format verification",
                        "Edge cases handling",
                    ],
                },
                {
                    "file": "quick_system_test.py",
                    "name": "Quick System Test",
                    "description": "Test cepat seluruh sistem untuk validation",
                    "usage": "python3 quick_system_test.py",
                    "features": [
                        "Fast system validation",
                        "Live recognition test",
                        "Component status check",
                        "Test report generation",
                    ],
                },
            ],
        },
        {
            "category": "🛠️ UTILITIES & MAINTENANCE",
            "tools": [
                {
                    "file": "reset_data.py",
                    "name": "Data Reset Manager",
                    "description": "Reset dan backup data sistem dengan aman",
                    "usage": "python3 reset_data.py",
                    "features": [
                        "Safe data backup",
                        "Selective reset options",
                        "Recovery capabilities",
                        "Data migration tools",
                    ],
                },
                {
                    "file": "migrate_attendance_data.py",
                    "name": "Attendance Data Migration",
                    "description": "Migrasi data attendance lama ke format clock in/clock out",
                    "usage": "python3 migrate_attendance_data.py",
                    "features": [
                        "Convert 'Present' to Clock In/Out",
                        "Backup original data",
                        "Batch processing",
                        "Data validation",
                    ],
                },
            ],
        },
        {
            "category": "📚 DEMO & EXAMPLES",
            "tools": [
                {
                    "file": "demo_clock_system.py",
                    "name": "Clock System Demo",
                    "description": "Demo simulasi penggunaan sistem clock in/clock out",
                    "usage": "python3 demo_clock_system.py",
                    "features": [
                        "Simulated work scenarios",
                        "Sample data generation",
                        "Different work patterns",
                        "Report examples",
                    ],
                }
            ],
        },
    ]

    for category_info in tools:
        print(f"\n{category_info['category']}")
        print("-" * 50)

        for tool in category_info["tools"]:
            status = check_file_exists(tool["file"])
            print(f"\n{status} {tool['name']}")
            print(f"   📁 File: {tool['file']}")
            print(f"   📝 {tool['description']}")
            print(f"   💻 Usage: {tool['usage']}")

            if "features" in tool:
                print("   ✨ Features:")
                for feature in tool["features"]:
                    print(f"      • {feature}")


def display_quick_start():
    """Display quick start guide"""
    print(f"\n🚀 QUICK START GUIDE")
    print("=" * 60)

    print("\n1️⃣ FRESH SETUP (for new installation):")
    print("   python3 setup_manager.py")
    print("   → Choose option 7 (Complete Setup) for full automatic setup")

    print("\n2️⃣ QUICK VALIDATION (check system status):")
    print("   python3 quick_system_test.py")
    print("   → Fast test of all system components")

    print("\n3️⃣ DATA COLLECTION (register new people):")
    print('   python3 collect_face_data.py --people "John,Jane,Bob"')
    print("   → Enhanced collection with quality control")

    print("\n4️⃣ TRAINING MODEL:")
    print("   python3 train_faces.py")
    print("   → Train face recognition from collected data")

    print("\n5️⃣ START ATTENDANCE SYSTEM:")
    print("   python3 take_attendance_touchscreen.py")
    print("   → Main attendance system with clock in/out")

    print("\n6️⃣ GENERATE REPORTS:")
    print("   python3 attendance_reports.py")
    print("   → Daily/weekly attendance reports")


def display_troubleshooting():
    """Display common troubleshooting tips"""
    print(f"\n🚨 TROUBLESHOOTING")
    print("=" * 60)

    issues = [
        {
            "problem": "Camera tidak dapat diakses",
            "solution": [
                "sudo usermod -a -G video $USER",
                "Logout dan login kembali",
                "Pastikan tidak ada aplikasi lain yang menggunakan camera",
            ],
        },
        {
            "problem": "Face recognition tidak akurat",
            "solution": [
                "Kumpulkan lebih banyak foto training (50+ per orang)",
                "Pastikan pencahayaan yang baik saat training",
                "Hapus foto berkualitas buruk dari direktori faces/",
                "Train ulang model dengan: python3 train_faces.py",
            ],
        },
        {
            "problem": "Clock status salah deteksi",
            "solution": [
                "Periksa file attendance CSV terakhir",
                "Reset status dengan: python3 reset_data.py --attendance-only",
                "Pastikan tidak ada multiple recognition dalam waktu singkat",
            ],
        },
        {
            "problem": "Work hours calculation salah",
            "solution": [
                "Jalankan test: python3 test_clock_system.py",
                "Periksa format waktu di CSV file",
                "Validasi dengan: python3 attendance_reports.py",
            ],
        },
    ]

    for issue in issues:
        print(f"\n❌ {issue['problem']}:")
        for solution in issue["solution"]:
            print(f"   • {solution}")


def display_file_structure():
    """Display expected file structure"""
    print(f"\n📁 FILE STRUCTURE")
    print("=" * 60)

    structure = """
smart-attendance-compatible-rpi/
├── 📁 faces/                    # Training face data
│   ├── Person1/
│   │   ├── Person1_001.jpg
│   │   └── ...
│   └── Person2/
│       ├── Person2_001.jpg
│       └── ...
├── 📁 Attendance/               # Attendance CSV files
│   ├── Attendance_2025-01-15.csv
│   └── backup/
├── 📁 trainer/                  # Trained models
│   └── trainer.yml
├── 📁 backup_before_reset/      # Backup data
├── 🐍 Main Scripts:
│   ├── setup_manager.py         # Setup manager (RECOMMENDED)
│   ├── take_attendance_touchscreen.py  # Main attendance system
│   ├── collect_face_data.py     # Enhanced data collection
│   ├── train_faces.py           # Model training
│   ├── attendance_reports.py    # Reports generator
│   └── quick_system_test.py     # Quick validation
└── 📖 Documentation:
    ├── RASPBERRY_PI_SETUP_GUIDE.md
    ├── DATA_COLLECTION_GUIDE.md
    └── SETUP_GUIDE.md
"""

    print(structure)


def main():
    """Main function"""
    display_header()
    display_tools_overview()
    display_quick_start()
    display_troubleshooting()
    display_file_structure()

    print(f"\n📞 SUPPORT")
    print("=" * 60)
    print("• Read RASPBERRY_PI_SETUP_GUIDE.md for detailed setup instructions")
    print("• Run 'python3 validate_system_readiness.py' for system diagnosis")
    print("• Check setup logs for detailed error information")
    print("• Use 'python3 setup_manager.py' for guided setup process")

    print(f"\n🎉 READY TO START!")
    print("=" * 60)
    print("Mulai dengan: python3 setup_manager.py")
    print("Atau untuk quick test: python3 quick_system_test.py")


if __name__ == "__main__":
    main()
