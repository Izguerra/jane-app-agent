import re
import logging

class GuardrailService:
    def __init__(self):
        # Basic Regex patterns for PII
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        }
        
        # Guardrail Jailbreak/Hack patterns (simple keyword matching)
        self.unsafe_patterns = [
            r"ignore previous instructions",
            r"system overload",
            r"delete database",
            r"drop table"
        ]

    def detect_pii(self, text: str) -> dict:
        """Detects if PII exists in the text. Returns dict of findings."""
        findings = {}
        for key, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                findings[key] = len(matches)
        return findings

    def sanitize_output(self, text: str) -> str:
        """Redacts PII from agent responses."""
        if not text:
            return text
            
        sanitized = text
        # Redact Credit Cards & SSNs strictly
        for key in ["credit_card", "ssn"]:
            pattern = self.patterns[key]
            sanitized = re.sub(pattern, f"[REDACTED {key.upper()}]", sanitized)
            
        # Optional: We might want to keep emails/phones if they are part of the business context,
        # but for now, let's leave them unless we decide to implement strict PII masking mode.
        
        return sanitized

    def validate_input(self, text: str) -> bool:
        """
        Check for common jailbreak or unsafe patterns. 
        Returns True if safe, False if unsafe.
        """
        if not text:
            return True
            
        lower_text = text.lower()
        for pattern in self.unsafe_patterns:
            if re.search(pattern, lower_text):
                logging.warning(f"Guardrail Alert: Unsafe input pattern detected - '{pattern}'")
                return False
                
        return True
