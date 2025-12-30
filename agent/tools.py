"""
Agent Tools - PydanticAI tool definitions

Critical design:
- Tools operate on Agent state (MemoryState)
- Tools DO NOT directly write to vector DB
- Actual persistence happens AFTER agent run (in chat flow)

This prevents:
- Hallucinated memories being stored
- Race conditions
- Inconsistent state
"""

from pydantic_ai import RunContext
from memory.models import MemoryState, MemoryUpdate, MemoryItem
from datetime import datetime
from uuid import uuid4


def register_memory_tools(agent):
    """
    Register all memory-related tools with the agent
    
    Call this after creating the agent instance
    """
    
    @agent.tool
    def update_memory(
        ctx: RunContext[MemoryState],
        update: MemoryUpdate
    ) -> str:
        """
        Store new memories for future conversations
        
        Use this when:
        - User shares preferences, facts, or important information
        - You learn something worth remembering
        - User makes a decision or commitment
        
        Args:
            update: Memory update containing new memories, type, and importance
        
        Returns:
            Confirmation message
        """
        # Add new memories to agent state (NOT to vector DB yet!)
        for text in update.new_memories:
            memory_item = MemoryItem(
                id=uuid4().hex,
                content=text,
                type=update.memory_type,
                importance=update.importance,
                created_at=datetime.utcnow()
            )
            ctx.deps.active_memories.append(memory_item)
        
        count = len(update.new_memories)
        return f"Added {count} new {update.memory_type} memory(ies) to remember for next time."
    
    @agent.tool
    def search_memories(
        ctx: RunContext[MemoryState],
        query: str,
        memory_type: str | None = None
    ) -> str:
        """
        Search existing memories (already loaded in active_memories)
        
        Note: This searches the CURRENT active_memories, not the full vector DB.
        Active memories are pre-loaded based on conversation context.
        
        Args:
            query: What to search for
            memory_type: Optional filter by type (semantic, preference, fact)
        
        Returns:
            Formatted list of matching memories
        """
        memories = ctx.deps.active_memories
        
        if memory_type:
            memories = [m for m in memories if m.type == memory_type]
        
        # Simple text matching (active memories are already relevant via vector search)
        query_lower = query.lower()
        matching = [
            m for m in memories
            if query_lower in m.content.lower()
        ]
        
        if not matching:
            return f"No memories found matching '{query}'"
        
        result_lines = [f"Found {len(matching)} matching memories:"]
        for mem in matching:
            result_lines.append(
                f"- [{mem.type}] {mem.content} (importance: {mem.importance:.1f})"
            )
        
        return "\n".join(result_lines)
    
    @agent.tool
    def list_active_memories(
        ctx: RunContext[MemoryState]
    ) -> str:
        """
        List all currently active memories
        
        Use this to:
        - Review what you remember about this conversation
        - Check for duplicates before creating new memories
        - Reference specific memories
        
        Returns:
            Formatted list of active memories
        """
        memories = ctx.deps.active_memories
        
        if not memories:
            return "No active memories for this conversation."
        
        result_lines = [f"Active memories ({len(memories)} total):"]
        
        # Group by type
        by_type = {}
        for mem in memories:
            by_type.setdefault(mem.type, []).append(mem)
        
        for mem_type, mems in sorted(by_type.items()):
            result_lines.append(f"\n{mem_type.upper()}:")
            for mem in mems:
                result_lines.append(f"  - {mem.content} (importance: {mem.importance:.1f})")
        
        return "\n".join(result_lines)


# Export for easy import
__all__ = ["register_memory_tools"]
