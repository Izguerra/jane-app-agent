# Backend Prompts Package
"""
System prompts for agents and workers.
"""

from backend.prompts.worker_prompts import (
    ORCHESTRATOR_WORKER_INSTRUCTIONS,
    WORKER_REWARD_MODEL,
    JOB_SEARCH_WORKER_PROMPT,
    LEAD_RESEARCH_WORKER_PROMPT,
    CONTENT_WRITER_WORKER_PROMPT,
    get_worker_prompt
)
from backend.prompts.general import GATEKEEPER_INSTRUCTION
from backend.prompts.personal_assistant import PERSONAL_ASSISTANT_INSTRUCTION

__all__ = [
    "ORCHESTRATOR_WORKER_INSTRUCTIONS",
    "WORKER_REWARD_MODEL",
    "JOB_SEARCH_WORKER_PROMPT",
    "LEAD_RESEARCH_WORKER_PROMPT",
    "CONTENT_WRITER_WORKER_PROMPT",
    "get_worker_prompt",
    "GATEKEEPER_INSTRUCTION",
    "PERSONAL_ASSISTANT_INSTRUCTION"
]

