#!/usr/bin/env python3
"""
Complete System Setup Manager
Script all-in-one untuk setup lengkap sistem clock in/clock out di Raspberry Pi
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


class SystemSetupManager:
    def __init__(self):
        """Initialize system setup manager"""
        self.base_dir = Path(".")
        self.setup_log = []

    def log_step(self, message, success=True):
        """Log a setup step"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅" if success else "❌"
        log_entry = f"[{timestamp}] {status} {message}"
        self.setup_log.append(log_entry)
        print(log_entry)

    def run_script(self, script_name, description, args=None):
        """Run a Python script and handle errors"""
        try:
            cmd = [sys.executable, script_name]
            if args:
                cmd.extend(args)

            self.log_step(f"Running {description}...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.log_step(f"{description} completed successfully")
                return True, result.stdout
            else:
                self.log_step(f"{description} failed: {result.stderr}", False)
                return False, result.stderr

        except Exception as e:
            self.log_step(f"{description} error: {str(e)}", False)
            return False, str(e)

    def display_menu(self):
        """Display main setup menu"""
        print("\n🚀 CLOCK IN/CLOCK OUT SYSTEM SETUP")
        print("=" * 50)
        print("1. 🔧 Fresh System Setup (Clean & Prepare)")
        print("2. 🔍 Validate System Readiness")
        print("3. 📸 Collect Face Data")
        print("4. 🎓 Train Face Recognition Model")
        print("5. 🧪 Test Complete System")
        print("6. 📊 Generate Sample Reports")
        print("7. 🎯 Complete Setup (All Steps)")
        print("8. 📋 View Setup Log")
        print("9. ❌ Exit")
        print("=" * 50)

    def fresh_system_setup(self):
        """Run fresh system setup"""
        print("\n🔧 FRESH SYSTEM SETUP")
        print("This will clean all existing data and prepare for fresh collection")

        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm.upper() != "YES":
            self.log_step("Fresh setup cancelled by user")
            return False

        success, output = self.run_script("setup_fresh_system.py", "Fresh System Setup")
        if success:
            self.log_step("System cleaned and prepared for fresh data")

        return success

    def validate_system(self):
        """Validate system readiness"""
        print("\n🔍 VALIDATING SYSTEM READINESS")

        success, output = self.run_script(
            "validate_system_readiness.py", "System Validation"
        )
        if success:
            self.log_step("System validation completed")
            print("\n📖 Check DATA_COLLECTION_GUIDE.md for detailed instructions")

        return success

    def collect_face_data(self):
        """Run face data collection"""
        print("\n📸 FACE DATA COLLECTION")
        print("Choose collection method:")
        print("1. Enhanced collection assistant (recommended)")
        print("2. Traditional take_pics.py")

        choice = input("Enter choice (1-2): ").strip()

        if choice == "1":
            people_input = input(
                "Enter names separated by commas (or press Enter for interactive): "
            ).strip()

            if people_input:
                people_list = [name.strip() for name in people_input.split(",")]
                args = ["--people"] + people_list
                success, output = self.run_script(
                    "collect_face_data.py", "Enhanced Data Collection", args
                )
            else:
                success, output = self.run_script(
                    "collect_face_data.py", "Enhanced Data Collection"
                )

        elif choice == "2":
            success, output = self.run_script(
                "take_pics.py", "Traditional Data Collection"
            )

        else:
            self.log_step("Invalid choice for data collection", False)
            return False

        if success:
            self.log_step("Face data collection completed")

        return success

    def train_model(self):
        """Train face recognition model"""
        print("\n🎓 TRAINING FACE RECOGNITION MODEL")

        # Check if faces directory has data
        faces_dir = self.base_dir / "faces"
        if not faces_dir.exists() or not any(faces_dir.iterdir()):
            self.log_step("No face data found. Run data collection first.", False)
            return False

        success, output = self.run_script("train_faces.py", "Model Training")
        if success:
            self.log_step("Face recognition model trained successfully")

            # Check if trainer file was created
            trainer_file = self.base_dir / "trainer" / "trainer.yml"
            if trainer_file.exists():
                self.log_step("Trainer file created successfully")
            else:
                self.log_step("Warning: Trainer file not found", False)

        return success

    def test_system(self):
        """Test the complete system"""
        print("\n🧪 TESTING COMPLETE SYSTEM")
        print("Choose test method:")
        print("1. Run automated test suite")
        print("2. Start interactive attendance system")

        choice = input("Enter choice (1-2): ").strip()

        if choice == "1":
            success, output = self.run_script(
                "test_clock_system.py", "Automated Test Suite"
            )
            if success:
                self.log_step("All automated tests passed")

        elif choice == "2":
            print("\n🎯 Starting interactive attendance system...")
            print("This will open the camera for live testing")
            print("Press Ctrl+C to stop")

            try:
                success, output = self.run_script(
                    "take_attendance_touchscreen.py", "Interactive Attendance System"
                )
            except KeyboardInterrupt:
                self.log_step("Interactive system stopped by user")
                success = True

        else:
            self.log_step("Invalid choice for system test", False)
            return False

        return success

    def generate_reports(self):
        """Generate sample reports"""
        print("\n📊 GENERATING SAMPLE REPORTS")

        success, output = self.run_script("attendance_reports.py", "Report Generation")
        if success:
            self.log_step("Sample reports generated")

        return success

    def complete_setup(self):
        """Run complete setup from start to finish"""
        print("\n🎯 COMPLETE SETUP - ALL STEPS")
        print("This will run the entire setup process:")
        print("1. Fresh system setup")
        print("2. System validation")
        print("3. Face data collection")
        print("4. Model training")
        print("5. System testing")

        confirm = input("\nContinue with complete setup? (y/n): ").strip().lower()
        if confirm != "y":
            self.log_step("Complete setup cancelled by user")
            return False

        steps = [
            ("Fresh System Setup", self.fresh_system_setup),
            ("System Validation", self.validate_system),
            ("Face Data Collection", self.collect_face_data),
            ("Model Training", self.train_model),
            ("System Testing", self.test_system),
        ]

        for step_name, step_function in steps:
            print(f"\n{'='*50}")
            print(f"STEP: {step_name}")
            print(f"{'='*50}")

            success = step_function()
            if not success:
                self.log_step(f"Complete setup failed at: {step_name}", False)
                print(f"\n❌ Setup failed at {step_name}")
                return False

            # Brief pause between steps
            if step_function != steps[-1][1]:  # Not the last step
                input(f"\n✅ {step_name} completed. Press Enter to continue...")

        self.log_step("Complete setup finished successfully")
        print("\n🎉 COMPLETE SETUP FINISHED!")
        print("Your clock in/clock out system is ready to use!")

        return True

    def view_setup_log(self):
        """Display setup log"""
        print("\n📋 SETUP LOG")
        print("=" * 50)

        if not self.setup_log:
            print("No setup steps recorded yet")
        else:
            for entry in self.setup_log:
                print(entry)

        print("=" * 50)

    def save_setup_log(self):
        """Save setup log to file"""
        if self.setup_log:
            log_file = (
                self.base_dir
                / f"setup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            with open(log_file, "w", encoding="utf-8") as f:
                f.write("CLOCK IN/CLOCK OUT SYSTEM SETUP LOG\n")
                f.write("=" * 50 + "\n")
                f.write(
                    f"Setup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for entry in self.setup_log:
                    f.write(entry + "\n")

            print(f"📄 Setup log saved to: {log_file.name}")

    def run(self):
        """Run the setup manager"""
        print("🎯 Welcome to Clock In/Clock Out System Setup Manager")

        while True:
            self.display_menu()

            try:
                choice = input("\nEnter your choice (1-9): ").strip()

                if choice == "1":
                    self.fresh_system_setup()
                elif choice == "2":
                    self.validate_system()
                elif choice == "3":
                    self.collect_face_data()
                elif choice == "4":
                    self.train_model()
                elif choice == "5":
                    self.test_system()
                elif choice == "6":
                    self.generate_reports()
                elif choice == "7":
                    self.complete_setup()
                elif choice == "8":
                    self.view_setup_log()
                elif choice == "9":
                    print("\n👋 Exiting setup manager...")
                    self.save_setup_log()
                    break
                else:
                    print("❌ Invalid choice. Please select 1-9.")

                # Pause before showing menu again
                if choice in ["1", "2", "3", "4", "5", "6", "7"]:
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\n👋 Setup interrupted by user")
                self.save_setup_log()
                break
            except Exception as e:
                self.log_step(f"Unexpected error: {str(e)}", False)
                print(f"❌ Error: {str(e)}")


def main():
    """Main function"""
    setup_manager = SystemSetupManager()
    setup_manager.run()


if __name__ == "__main__":
    main()
