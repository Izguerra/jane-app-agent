"""
Dynamic Acknowledgement Service

Generates context-aware, natural acknowledgement phrases using a fast LLM call.
These are yielded immediately to the user while the main agent processes the request,
creating the perception of near-instant response times.

Also provides timed follow-up acknowledgements when the agent takes longer than expected.
"""
import os
import asyncio
import random
import logging
import time

logger = logging.getLogger(__name__)

# Fallback phrases in case the LLM call fails or times out
FALLBACK_PHRASES = [
    "Great question! Let me look into that for you...",
    "Good question — checking on that now...",
    "Sure thing! Give me just a moment...",
    "On it! Let me pull that up...",
    "Absolutely, let me find that out for you...",
    "Interesting question! Let me check...",
    "Let me dig into that real quick...",
    "Working on that for you now...",
    "Great, let me get the details on that...",
    "One sec — looking into it!",
]

# Follow-up phrases when the agent takes longer than expected
FOLLOWUP_PHRASES = [
    "\n\nStill working on this — almost there...",
    "\n\nThis is taking a bit longer than usual, hang tight...",
    "\n\nStill pulling the details together for you...",
    "\n\nJust a little more time — getting a thorough answer...",
    "\n\nApologies for the wait, nearly done...",
    "\n\nGathering the best info for you, one more moment...",
    "\n\nAlmost got it — just finishing up...",
    "\n\nThanks for your patience, wrapping this up now...",
]


GREETING_MAP = {
    "hi": "Hello! How can I help you today?",
    "hello": "Hi there! What can I do for you?",
    "hey": "Hey! How's it going? How can I assist?",
    "how are you": "I'm doing great, thank you! How can I help you today?",
    "how are you?": "I'm doing great, thank you! How can I help you today?",
    "thanks": "You're very welcome!",
    "thank you": "You're very welcome!",
}

async def generate_dynamic_acknowledgement(user_message: str, timeout: float = 1.0) -> str:
    """
    Generate a dynamic, context-aware acknowledgement phrase using a fast LLM.
    
    This runs as a quick side-call (< 1.0s) while the main agent processes
    the user's actual request. If the LLM call exceeds the timeout, we
    fall back to a random pre-written phrase.
    """
    msg_clean = user_message.strip().lower().replace("?", "").replace(".", "").replace("!", "")
    
    # FAST PATH: For simple greetings, send a pre-canned friendly response.
    # The main agent will still generate a completion, but this ensures an immediate bubble.
    greetings = ["hi", "hello", "hey", "hola", "how are you", "how are you?"]
    if msg_clean in greetings:
        return GREETING_MAP.get(msg_clean, "Hello! How can I assist you today? ")
    
    # If it's a very short message but not a greeting, use a generic "On it"
    if len(msg_clean) < 10:
        return "Sure! Let me look into that... "

    try:
        ack = await asyncio.wait_for(
            _call_fast_llm(user_message),
            timeout=timeout
        )
        if ack and len(ack.strip()) > 5:
            return ack.strip()
    except asyncio.TimeoutError:
        logger.debug("Acknowledgement LLM timed out, using fallback")
    except Exception as e:
        logger.debug(f"Acknowledgement LLM error: {e}, using fallback")
    
    return random.choice(FALLBACK_PHRASES)


def get_followup_phrase() -> str:
    """Get a random follow-up phrase for when the agent takes longer than expected."""
    return random.choice(FOLLOWUP_PHRASES)


