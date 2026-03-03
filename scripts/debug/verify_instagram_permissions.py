#!/usr/bin/env python3
"""
Instagram Integration Permission Verifier
Comprehensive tool to diagnose and fix the "One-Way Silence" issue
"""

import requests
import json
from typing import Dict, List, Tuple
import os
from datetime import datetime

class InstagramPermissionVerifier:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.graph_url = "https://graph.facebook.com/v21.0"
        self.results = []
        
    def check_token_permissions(self) -> Dict:
        """Check all permissions associated with the current access token"""
        url = f"{self.graph_url}/debug_token"
        params = {
            "input_token": self.access_token,
            "access_token": self.access_token
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "data" in data:
            token_data = data["data"]
            permissions = token_data.get("scopes", [])
            
            # Required permissions for Instagram messaging
            required_permissions = [
                "pages_messaging",
                "pages_messaging_subscriptions", 
                "instagram_basic",
                "instagram_manage_messages",
                "pages_manage_metadata",  # CRITICAL - Missing in your case
                "pages_read_engagement",
                "business_management",
                "instagram_manage_insights"
            ]
            
            missing_permissions = [p for p in required_permissions if p not in permissions]
            
            result = {
                "status": "SUCCESS" if not missing_permissions else "MISSING_PERMISSIONS",
                "current_permissions": permissions,
                "missing_permissions": missing_permissions,
                "token_expires": token_data.get("expires_at"),
                "app_id": token_data.get("app_id"),
                "is_valid": token_data.get("is_valid", False)
            }
            
            self.results.append(("Token Permissions", result))
            return result
        else:
            error_result = {"status": "ERROR", "error": data.get("error", "Unknown error")}
            self.results.append(("Token Permissions", error_result))
            return error_result
    
    def check_webhook_subscriptions(self, app_id: str) -> Dict:
        """Verify webhook subscription configuration"""
        url = f"{self.graph_url}/{app_id}/subscriptions"
        params = {"access_token": self.access_token}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "data" in data:
            instagram_sub = None
            for sub in data["data"]:
                if sub["object"] == "instagram":
                    instagram_sub = sub
                    break
            
            if instagram_sub:
                required_fields = ["messages", "messaging_seen"]
                optional_fields = ["messaging_handovers", "standby"]
                
                active_fields = instagram_sub.get("fields", [])
                missing_required = [f for f in required_fields if f not in active_fields]
                
                result = {
                    "status": "CONFIGURED" if not missing_required else "INCOMPLETE",
                    "callback_url": instagram_sub.get("callback_url"),
                    "active_fields": active_fields,
                    "missing_required_fields": missing_required,
                    "has_optional_fields": {
                        field: field in active_fields for field in optional_fields
                    }
                }
            else:
                result = {"status": "NOT_CONFIGURED", "message": "No Instagram subscription found"}
            
            self.results.append(("Webhook Subscriptions", result))
            return result
        else:
            error_result = {"status": "ERROR", "error": data.get("error", "Unknown error")}
            self.results.append(("Webhook Subscriptions", error_result))
            return error_result
    
    def check_page_subscribed_apps(self, page_id: str) -> Dict:
        """Check if the app is properly subscribed to the page"""
        url = f"{self.graph_url}/{page_id}/subscribed_apps"
        params = {"access_token": self.access_token}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "data" in data:
            apps = data.get("data", [])
            result = {
                "status": "SUBSCRIBED" if apps else "NOT_SUBSCRIBED",
                "subscribed_apps": apps,
                "count": len(apps)
            }
            
            # Check subscription fields for each app
            for app in apps:
                if "subscribed_fields" in app:
                    app["missing_fields"] = [
                        f for f in ["messages", "messaging_seen"] 
                        if f not in app["subscribed_fields"]
                    ]
            
            self.results.append(("Page Subscriptions", result))
            return result
        else:
            error_result = {"status": "ERROR", "error": data.get("error", "Unknown error")}
            self.results.append(("Page Subscriptions", error_result))
            return error_result
    
    def test_send_message(self, instagram_account_id: str, recipient_id: str) -> Dict:
        """Test outbound message capability"""
        url = f"{self.graph_url}/{instagram_account_id}/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": f"Test message from SupaAgent - {datetime.now().isoformat()}"}
        }
        
        headers = {"Content-Type": "application/json"}
        params = {"access_token": self.access_token}
        
        response = requests.post(url, json=payload, headers=headers, params=params)
        data = response.json()
        
        if "message_id" in data:
            result = {"status": "SUCCESS", "message_id": data["message_id"]}
        else:
            result = {"status": "FAILED", "error": data.get("error", "Unknown error")}
        
        self.results.append(("Outbound Message Test", result))
        return result
    
    def generate_report(self) -> str:
        """Generate comprehensive diagnostic report"""
        report = [
            "=" * 60,
            "INSTAGRAM INTEGRATION DIAGNOSTIC REPORT",
            "=" * 60,
            f"Generated: {datetime.now().isoformat()}",
            ""
        ]
        
        for test_name, result in self.results:
            report.append(f"\n{test_name}:")
            report.append("-" * 40)
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, list):
                        report.append(f"  {key}:")
                        for item in value:
                            report.append(f"    - {item}")
                    elif isinstance(value, dict):
                        report.append(f"  {key}:")
                        for k, v in value.items():
                            report.append(f"    {k}: {v}")
                    else:
                        report.append(f"  {key}: {value}")
        
        # Add recommendations
        report.extend([
            "\n" + "=" * 60,
            "RECOMMENDATIONS:",
            "=" * 60
        ])
        
        # Check for critical missing permission
        for test_name, result in self.results:
            if test_name == "Token Permissions" and result.get("status") == "MISSING_PERMISSIONS":
                if "pages_manage_metadata" in result.get("missing_permissions", []):
                    report.extend([
                        "\n🚨 CRITICAL ISSUE FOUND:",
                        "Missing 'pages_manage_metadata' permission!",
                        "",
                        "REQUIRED ACTION - Nuclear Reset:",
                        "1. Go to SupaAgent Dashboard > Settings > Integrations",
                        "2. Click 'Delete' on Instagram integration",
                        "3. Go to Facebook Business Settings > Business Integrations",
                        "4. Find 'SupaAgent' and click 'Remove'",
                        "5. Clear browser cache/cookies for facebook.com",
                        "6. Re-connect Instagram in SupaAgent Dashboard",
                        "7. When permission dialog appears:",
                        "   - Ensure ALL checkboxes are selected",
                        "   - Look specifically for 'Manage Page Metadata'",
                        "   - Take a screenshot before confirming",
                        "8. Test with this script again to verify"
                    ])
                    break
        
        return "\n".join(report)

