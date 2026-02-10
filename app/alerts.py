"""
Alert system for Slack/Discord/Email notifications.
Sends alerts when critical issues occur.
"""

import os
import json
import requests
from typing import Optional, Dict, List
from datetime import datetime
from app.logger import get_logger

logger = get_logger(__name__)


class AlertManager:
    """Manages alerts and notifications to external services."""
    
    SEVERITY_EMOJI = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨"
    }
    
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.alert_email = os.getenv("ALERT_EMAIL")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.slack_webhook or self.discord_webhook or (self.telegram_bot_token and self.telegram_chat_id))
        
        if not self.enabled:
            logger.info("Alert system disabled (no webhooks/bots configured)")
        elif self.telegram_bot_token and self.telegram_chat_id:
            logger.info("Alert system enabled: Telegram")
    
    def send_slack_alert(self, message: str, severity: str = "INFO", metadata: Optional[Dict] = None) -> bool:
        """Send alert to Slack."""
        if not self.slack_webhook:
            return False
        
        try:
            emoji = self.SEVERITY_EMOJI.get(severity, "ℹ️")
            
            payload = {
                "text": f"{emoji} *{severity}* - News Bot Alert",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} {severity} Alert"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            # Add metadata if provided
            if metadata:
                fields = []
                for key, value in metadata.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                
                payload["blocks"].append({
                    "type": "section",
                    "fields": fields
                })
            
            # Add timestamp
            payload["blocks"].append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            })
            
            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent: {severity}")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def send_discord_alert(self, message: str, severity: str = "INFO", metadata: Optional[Dict] = None) -> bool:
        """Send alert to Discord."""
        if not self.discord_webhook:
            return False
        
        try:
            emoji = self.SEVERITY_EMOJI.get(severity, "ℹ️")
            
            # Color based on severity
            color_map = {
                "INFO": 0x3498db,      # Blue
                "WARNING": 0xf39c12,   # Orange
                "ERROR": 0xe74c3c,     # Red
                "CRITICAL": 0x992d22   # Dark red
            }
            
            embed = {
                "title": f"{emoji} {severity} Alert",
                "description": message,
                "color": color_map.get(severity, 0x3498db),
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "News Bot Alert System"
                }
            }
            
            # Add metadata fields
            if metadata:
                embed["fields"] = [
                    {"name": key, "value": str(value), "inline": True}
                    for key, value in metadata.items()
                ]
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Discord alert sent: {severity}")
                return True
            else:
                logger.error(f"Discord alert failed: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending Discord alert: {str(e)}")
            return False
    
    def send_telegram_alert(self, message: str, severity: str = "INFO", metadata: Optional[Dict] = None) -> bool:
        """Send alert to Telegram."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False
        
        try:
            emoji = self.SEVERITY_EMOJI.get(severity, "ℹ️")
            
            # Format message for Telegram (supports Markdown)
            formatted_message = f"{emoji} *{severity} ALERT*\n\n{message}"
            
            # Add metadata if provided
            if metadata:
                formatted_message += "\n\n*Details:*"
                for key, value in metadata.items():
                    formatted_message += f"\n• *{key}:* {value}"
            
            # Add timestamp
            formatted_message += f"\n\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            # Send via Telegram Bot API
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram alert sent: {severity}")
                return True
            else:
                logger.error(f"Telegram alert failed: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {str(e)}")
            return False
    
    def send_alert(self, message: str, severity: str = "INFO", metadata: Optional[Dict] = None) -> bool:
        """Send alert to all configured services."""
        if not self.enabled:
            logger.debug(f"Alert (not sent): [{severity}] {message}")
            return False
        
        results = []
        
        if self.telegram_bot_token and self.telegram_chat_id:
            results.append(self.send_telegram_alert(message, severity, metadata))
        
        if self.slack_webhook:
            results.append(self.send_slack_alert(message, severity, metadata))
        
        if self.discord_webhook:
            results.append(self.send_discord_alert(message, severity, metadata))
        
        return any(results)
    
    def alert_health_check_failed(self, failed_checks: List[str]):
        """Alert when health check fails."""
        message = f"Health check failed!\n\n*Failed checks:*\n" + "\n".join([f"• {check}" for check in failed_checks])
        
        metadata = {
            "Failed Count": str(len(failed_checks)),
            "Status": "UNHEALTHY"
        }
        
        self.send_alert(message, severity="ERROR", metadata=metadata)
    
    def alert_post_success(self, headline: str, score: int, safety_score: int):
        """Alert when post is successful."""
        message = f"✅ Post successful!\n\n*Headline:* {headline[:100]}..."
        
        metadata = {
            "Quality Score": f"{score}/100",
            "Safety Score": f"{safety_score}/100",
            "Status": "Posted to Instagram"
        }
        
        self.send_alert(message, severity="INFO", metadata=metadata)
    
    def alert_post_skipped(self, headline: str, score: int, reason: str):
        """Alert when post is skipped."""
        message = f"⏭️ Post skipped\n\n*Headline:* {headline[:100]}...\n\n*Reason:* {reason}"
        
        metadata = {
            "Quality Score": f"{score}/100",
            "Action": "Skipped"
        }
        
        self.send_alert(message, severity="INFO", metadata=metadata)
    
    def alert_fetch_complete(self, stories_fetched: int, sources_count: int):
        """Alert when news fetch completes."""
        message = f"📰 News fetch complete!\n\n*Stories fetched:* {stories_fetched}\n*Sources:* {sources_count}"
        
        metadata = {
            "Stories": str(stories_fetched),
            "Sources": str(sources_count),
            "Status": "Ready for posting"
        }
        
        self.send_alert(message, severity="INFO", metadata=metadata)
    
    def alert_high_error_rate(self, error_rate: float, threshold: float):
        """Alert when error rate is high."""
        message = f"High error rate detected!\n\nCurrent rate: {error_rate:.2f} errors/min\nThreshold: {threshold:.2f} errors/min"
        
        metadata = {
            "Error Rate": f"{error_rate:.2f}/min",
            "Threshold": f"{threshold:.2f}/min"
        }
        
        self.send_alert(message, severity="WARNING", metadata=metadata)
    
    def alert_posting_stopped(self, hours_since_last_post: int):
        """Alert when posting has stopped."""
        message = f"⚠️ No posts in {hours_since_last_post} hours!\n\nThe bot may have stopped working."
        
        metadata = {
            "Last Post": f"{hours_since_last_post}h ago",
            "Action": "Check logs and CI/CD"
        }
        
        self.send_alert(message, severity="CRITICAL", metadata=metadata)
    
    def alert_api_failure(self, api_name: str, error: str):
        """Alert when API fails."""
        message = f"{api_name} API failure!\n\n```{error}```"
        
        metadata = {
            "API": api_name,
            "Time": datetime.utcnow().strftime("%H:%M:%S UTC")
        }
        
        self.send_alert(message, severity="ERROR", metadata=metadata)
    
    def alert_content_safety_violation(self, headline: str, violations: List[str]):
        """Alert when content safety violation detected."""
        message = f"Content safety violation blocked!\n\n*Headline:* {headline[:100]}...\n\n*Violations:*\n" + "\n".join([f"• {v}" for v in violations[:3]])
        
        metadata = {
            "Violations": str(len(violations)),
            "Action": "Content blocked"
        }
        
        self.send_alert(message, severity="WARNING", metadata=metadata)
    
    def alert_daily_summary(self, posts_count: int, skipped_count: int, error_count: int):
        """Send daily summary alert."""
        message = f"📊 Daily Summary\n\n✅ Posts: {posts_count}\n⏭️ Skipped: {skipped_count}\n❌ Errors: {error_count}"
        
        success_rate = (posts_count / (posts_count + skipped_count) * 100) if (posts_count + skipped_count) > 0 else 0
        
        metadata = {
            "Success Rate": f"{success_rate:.1f}%",
            "Total Processed": str(posts_count + skipped_count)
        }
        
        self.send_alert(message, severity="INFO", metadata=metadata)
    
    def alert_circuit_breaker_open(self, service_name: str):
        """Alert when circuit breaker opens."""
        message = f"🔌 Circuit breaker OPEN for {service_name}!\n\nService is temporarily blocked due to repeated failures."
        
        metadata = {
            "Service": service_name,
            "Status": "BLOCKED"
        }
        
        self.send_alert(message, severity="ERROR", metadata=metadata)
    
    def alert_storage_warning(self, current_mb: float, limit_mb: float):
        """Alert when storage is running low."""
        percentage = (current_mb / limit_mb * 100) if limit_mb > 0 else 0
        
        message = f"💾 Storage warning!\n\nUsing {current_mb:.1f}MB of {limit_mb:.1f}MB ({percentage:.1f}%)"
        
        metadata = {
            "Usage": f"{current_mb:.1f}MB",
            "Limit": f"{limit_mb:.1f}MB",
            "Action": "Consider cleanup"
        }
        
        self.send_alert(message, severity="WARNING", metadata=metadata)


# Global instance
alert_manager = AlertManager()


def send_alert(message: str, severity: str = "INFO", metadata: Optional[Dict] = None):
    """Quick function to send alert."""
    alert_manager.send_alert(message, severity, metadata)


# Convenience functions
def alert_info(message: str, metadata: Optional[Dict] = None):
    """Send info alert."""
    alert_manager.send_alert(message, "INFO", metadata)


def alert_warning(message: str, metadata: Optional[Dict] = None):
    """Send warning alert."""
    alert_manager.send_alert(message, "WARNING", metadata)


def alert_error(message: str, metadata: Optional[Dict] = None):
    """Send error alert."""
    alert_manager.send_alert(message, "ERROR", metadata)


def alert_critical(message: str, metadata: Optional[Dict] = None):
    """Send critical alert."""
    alert_manager.send_alert(message, "CRITICAL", metadata)
