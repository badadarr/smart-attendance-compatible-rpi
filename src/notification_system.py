#!/usr/bin/env python3
"""
Enhanced Notification System for Smart Attendance
Supports multiple notification types: audio, visual, email, SMS
"""

import pyttsx3
import smtplib
import json
import requests
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pygame
import threading


class NotificationSystem:
    def __init__(self):
        self.config_file = (
            Path(__file__).parent.parent / "config" / "notifications.json"
        )
        self.load_config()
        self.init_audio()
        self.init_tts()

    def load_config(self):
        """Load notification configuration"""
        default_config = {
            "audio_enabled": True,
            "tts_enabled": True,
            "email_enabled": False,
            "sms_enabled": False,
            "sounds": {
                "clock_in": "assets/sounds/clock_in.wav",
                "clock_out": "assets/sounds/clock_out.wav",
                "success": "assets/sounds/success.wav",
                "error": "assets/sounds/error.wav",
            },
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "admin_email": "",
            },
            "sms": {"api_key": "", "api_url": "", "admin_phone": ""},
        }

        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save notification configuration"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def init_audio(self):
        """Initialize pygame for sound effects"""
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False
            print("⚠️ Audio system not available")

    def init_tts(self):
        """Initialize text-to-speech"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", 150)
            self.tts_engine.setProperty("volume", 0.8)
            self.tts_available = True
        except:
            self.tts_available = False
            print("⚠️ TTS system not available")

    def play_sound(self, sound_type):
        """Play notification sound"""
        if not self.config["audio_enabled"] or not self.audio_available:
            return

        sound_file = self.config["sounds"].get(sound_type)
        if sound_file and Path(sound_file).exists():
            try:
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"❌ Error playing sound: {e}")

    def speak_message(self, message):
        """Text-to-speech notification"""
        if not self.config["tts_enabled"] or not self.tts_available:
            return

        def speak():
            try:
                self.tts_engine.say(message)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"❌ TTS Error: {e}")

        # Run TTS in separate thread to avoid blocking
        threading.Thread(target=speak, daemon=True).start()

    def send_email_notification(self, subject, message, recipient=None):
        """Send email notification"""
        if not self.config["email_enabled"]:
            return False

        try:
            email_config = self.config["email"]
            recipient = recipient or email_config["admin_email"]

            msg = MIMEMultipart()
            msg["From"] = email_config["username"]
            msg["To"] = recipient
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP(
                email_config["smtp_server"], email_config["smtp_port"]
            )
            server.starttls()
            server.login(email_config["username"], email_config["password"])

            text = msg.as_string()
            server.sendmail(email_config["username"], recipient, text)
            server.quit()

            return True
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
            return False

    def send_sms_notification(self, message, recipient=None):
        """Send SMS notification"""
        if not self.config["sms_enabled"]:
            return False

        try:
            sms_config = self.config["sms"]
            recipient = recipient or sms_config["admin_phone"]

            payload = {
                "api_key": sms_config["api_key"],
                "to": recipient,
                "message": message,
            }

            response = requests.post(sms_config["api_url"], data=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ SMS notification failed: {e}")
            return False

    def notify_attendance(self, name, status, time=None):
        """Send attendance notification with multiple methods"""
        time = time or datetime.now().strftime("%H:%M:%S")

        # Audio notification
        sound_type = "clock_in" if status == "Clock In" else "clock_out"
        self.play_sound(sound_type)

        # TTS notification
        tts_message = f"{name} has {status.lower()} at {time}"
        self.speak_message(tts_message)

        # Email notification (for admin)
        if status == "Clock In":
            subject = f"🟢 {name} - Clock In"
            message = (
                f"{name} arrived at {time} on {datetime.now().strftime('%Y-%m-%d')}"
            )
        else:
            subject = f"🔴 {name} - Clock Out"
            message = f"{name} left at {time} on {datetime.now().strftime('%Y-%m-%d')}"

        self.send_email_notification(subject, message)

        # SMS notification for important events
        if status == "Clock In":
            sms_message = f"✅ {name} arrived - {time}"
        else:
            sms_message = f"🚪 {name} left - {time}"

        self.send_sms_notification(sms_message)

    def notify_error(self, error_message):
        """Send error notification"""
        self.play_sound("error")
        self.speak_message("System error occurred")

        # Email admin about errors
        subject = "🚨 Attendance System Error"
        self.send_email_notification(subject, error_message)

    def notify_success(self, message):
        """Send success notification"""
        self.play_sound("success")
        self.speak_message(message)

    def test_notifications(self):
        """Test all notification methods"""
        print("🔔 Testing notification system...")

        # Test audio
        self.play_sound("success")

        # Test TTS
        self.speak_message("Testing notification system")

        # Test email
        if self.send_email_notification(
            "Test Email", "This is a test email from attendance system"
        ):
            print("✅ Email notification working")
        else:
            print("❌ Email notification failed")

        # Test SMS
        if self.send_sms_notification("Test SMS from attendance system"):
            print("✅ SMS notification working")
        else:
            print("❌ SMS notification failed")


# Usage example
if __name__ == "__main__":
    notifier = NotificationSystem()
    notifier.test_notifications()

    # Example attendance notification
    notifier.notify_attendance("John Doe", "Clock In", "09:00:00")
