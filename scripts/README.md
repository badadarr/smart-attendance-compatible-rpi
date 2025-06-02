# Scripts Directory

This directory contains all the automation and management scripts for the Face Recognition Attendance System.

## 📁 Directory Structure

### 🔧 Installation (`installation/`)
Scripts for initial system setup and installation:
- `install_rpi.sh` - Main automated installation script
- `install_missing.sh` - Install missing dependencies
- `requirements_rpi_minimal.txt` - Minimal requirements for ARM systems

**Usage:**
```bash
cd scripts/installation
chmod +x *.sh
./install_rpi.sh
```

### 🚨 Troubleshooting (`troubleshooting/`)
Scripts to fix common issues and problems:
- `troubleshoot.sh` - Interactive troubleshooting menu
- `emergency_fix.sh` - Quick fix for critical issues
- `complete_fix.sh` - Complete system repair
- `fix_rpi_installation.sh` - Fix ARM installation issues
- `fix_camera_issues.sh` - Fix camera-related problems
- `fix_config_camera.sh` - Fix camera configuration
- `fix_permissions.sh` - Fix file permissions

**Usage:**
```bash
cd scripts/troubleshooting
chmod +x *.sh
./troubleshoot.sh
```

### 🔧 Maintenance (`maintenance/`)
Scripts for system maintenance and monitoring:
- `validate_setup.py` - Comprehensive setup validation
- `performance_monitor.py` - Real-time system monitoring
- `system_check.py` - System diagnostic tool
- `backup_restore.sh` - Backup and restore utility

**Usage:**
```bash
cd scripts/maintenance
python validate_setup.py
python performance_monitor.py
./backup_restore.sh
```

### 🧪 Testing (`testing/`)
Scripts for testing system components:
- `test_camera.py` - Camera functionality test
- `test_system.py` - Complete system test
- `quick_test.sh` - Quick component test
- `face_detection_troubleshoot.py` - Face detection diagnostics
- `check_data.py` - Training data validation
- `camera_audit.py` - Camera audit tool

**Usage:**
```bash
cd scripts/testing
python test_system.py
python test_camera.py
./quick_test.sh
```

## 🚀 Quick Commands

| Task | Command |
|------|---------|
| Install System | `scripts/installation/install_rpi.sh` |
| Troubleshoot | `scripts/troubleshooting/troubleshoot.sh` |
| Validate Setup | `scripts/maintenance/validate_setup.py` |
| Test System | `scripts/testing/test_system.py` |
| Backup Data | `scripts/maintenance/backup_restore.sh` |

## 📋 Usage Notes

1. **Make scripts executable first:**
   ```bash
   find scripts/ -name "*.sh" -exec chmod +x {} \;
   ```

2. **Run from project root directory:**
   ```bash
   # From smart-attendance-compatible-rpi/
   scripts/installation/install_rpi.sh
   ```

3. **For Python scripts, ensure virtual environment is active:**
   ```bash
   source venv/bin/activate
   python scripts/maintenance/validate_setup.py
   ```
