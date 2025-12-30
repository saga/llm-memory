"""
PydanticAI Agent Definition

Core architecture:
- Agent operates on MemoryState (working memory)
- Memory retrieval happens BEFORE agent run
- Memory persistence happens AFTER agent run
- Agent is stateless - state is passed in each run

This design ensures:
- No hallucinated memories in vector DB
- Clean separation between logic and storage
- Easy testing and debugging
"""

from pydantic_ai import Agent
from memory.models import MemoryState
from agent.prompts import get_system_prompt
from agent.tools import register_memory_tools


def create_memory_agent(
    model: str = "openai:gpt-4",
    custom_instructions: str | None = None
) -> Agent[MemoryState]:
    """
    Create a PydanticAI agent with memory capabilities
    
    Args:
        model: Model identifier (e.g., "openai:gpt-4", "anthropic:claude-3")
        custom_instructions: Additional system prompt instructions
    
    Returns:
        Configured Agent instance
    """
    # Get system prompt
    system_prompt = get_system_prompt(custom_instructions)
    
    # Create agent with MemoryState as state type
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        deps_type=MemoryState,  # Agent operates on MemoryState
        retries=2  # Retry on failures
    )
    
    # Register memory tools
    register_memory_tools(agent)
    
    return agent


# Default agent instance (can be imported directly)
default_agent = create_memory_agent()


# Export
__all__ = ["create_memory_agent", "default_agent"]
