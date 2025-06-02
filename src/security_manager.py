#!/usr/bin/env python3
"""
Security and Access Control System for Smart Attendance
Implements authentication, authorization, and audit logging
"""

import hashlib
import jwt
import json
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
import secrets
import logging
from typing import Dict, List, Optional


class SecurityManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        self.users_file = self.config_dir / "users.json"
        self.security_config_file = self.config_dir / "security.json"

        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Initialize logging
        self.setup_logging()

        # Load configurations
        self.load_security_config()
        self.load_users()

        # Generate JWT secret if not exists
        if not hasattr(self, "jwt_secret"):
            self.jwt_secret = secrets.token_hex(32)
            self.save_security_config()

    def setup_logging(self):
        """Setup security audit logging"""
        log_file = self.logs_dir / "security_audit.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        self.logger = logging.getLogger(__name__)

    def load_security_config(self):
        """Load security configuration"""
        default_config = {
            "session_timeout": 3600,  # 1 hour
            "max_login_attempts": 5,
            "lockout_duration": 300,  # 5 minutes
            "password_min_length": 8,
            "require_complex_password": True,
            "jwt_expiry": 3600,
            "audit_retention_days": 90,
        }

        if self.security_config_file.exists():
            with open(self.security_config_file, "r") as f:
                self.security_config = {**default_config, **json.load(f)}
        else:
            self.security_config = default_config
            self.save_security_config()

    def save_security_config(self):
        """Save security configuration"""
        config_to_save = self.security_config.copy()
        if hasattr(self, "jwt_secret"):
            config_to_save["jwt_secret"] = self.jwt_secret

        with open(self.security_config_file, "w") as f:
            json.dump(config_to_save, f, indent=2)

    def load_users(self):
        """Load user database"""
        if self.users_file.exists():
            with open(self.users_file, "r") as f:
                self.users = json.load(f)
        else:
            # Create default admin user
            self.users = {}
            self.create_default_admin()

    def save_users(self):
        """Save user database"""
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=2)

    def create_default_admin(self):
        """Create default admin user"""
        admin_password = "admin123"  # Change this in production!
        self.create_user(
            "admin", admin_password, "admin", "Administrator", "admin@company.com"
        )
        print("🔐 Default admin user created: admin/admin123")
        print("⚠️  Please change the admin password immediately!")

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed.split(":")
            return (
                hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
            )
        except:
            return False

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < self.security_config["password_min_length"]:
            return (
                False,
                f"Password must be at least {self.security_config['password_min_length']} characters",
            )

        if self.security_config["require_complex_password"]:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

            if not all([has_upper, has_lower, has_digit, has_special]):
                return (
                    False,
                    "Password must contain uppercase, lowercase, digit, and special character",
                )

        return True, "Password is strong"

    def create_user(
        self, username: str, password: str, role: str, full_name: str, email: str
    ) -> bool:
        """Create new user"""
        if username in self.users:
            return False, "Username already exists"

        # Validate password
        is_strong, message = self.validate_password_strength(password)
        if not is_strong:
            return False, message

        # Validate role
        if role not in ["admin", "manager", "user", "viewer"]:
            return False, "Invalid role"

        user_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "role": role,
            "full_name": full_name,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True,
            "failed_attempts": 0,
            "locked_until": None,
        }

        self.users[username] = user_data
        self.save_users()

        self.logger.info(f"User created: {username} with role {role}")
        return True, "User created successfully"

    def authenticate_user(
        self, username: str, password: str
    ) -> tuple[bool, str, Optional[Dict]]:
        """Authenticate user credentials"""
        if username not in self.users:
            self.logger.warning(f"Login attempt with non-existent username: {username}")
            return False, "Invalid credentials", None

        user = self.users[username]

        # Check if user is active
        if not user.get("is_active", True):
            self.logger.warning(f"Login attempt for inactive user: {username}")
            return False, "Account is disabled", None

        # Check if user is locked out
        if user.get("locked_until"):
            lockout_time = datetime.fromisoformat(user["locked_until"])
            if datetime.now() < lockout_time:
                self.logger.warning(f"Login attempt for locked user: {username}")
                return (
                    False,
                    f"Account locked until {lockout_time.strftime('%H:%M:%S')}",
                    None,
                )
            else:
                # Reset lockout
                user["locked_until"] = None
                user["failed_attempts"] = 0

        # Verify password
        if self.verify_password(password, user["password_hash"]):
            # Successful login
            user["last_login"] = datetime.now().isoformat()
            user["failed_attempts"] = 0
            user["locked_until"] = None
            self.save_users()

            self.logger.info(f"Successful login: {username}")
            return True, "Login successful", user
        else:
            # Failed login
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1

            if user["failed_attempts"] >= self.security_config["max_login_attempts"]:
                # Lock account
                lockout_time = datetime.now() + timedelta(
                    seconds=self.security_config["lockout_duration"]
                )
                user["locked_until"] = lockout_time.isoformat()
                self.logger.warning(
                    f"Account locked due to failed attempts: {username}"
                )
                self.save_users()
                return (
                    False,
                    f"Account locked for {self.security_config['lockout_duration']//60} minutes",
                    None,
                )

            self.save_users()
            self.logger.warning(
                f"Failed login attempt: {username} ({user['failed_attempts']}/{self.security_config['max_login_attempts']})"
            )
            return False, "Invalid credentials", None

    def generate_token(self, user_data: Dict) -> str:
        """Generate JWT token"""
        payload = {
            "username": user_data["username"],
            "role": user_data["role"],
            "exp": datetime.utcnow()
            + timedelta(seconds=self.security_config["jwt_expiry"]),
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_token(self, token: str) -> tuple[bool, Optional[Dict]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None

    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        permissions = {
            "admin": ["read", "write", "delete", "admin", "manage_users"],
            "manager": ["read", "write", "delete", "manage_attendance"],
            "user": ["read", "write", "record_attendance"],
            "viewer": ["read"],
        }

        user_permissions = permissions.get(user_role, [])
        return required_permission in user_permissions

    def log_action(self, username: str, action: str, details: str = ""):
        """Log user action for audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "action": action,
            "details": details,
            "ip_address": "127.0.0.1",  # Can be extended to capture real IP
        }

        # Log to file
        audit_file = self.logs_dir / f"audit_{datetime.now().strftime('%Y%m')}.json"

        if audit_file.exists():
            with open(audit_file, "r") as f:
                audit_log = json.load(f)
        else:
            audit_log = []

        audit_log.append(audit_entry)

        with open(audit_file, "w") as f:
            json.dump(audit_log, f, indent=2)

        self.logger.info(f"Action logged: {username} - {action}")

    def get_audit_trail(self, username: str = None, days: int = 30) -> List[Dict]:
        """Get audit trail for user or all users"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        audit_entries = []

        # Check audit files for the period
        current_date = start_date
        while current_date <= end_date:
            audit_file = self.logs_dir / f"audit_{current_date.strftime('%Y%m')}.json"

            if audit_file.exists():
                with open(audit_file, "r") as f:
                    monthly_audit = json.load(f)

                for entry in monthly_audit:
                    entry_date = datetime.fromisoformat(entry["timestamp"])
                    if start_date <= entry_date <= end_date:
                        if username is None or entry["username"] == username:
                            audit_entries.append(entry)

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        return sorted(audit_entries, key=lambda x: x["timestamp"], reverse=True)


# Decorator for Flask routes requiring authentication
def require_auth(required_permission=None):
    """Decorator for requiring authentication and permission"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify, session

            # Check session or token
            token = request.headers.get("Authorization")
            if token and token.startswith("Bearer "):
                token = token[7:]
                security = SecurityManager()
                is_valid, payload = security.verify_token(token)

                if not is_valid:
                    return jsonify({"error": "Invalid or expired token"}), 401

                if required_permission and not security.check_permission(
                    payload["role"], required_permission
                ):
                    return jsonify({"error": "Insufficient permissions"}), 403

                # Add user info to request
                request.user = payload
            else:
                return jsonify({"error": "Authentication required"}), 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Usage example
if __name__ == "__main__":
    security = SecurityManager()

    # Test authentication
    success, message, user = security.authenticate_user("admin", "admin123")
    if success:
        token = security.generate_token(user)
        print(f"🔐 Login successful, token: {token}")

        # Test permission
        has_permission = security.check_permission(user["role"], "admin")
        print(f"👤 Admin permission: {has_permission}")

        # Log action
        security.log_action("admin", "login", "Successful login from test")
    else:
        print(f"❌ Login failed: {message}")
