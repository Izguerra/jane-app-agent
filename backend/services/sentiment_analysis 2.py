"""
Sentiment Analysis Service
Analyzes the sentiment of conversations using Mistral
"""
import os
import logging

logger = logging.getLogger(__name__)

def analyze_sentiment(text: str) -> str:
    """
    Analyze the sentiment of a conversation.
    
    Args:
        text: The conversation text to analyze
        
    Returns:
        str: 'positive', 'negative', or 'neutral'
    """
    if not text or len(text) < 10:
        return 'neutral'
    
    try:
        from backend.lib.ai_client import get_ai_client
        client, model_name = get_ai_client(async_mode=False)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system", 
                    "content": "Analyze the sentiment of this conversation. Respond with only one word: 'positive', 'negative', or 'neutral'."
                },
                {"role": "user", "content": text}
            ],
            max_tokens=10,
            temperature=0
        )
        
        sentiment = response.choices[0].message.content.strip().lower()
        
        # Validate response
        if sentiment in ['positive', 'negative', 'neutral']:
            logger.info(f"Sentiment analysis: {sentiment}")
            return sentiment
        else:
            logger.warning(f"Unexpected sentiment value: {sentiment}, defaulting to neutral")
            return 'neutral'
            
    except Exception as e:
        logger.error(f"Failed to analyze sentiment: {e}")
        return 'neutral'
