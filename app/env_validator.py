"""
Environment validation on startup.
Validates all configuration before bot runs.
"""

import os
import sys
from typing import List, Tuple
from app.logger import get_logger

logger = get_logger(__name__)


class ConfigValidator:
    """Validates environment configuration before startup."""
    
    REQUIRED_VARS = {
        "SUPABASE_URL": {
            "description": "Supabase project URL",
            "validation": lambda v: v.startswith("https://") and ".supabase.co" in v,
            "example": "https://xxxxx.supabase.co"
        },
        "SUPABASE_KEY": {
            "description": "Supabase anon/service role key",
            "validation": lambda v: len(v) > 20 and v.startswith("eyJ"),
            "example": "eyJhbGciOiJI..."
        },
        "GROQ_API_KEY": {
            "description": "GROQ API key for AI scoring (or use GROQ_API_KEYS for multiple)",
            "validation": lambda v: len(v) > 20 and v.startswith("gsk_"),
            "example": "gsk_xxxxx..."
        },
        "INSTAGRAM_ACCESS_TOKEN": {
            "description": "Instagram Graph API access token",
            "validation": lambda v: len(v) > 20 and (v.startswith("IGAA") or v.startswith("EAA")),
            "example": "IGAAxxxxx... or EAAxxxxx..."
        },
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": {
            "description": "Instagram Business Account ID",
            "validation": lambda v: v.isdigit() and len(v) > 10,
            "example": "17841405309123456"
        },
        "IMGBB_API_KEY": {
            "description": "imgbb API key for image hosting (Graph API requires public URLs)",
            "validation": lambda v: len(v) == 32,
            "example": "your_32_character_imgbb_key"
        },
    }
    
    OPTIONAL_VARS = {
        "RSS_FEEDS": {
            "description": "Comma-separated RSS feed URLs",
            "default": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "validation": lambda v: v.startswith("http"),
        },
        "MIN_SCORE_THRESHOLD": {
            "description": "Minimum quality score to post (0-100)",
            "default": "50",
            "validation": lambda v: v.isdigit() and 0 <= int(v) <= 100,
        },
        "TELEGRAM_BOT_TOKEN": {
            "description": "Telegram bot token for alerts",
            "default": None,
            "validation": lambda v: ":" in v and len(v) > 20,
        },
        "TELEGRAM_CHAT_ID": {
            "description": "Telegram chat ID for alerts",
            "default": None,
            "validation": lambda v: v.lstrip("-").isdigit(),
        },
        "SLACK_WEBHOOK_URL": {
            "description": "Slack webhook for alerts",
            "default": None,
            "validation": lambda v: v.startswith("https://"),
        },
        "DISCORD_WEBHOOK_URL": {
            "description": "Discord webhook for alerts",
            "default": None,
            "validation": lambda v: v.startswith("https://"),
        },
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.validated = False
    
    def validate_required_vars(self) -> bool:
        """Validate all required environment variables."""
        all_valid = True
        
        for var_name, config in self.REQUIRED_VARS.items():
            value = os.getenv(var_name)
            
            # Special case: Allow either GROQ_API_KEY or GROQ_API_KEYS
            if var_name == "GROQ_API_KEY" and not value:
                value = os.getenv("GROQ_API_KEYS")
                if value:
                    # Valid if we have GROQ_API_KEYS instead
                    continue
            
            if not value:
                self.errors.append(
                    f"❌ Missing required variable: {var_name}\n"
                    f"   Description: {config['description']}\n"
                    f"   Example: {config['example']}"
                )
                all_valid = False
                continue
            
            # Validate format
            try:
                if not config["validation"](value):
                    self.errors.append(
                        f"❌ Invalid format for {var_name}\n"
                        f"   Expected format: {config['example']}"
                    )
                    all_valid = False
            except Exception as e:
                self.errors.append(
                    f"❌ Error validating {var_name}: {str(e)}"
                )
                all_valid = False
        
        return all_valid
    
    def validate_optional_vars(self):
        """Validate optional variables and set defaults."""
        for var_name, config in self.OPTIONAL_VARS.items():
            value = os.getenv(var_name)
            
            if not value:
                if config["default"]:
                    self.warnings.append(
                        f"⚠️  Using default for {var_name}: {config['default']}"
                    )
                    os.environ[var_name] = config["default"]
                continue
            
            # Validate format if provided
            if config["validation"]:
                try:
                    if not config["validation"](value):
                        self.warnings.append(
                            f"⚠️  Invalid format for {var_name}, using default"
                        )
                        if config["default"]:
                            os.environ[var_name] = config["default"]
                except Exception as e:
                    self.warnings.append(
                        f"⚠️  Error validating {var_name}: {str(e)}"
                    )
    
    def check_file_structure(self) -> bool:
        """Validate required files and directories exist."""
        required_files = [
            "scripts/fetch_news.py",
            "scripts/post_instagram_graph.py",
            "scripts/content_filter.py",
            "app/config.py",
            "app/db.py",
            "app/logger.py",
        ]
        
        all_exist = True
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                self.errors.append(f"❌ Missing required file: {file_path}")
                all_exist = False
        
        # Check directories
        required_dirs = ["app", "scripts", "templates", "fonts"]
        
        for dir_path in required_dirs:
            if not os.path.isdir(dir_path):
                self.errors.append(f"❌ Missing required directory: {dir_path}")
                all_exist = False
        
        return all_exist
    
    def check_database_schema(self) -> bool:
        """Check if database tables exist."""
        try:
            from app.db_pool import get_supabase_client
            from app.config import SUPABASE_URL, SUPABASE_KEY
            
            # Use configured credentials explicitly
            supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Try to query each required table
            tables = ["stories", "posting_history"]
            
            for table in tables:
                result = supabase.table(table).select("id").limit(1).execute()
                if not hasattr(result, 'data'):
                    self.errors.append(f"❌ Database table '{table}' not accessible")
                    return False
            
            logger.info("✅ Database schema validated")
            return True
        
        except Exception as e:
            self.errors.append(f"❌ Database validation failed: {str(e)}")
            return False
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validations.
        
        Returns:
            success: bool
            errors: list of error messages
            warnings: list of warning messages
        """
        logger.info("Starting environment validation...")
        
        # Validate environment variables
        env_valid = self.validate_required_vars()
        self.validate_optional_vars()
        
        # Validate file structure
        files_valid = self.check_file_structure()
        
        # Validate database (only if env vars are valid)
        db_valid = True
        if env_valid:
            db_valid = self.check_database_schema()
        
        # Overall success
        success = env_valid and files_valid and db_valid
        self.validated = True
        
        return success, self.errors, self.warnings
    
    def print_report(self):
        """Print validation report."""
        if not self.validated:
            print("⚠️  Validation not run yet")
            return
        
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION REPORT")
        print("="*60 + "\n")
        
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(error)
            print()
        
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(warning)
            print()
        
        if not self.errors:
            print("✅ All required validations passed!")
            print()
        
        print("="*60 + "\n")
    
    def exit_if_invalid(self):
        """Exit program if validation failed."""
        if not self.validated:
            logger.error("Validation not run before exit check")
            sys.exit(1)
        
        if self.errors:
            logger.error("Validation failed, exiting...")
            self.print_report()
            sys.exit(1)
        
        if self.warnings:
            logger.warning("Validation passed with warnings")
            self.print_report()
        else:
            logger.info("✅ Environment validation successful")


def validate_environment() -> bool:
    """
    Quick validation function. Returns True if valid, False otherwise.
    """
    validator = ConfigValidator()
    success, errors, warnings = validator.validate_all()
    
    if not success:
        validator.print_report()
    
    return success


def validate_and_exit_if_invalid():
    """
    Validate environment and exit if invalid.
    Use this at the start of main scripts.
    """
    validator = ConfigValidator()
    validator.validate_all()
    validator.exit_if_invalid()


if __name__ == "__main__":
    # Run validation from command line
    validator = ConfigValidator()
    success, errors, warnings = validator.validate_all()
    validator.print_report()
    
    sys.exit(0 if success else 1)
