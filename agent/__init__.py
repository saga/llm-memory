"""Agent layer - Exports"""

from agent.agent import create_memory_agent, default_agent
from agent.tools import register_memory_tools
from agent.prompts import (
    get_system_prompt,
    get_memory_context_prompt,
    SYSTEM_PROMPT,
    MEMORY_RETENTION_POLICY
)

__all__ = [
    "create_memory_agent",
    "default_agent",
    "register_memory_tools",
    "get_system_prompt",
    "get_memory_context_prompt",
    "SYSTEM_PROMPT",
    "MEMORY_RETENTION_POLICY",
]
