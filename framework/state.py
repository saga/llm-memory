from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import hashlib
import json


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    USER_INPUT = "user_input"
    ASSISTANT_RESPONSE = "assistant_response"
    SYSTEM_MESSAGE = "system_message"
    MEMORY_RECALL = "memory_recall"


class MemoryType(str, Enum):
    """Memory types following cognitive science classification.
    
    SEMANTIC: Facts, concepts, and general knowledge (relatively stable)
    EPISODIC: Events, conversations, and specific experiences (time-bound)
    PROCEDURAL: Behavioral patterns, preferences, and style rules
    """
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"


class SummarizationTrigger(str, Enum):
    """Conditions that trigger memory summarization."""
    TIME_BASED = "time_based"        # Summarize after certain time period
    COUNT_BASED = "count_based"      # Summarize after N memories
    TOKEN_BASED = "token_based"      # Summarize when token count exceeds threshold
    MANUAL = "manual"                # Manually triggered
    HYBRID = "hybrid"                # Combination of triggers


class Message(BaseModel):
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.USER_INPUT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        validate_assignment = True
        use_enum_values = True


class MemoryEntry(BaseModel):
    id: str
    content: str
    context: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    hash: str
    message_type: MessageType = MessageType.USER_INPUT
    
    # Enhanced fields for advanced memory management
    memory_type: MemoryType = Field(default=MemoryType.EPISODIC)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0, ge=0)
    last_accessed: Optional[datetime] = None
    
    # Summarization fields
    is_summarized: bool = Field(default=False)
    original_content: Optional[str] = None
    summarized_at: Optional[datetime] = None
    source_memory_ids: List[str] = Field(default_factory=list)  # IDs of memories this summary consolidates
    token_estimate: Optional[int] = None  # Estimated token count
    
    class Config:
        validate_assignment = True
        use_enum_values = True
    
    def increment_access(self) -> None:
        """Track memory access for retrieval optimization."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def summarize(self, summary_content: str, source_ids: Optional[List[str]] = None) -> None:
        """Mark memory as summarized and store original content."""
        if not self.is_summarized:
            self.original_content = self.content
        self.content = summary_content
        self.is_summarized = True
        self.summarized_at = datetime.utcnow()
        if source_ids:
            self.source_memory_ids = source_ids
    
    def estimate_tokens(self) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)."""
        if self.token_estimate is not None:
            return self.token_estimate
        self.token_estimate = len(self.content) // 4
        return self.token_estimate


class AgentState(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    memories: Dict[str, MemoryEntry] = Field(default_factory=dict)
    facts: Dict[str, str] = Field(default_factory=dict)

    step: int = Field(default=0, ge=0)
    status: Literal["idle", "processing", "waiting_input", "error", "complete"] = "idle"
    decision: Optional[str] = None

    session_id: str = Field(default="")
    user_id: Optional[str] = None
    context: str = Field(default="default")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_assignment = True
        use_enum_values = True

    @field_validator('step')
    def validate_step(cls, v):
        if v < 0:
            raise ValueError('step must be non-negative')
        return v

    def compute_hash(self) -> str:
        state_dict = self.model_dump(exclude={'last_updated'})
        state_json = json.dumps(state_dict, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()

    def add_message(self, role: MessageRole, content: str,
                    message_type: MessageType = MessageType.USER_INPUT,
                    metadata: Optional[Dict[str, Any]] = None) -> Message:
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_updated = datetime.utcnow()
        return message

    def add_fact(self, key: str, value: str) -> None:
        self.facts[key] = value
        self.last_updated = datetime.utcnow()

    def get_fact(self, key: str) -> Optional[str]:
        return self.facts.get(key)

    def add_memory(self, memory: MemoryEntry) -> None:
        self.memories[memory.id] = memory
        self.last_updated = datetime.utcnow()

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        return self.memories.get(memory_id)

    def get_messages_by_role(self, role: MessageRole) -> List[Message]:
        return [msg for msg in self.messages if msg.role == role]

    def get_latest_message(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None

    def increment_step(self) -> int:
        self.step += 1
        self.last_updated = datetime.utcnow()
        return self.step

    def set_status(self, status: Literal["idle", "processing", "waiting_input", "error", "complete"]) -> None:
        self.status = status
        self.last_updated = datetime.utcnow()

    def get_audit_info(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "step": self.step,
            "status": self.status,
            "message_count": len(self.messages),
            "memory_count": len(self.memories),
            "fact_count": len(self.facts),
            "last_updated": self.last_updated.isoformat(),
            "context": self.context
        }
    
    def get_memories_by_type(self, memory_type: 'MemoryType') -> List[MemoryEntry]:
        """Get all memories of a specific type."""
        return [mem for mem in self.memories.values() if mem.memory_type == memory_type]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        memories_list = list(self.memories.values())
        
        if not memories_list:
            return {
                "total": 0,
                "by_type": {},
                "avg_importance": 0.0,
                "most_accessed": None
            }
        
        semantic_count = sum(1 for m in memories_list if m.memory_type == MemoryType.SEMANTIC)
        episodic_count = sum(1 for m in memories_list if m.memory_type == MemoryType.EPISODIC)
        procedural_count = sum(1 for m in memories_list if m.memory_type == MemoryType.PROCEDURAL)
        
        avg_importance = sum(m.importance_score for m in memories_list) / len(memories_list)
        most_accessed = max(memories_list, key=lambda m: m.access_count)
        
        return {
            "total": len(memories_list),
            "by_type": {
                "semantic": semantic_count,
                "episodic": episodic_count,
                "procedural": procedural_count
            },
            "avg_importance": round(avg_importance, 3),
            "most_accessed": {
                "id": most_accessed.id,
                "type": most_accessed.memory_type,
                "access_count": most_accessed.access_count
            }
        }
