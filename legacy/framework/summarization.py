"""
Memory Summarization Module
Provides strategies and utilities for compressing and consolidating memories.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from framework.state import AgentState, MemoryEntry, MemoryType, SummarizationTrigger
import hashlib


class SummarizationConfig:
    """Configuration for memory summarization policies."""
    
    def __init__(
        self,
        trigger: SummarizationTrigger = SummarizationTrigger.HYBRID,
        max_episodic_age_hours: float = 24.0,
        max_episodic_count: int = 20,
        max_total_tokens: int = 4000,
        min_memories_to_summarize: int = 3,
        preserve_recent_count: int = 5,
        preserve_high_importance: bool = True,
        importance_threshold: float = 0.8
    ):
        self.trigger = trigger
        self.max_episodic_age_hours = max_episodic_age_hours
        self.max_episodic_count = max_episodic_count
        self.max_total_tokens = max_total_tokens
        self.min_memories_to_summarize = min_memories_to_summarize
        self.preserve_recent_count = preserve_recent_count
        self.preserve_high_importance = preserve_high_importance
        self.importance_threshold = importance_threshold


def should_trigger_summarization(state: AgentState, config: SummarizationConfig) -> Tuple[bool, str]:
    """Check if summarization should be triggered based on policy.
    
    Returns:
        (should_trigger, reason)
    """
    episodic_memories = state.get_memories_by_type(MemoryType.EPISODIC)
    
    if len(episodic_memories) < config.min_memories_to_summarize:
        return False, "not_enough_memories"
    
    # Count-based trigger
    if config.trigger in [SummarizationTrigger.COUNT_BASED, SummarizationTrigger.HYBRID]:
        if len(episodic_memories) > config.max_episodic_count:
            return True, "count_exceeded"
    
    # Time-based trigger
    if config.trigger in [SummarizationTrigger.TIME_BASED, SummarizationTrigger.HYBRID]:
        cutoff_time = datetime.utcnow() - timedelta(hours=config.max_episodic_age_hours)
        old_memories = [m for m in episodic_memories if m.timestamp < cutoff_time]
        if len(old_memories) >= config.min_memories_to_summarize:
            return True, "time_exceeded"
    
    # Token-based trigger
    if config.trigger in [SummarizationTrigger.TOKEN_BASED, SummarizationTrigger.HYBRID]:
        total_tokens = sum(m.estimate_tokens() for m in episodic_memories)
        if total_tokens > config.max_total_tokens:
            return True, "token_limit_exceeded"
    
    return False, "no_trigger"


def select_memories_for_summarization(
    state: AgentState,
    config: SummarizationConfig
) -> List[MemoryEntry]:
    """Select which memories should be summarized.
    
    Strategy:
    1. Preserve recent memories (configurable count)
    2. Preserve high-importance memories (if enabled)
    3. Select older, lower-importance episodic memories for summarization
    """
    episodic_memories = state.get_memories_by_type(MemoryType.EPISODIC)
    
    if len(episodic_memories) < config.min_memories_to_summarize:
        return []
    
    # Sort by timestamp (newest first)
    sorted_memories = sorted(episodic_memories, key=lambda m: m.timestamp, reverse=True)
    
    # Preserve recent memories
    preserve_ids = set()
    for mem in sorted_memories[:config.preserve_recent_count]:
        preserve_ids.add(mem.id)
    
    # Preserve high-importance memories
    if config.preserve_high_importance:
        for mem in episodic_memories:
            if mem.importance_score >= config.importance_threshold:
                preserve_ids.add(mem.id)
    
    # Select memories for summarization (older, lower importance, not preserved)
    candidates = [
        mem for mem in sorted_memories
        if mem.id not in preserve_ids and not mem.is_summarized
    ]
    
    return candidates


def generate_memory_summary(memories: List[MemoryEntry], use_llm: bool = False) -> str:
    """Generate a summary of multiple memories.
    
    Args:
        memories: List of memories to summarize
        use_llm: If True, would use LLM for summarization (placeholder for now)
    
    Returns:
        Summary text
    """
    if not memories:
        return ""
    
    if use_llm:
        # Placeholder for LLM-based summarization
        # In production, this would call an LLM to generate a coherent summary
        return _llm_summarize(memories)
    else:
        # Simple extraction-based summarization
        return _extractive_summarize(memories)


def _extractive_summarize(memories: List[MemoryEntry]) -> str:
    """Simple extractive summarization (no LLM required)."""
    if len(memories) == 1:
        return memories[0].content
    
    # Group by time periods
    sorted_memories = sorted(memories, key=lambda m: m.timestamp)
    
    start_time = sorted_memories[0].timestamp
    end_time = sorted_memories[-1].timestamp
    
    # Extract key information
    summary_parts = [
        f"[摘要] {len(memories)}条对话记录 ({start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')})"
    ]
    
    # Include high-importance or frequently accessed memories
    key_memories = sorted(memories, key=lambda m: (m.importance_score, m.access_count), reverse=True)[:3]
    
    for i, mem in enumerate(key_memories, 1):
        content_preview = mem.content[:100].replace('\n', ' ')
        summary_parts.append(f"  {i}. {content_preview}...")
    
    if len(memories) > 3:
        summary_parts.append(f"  ... 还有 {len(memories) - 3} 条相关对话")
    
    return '\n'.join(summary_parts)


def _llm_summarize(memories: List[MemoryEntry]) -> str:
    """LLM-based summarization (placeholder for future implementation).
    
    In production, this would:
    1. Prepare conversation context
    2. Call LLM with summarization prompt
    3. Return coherent, information-dense summary
    """
    # Prepare context for LLM
    conversation_history = []
    for mem in sorted(memories, key=lambda m: m.timestamp):
        conversation_history.append(mem.content)
    
    context = '\n\n'.join(conversation_history)
    
    # Placeholder: In real implementation, call LLM here
    # Example prompt:
    # """
    # 请总结以下对话历史，保留关键信息和重要细节：
    # 
    # {context}
    # 
    # 总结应该：
    # 1. 简洁但信息密度高
    # 2. 保留用户的关键需求和偏好
    # 3. 保留重要的事实和决策
    # """
    
    # For now, fall back to extractive
    return _extractive_summarize(memories)


