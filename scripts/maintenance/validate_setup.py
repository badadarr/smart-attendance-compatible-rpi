#!/usr/bin/env python3
"""
Setup Validation Script for Face Recognition Attendance System
Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit
"""

import os
import sys
import subprocess
import importlib
import platform
from pathlib import Path
import json


class SetupValidator:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "recommendations": [],
        }
        self.script_dir = Path(__file__).parent.absolute()

    def log_pass(self, test_name, message=""):
        """Log a passed test"""
        self.results["passed"].append(f"{test_name}: {message}")
        print(f"✅ {test_name}" + (f" - {message}" if message else ""))

    def log_fail(self, test_name, message=""):
        """Log a failed test"""
        self.results["failed"].append(f"{test_name}: {message}")
        print(f"❌ {test_name}" + (f" - {message}" if message else ""))

    def log_warning(self, test_name, message=""):
        """Log a warning"""
        self.results["warnings"].append(f"{test_name}: {message}")
        print(f"⚠️  {test_name}" + (f" - {message}" if message else ""))

    def log_recommendation(self, message):
        """Log a recommendation"""
        self.results["recommendations"].append(message)
        print(f"💡 {message}")

    def validate_system_requirements(self):
        """Validate system requirements"""
        print("\n🔍 System Requirements Validation")
        print("=" * 50)

        # Python version check
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.log_pass(
                "Python Version",
                f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            )
        else:
            self.log_fail(
                "Python Version",
                f"{python_version.major}.{python_version.minor}.{python_version.micro} (requires >= 3.8)",
            )

        # Platform check
        platform_info = platform.platform()
        if "Linux" in platform_info:
            self.log_pass("Operating System", platform_info)
        else:
            self.log_warning(
                "Operating System",
                f"{platform_info} (optimized for Linux/Raspberry Pi OS)",
            )

        # Raspberry Pi detection
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
                if "Raspberry Pi" in content:
                    # Extract model info
                    for line in content.split("\n"):
                        if "Model" in line:
                            model = line.split(":")[-1].strip()
                            self.log_pass("Raspberry Pi Detection", model)
                            break
                else:
                    self.log_warning(
                        "Raspberry Pi Detection", "Not running on Raspberry Pi"
                    )
        except FileNotFoundError:
            self.log_warning("Raspberry Pi Detection", "Cannot detect hardware")

        # Architecture check
        arch = platform.machine()
        if arch in ["aarch64", "armv7l"]:
            self.log_pass("Architecture", arch)
        else:
            self.log_warning("Architecture", f"{arch} (optimized for ARM)")

    def validate_python_dependencies(self):
        """Validate Python dependencies"""
        print("\n📦 Python Dependencies Validation")
        print("=" * 50)

        required_packages = {
            "cv2": "opencv-python",
            "numpy": "numpy",
            "pandas": "pandas",
            "flask": "Flask",
            "sklearn": "scikit-learn",
            "pyttsx3": "pyttsx3",
            "PIL": "Pillow",
        }

        for import_name, package_name in required_packages.items():
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, "__version__", "unknown")
                self.log_pass(f"{package_name}", f"version {version}")
            except ImportError:
                self.log_fail(f"{package_name}", "not installed")

    def validate_system_packages(self):
        """Validate system packages"""
        print("\n🔧 System Packages Validation")
        print("=" * 50)

        required_packages = [
            "libopencv-dev",
            "python3-dev",
            "cmake",
            "libatlas-base-dev",
            "libjpeg-dev",
            "libpng-dev",
            "libv4l-dev",
        ]

        for package in required_packages:
            try:
                result = subprocess.run(
                    ["dpkg", "-l", package], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and "ii" in result.stdout:
                    self.log_pass(f"System Package: {package}")
                else:
                    self.log_fail(f"System Package: {package}", "not installed")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log_warning(f"System Package: {package}", "cannot verify")    def validate_file_structure(self):
        """Validate project file structure"""
        print("\n📁 File Structure Validation")
        print("=" * 50)

        # Get project root (2 levels up from scripts/maintenance/)
        project_root = self.script_dir.parent.parent

        required_files = [
            "app.py",
            "add_faces_rpi.py",
            "take_attendance_rpi.py", 
            "requirements.txt",
            "config.ini",
            "README.md",
            "start.sh",
            ("scripts/installation/install_rpi.sh", "install_rpi.sh"),
            ("scripts/maintenance/system_check.py", "system_check.py"),
        ]

        required_dirs = ["data", "templates", "scripts", "static"]

        for file_item in required_files:
            if isinstance(file_item, tuple):
                file_path, display_name = file_item
                full_path = project_root / file_path
            else:
                file_path = file_item
                display_name = file_item
                full_path = project_root / file_path
                
            if full_path.exists():
                self.log_pass(f"File: {display_name}")
            else:
                self.log_fail(f"File: {display_name}", "missing")

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.log_pass(f"Directory: {dir_name}")
            else:
                self.log_fail(f"Directory: {dir_name}", "missing")        # Check data directory contents
        data_dir = project_root / "data"
        if data_dir.exists():
            required_data_files = ["haarcascade_frontalface_default.xml"]

            for file_name in required_data_files:
                file_path = data_dir / file_name
                if file_path.exists():
                    self.log_pass(f"Data File: {file_name}")
                else:
                    self.log_fail(f"Data File: {file_name}", "missing")

    def validate_camera(self):
        """Validate camera setup"""
        print("\n📹 Camera Validation")
        print("=" * 50)

        # Check for camera interfaces
        camera_found = False

        # Check Pi Camera
        try:
            result = subprocess.run(
                ["vcgencmd", "get_camera"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                if "detected=1" in result.stdout:
                    self.log_pass("Pi Camera", "detected")
                    camera_found = True
                else:
                    self.log_warning("Pi Camera", "not detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_warning("Pi Camera", "vcgencmd not available")

        # Check USB cameras
        video_devices = list(Path("/dev").glob("video*"))
        if video_devices:
            self.log_pass("USB Camera", f"found {len(video_devices)} video device(s)")
            camera_found = True
        else:
            self.log_warning("USB Camera", "no video devices found")

        if not camera_found:
            self.log_fail("Camera Setup", "no cameras detected")
            self.log_recommendation("Ensure camera is connected and enabled")    def validate_permissions(self):
        """Validate file permissions"""
        print("\n🔐 Permissions Validation")
        print("=" * 50)

        # Get project root (2 levels up from scripts/maintenance/)
        project_root = self.script_dir.parent.parent

        # Check script permissions
        script_files = [
            ("scripts/installation/install_rpi.sh", "install_rpi.sh"),
            ("start.sh", "start.sh"),
            ("scripts/troubleshooting/troubleshoot.sh", "troubleshoot.sh"),
            ("scripts/maintenance/backup_restore.sh", "backup_restore.sh"),
        ]

        for script_item in script_files:
            if isinstance(script_item, tuple):
                script_path, display_name = script_item
                full_path = project_root / script_path
            else:
                script_path = script_item
                display_name = script_item
                full_path = project_root / script_path
                
            if full_path.exists():
                if os.access(full_path, os.X_OK):
                    self.log_pass(f"Execute Permission: {display_name}")
                else:
                    self.log_fail(f"Execute Permission: {display_name}", "not executable")
            else:
                self.log_warning(f"Script: {display_name}", "not found")

        # Check data directory permissions
        data_dir = project_root / "data"
        if data_dir.exists():
            if os.access(data_dir, os.W_OK):
                self.log_pass("Data Directory", "writable")
            else:
                self.log_fail("Data Directory", "not writable")

        # Check for video group membership (for camera access)
        try:
            import grp

            video_group = grp.getgrnam("video")
            current_user = os.getenv("USER", "unknown")

            if current_user in video_group.gr_mem:
                self.log_pass("Video Group", f"user {current_user} is member")
            else:
                self.log_warning(
                    "Video Group", f"user {current_user} not in video group"
                )
                self.log_recommendation(
                    "Add user to video group: sudo usermod -a -G video $USER"
                )
        except KeyError:
            self.log_warning("Video Group", "cannot check membership")    def validate_configuration(self):
        """Validate configuration files"""
        print("\n⚙️  Configuration Validation")
        print("=" * 50)

        # Get project root (2 levels up from scripts/maintenance/)
        project_root = self.script_dir.parent.parent

        # Check config.ini
        config_file = project_root / "config.ini"
        if config_file.exists():
            try:
                import configparser

                config = configparser.ConfigParser()
                config.read(config_file)

                required_sections = ["CAMERA", "RECOGNITION", "SYSTEM", "WEB"]
                for section in required_sections:
                    if config.has_section(section):
                        self.log_pass(f"Config Section: {section}")
                    else:
                        self.log_fail(f"Config Section: {section}", "missing")

            except Exception as e:
                self.log_fail("Config File", f"invalid format: {e}")
        else:
            self.log_fail("Config File", "config.ini not found")

        # Check requirements.txt
        req_file = project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r") as f:
                    requirements = f.read().strip()
                    if requirements:
                        req_count = len(requirements.split("\n"))
                        self.log_pass(
                            "Requirements File", f"{req_count} dependencies listed"
                        )
                    else:
                        self.log_fail("Requirements File", "empty")
            except Exception as e:
                self.log_fail("Requirements File", f"cannot read: {e}")
        else:
            self.log_fail("Requirements File", "not found")

    def validate_network(self):
        """Validate network connectivity"""
        print("\n🌐 Network Validation")
        print("=" * 50)

        # Check if Flask can bind to ports
        import socket

        ports_to_check = [5000, 8080]
        for port in ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                sock.close()

                if result == 0:
                    self.log_warning(f"Port {port}", "already in use")
                else:
                    self.log_pass(f"Port {port}", "available")
            except Exception as e:
                self.log_warning(f"Port {port}", f"cannot check: {e}")

    def validate_performance(self):
        """Validate system performance"""
        print("\n⚡ Performance Validation")
        print("=" * 50)

        try:
            import psutil

            # Memory check
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)

            if memory_gb >= 4:
                self.log_pass("Memory", f"{memory_gb:.1f} GB")
            elif memory_gb >= 2:
                self.log_warning("Memory", f"{memory_gb:.1f} GB (recommended: 4GB+)")
            else:
                self.log_fail("Memory", f"{memory_gb:.1f} GB (minimum: 2GB)")

            # CPU cores check
            cpu_count = psutil.cpu_count()
            if cpu_count >= 4:
                self.log_pass("CPU Cores", f"{cpu_count} cores")
            else:
                self.log_warning("CPU Cores", f"{cpu_count} cores (recommended: 4+)")

            # Disk space check
            disk = psutil.disk_usage("/")
            disk_free_gb = disk.free / (1024**3)

            if disk_free_gb >= 8:
                self.log_pass("Disk Space", f"{disk_free_gb:.1f} GB free")
            elif disk_free_gb >= 4:
                self.log_warning(
                    "Disk Space", f"{disk_free_gb:.1f} GB free (recommended: 8GB+)"
                )
            else:
                self.log_fail(
                    "Disk Space", f"{disk_free_gb:.1f} GB free (minimum: 4GB)"
                )

        except ImportError:
            self.log_warning("Performance Check", "psutil not available")

    def generate_report(self):
        """Generate validation report"""
        print("\n📊 Validation Report")
        print("=" * 50)

        total_tests = len(self.results["passed"]) + len(self.results["failed"])
        pass_rate = (
            len(self.results["passed"]) / total_tests * 100 if total_tests > 0 else 0
        )

        print(f"Tests passed: {len(self.results['passed'])}")
        print(f"Tests failed: {len(self.results['failed'])}")
        print(f"Warnings: {len(self.results['warnings'])}")
        print(f"Pass rate: {pass_rate:.1f}%")

        if self.results["failed"]:
            print("\n❌ Failed Tests:")
            for failure in self.results["failed"]:
                print(f"   • {failure}")

        if self.results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in self.results["warnings"]:
                print(f"   • {warning}")

        if self.results["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in self.results["recommendations"]:
                print(f"   • {rec}")

        # Overall status
        if len(self.results["failed"]) == 0:
            if len(self.results["warnings"]) == 0:
                print("\n🎉 System is ready for production!")
            else:
                print("\n✅ System is ready with minor issues noted above")
        else:
            print("\n⚠️  System needs attention before use")

        # Save report to file
        report_file = self.script_dir / "validation_report.json"
        try:
            with open(report_file, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📁 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"\n❌ Could not save report: {e}")

    def run_all_validations(self):
        """Run all validation tests"""
        print("🔍 Face Recognition Attendance System - Setup Validation")
        print("=" * 60)

        self.validate_system_requirements()
        self.validate_python_dependencies()
        self.validate_system_packages()
        self.validate_file_structure()
        self.validate_camera()
        self.validate_permissions()
        self.validate_configuration()
        self.validate_network()
        self.validate_performance()
        self.generate_report()


def main():
    """Main function"""
    validator = SetupValidator()

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick validation - only essential checks
        print("🚀 Quick Validation Mode")
        validator.validate_system_requirements()
        validator.validate_python_dependencies()
        validator.validate_file_structure()
        validator.validate_camera()
        validator.generate_report()
    else:
        # Full validation
        validator.run_all_validations()


if __name__ == "__main__":
    main()
