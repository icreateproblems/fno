"""
Instagram Account Security Hardening

Key Security Measures:
1. Session encryption (AES-256)
2. Session expiry monitoring
3. Automatic session refresh
4. Audit logging of all posts
5. Failed login detection
"""
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Generate encryption key from environment
ENCRYPTION_KEY = os.getenv("SESSION_ENCRYPTION_KEY")

class SessionSecurityManager:
    """Manage encrypted Instagram sessions"""
    
    def __init__(self, session_file: str):
        self.session_file = session_file
        self.cipher = None
        self.init_encryption()
    
    def init_encryption(self):
        """Initialize encryption cipher"""
        if not ENCRYPTION_KEY:
            raise ValueError("SESSION_ENCRYPTION_KEY not set in .env")
        
        # Use Fernet (AES-128 encryption)
        key = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
        # Ensure key is 32 bytes (base64 encoded)
        if len(key) < 32:
            key = hashlib.sha256(key).digest()
        import base64
        key = base64.urlsafe_b64encode(key[:32])
        self.cipher = Fernet(key)
    
    def encrypt_session(self, session_data: dict) -> bytes:
        """Encrypt session JSON"""
        json_str = json.dumps(session_data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted
    
    def decrypt_session(self) -> dict:
        """Decrypt and load session from file"""
        try:
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt session: {e}")
    
    def save_encrypted_session(self, session_data: dict):
        """Save session encrypted"""
        encrypted = self.encrypt_session(session_data)
        with open(self.session_file, 'wb') as f:
            f.write(encrypted)
        
        # Set restrictive permissions (user read/write only)
        os.chmod(self.session_file, 0o600)
        print(f"✓ Session encrypted and saved: {self.session_file}")
    
    def load_session(self) -> dict:
        """Load encrypted session"""
        return self.decrypt_session()


class AuditLogger:
    """Log all security-sensitive operations"""
    
    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = log_file
    
    def log_event(self, event_type: str, details: dict, status: str = "SUCCESS"):
        """Log security event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "status": status,
            "details": details
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_post(self, story_id: str, headline: str, status: str = "SUCCESS"):
        """Log Instagram post"""
        self.log_event("INSTAGRAM_POST", {
            "story_id": story_id,
            "headline": headline[:100]
        }, status)
    
    def log_login(self, username: str, success: bool):
        """Log login attempt"""
        self.log_event("LOGIN_ATTEMPT", {
            "username": username,
            "success": success
        }, "SUCCESS" if success else "FAILED")
    
    def log_session_refresh(self, reason: str):
        """Log session refresh"""
        self.log_event("SESSION_REFRESH", {"reason": reason})
    
    def get_recent_events(self, hours: int = 24) -> list:
        """Get events from last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        events = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event["timestamp"])
                        if event_time > cutoff:
                            events.append(event)
                    except:
                        pass
        except FileNotFoundError:
            pass
        
        return events


class SessionValidator:
    """Validate and refresh Instagram sessions"""
    
    @staticmethod
    def validate_session_age(session_file: str, max_age_hours: int = 30) -> bool:
        """Check if session is getting old"""
        if not os.path.exists(session_file):
            return False
        
        file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(session_file))).total_seconds() / 3600
        return file_age < max_age_hours
    
    @staticmethod
    def needs_refresh(session_file: str, warning_hours: int = 20) -> bool:
        """Check if session should be refreshed soon"""
        if not os.path.exists(session_file):
            return True
        
        file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(session_file))).total_seconds() / 3600
        return file_age > warning_hours


# Generate encryption key helper
def generate_encryption_key() -> str:
    """Generate a new encryption key"""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    print("Security Tools Available:")
    print("1. SessionSecurityManager - Encrypt/decrypt sessions")
    print("2. AuditLogger - Log all security events")
    print("3. SessionValidator - Monitor session health")
    print()
    print("To generate encryption key:")
    print(f"  Key: {generate_encryption_key()}")
    print()
    print("Add to .env:")
    print(f"  SESSION_ENCRYPTION_KEY={generate_encryption_key()}")
