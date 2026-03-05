"""
Progress-aware tool wrapper for voice and avatar agents.

Automatically sends acknowledgments and progress updates during long-running operations.
"""

import asyncio
import time
import random
from typing import Callable, List, Optional
import logging

logger = logging.getLogger(__name__)


class ProgressAwareToolWrapper:
    """
    Wraps agent tools to provide automatic progress acknowledgments
    for voice and avatar agents.
    """
    
    def __init__(
        self,
        tool: Callable,
        session,  # AgentSession or MultimodalAgent
        tool_name: str,
        acknowledgment_phrases: Optional[List[str]] = None,
        progress_threshold: float = 5.0,  # seconds
        progress_interval: float = 5.0,   # seconds
    ):
        self.tool = tool
        self.session = session
        self.tool_name = tool_name
        self.progress_threshold = progress_threshold
        self.progress_interval = progress_interval
        
        # Default acknowledgment phrases
        self.acknowledgment_phrases = acknowledgment_phrases or [
            "Let me check that for you...",
            "Sure, give me just a moment...",
            "Looking into that now...",
            "Let me find that information...",
        ]
        
        # Tool-specific phrases
        self.tool_specific_phrases = {
            "search_calendar": ["Let me check the calendar...", "Checking your schedule..."],
            "book_appointment": ["Let me book that for you...", "Setting up your appointment..."],
            "send_email": ["Sending that email now...", "Let me send that for you..."],
            "search_products": ["Searching our products...", "Let me find that for you..."],
            "run_task_now": ["Running that task now...", "Let me take care of that..."],
            "dispatch_worker_task": ["Starting that background job...", "I'll get that started for you..."],
            "dispatch_to_openclaw": ["Opening the browser now...", "Let me navigate to that for you..."],
        }
    
    async def __call__(self, *args, **kwargs):
        """Execute tool with progress acknowledgments"""
        
        # 1. Send immediate acknowledgment
        phrases = self.tool_specific_phrases.get(
            self.tool_name, 
            self.acknowledgment_phrases
        )
        phrase = random.choice(phrases)
        
        try:
            await self._say(phrase)
        except Exception as e:
            logger.warning(f"Failed to send acknowledgment: {e}")
        
        # 2. Start progress monitoring
        start_time = time.time()
        progress_task = asyncio.create_task(
            self._monitor_progress(start_time)
        )
        
        try:
            # 3. Execute the actual tool
            logger.info(f"Executing tool: {self.tool_name}")
            result = await self.tool(*args, **kwargs)
            
            elapsed = time.time() - start_time
            logger.info(f"Tool {self.tool_name} completed in {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Tool {self.tool_name} failed: {e}")
            raise
            
        finally:
            # 4. Cancel progress monitoring
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_progress(self, start_time: float):
        """Send periodic progress updates"""
        try:
            # Wait for initial threshold
            await asyncio.sleep(self.progress_threshold)
            
            # First progress update
            await self._say("Still working on that...")
            
            # Continue monitoring
            while True:
                await asyncio.sleep(self.progress_interval)
                
                elapsed = time.time() - start_time
                
                if elapsed > 15:
                    await self._say(
                        "This is taking a bit longer than expected. "
                        "I'm still processing your request."
                    )
                elif elapsed > 10:
                    await self._say("Almost there...")
                    
        except asyncio.CancelledError:
            # Normal cancellation when tool completes
            pass
        except Exception as e:
            logger.error(f"Progress monitoring error: {e}")
    
    async def _say(self, message: str):
        """Send message to user via session"""
        try:
            if hasattr(self.session, 'say'):
                # VoicePipelineAgent (AgentSession)
                self.session.say(message, allow_interruptions=False)
            elif hasattr(self.session, 'response') and hasattr(self.session.response, 'create'):
                # MultimodalAgent (xAI/Grok)
                await self.session.response.create(
                    type="message",
                    role="assistant",
                    content=[{"type": "text", "text": message}]
                )
            else:
                logger.warning(f"Session type {type(self.session)} doesn't support .say() or .response.create()")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
