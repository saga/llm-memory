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

    class Config:
        validate_assignment = True
        use_enum_values = True


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
