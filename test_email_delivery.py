import os
import resend
from dotenv import load_dotenv

load_dotenv()

def test_email():
    api_key = os.getenv("RESEND_API")
    from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
    to_email = "randy@supaagent.com"
    
    print(f"Testing email with API key: {api_key[:5]}...")
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    
    resend.api_key = api_key
    try:
        r = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": "Test Email from JaneApp Agent",
            "html": "<p>Hello Randy, this is a test email to verify Resend delivery.</p>"
        })
        print(f"Success! Result: {r}")
    except Exception as e:
        print(f"Failure: {e}")

if __name__ == "__main__":
    test_email()
