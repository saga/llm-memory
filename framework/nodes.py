from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from framework.state import AgentState, MessageRole, MessageType, MemoryEntry, MemoryType


# ===== Memory Retrieval Strategies =====

def retrieve_semantic_memories(state: AgentState, query: str, top_k: int = 3) -> List[MemoryEntry]:
    """Retrieve semantic memories using content relevance.
    
    For semantic memories (facts, concepts), we prioritize:
    1. High importance score
    2. Frequently accessed (high access_count)
    3. Content similarity (simple keyword matching, can be enhanced with embeddings)
    """
    semantic_memories = [
        mem for mem in state.memories.values()
        if mem.memory_type == MemoryType.SEMANTIC
    ]
    
    if not semantic_memories:
        return []
    
    # Score memories based on importance and access patterns
    scored_memories = []
    query_lower = query.lower()
    
    for mem in semantic_memories:
        score = mem.importance_score * 0.6  # Base importance weight
        score += min(mem.access_count / 10.0, 0.3)  # Access frequency (capped at 0.3)
        
        # Simple keyword matching (can be enhanced with semantic embeddings)
        if any(word in mem.content.lower() for word in query_lower.split()):
            score += 0.1
        
        scored_memories.append((score, mem))
    
    # Sort by score and return top_k
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    return [mem for _, mem in scored_memories[:top_k]]


def retrieve_episodic_memories(state: AgentState, recent_n: int = 5, 
                               max_age_hours: Optional[float] = None) -> List[MemoryEntry]:
    """Retrieve episodic memories using time-based ordering.
    
    For episodic memories (conversations, events), we prioritize:
    1. Recency (most recent first)
    2. Optionally filter by time window
    3. Can be summarized for efficiency
    """
    episodic_memories = [
        mem for mem in state.memories.values()
        if mem.memory_type == MemoryType.EPISODIC
    ]
    
    if not episodic_memories:
        return []
    
    # Filter by age if specified
    if max_age_hours is not None:
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        episodic_memories = [
            mem for mem in episodic_memories
            if mem.timestamp.timestamp() >= cutoff_time
        ]
    
    # Sort by timestamp (most recent first)
    episodic_memories.sort(key=lambda x: x.timestamp, reverse=True)
    return episodic_memories[:recent_n]


def retrieve_procedural_memories(state: AgentState, context: Optional[str] = None) -> List[MemoryEntry]:
    """Retrieve procedural memories (behavioral patterns, preferences).
    
    For procedural memories (preferences, style rules), we prioritize:
    1. Context matching
    2. High importance score
    3. All relevant procedures (typically small set)
    """
    procedural_memories = [
        mem for mem in state.memories.values()
        if mem.memory_type == MemoryType.PROCEDURAL
    ]
    
    if not procedural_memories:
        return []
    
    # Filter by context if specified
    if context:
        procedural_memories = [
            mem for mem in procedural_memories
            if mem.context == context or mem.context == "default"
        ]
    
    # Sort by importance score
    procedural_memories.sort(key=lambda x: x.importance_score, reverse=True)
    return procedural_memories


def retrieve_mixed_memories(state: AgentState, query: str, top_k: int = 5) -> List[MemoryEntry]:
    """Intelligent mixed retrieval combining all memory types.
    
    Balances different memory types:
    - 40% semantic (facts relevant to query)
    - 40% episodic (recent context)
    - 20% procedural (behavioral preferences)
    """
    results = []
    
    # Get memories from each type
    semantic = retrieve_semantic_memories(state, query, top_k=2)
    episodic = retrieve_episodic_memories(state, recent_n=2)
    procedural = retrieve_procedural_memories(state, context=state.context)
    
    # Combine with priority
    results.extend(semantic)
    results.extend(episodic)
    results.extend(procedural[:1])  # Top procedural memory
    
    # Remove duplicates and limit to top_k
    seen_ids = set()
    unique_results = []
    for mem in results:
        if mem.id not in seen_ids:
            seen_ids.add(mem.id)
            unique_results.append(mem)
    
    return unique_results[:top_k]


# ===== Node Functions =====



def planner_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    latest_message = new_state.get_latest_message()
    if not latest_message or latest_message.role != MessageRole.USER:
        return new_state
    new_state.decision = "general"
    new_state.add_message(
        role=MessageRole.SYSTEM,
        content=f"路由决策: {new_state.decision}",
        message_type=MessageType.SYSTEM_MESSAGE
    )
    new_state.increment_step()
    return new_state


