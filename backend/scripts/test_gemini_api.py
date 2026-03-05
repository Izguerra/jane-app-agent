import os
import google.generativeai as genai

def test_gemini():
    gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not gemini_key:
        print("No GOOGLE_GEMINI_API_KEY found in env.")
        return
        
    print("Testing gemini-3-flash-preview initialization...")
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        print("Initialization successful.")
        
        print("Testing a simple prompt...")
        response = model.generate_content("Hello, are you online? Respond with just 'Yes.'")
        print(f"Response: {response.text}")
        print("Test complete.")
    except Exception as e:
        print(f"Error connecting to Gemini: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_gemini()
