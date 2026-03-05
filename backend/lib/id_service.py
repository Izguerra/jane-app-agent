import time
import os
import string
import random

# Standard Base62 Alphabet (0-9, A-Z, a-z)
# This order (0..9, A..Z, a..z) preserves ASCII sort order logic reasonably well for ID generation
# provided we PAD the timestamp component.
ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase

def base62_encode(num: int, min_length: int = 0) -> str:
    """Encode an integer to Base62 string."""
    if num == 0:
        return ALPHABET[0] * max(1, min_length)
    
    arr = []
    base = len(ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    
    arr.reverse()
    encoded = ''.join(arr)
    
    # Pad with leading zeros if necessary to maintain sort order for timestamps
    if len(encoded) < min_length:
        encoded = ALPHABET[0] * (min_length - len(encoded)) + encoded
        
    return encoded

class IdService:
    @staticmethod
    def generate(prefix: str) -> str:
        """
        Generate a prefixed, K-Sortable ID.
        Format: {prefix}_{timestamp_8chars}{random_16chars}
        
        The timestamp is 48-bit milliseconds, Base62 encoded, and PADDED to 10 chars.
        This ensures string sorting == chronological sorting.
        """
        # 1. Timestamp (Milliseconds)
        # 48 bits covers ~8900 years.
        timestamp_ms = int(time.time() * 1000)
        
        # Encode Timestamp (Pad to 10 chars to ensure "000..." < "zzz...")
        # 2^48 in base62 is roughly 8 chars, 10 is safe margin.
        ts_part = base62_encode(timestamp_ms, min_length=10)
        
        # 2. Entropy (Randomness)
        # We want ~16 chars of randomness for uniqueness.
        # 16 Base62 chars is ~95 bits of entropy.
        rand_bytes = os.urandom(12) # 96 bits
        rand_int = int.from_bytes(rand_bytes, 'big')
        rand_part = base62_encode(rand_int, min_length=16)
        
        # Ensure strict length limit if needed, but ~26 chars is fine.
        return f"{prefix}_{ts_part}{rand_part}"

    @staticmethod
    def prefixes():
        """Registry of official prefixes for reference."""
        return {
            "organization": "org",
            "workspace": "wrk",
            "team_member": "mem",
            "integration": "int",
            "agent": "agnt",
            "customer": "cust",
            "communication": "comm",
            "phone_call": "call",
            "transcription": "tran",
            "appointment": "appt",
            "deal": "deal",
            "document": "doc",
            "phone_number": "phn",
            "message": "msg",
            "template": "tmpl",
            "reminder": "rem",
            "order": "ord",
            "product": "prod",
            "invoice": "inv",
            "file": "file",
            "email": "mail",
            "calendar_event": "evt",
            "guest": "guest",
            "skill": "skll",
            "agent_skill": "askl",
            "agent_personality": "psnl",
            "workspace_llm_config": "lcfg"
        }
