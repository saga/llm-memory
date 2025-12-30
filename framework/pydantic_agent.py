"""
PydanticAI-based Memory Agent
Simplified implementation using PydanticAI framework
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName

from framework.state import AgentState, MemoryEntry, MemoryType, MessageRole, MessageType
from framework.summarization import compress_memories, SummarizationConfig


# ===== Dependencies =====

class MemoryDeps(BaseModel):
    """Dependencies for the memory agent"""
    state: AgentState
    summarization_config: Optional[SummarizationConfig] = None
    enable_summarization: bool = False


# ===== Agent Definition =====

memory_agent = Agent(
    'openai:gpt-4o-mini',
    deps_type=MemoryDeps,
    result_type=str,
    system_prompt=(
        "You are a helpful AI assistant with long-term memory capabilities. "
        "You can remember previous conversations and user preferences. "
        "Use the provided tools to recall and store memories effectively."
    ),
)


# ===== Tools =====

@memory_agent.tool
async def recall_memories(
    ctx: RunContext[MemoryDeps],
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 5
) -> str:
    """Recall relevant memories based on query.
    
    Args:
        ctx: Runtime context with state
        query: Search query for memories
        memory_type: Filter by memory type (semantic/episodic/procedural)
        limit: Maximum number of memories to return
    
    Returns:
        Formatted string of recalled memories
    """
    state = ctx.deps.state
    
    if memory_type:
        # Filter by type
        try:
            mem_type = MemoryType(memory_type.lower())
            memories = state.get_memories_by_type(mem_type)
        except ValueError:
            return f"Invalid memory type: {memory_type}"
    else:
        memories = list(state.memories.values())
    
    if not memories:
        return "No memories found."
    
    # Simple relevance scoring
    scored_memories = []
    query_lower = query.lower()
    
    for mem in memories:
        score = mem.importance_score
        if any(word in mem.content.lower() for word in query_lower.split()):
            score += 0.5
        scored_memories.append((score, mem))
    
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    top_memories = scored_memories[:limit]
    
    # Format output
    result_lines = [f"Found {len(top_memories)} relevant memories:\n"]
    for i, (score, mem) in enumerate(top_memories, 1):
        mem.increment_access()
        result_lines.append(
            f"{i}. [{mem.memory_type.value}] {mem.content[:100]}... "
            f"(importance: {mem.importance_score:.2f})"
        )
    
    return "\n".join(result_lines)


@memory_agent.tool
async def store_memory(
    ctx: RunContext[MemoryDeps],
    content: str,
    memory_type: str = "episodic",
    importance: float = 0.5
) -> str:
    """Store a new memory.
    
    Args:
        ctx: Runtime context with state
        content: Memory content to store
        memory_type: Type of memory (semantic/episodic/procedural)
        importance: Importance score 0.0-1.0
    
    Returns:
        Confirmation message
    """
    state = ctx.deps.state
    
    try:
        mem_type = MemoryType(memory_type.lower())
    except ValueError:
        return f"Invalid memory type: {memory_type}. Use semantic, episodic, or procedural."
    
    # Create memory
    memory_id = hashlib.md5(
        f"{content}_{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16]
    
    memory = MemoryEntry(
        id=memory_id,
        content=content,
        context=state.context,
        timestamp=datetime.utcnow(),
        metadata={},
        hash=hashlib.sha256(content.encode()).hexdigest(),
        message_type=MessageType.ASSISTANT_RESPONSE,
        memory_type=mem_type,
        importance_score=min(max(importance, 0.0), 1.0),
        access_count=0,
        last_accessed=None
    )
    
    state.add_memory(memory)
    
    # Trigger summarization if enabled
    if ctx.deps.enable_summarization:
        config = ctx.deps.summarization_config or SummarizationConfig()
        new_state, stats = compress_memories(state, config=config)
        if stats['triggered']:
            ctx.deps.state = new_state
            return (
                f"Memory stored successfully (ID: {memory_id}). "
                f"Auto-compression triggered: {stats['memories_compressed']} memories "
                f"compressed, saved {stats['tokens_saved']} tokens."
            )
    
    return f"Memory stored successfully as {mem_type.value} (ID: {memory_id})"


@memory_agent.tool
async def get_memory_stats(ctx: RunContext[MemoryDeps]) -> str:
    """Get statistics about stored memories.
    
    Args:
        ctx: Runtime context with state
    
    Returns:
        Formatted memory statistics
    """
    state = ctx.deps.state
    stats = state.get_memory_stats()
    
    result = [
        f"Memory Statistics:",
        f"  Total memories: {stats['total']}",
        f"  By type:",
        f"    - Semantic: {stats['by_type']['semantic']}",
        f"    - Episodic: {stats['by_type']['episodic']}",
        f"    - Procedural: {stats['by_type']['procedural']}",
        f"  Average importance: {stats['avg_importance']:.3f}",
    ]
    
    if stats['most_accessed']:
        result.append(
            f"  Most accessed: {stats['most_accessed']['type']} "
            f"({stats['most_accessed']['access_count']} times)"
        )
    
    return "\n".join(result)


@memory_agent.tool
async def compress_old_memories(ctx: RunContext[MemoryDeps]) -> str:
    """Manually trigger memory compression to save tokens.
    
    Args:
        ctx: Runtime context with state
    
    Returns:
        Compression results
    """
    state = ctx.deps.state
    config = ctx.deps.summarization_config or SummarizationConfig()
    
    new_state, stats = compress_memories(state, config=config)
    
    if not stats['triggered']:
        return f"Compression not triggered: {stats['reason']}"
    
    ctx.deps.state = new_state
    
    return (
        f"Compression completed:\n"
        f"  Memories compressed: {stats['memories_compressed']}\n"
        f"  Tokens saved: {stats['tokens_saved']} ({stats['compression_ratio']}%)\n"
        f"  New total: {len(new_state.memories)} memories"
    )


# ===== System Prompt Customization =====

@memory_agent.system_prompt
async def add_memory_context(ctx: RunContext[MemoryDeps]) -> str:
    """Add current memory state to system prompt."""
    state = ctx.deps.state
    stats = state.get_memory_stats()
    
    # Get recent episodic memories for context
    episodic = state.get_memories_by_type(MemoryType.EPISODIC)
    recent = sorted(episodic, key=lambda m: m.timestamp, reverse=True)[:3]
    
    # Get important procedural memories (user preferences)
    procedural = state.get_memories_by_type(MemoryType.PROCEDURAL)
    prefs = sorted(procedural, key=lambda m: m.importance_score, reverse=True)[:2]
    
    context_parts = [
        f"Current session: {state.session_id}",
        f"Total memories: {stats['total']}",
    ]
    
    if recent:
        context_parts.append("\nRecent conversation context:")
        for mem in recent:
            context_parts.append(f"  - {mem.content[:80]}...")
    
    if prefs:
        context_parts.append("\nUser preferences:")
        for pref in prefs:
            context_parts.append(f"  - {pref.content}")
    
    return "\n".join(context_parts)


# ===== Helper Functions =====

import hashlib


async def run_agent_with_memory(
    user_input: str,
    state: AgentState,
    model: KnownModelName = 'openai:gpt-4o-mini',
    enable_summarization: bool = False,
    summarization_config: Optional[SummarizationConfig] = None
) -> tuple[str, AgentState]:
    """Run the memory agent with given input.
    
    Args:
        user_input: User's message
        state: Current agent state
        model: Model to use
        enable_summarization: Whether to enable auto-summarization
        summarization_config: Custom summarization configuration
    
    Returns:
        Tuple of (response, updated_state)
    """
    # Add user message to state
    state.add_message(MessageRole.USER, user_input)
    
    # Create dependencies
    deps = MemoryDeps(
        state=state,
        enable_summarization=enable_summarization,
        summarization_config=summarization_config
    )
    
    # Run agent
    result = await memory_agent.run(user_input, deps=deps)
    
    # Add assistant response to state
    state.add_message(MessageRole.ASSISTANT, result.data)
    
    # Return response and updated state
    return result.data, deps.state


# ===== Simplified Workflow =====

class MemoryAgentWorkflow:
    """Simplified workflow using PydanticAI agent"""
    
    def __init__(
        self,
        model: KnownModelName = 'openai:gpt-4o-mini',
        enable_summarization: bool = True,
        summarization_config: Optional[SummarizationConfig] = None
    ):
        self.model = model
        self.enable_summarization = enable_summarization
        self.summarization_config = summarization_config or SummarizationConfig()
        self.sessions: Dict[str, AgentState] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session"""
        import uuid
        session_id = session_id or str(uuid.uuid4())
        self.sessions[session_id] = AgentState(session_id=session_id)
        return session_id
    
    async def chat(self, session_id: str, user_input: str) -> str:
        """Process a chat message"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        state = self.sessions[session_id]
        
        response, updated_state = await run_agent_with_memory(
            user_input=user_input,
            state=state,
            model=self.model,
            enable_summarization=self.enable_summarization,
            summarization_config=self.summarization_config
        )
        
        self.sessions[session_id] = updated_state
        return response
    
    def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Get session state"""
        return self.sessions.get(session_id)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session statistics"""
        state = self.sessions.get(session_id)
        if not state:
            return None
        
        return {
            "session_id": session_id,
            "message_count": len(state.messages),
            "memory_stats": state.get_memory_stats(),
            "status": state.status
        }
