#!/usr/bin/env python3
"""
Performance Monitor for Face Recognition Attendance System
Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit
"""

import time
import psutil
import os
import sys
from datetime import datetime, timedelta
import json


class PerformanceMonitor:
    def __init__(self):
        self.log_file = "performance_log.json"
        self.monitoring = False

    def get_system_stats(self):
        """Get current system statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "used_mb": psutil.virtual_memory().used / 1024 / 1024,
            },
            "temperature": self.get_cpu_temperature(),
            "disk_usage": psutil.disk_usage("/").percent,
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }
        return stats

    def get_cpu_temperature(self):
        """Get CPU temperature (Raspberry Pi specific)"""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000.0
                return round(temp, 1)
        except:
            return None

    def log_stats(self, stats):
        """Log statistics to file"""
        try:
            # Read existing data
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    data = json.load(f)
            else:
                data = []

            # Add new stats
            data.append(stats)

            # Keep only last 1000 entries
            if len(data) > 1000:
                data = data[-1000:]

            # Write back to file
            with open(self.log_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error logging stats: {e}")

    def display_current_stats(self):
        """Display current system statistics"""
        stats = self.get_system_stats()

        print("🔍 Current System Performance")
        print("=" * 40)
        print(f"Time: {stats['timestamp']}")
        print(f"CPU Usage: {stats['cpu_percent']:.1f}%")
        print(f"Memory Usage: {stats['memory']['percent']:.1f}%")
        print(f"Memory Available: {stats['memory']['available_mb']:.1f} MB")
        print(f"Memory Used: {stats['memory']['used_mb']:.1f} MB")

        if stats["temperature"]:
            temp_status = "🔥" if stats["temperature"] > 70 else "🌡️"
            print(f"CPU Temperature: {temp_status} {stats['temperature']}°C")

        print(f"Disk Usage: {stats['disk_usage']:.1f}%")

        if stats["load_average"]:
            print(
                f"Load Average: {stats['load_average'][0]:.2f}, {stats['load_average'][1]:.2f}, {stats['load_average'][2]:.2f}"
            )

        # Performance warnings
        warnings = []
        if stats["cpu_percent"] > 80:
            warnings.append("High CPU usage detected")
        if stats["memory"]["percent"] > 85:
            warnings.append("High memory usage detected")
        if stats["temperature"] and stats["temperature"] > 75:
            warnings.append("High CPU temperature detected")
        if stats["disk_usage"] > 90:
            warnings.append("High disk usage detected")

        if warnings:
            print("\n⚠️  Performance Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
        else:
            print("\n✅ System performance is good")

        print()

    def monitor_continuous(self, interval=5, duration=300):
        """Monitor system continuously"""
        print(
            f"🔄 Starting continuous monitoring (interval: {interval}s, duration: {duration}s)"
        )
        print("Press Ctrl+C to stop")

        start_time = time.time()
        self.monitoring = True

        try:
            while self.monitoring and (time.time() - start_time) < duration:
                stats = self.get_system_stats()
                self.log_stats(stats)

                # Display abbreviated stats
                print(
                    f"{stats['timestamp'][:19]} | "
                    f"CPU: {stats['cpu_percent']:5.1f}% | "
                    f"MEM: {stats['memory']['percent']:5.1f}% | "
                    f"TEMP: {stats['temperature'] or 'N/A':>4}°C"
                )

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")

        self.monitoring = False
        print("📊 Monitoring complete")

    def analyze_logs(self):
        """Analyze performance logs"""
        if not os.path.exists(self.log_file):
            print("❌ No performance log file found")
            return

        try:
            with open(self.log_file, "r") as f:
                data = json.load(f)

            if not data:
                print("❌ No data in performance log")
                return

            print("📊 Performance Analysis")
            print("=" * 40)

            # Calculate averages
            cpu_avg = sum(entry["cpu_percent"] for entry in data) / len(data)
            memory_avg = sum(entry["memory"]["percent"] for entry in data) / len(data)

            temperatures = [
                entry["temperature"] for entry in data if entry["temperature"]
            ]
            temp_avg = sum(temperatures) / len(temperatures) if temperatures else 0

            print(f"Total entries: {len(data)}")
            print(f"Time range: {data[0]['timestamp']} to {data[-1]['timestamp']}")
            print(f"Average CPU usage: {cpu_avg:.1f}%")
            print(f"Average memory usage: {memory_avg:.1f}%")

            if temp_avg:
                print(f"Average temperature: {temp_avg:.1f}°C")

            # Find peaks
            max_cpu = max(data, key=lambda x: x["cpu_percent"])
            max_memory = max(data, key=lambda x: x["memory"]["percent"])

            print(
                f"\nPeak CPU usage: {max_cpu['cpu_percent']:.1f}% at {max_cpu['timestamp']}"
            )
            print(
                f"Peak memory usage: {max_memory['memory']['percent']:.1f}% at {max_memory['timestamp']}"
            )

            if temperatures:
                max_temp_entry = max(data, key=lambda x: x["temperature"] or 0)
                print(
                    f"Peak temperature: {max_temp_entry['temperature']:.1f}°C at {max_temp_entry['timestamp']}"
                )

            # Performance recommendations
            print("\n💡 Recommendations:")
            if cpu_avg > 70:
                print("   • Consider optimizing CPU-intensive operations")
            if memory_avg > 70:
                print("   • Consider reducing memory usage or adding swap")
            if temp_avg > 65:
                print("   • Consider improving cooling or reducing system load")

            if cpu_avg < 50 and memory_avg < 50:
                print("   • System performance is optimal")

        except Exception as e:
            print(f"❌ Error analyzing logs: {e}")

    def clear_logs(self):
        """Clear performance logs"""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            print("🗑️  Performance logs cleared")
        else:
            print("ℹ️  No performance logs to clear")

    def check_system_health(self):
        """Quick system health check"""
        print("🏥 System Health Check")
        print("=" * 40)

        stats = self.get_system_stats()
        health_score = 100
        issues = []

        # CPU check
        if stats["cpu_percent"] > 90:
            health_score -= 30
            issues.append("Critical CPU usage")
        elif stats["cpu_percent"] > 70:
            health_score -= 15
            issues.append("High CPU usage")

        # Memory check
        if stats["memory"]["percent"] > 95:
            health_score -= 25
            issues.append("Critical memory usage")
        elif stats["memory"]["percent"] > 80:
            health_score -= 10
            issues.append("High memory usage")

        # Temperature check
        if stats["temperature"]:
            if stats["temperature"] > 80:
                health_score -= 20
                issues.append("Critical CPU temperature")
            elif stats["temperature"] > 70:
                health_score -= 10
                issues.append("High CPU temperature")

        # Disk check
        if stats["disk_usage"] > 95:
            health_score -= 15
            issues.append("Critical disk usage")
        elif stats["disk_usage"] > 85:
            health_score -= 5
            issues.append("High disk usage")

        # Display results
        if health_score >= 90:
            status = "🟢 Excellent"
        elif health_score >= 70:
            status = "🟡 Good"
        elif health_score >= 50:
            status = "🟠 Fair"
        else:
            status = "🔴 Poor"

        print(f"Health Score: {health_score}/100 - {status}")

        if issues:
            print("\n⚠️  Issues detected:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("\n✅ No issues detected")

        return health_score


def main():
    """Main function"""
    monitor = PerformanceMonitor()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
            monitor.monitor_continuous(interval, duration)
        elif command == "analyze":
            monitor.analyze_logs()
        elif command == "clear":
            monitor.clear_logs()
        elif command == "health":
            monitor.check_system_health()
        else:
            print(
                "Usage: python3 performance_monitor.py [monitor|analyze|clear|health]"
            )
    else:
        # Interactive menu
        while True:
            print("\n🔧 Performance Monitor")
            print("=" * 30)
            print("1. Show current stats")
            print("2. Start continuous monitoring")
            print("3. Analyze logs")
            print("4. Clear logs")
            print("5. System health check")
            print("0. Exit")

            choice = input("\nEnter choice [0-5]: ").strip()

            if choice == "1":
                monitor.display_current_stats()
            elif choice == "2":
                try:
                    interval = (
                        input("Monitoring interval (seconds) [5]: ").strip() or "5"
                    )
                    duration = input("Duration (seconds) [300]: ").strip() or "300"
                    monitor.monitor_continuous(int(interval), int(duration))
                except ValueError:
                    print("❌ Invalid input")
            elif choice == "3":
                monitor.analyze_logs()
            elif choice == "4":
                monitor.clear_logs()
            elif choice == "5":
                monitor.check_system_health()
            elif choice == "0":
                break
            else:
                print("❌ Invalid choice")


if __name__ == "__main__":
    main()
