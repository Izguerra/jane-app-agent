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
    
    # FAST PATH: For simple greetings, DON'T send a filler. 
    # The main agent has an optimized fast-path for these and will respond in < 1s.
    greetings = ["hi", "hello", "hey", "hola", "how are you"]
    if msg_clean in greetings:
        return ""
    
    # If it's a very short message but not a greeting, use a generic "On it"
    if len(msg_clean) < 10:
        return "Sure! Let me look into that... "

    try:
        ack = await asyncio.wait_for(
            _call_fast_llm(user_message),
            timeout=timeout
        )
        if ack and len(ack.strip()) > 5:
            return ack.strip() + " "
    except asyncio.TimeoutError:
        logger.debug("Acknowledgement LLM timed out, using fallback")
    except Exception as e:
        logger.debug(f"Acknowledgement LLM error: {e}, using fallback")
    
    return random.choice(FALLBACK_PHRASES) + " "


def get_followup_phrase() -> str:
    """Get a random follow-up phrase for when the agent takes longer than expected."""
    return random.choice(FOLLOWUP_PHRASES)


async def stream_with_followup(
    response_generator,
    initial_ack: str,
    followup_delay: float = 4.0,
    second_followup_delay: float = 8.0,
):
    """
    Async generator that wraps a response stream with timed follow-up
    acknowledgements. If no chunks arrive within `followup_delay` seconds
    after the initial ack, a follow-up phrase is injected.
    
    Args:
        response_generator: The async generator from the agent
        initial_ack: The initial acknowledgement already yielded
        followup_delay: Seconds to wait before first follow-up (default 4s)
        second_followup_delay: Seconds to wait before second follow-up (default 8s)
    
    Yields:
        Text chunks — including injected follow-up phrases
    """
    full_content = initial_ack
    first_real_chunk_received = False
    followup_sent = False
    second_followup_sent = False
    start_time = time.monotonic()
    
    # We use an asyncio.Queue to race between chunks and timeouts
    chunk_queue: asyncio.Queue = asyncio.Queue()
    stream_done = asyncio.Event()
    
    async def _consume_stream():
        """Read chunks from the generator and push to queue."""
        try:
            async for chunk in response_generator:
                is_tool_call = False
                # Detect tool calls in Agno RunResponse (chunk)
                if hasattr(chunk, 'tools') and chunk.tools:
                    is_tool_call = True
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    is_tool_call = True

                if chunk and hasattr(chunk, 'content') and chunk.content:
                    await chunk_queue.put(chunk.content)
                elif is_tool_call:
                    # Signal that a tool is active to postpone follow-ups
                    logger.debug(f"Detected Tool Call chunk from Agno. Postponing fillers.")
                    await chunk_queue.put("TOOL_RUNNING_SENTINEL")
                else:
                    # Maybe it's a metadata chunk (usage, etc) — ignore unless it's the end
                    pass
        except Exception as e:
            logger.error(f"Error in chatbot stream consumption: {e}")
            await chunk_queue.put(f"Error: {e}")
        finally:
            stream_done.set()
            # Push sentinel to unblock any waiting get()
            await chunk_queue.put(None)
    
    # Start consuming the stream in background
    consumer_task = asyncio.create_task(_consume_stream())
    
    try:
        while True:
            # Calculate appropriate timeout based on what we've sent
            elapsed = time.monotonic() - start_time
            
            if not first_real_chunk_received and not followup_sent and elapsed < followup_delay:
                wait_time = followup_delay - elapsed
            elif not first_real_chunk_received and followup_sent and not second_followup_sent and elapsed < second_followup_delay:
                wait_time = second_followup_delay - elapsed
            else:
                wait_time = 30.0  # Long timeout — just wait for chunks
            
            try:
                content = await asyncio.wait_for(chunk_queue.get(), timeout=max(0.1, wait_time))
                
                if content is None:
                    # Stream finished
                    break
                
                if content == "TOOL_RUNNING_SENTINEL":
                    # Extend the wait time and don't yield anything
                    start_time = time.monotonic() # Reset timer because agent is active
                    followup_delay += 2.0 # Give it more breathing room for tools
                    continue
                
                first_real_chunk_received = True
                full_content += content
                yield content
                
            except asyncio.TimeoutError:
                # No chunk arrived in time — inject follow-up
                if not first_real_chunk_received and not followup_sent:
                    followup = get_followup_phrase()
                    full_content += followup
                    followup_sent = True
                    yield followup
                elif not first_real_chunk_received and followup_sent and not second_followup_sent:
                    second_followup = "\n\nAlmost there, just a few more seconds..."
                    full_content += second_followup
                    second_followup_sent = True
                    yield second_followup
                
                # Check if stream is done
                if stream_done.is_set() and chunk_queue.empty():
                    break
    finally:
        # Ensure consumer is cleaned up
        if not consumer_task.done():
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
    
    # The caller is already building the full_content string, so we just finish here


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