async def stream_with_followup(
    response_generator,
    initial_ack: str,
    followup_delay: float = 4.0,
    second_followup_delay: float = 8.0
):
    """
    Async generator that wraps a response stream with timed follow-up
    acknowledgements. 
    
    CRITICAL FIX: This uses a single-loop approach with anext() + wait_for 
    to maintain the same async task and cancel scope, preventing
    'RuntimeError: Attempted to exit cancel scope in a different task'
    which occurs when using a separate background drain task with AnyIO/MCP.
    """
    first_real_chunk_received = False
    followup_sent = False
    second_followup_sent = False
    
    # CRITICAL FIX: Ensure we have an async iterator for anext()
    try:
        response_iterator = response_generator.__aiter__()
    except AttributeError:
        # Fallback if it's already an iterator or doesn't support __aiter__
        response_iterator = response_generator

    # initial_ack should be yielded by the CALLER (e.g. routers/chat.py) 
    # if they want immediate feedback, to prevent double-yielding in the 
    # combined stream content.

    start_time = asyncio.get_event_loop().time()
    buffer = "" # Phase 20 Fix: Local buffer for prefix stripping
    
    try:
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Determine wait timeout based on follow-up delays
            wait_time = None
            if not first_real_chunk_received:
                if not followup_sent:
                    wait_time = max(0.1, followup_delay - elapsed)
                elif not second_followup_sent:
                    wait_time = max(0.1, second_followup_delay - elapsed)
            
            try:
                # Use anext() for Python 3.10+ compatibility
                if wait_time is not None:
                    chunk = await asyncio.wait_for(anext(response_iterator), timeout=wait_time)
                else:
                    chunk = await anext(response_iterator)
                
                if chunk:
                    content = None
                    if hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content
                    elif isinstance(chunk, str):
                        content = chunk
                    else:
                        # Fallback for unexpected types (like Agno RunResponse if passed)
                        # If it's a tool call (like Agno Action), content might be empty
                        content = getattr(chunk, 'content', None)
                    
                    if content:
                        if not first_real_chunk_received and initial_ack:
                            # Phase 20 Fix: BUFFER chunks until we can determine if they match the initial_ack
                            buffer += content
                            
                            def normalize_for_comp(t):
                                if not t: return ""
                                import re
                                # Remove all non-alphanumeric characters to be ultra-robust against punctuation/spacing differences
                                return re.sub(r'[^a-zA-Z0-9]', '', t).lower()
                            
                            b_norm = normalize_for_comp(buffer)
                            a_norm = normalize_for_comp(initial_ack)
                            
                            logger.info(f"Prefix Check: buffer_norm='{b_norm}', ack_norm='{a_norm}'")
                            
                            # If buffer is still shorter than ack, and looks like a match so far, keep buffering
                            if len(b_norm) < len(a_norm) and a_norm.startswith(b_norm):
                                logger.info(f"Buffering prefix chunk: '{content}'")
                                continue
                                
                            # If it matches the full ack, strip it
                            if a_norm and b_norm.startswith(a_norm):
                                logger.info(f"MATCH FOUND: Stripping '{initial_ack}' from buffer")
                                content = buffer[len(initial_ack):].lstrip()
                                first_real_chunk_received = True
                                if not content:
                                    continue
                            else:
                                # Doesn't match, yield the whole buffer and stop stripping
                                logger.info(f"Prefix MISMATCH. Yielding whole buffer: '{buffer}'")
                                content = buffer
                                first_real_chunk_received = True
                        
                        first_real_chunk_received = True
                        logger.debug(f"Streaming chunk: {len(content)} chars")
                        yield content
                    elif not first_real_chunk_received:
                        # If it's a tool call chunk and no text yet, yield a thought indicator
                        # to keep the bubble alive and prevent "empty bubble" perception
                        logger.debug("Received tool call or empty chunk before first text. Yielding indicator.")
                        yield " " # Just a space to keep it alive
                        
            except asyncio.TimeoutError:
                # Inject follow-up if we haven't received anything yet
                if not first_real_chunk_received:
                    if not followup_sent:
                        followup_sent = True
                        logger.debug("Yielding first follow-up acknowledgment")
                        yield get_followup_phrase()
                    elif not second_followup_sent:
                        second_followup_sent = True
                        logger.debug("Yielding second follow-up acknowledgment")
                        yield "\n\nAlmost there, just a few more seconds..."
                        
            except StopAsyncIteration:
                # Generator finished
                break
                
    except Exception as e:
        logger.error(f"Error in stream_with_followup: {e}", exc_info=True)
        yield f"\n[Error: {str(e)}]"


async def _call_fast_llm(user_message: str) -> str:
    """
    Make a minimal, ultra-fast LLM call to generate a brief acknowledgement.
    Uses the fastest available model with very low max_tokens.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    system_prompt = (
        "You are generating a brief, natural acknowledgement phrase for a customer service AI assistant. "
        "The user just asked a question, and you need to generate a SHORT (1 sentence max, under 12 words) "
        "acknowledgement that: \n"
        "1. Feels natural and conversational\n"
        "2. Is contextually relevant to what they asked\n"
        "3. Indicates you're working on getting the answer\n"
        "4. NEVER starts with 'I' — vary your openings\n"
        "5. Uses varied, friendly language — NOT robotic\n\n"
        "Examples of great acknowledgements:\n"
        "- 'Great question! Let me check on that...'\n"
        "- 'Sure thing, looking into that now...'\n"
        "- 'On it! Give me just a second...'\n"
        "- 'Absolutely, let me pull that up for you...'\n"
        "- 'Good one — checking on that right now...'\n\n"
        "RESPOND WITH ONLY THE ACKNOWLEDGEMENT PHRASE. Nothing else."
    )
    
    if gemini_key:
        return await _call_gemini(gemini_key, system_prompt, user_message)
    elif openai_key:
        return await _call_openai(openai_key, system_prompt, user_message)
    else:
        return random.choice(FALLBACK_PHRASES)


async def _call_gemini(api_key: str, system_prompt: str, user_message: str) -> str:
    """Ultra-fast Gemini Flash call for acknowledgement generation."""
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=150,
            temperature=0.9,
        )
    )
    
    # Run in executor since google-generativeai is sync
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: model.generate_content(f"User asked: {user_message}")
    )
    return response.text


async def _call_openai(api_key: str, system_prompt: str, user_message: str) -> str:
    """Ultra-fast OpenAI call for acknowledgement generation."""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=30,
        temperature=0.9,
    )
    return response.choices[0].message.content
