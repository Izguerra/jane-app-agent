import asyncio
import re

def clean_address(addr: str) -> str:
    # 1. Handle Canadian Postal codes with spaces (L 9 T 0 E 2 -> L9T0E2)
    # Find patterns like "L 9 T 0 E 2" and collapse them
    # Look for 6 individual characters separated by optional spaces
    addr = re.sub(r'([A-Z])\s*(\d)\s*([A-Z])\s*(\d)\s*([A-Z])\s*(\d)', r'\1\2\3\4\5\6', addr, flags=re.IGNORECASE)
    
    # 2. Handle hyphens (L9T-0E2 -> L9T0E2)
    addr = addr.replace("-", "")
    
    # 3. Clean up extra internal spaces
    addr = " ".join(addr.split())
    return addr

def test_sanitization():
    test_cases = [
        ("L 9 T 0 E 2", "L9T0E2"),
        ("l 9 t 0 e 2", "l9t0e2"),
        ("L9T-0E2", "L9T0E2"),
        ("L9T 0E2", "L9T 0E2"), # Should ideally remain or be collapsed? re.sub only hits individual letters.
        ("Toronto to L 9 T 0 E 2", "Toronto to L9T0E2"),
        ("CN Tower to L9T-0E2", "CN Tower to L9T0E2"),
        ("L  9  T  0  E  2", "L9T0E2"),
    ]
    
    for input_str, expected in test_cases:
        actual = clean_address(input_str)
        print(f"Input: '{input_str}' -> Actual: '{actual}' | Match: {actual.lower() == expected.lower()}")

if __name__ == "__main__":
    test_sanitization()