def memory_recall_node(state: AgentState) -> AgentState:
    """Enhanced memory recall with type-specific retrieval strategies."""
    new_state = state.model_copy(deep=True)
    latest_message = new_state.get_latest_message()
    
    if not latest_message:
        return new_state
    
    # Use intelligent mixed retrieval for conversational context
    recalled_memories = retrieve_mixed_memories(
        new_state,
        query=latest_message.content,
        top_k=5
    )
    
    # Mark memories as accessed
    for mem in recalled_memories:
        if mem.id in new_state.memories:
            new_state.memories[mem.id].increment_access()
    
    recalled_count = len(recalled_memories)
    
    if recalled_count:
        # Build detailed recall metadata
        memory_breakdown = {
            "semantic": sum(1 for m in recalled_memories if m.memory_type == MemoryType.SEMANTIC),
            "episodic": sum(1 for m in recalled_memories if m.memory_type == MemoryType.EPISODIC),
            "procedural": sum(1 for m in recalled_memories if m.memory_type == MemoryType.PROCEDURAL)
        }
        
        new_state.add_message(
            role=MessageRole.SYSTEM,
            content=f"召回 {recalled_count} 条记忆 (语义: {memory_breakdown['semantic']}, "
                   f"情节: {memory_breakdown['episodic']}, 程序: {memory_breakdown['procedural']})",
            message_type=MessageType.MEMORY_RECALL,
            metadata={
                "recalled_count": recalled_count,
                "memory_breakdown": memory_breakdown,
                "memory_ids": [m.id for m in recalled_memories]
            }
        )
    
    new_state.increment_step()
    return new_state


def decision_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    new_state.set_status("processing")
    new_state.increment_step()
    return new_state


def response_generator_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    if not user_messages:
        return new_state
    latest_user_message = user_messages[-1]
    response_content = generate_general_response(new_state, latest_user_message.content)
    new_state.add_message(
        role=MessageRole.ASSISTANT,
        content=response_content,
        message_type=MessageType.ASSISTANT_RESPONSE
    )
    new_state.increment_step()
    return new_state


def memory_storage_node(state: AgentState) -> AgentState:
    """Store memories with intelligent type classification."""
    new_state = state.model_copy(deep=True)
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    
    if user_messages and assistant_messages:
        user_content = user_messages[-1].content
        assistant_content = assistant_messages[-1].content
        
        # Intelligent memory type classification
        memory_type, importance_score = classify_memory_type(user_content, assistant_content)
        
        memory_content = f"用户: {user_content}\\n助手: {assistant_content}"
        memory_entry = create_memory_entry(
            content=memory_content,
            context=new_state.context,
            message_type=MessageType.USER_INPUT,
            metadata={"decision": new_state.decision},
            memory_type=memory_type,
            importance_score=importance_score
        )
        new_state.add_memory(memory_entry)
    
    new_state.increment_step()
    return new_state


def classify_memory_type(user_input: str, assistant_response: str) -> tuple[MemoryType, float]:
    """Classify memory type and importance based on content.
    
    Heuristic classification (can be enhanced with LLM):
    - SEMANTIC: Contains definitions, facts, or explanations
    - PROCEDURAL: Contains preferences, instructions, or rules
    - EPISODIC: General conversation and events (default)
    
    Returns:
        (memory_type, importance_score)
    """
    user_lower = user_input.lower()
    
    # Keywords for semantic memories (facts, definitions)
    semantic_keywords = ['是什么', '定义', '解释', '什么是', 'what is', 'define', 'explain']
    
    # Keywords for procedural memories (preferences, rules)
    procedural_keywords = ['我喜欢', '我想要', '帮我', '总是', '不要', '偏好', 
                          'i prefer', 'i like', 'always', 'never', 'please']
    
    # Keywords for high importance
    importance_keywords = ['重要', '关键', '必须', '一定', 'important', 'critical', 'must']
    
    # Classify type
    if any(keyword in user_lower for keyword in semantic_keywords):
        memory_type = MemoryType.SEMANTIC
        base_importance = 0.7
    elif any(keyword in user_lower for keyword in procedural_keywords):
        memory_type = MemoryType.PROCEDURAL
        base_importance = 0.8  # Preferences are generally important
    else:
        memory_type = MemoryType.EPISODIC
        base_importance = 0.5
    
    # Adjust importance based on keywords
    importance_boost = 0.2 if any(keyword in user_lower for keyword in importance_keywords) else 0.0
    importance_score = min(1.0, base_importance + importance_boost)
    
    return memory_type, importance_score


def create_memory_entry(content: str, context: str, message_type: MessageType,
                       metadata: Optional[Dict[str, Any]] = None,
                       memory_type: MemoryType = MemoryType.EPISODIC,
                       importance_score: float = 0.5) -> MemoryEntry:
    """Create a memory entry with enhanced metadata.
    
    Args:
        content: Memory content
        context: Context identifier
        message_type: Type of message this memory relates to
        metadata: Additional metadata dictionary
        memory_type: Type of memory (semantic/episodic/procedural)
        importance_score: Importance score from 0.0 to 1.0
    
    Returns:
        MemoryEntry with all fields populated
    """
    memory_id = hashlib.md5(f"{content}_{context}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
    memory_hash = hashlib.sha256(f"{content}_{context}".encode()).hexdigest()
    timestamp = datetime.utcnow()
    
    return MemoryEntry(
        id=memory_id,
        content=content,
        context=context,
        timestamp=timestamp,
        metadata=metadata or {},
        hash=memory_hash,
        message_type=message_type,
        memory_type=memory_type,
        importance_score=importance_score,
        access_count=0,
        last_accessed=None
    )


def generate_general_response(state: AgentState, user_input: str) -> str:
    return "我理解您的问题。作为AI助手，我会尽力为您提供准确和有用的信息。"
