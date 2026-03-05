"""
Enhanced Webhook Inspector for Instagram Integration
Provides deep inspection and logging of all Meta webhook events
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import hashlib
from pathlib import Path

class WebhookInspector:
    def __init__(self, log_dir: str = "webhook_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup detailed logging
        self.setup_logging()
        
        # Event statistics
        self.event_stats = {
            "total_events": 0,
            "message_events": 0,
            "empty_messages": 0,
            "read_receipts": 0,
            "standby_events": 0,
            "handover_events": 0,
            "unknown_events": 0
        }
    
    def setup_logging(self):
        """Configure comprehensive logging"""
        log_file = self.log_dir / f"webhook_inspector_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("WebhookInspector")
    
    def inspect_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Deep inspection of webhook payload"""
        self.event_stats["total_events"] += 1
        
        inspection_result = {
            "timestamp": datetime.now().isoformat(),
            "payload_size": len(json.dumps(payload)),
            "structure": self.analyze_structure(payload),
            "event_type": self.identify_event_type(payload),
            "has_message_content": False,
            "issues_detected": [],
            "recommendations": []
        }
        
        # Check for entry array
        if "entry" in payload:
            for entry in payload["entry"]:
                entry_analysis = self.analyze_entry(entry)
                inspection_result.update(entry_analysis)
        
        # Log the full payload for debugging
        self.log_payload(payload, inspection_result)
        
        # Generate recommendations based on findings
        inspection_result["recommendations"] = self.generate_recommendations(inspection_result)
        
        return inspection_result
    
    def analyze_structure(self, payload: Dict) -> Dict:
        """Analyze the structure of the payload"""
        structure = {
            "has_object": "object" in payload,
            "object_type": payload.get("object"),
            "has_entry": "entry" in payload,
            "entry_count": len(payload.get("entry", [])),
            "top_level_keys": list(payload.keys())
        }
        return structure
    
    def identify_event_type(self, payload: Dict) -> str:
        """Identify the type of webhook event"""
        if "object" not in payload:
            return "unknown"
        
        if payload["object"] == "instagram":
            if "entry" in payload:
                for entry in payload["entry"]:
                    if "messaging" in entry:
                        return "messaging"
                    elif "standby" in entry:
                        self.event_stats["standby_events"] += 1
                        return "standby"
                    elif "changes" in entry:
                        for change in entry["changes"]:
                            if change.get("field") == "messages":
                                return "messages"
        
        return "unknown"
    
    def analyze_entry(self, entry: Dict) -> Dict:
        """Analyze individual entry in the webhook payload"""
        result = {
            "entry_id": entry.get("id"),
            "entry_time": entry.get("time"),
            "messaging_events": [],
            "standby_events": [],
            "changes": []
        }
        
        # Check for messaging events
        if "messaging" in entry:
            for msg_event in entry["messaging"]:
                msg_analysis = self.analyze_messaging_event(msg_event)
                result["messaging_events"].append(msg_analysis)
                
                if msg_analysis["has_text_content"]:
                    result["has_message_content"] = True
                    self.event_stats["message_events"] += 1
                elif msg_analysis["is_read_receipt"]:
                    self.event_stats["read_receipts"] += 1
                else:
                    self.event_stats["empty_messages"] += 1
        
        # Check for standby events
        if "standby" in entry:
            for standby_event in entry["standby"]:
                result["standby_events"].append(self.analyze_standby_event(standby_event))
        
        # Check for changes (Graph API format)
        if "changes" in entry:
            for change in entry["changes"]:
                result["changes"].append(self.analyze_change(change))
        
        return result
    
    def analyze_messaging_event(self, event: Dict) -> Dict:
        """Analyze a messaging event"""
        analysis = {
            "sender_id": event.get("sender", {}).get("id"),
            "recipient_id": event.get("recipient", {}).get("id"),
            "timestamp": event.get("timestamp"),
            "has_message": "message" in event,
            "has_text_content": False,
            "is_read_receipt": False,
            "is_delivery": False,
            "message_content": None,
            "message_type": None
        }
        
        if "message" in event:
            msg = event["message"]
            analysis["message_id"] = msg.get("mid")
            
            if "text" in msg:
                analysis["has_text_content"] = True
                analysis["message_content"] = msg["text"]
                analysis["message_type"] = "text"
            elif "attachments" in msg:
                analysis["message_type"] = "attachment"
                analysis["attachments"] = msg["attachments"]
            elif "is_echo" in msg:
                analysis["message_type"] = "echo"
            else:
                # Empty message - this is the problem!
                analysis["message_type"] = "empty"
                analysis["issues_detected"] = ["Message object exists but has no content"]
        
        elif "read" in event:
            analysis["is_read_receipt"] = True
            analysis["watermark"] = event["read"].get("watermark")
        
        elif "delivery" in event:
            analysis["is_delivery"] = True
            analysis["watermark"] = event["delivery"].get("watermark")
        
        return analysis
    
    def analyze_standby_event(self, event: Dict) -> Dict:
        """Analyze a standby event"""
        return {
            "type": "standby",
            "sender_id": event.get("sender", {}).get("id"),
            "recipient_id": event.get("recipient", {}).get("id"),
            "timestamp": event.get("timestamp"),
            "has_message": "message" in event,
            "message_text": event.get("message", {}).get("text")
        }
    
    def analyze_change(self, change: Dict) -> Dict:
        """Analyze a change event (Graph API format)"""
        return {
            "field": change.get("field"),
            "value": change.get("value"),
            "verb": change.get("value", {}).get("verb")
        }
    
    def log_payload(self, payload: Dict, analysis: Dict):
        """Log the full payload and analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create unique filename based on payload hash
        payload_hash = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:8]
        
        # Save raw payload
        raw_file = self.log_dir / f"raw_{timestamp}_{payload_hash}.json"
        with open(raw_file, "w") as f:
            json.dump(payload, f, indent=2)
        
        # Save analysis
        analysis_file = self.log_dir / f"analysis_{timestamp}_{payload_hash}.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)
        
        # Log summary
        self.logger.info(f"Webhook event logged: {analysis['event_type']}")
        
        if analysis.get("issues_detected"):
            self.logger.warning(f"Issues detected: {analysis['issues_detected']}")
    
    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not analysis.get("has_message_content"):
            recommendations.append("No message content found - check token permissions")
            recommendations.append("Verify 'pages_manage_metadata' permission is granted")
        
        if analysis.get("standby_events"):
            recommendations.append("Standby events detected - app may be secondary receiver")
            recommendations.append("Enable Handover Protocol in Page settings or take thread control")
        
        if analysis["event_type"] == "unknown":
            recommendations.append("Unknown event type - review webhook subscription configuration")
        
        return recommendations
    
    def get_statistics(self) -> Dict:
        """Get current event statistics"""
        return {
            **self.event_stats,
            "empty_message_rate": (
                self.event_stats["empty_messages"] / max(self.event_stats["message_events"], 1)
            ) if self.event_stats["message_events"] > 0 else 0
        }
    
    def generate_report(self) -> str:
        """Generate a summary report"""
        stats = self.get_statistics()
        
        report = [
            "=" * 60,
            "WEBHOOK INSPECTION REPORT",
            "=" * 60,
            f"Generated: {datetime.now().isoformat()}",
            "",
            "EVENT STATISTICS:",
            f"  Total Events: {stats['total_events']}",
            f"  Message Events: {stats['message_events']}",
            f"  Empty Messages: {stats['empty_messages']}",
            f"  Read Receipts: {stats['read_receipts']}",
            f"  Standby Events: {stats['standby_events']}",
            f"  Unknown Events: {stats['unknown_events']}",
            "",
            "ANALYSIS:",
            f"  Empty Message Rate: {stats['empty_message_rate']:.2%}"
        ]
        
        if stats['empty_messages'] > 0:
            report.extend([
                "",
                "⚠️ WARNING: Empty messages detected!",
                "This indicates the 'One-Way Silence' issue.",
                "Recommended action: Perform Nuclear Reset to fix token permissions."
            ])
        
        return "\n".join(report)

# Integration with existing webhook handler
def integrate_with_webhook(inspector: WebhookInspector):
    """Example of how to integrate with your existing webhook handler"""
    
    def enhanced_webhook_handler(request_data: Dict) -> Dict:
        # Inspect the incoming payload
        inspection = inspector.inspect_payload(request_data)
        
        # Log any issues
        if inspection.get("issues_detected"):
            logging.warning(f"Webhook issues: {inspection['issues_detected']}")
        
        # Continue with normal processing
        # ... your existing webhook logic ...
        
        # Return inspection result for monitoring
        return inspection
    
    return enhanced_webhook_handler