def consolidate_memories(
    state: AgentState,
    memories_to_consolidate: List[MemoryEntry],
    summary_content: str
) -> MemoryEntry:
    """Create a consolidated summary memory and mark originals as summarized.
    
    Args:
        state: Current agent state
        memories_to_consolidate: List of memories to consolidate
        summary_content: The summary text
    
    Returns:
        New consolidated memory entry
    """
    if not memories_to_consolidate:
        raise ValueError("No memories to consolidate")
    
    # Create consolidated memory
    source_ids = [m.id for m in memories_to_consolidate]
    
    # Calculate consolidated importance (weighted average)
    total_importance = sum(m.importance_score for m in memories_to_consolidate)
    avg_importance = total_importance / len(memories_to_consolidate)
    
    # Use earliest timestamp
    earliest_time = min(m.timestamp for m in memories_to_consolidate)
    
    # Create memory ID
    memory_id = hashlib.md5(
        f"{summary_content}_{earliest_time.isoformat()}".encode()
    ).hexdigest()[:16]
    
    memory_hash = hashlib.sha256(summary_content.encode()).hexdigest()
    
    consolidated_memory = MemoryEntry(
        id=memory_id,
        content=summary_content,
        context=state.context,
        timestamp=earliest_time,
        metadata={
            "consolidation_count": len(memories_to_consolidate),
            "consolidation_time": datetime.utcnow().isoformat(),
            "original_token_estimate": sum(m.estimate_tokens() for m in memories_to_consolidate)
        },
        hash=memory_hash,
        message_type=memories_to_consolidate[0].message_type,
        memory_type=MemoryType.EPISODIC,
        importance_score=avg_importance,
        access_count=0,
        last_accessed=None,
        is_summarized=True,
        original_content=None,
        summarized_at=datetime.utcnow(),
        source_memory_ids=source_ids,
        token_estimate=len(summary_content) // 4
    )
    
    return consolidated_memory


def compress_memories(
    state: AgentState,
    config: Optional[SummarizationConfig] = None,
    use_llm: bool = False
) -> Tuple[AgentState, Dict[str, Any]]:
    """Main function to compress and consolidate memories.
    
    Args:
        state: Current agent state
        config: Summarization configuration
        use_llm: Whether to use LLM for summarization
    
    Returns:
        (new_state, compression_stats)
    """
    if config is None:
        config = SummarizationConfig()
    
    new_state = state.model_copy(deep=True)
    
    # Check if summarization should be triggered
    should_trigger, reason = should_trigger_summarization(new_state, config)
    
    if not should_trigger:
        return new_state, {
            "triggered": False,
            "reason": reason,
            "memories_compressed": 0,
            "tokens_saved": 0
        }
    
    # Select memories for summarization
    memories_to_summarize = select_memories_for_summarization(new_state, config)
    
    if not memories_to_summarize:
        return new_state, {
            "triggered": True,
            "reason": reason,
            "memories_compressed": 0,
            "tokens_saved": 0
        }
    
    # Calculate original token count
    original_tokens = sum(m.estimate_tokens() for m in memories_to_summarize)
    
    # Generate summary
    summary_content = generate_memory_summary(memories_to_summarize, use_llm=use_llm)
    
    # Create consolidated memory
    consolidated_memory = consolidate_memories(
        new_state,
        memories_to_summarize,
        summary_content
    )
    
    # Remove original memories and add consolidated one
    for mem in memories_to_summarize:
        if mem.id in new_state.memories:
            del new_state.memories[mem.id]
    
    new_state.add_memory(consolidated_memory)
    
    # Calculate compression stats
    new_tokens = consolidated_memory.estimate_tokens()
    tokens_saved = original_tokens - new_tokens
    compression_ratio = (1 - new_tokens / original_tokens) * 100 if original_tokens > 0 else 0
    
    stats = {
        "triggered": True,
        "reason": reason,
        "memories_compressed": len(memories_to_summarize),
        "original_tokens": original_tokens,
        "new_tokens": new_tokens,
        "tokens_saved": tokens_saved,
        "compression_ratio": round(compression_ratio, 2),
        "consolidated_memory_id": consolidated_memory.id
    }
    
    return new_state, stats


def get_compression_stats(state: AgentState) -> Dict[str, Any]:
    """Get statistics about memory compression."""
    all_memories = list(state.memories.values())
    summarized_memories = [m for m in all_memories if m.is_summarized]
    
    total_tokens = sum(m.estimate_tokens() for m in all_memories)
    summarized_tokens = sum(m.estimate_tokens() for m in summarized_memories)
    
    original_tokens_estimate = sum(
        m.metadata.get("original_token_estimate", m.estimate_tokens())
        for m in summarized_memories
    )
    
    return {
        "total_memories": len(all_memories),
        "summarized_memories": len(summarized_memories),
        "summarization_rate": round(len(summarized_memories) / len(all_memories) * 100, 2) if all_memories else 0,
        "total_tokens": total_tokens,
        "estimated_tokens_saved": original_tokens_estimate - summarized_tokens,
        "average_compression_ratio": round(
            (1 - summarized_tokens / original_tokens_estimate) * 100, 2
        ) if original_tokens_estimate > 0 else 0
    }
