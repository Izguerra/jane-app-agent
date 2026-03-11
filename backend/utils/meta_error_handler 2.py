"""
Enhanced Meta API Error Handler
Provides detailed error analysis and recovery suggestions for Instagram/Meta API errors
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

class MetaErrorCode(Enum):
    """Known Meta API error codes and their meanings"""
    INVALID_OAUTH_TOKEN = 190
    EXPIRED_TOKEN = 463
    PERMISSION_DENIED = 200
    RATE_LIMIT = 613
    DUPLICATE_POST = 506
    PAGE_NOT_FOUND = 803
    USER_NOT_VISIBLE = 10
    CONVERSATION_ROUTING_DISABLED = 27
    APP_NOT_INSTALLED = 2500
    WEBHOOK_UPDATE_FAILED = 2200
    INSUFFICIENT_PERMISSIONS = 10303
    MESSAGE_SEND_FAILED = 100
    INVALID_PARAMETER = 100
    API_TOO_MANY_CALLS = 17
    USER_REQUEST_LIMIT = 32
    APP_REQUEST_LIMIT = 4
    
class MetaErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Error recovery strategies
        self.recovery_strategies = {
            MetaErrorCode.INVALID_OAUTH_TOKEN: self.handle_invalid_token,
            MetaErrorCode.EXPIRED_TOKEN: self.handle_expired_token,
            MetaErrorCode.PERMISSION_DENIED: self.handle_permission_denied,
            MetaErrorCode.RATE_LIMIT: self.handle_rate_limit,
            MetaErrorCode.CONVERSATION_ROUTING_DISABLED: self.handle_routing_disabled,
            MetaErrorCode.INSUFFICIENT_PERMISSIONS: self.handle_insufficient_permissions,
            MetaErrorCode.API_TOO_MANY_CALLS: self.handle_too_many_calls,
        }
        
        # Track error patterns
        self.error_history = []
        self.max_history = 100
    
    def handle_error(self, error_response: Dict[str, Any]) -> Dict[str, Any]:
        """Main error handler for Meta API responses"""
        
        # Extract error details
        error_info = self.extract_error_info(error_response)
        
        # Log error for pattern analysis
        self.log_error(error_info)
        
        # Generate recovery strategy
        recovery = self.generate_recovery_strategy(error_info)
        
        # Check for patterns
        patterns = self.detect_error_patterns()
        
        return {
            "error_info": error_info,
            "recovery": recovery,
            "patterns": patterns,
            "timestamp": datetime.now().isoformat()
        }
    
    def extract_error_info(self, response: Dict) -> Dict:
        """Extract detailed error information from Meta API response"""
        
        if "error" in response:
            error = response["error"]
            return {
                "code": error.get("code"),
                "message": error.get("message"),
                "type": error.get("type"),
                "error_subcode": error.get("error_subcode"),
                "error_user_title": error.get("error_user_title"),
                "error_user_msg": error.get("error_user_msg"),
                "fbtrace_id": error.get("fbtrace_id"),
                "is_transient": error.get("is_transient", False)
            }
        
        # Handle non-standard error format
        return {
            "code": response.get("code", "unknown"),
            "message": response.get("message", str(response)),
            "raw_response": response
        }
    
    def log_error(self, error_info: Dict):
        """Log error for pattern detection"""
        
        self.error_history.append({
            "timestamp": datetime.now().isoformat(),
            "error": error_info
        })
        
        # Maintain history size
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        # Log to file
        self.logger.error(f"Meta API Error: {json.dumps(error_info)}")
    
    def generate_recovery_strategy(self, error_info: Dict) -> Dict:
        """Generate recovery strategy based on error type"""
        
        error_code = error_info.get("code")
        
        # Try to match known error codes
        for known_code in MetaErrorCode:
            if known_code.value == error_code:
                if known_code in self.recovery_strategies:
                    return self.recovery_strategies[known_code](error_info)
        
        # Default strategy for unknown errors
        return self.handle_unknown_error(error_info)
    
    def handle_invalid_token(self, error_info: Dict) -> Dict:
        """Handle invalid OAuth token error"""
        return {
            "action": "REAUTH_REQUIRED",
            "steps": [
                "Token is invalid or revoked",
                "Perform Nuclear Reset procedure",
                "1. Delete integration from SupaAgent",
                "2. Remove app from Facebook Business Settings",
                "3. Reconnect with all permissions"
            ],
            "severity": "CRITICAL",
            "user_action_required": True,
            "automated_recovery": False
        }
    
    def handle_expired_token(self, error_info: Dict) -> Dict:
        """Handle expired token error"""
        return {
            "action": "TOKEN_REFRESH",
            "steps": [
                "Token has expired",
                "Exchange for long-lived token",
                "Or re-authenticate user"
            ],
            "severity": "HIGH",
            "user_action_required": True,
            "automated_recovery": False,
            "api_endpoint": "https://graph.facebook.com/v21.0/oauth/access_token"
        }
    
    def handle_permission_denied(self, error_info: Dict) -> Dict:
        """Handle permission denied error"""
        
        missing_permission = self.identify_missing_permission(error_info)
        
        return {
            "action": "PERMISSION_GRANT",
            "steps": [
                f"Permission denied: {missing_permission or 'Unknown'}",
                "Check app permissions in Meta App Dashboard",
                "May require app review for production",
                "Or perform Nuclear Reset with all permissions"
            ],
            "severity": "HIGH",
            "user_action_required": True,
            "missing_permission": missing_permission,
            "automated_recovery": False
        }
    
    def handle_rate_limit(self, error_info: Dict) -> Dict:
        """Handle rate limiting error"""
        return {
            "action": "RATE_LIMIT_BACKOFF",
            "steps": [
                "Rate limit exceeded",
                "Implement exponential backoff",
                "Wait before retrying",
                "Consider batching requests"
            ],
            "severity": "MEDIUM",
            "user_action_required": False,
            "automated_recovery": True,
            "retry_after": 60,  # seconds
            "backoff_multiplier": 2
        }
    
    def handle_routing_disabled(self, error_info: Dict) -> Dict:
        """Handle conversation routing disabled error"""
        return {
            "action": "ENABLE_HANDOVER",
            "steps": [
                "Conversation Routing/Handover Protocol is disabled",
                "Go to Facebook Page Settings",
                "Navigate to 'Advanced Messaging'",
                "Enable 'Handover Protocol'",
                "Configure primary and secondary receivers"
            ],
            "severity": "HIGH",
            "user_action_required": True,
            "automated_recovery": False,
            "settings_url": "https://www.facebook.com/settings/business_tools/"
        }
    
    def handle_insufficient_permissions(self, error_info: Dict) -> Dict:
        """Handle insufficient permissions error"""
        return {
            "action": "PERMISSION_UPGRADE",
            "steps": [
                "App has insufficient permissions",
                "Critical: Missing 'pages_manage_metadata'",
                "Perform Nuclear Reset procedure",
                "Ensure ALL permissions are granted during reconnection"
            ],
            "severity": "CRITICAL",
            "user_action_required": True,
            "automated_recovery": False,
            "required_permissions": [
                "pages_messaging",
                "pages_messaging_subscriptions",
                "instagram_basic",
                "instagram_manage_messages",
                "pages_manage_metadata"
            ]
        }
    
    def handle_too_many_calls(self, error_info: Dict) -> Dict:
        """Handle too many API calls error"""
        return {
            "action": "THROTTLE_REQUESTS",
            "steps": [
                "Too many API calls",
                "Implement request throttling",
                "Use batch requests where possible",
                "Cache frequently accessed data"
            ],
            "severity": "MEDIUM",
            "user_action_required": False,
            "automated_recovery": True,
            "throttle_config": {
                "max_requests_per_hour": 200,
                "batch_size": 50,
                "cache_ttl": 300  # seconds
            }
        }
    
    def handle_unknown_error(self, error_info: Dict) -> Dict:
        """Handle unknown errors"""
        return {
            "action": "MANUAL_REVIEW",
            "steps": [
                f"Unknown error: {error_info.get('message')}",
                "Check Meta Developer documentation",
                "Review error trace ID with Meta Support",
                f"Trace ID: {error_info.get('fbtrace_id', 'N/A')}"
            ],
            "severity": "UNKNOWN",
            "user_action_required": True,
            "automated_recovery": False
        }
    
    def identify_missing_permission(self, error_info: Dict) -> Optional[str]:
        """Try to identify which permission is missing from error message"""
        
        message = error_info.get("message", "").lower()
        error_user_msg = error_info.get("error_user_msg", "").lower()
        
        permission_keywords = {
            "pages_manage_metadata": ["metadata", "page metadata"],
            "instagram_manage_messages": ["instagram message", "direct message"],
            "pages_messaging": ["messaging", "send message"],
            "instagram_basic": ["instagram", "instagram account"],
            "pages_messaging_subscriptions": ["webhook", "subscription"]
        }
        
        for permission, keywords in permission_keywords.items():
            for keyword in keywords:
                if keyword in message or keyword in error_user_msg:
                    return permission
        
        return None
    
    def detect_error_patterns(self) -> List[Dict]:
        """Detect patterns in error history"""
        
        if len(self.error_history) < 3:
            return []
        
        patterns = []
        
        # Check for repeated errors
        recent_errors = self.error_history[-10:]
        error_counts = {}
        
        for entry in recent_errors:
            error_code = entry["error"].get("code")
            if error_code:
                error_counts[error_code] = error_counts.get(error_code, 0) + 1
        
        for code, count in error_counts.items():
            if count >= 3:
                patterns.append({
                    "type": "REPEATED_ERROR",
                    "error_code": code,
                    "frequency": count,
                    "recommendation": "This error is occurring frequently. Root cause analysis needed."
                })
        
        # Check for permission cascade (multiple permission errors)
        permission_errors = [
            e for e in recent_errors 
            if e["error"].get("code") in [200, 10303, MetaErrorCode.INSUFFICIENT_PERMISSIONS.value]
        ]
        
        if len(permission_errors) >= 2:
            patterns.append({
                "type": "PERMISSION_CASCADE",
                "count": len(permission_errors),
                "recommendation": "Multiple permission errors detected. Nuclear Reset recommended."
            })
        
        return patterns
    
    def generate_diagnostic_report(self) -> str:
        """Generate a diagnostic report of recent errors"""
        
        if not self.error_history:
            return "No errors recorded."
        
        report = [
            "=" * 60,
            "META API ERROR DIAGNOSTIC REPORT",
            "=" * 60,
            f"Generated: {datetime.now().isoformat()}",
            f"Total Errors: {len(self.error_history)}",
            ""
        ]
        
        # Error frequency analysis
        error_freq = {}
        for entry in self.error_history:
            code = entry["error"].get("code", "unknown")
            error_freq[code] = error_freq.get(code, 0) + 1
        
        report.append("ERROR FREQUENCY:")
        for code, count in sorted(error_freq.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  Code {code}: {count} occurrences")
        
        # Recent errors
        report.append("\nRECENT ERRORS (Last 5):")
        for entry in self.error_history[-5:]:
            error = entry["error"]
            report.append(f"\n  Time: {entry['timestamp']}")
            report.append(f"  Code: {error.get('code')}")
            report.append(f"  Message: {error.get('message')}")
            report.append(f"  Type: {error.get('type')}")
        
        # Pattern detection
        patterns = self.detect_error_patterns()
        if patterns:
            report.append("\nPATTERNS DETECTED:")
            for pattern in patterns:
                report.append(f"  - {pattern['type']}: {pattern['recommendation']}")
        
        return "\n".join(report)

# Decorator for automatic error handling
def handle_meta_errors(handler: MetaErrorHandler):
    """Decorator to automatically handle Meta API errors"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                
                # Check if response contains error
                if isinstance(response, dict) and "error" in response:
                    error_result = handler.handle_error(response)
                    
                    # Log recovery strategy
                    logging.info(f"Error recovery strategy: {error_result['recovery']}")
                    
                    # Raise exception with recovery info
                    raise MetaAPIError(response, error_result)
                
                return response
                
            except Exception as e:
                if not isinstance(e, MetaAPIError):
                    # Wrap unexpected errors
                    error_response = {
                        "error": {
                            "message": str(e),
                            "type": type(e).__name__
                        }
                    }
                    error_result = handler.handle_error(error_response)
                    raise MetaAPIError(error_response, error_result)
                raise
        
        return wrapper
    return decorator

class MetaAPIError(Exception):
    """Custom exception for Meta API errors with recovery information"""
    
    def __init__(self, error_response: Dict, recovery_info: Dict):
        self.error_response = error_response
        self.recovery_info = recovery_info
        super().__init__(f"Meta API Error: {error_response}")
    
    def get_recovery_steps(self) -> List[str]:
        """Get recovery steps for this error"""
        return self.recovery_info.get("recovery", {}).get("steps", [])
    
    def requires_user_action(self) -> bool:
        """Check if user action is required"""
        return self.recovery_info.get("recovery", {}).get("user_action_required", False)
    
    def can_auto_recover(self) -> bool:
        """Check if automated recovery is possible"""
        return self.recovery_info.get("recovery", {}).get("automated_recovery", False)