def main():
    # Load configuration
    config_file = "instagram_config.json"
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
    else:
        print("Please create instagram_config.json with:")
        print(json.dumps({
            "access_token": "YOUR_ACCESS_TOKEN",
            "app_id": "YOUR_APP_ID",
            "page_id": "YOUR_PAGE_ID",
            "instagram_account_id": "YOUR_INSTAGRAM_ACCOUNT_ID",
            "test_recipient_id": "TEST_USER_ID (optional)"
        }, indent=2))
        return
    
    verifier = InstagramPermissionVerifier(config["access_token"])
    
    print("Running Instagram Integration Diagnostics...")
    print("=" * 60)
    
    # Run all checks
    print("1. Checking token permissions...")
    verifier.check_token_permissions()
    
    print("2. Verifying webhook subscriptions...")
    verifier.check_webhook_subscriptions(config["app_id"])
    
    print("3. Checking page subscriptions...")
    verifier.check_page_subscribed_apps(config["page_id"])
    
    if config.get("test_recipient_id"):
        print("4. Testing outbound message...")
        verifier.test_send_message(
            config["instagram_account_id"],
            config["test_recipient_id"]
        )
    
    # Generate and save report
    report = verifier.generate_report()
    
    report_file = f"instagram_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"\n{report}")
    print(f"\nReport saved to: {report_file}")

if __name__ == "__main__":
    main()