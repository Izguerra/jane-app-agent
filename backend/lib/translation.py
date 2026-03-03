import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=100)
def translate_text(text: str, target_language: str) -> str:
    """
    Translates text to the target language using Mistral.
    Results are cached to improve performance and reduce costs.
    """
    if not text or not target_language or target_language == "en":
        return text

    try:
        from backend.lib.ai_client import get_ai_client
        client, model_name = get_ai_client(async_mode=False)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a professional translator. Translate the following text to {target_language}. Return ONLY the translated text, no explanations."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text
