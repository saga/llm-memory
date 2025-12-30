"""
Memory Data Models - Pydantic schemas for memory management

Core Principle:
- MemoryState ≠ vector DB content
- MemoryState = Agent's working memory (what agent needs NOW)
- Vector DB = long-term storage (what agent CAN recall)
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """
    A single memory entry
    
    Used by:
    - Agent state (active memories)
    - Vector DB storage (via metadata)
    - Memory updates from LLM
    """
    id: str = Field(description="Unique memory identifier")
    content: str = Field(description="The actual memory content")
    type: Literal["semantic", "preference", "fact"] = Field(
        description="Memory category for retrieval optimization"
    )
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score (0-1) for retention policy"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp for recency scoring"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "mem_abc123",
                "content": "User prefers morning meetings",
                "type": "preference",
                "importance": 0.8,
                "created_at": "2025-12-30T10:00:00Z"
            }
        }


class MemoryState(BaseModel):
    """
    Agent's working memory state (NOT full vector DB)
    
    Design:
    - Only contains memories relevant to CURRENT conversation
    - Retrieved from vector DB at conversation start
    - Updated during conversation
    - Persisted back to vector DB after conversation
    
    Why separate from vector DB?
    - Agent shouldn't know about storage details
    - Working memory should be small (< 10 items)
    - Vector DB is "brain", state is "working memory"
    """
    recent_summary: str | None = Field(
        default=None,
        description="Compressed summary of recent conversation context"
    )
    active_memories: list[MemoryItem] = Field(
        default_factory=list,
        description="Currently active memories (retrieved + newly created)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recent_summary": "User asked about Python best practices",
                "active_memories": [
                    {
                        "id": "mem_001",
                        "content": "User is learning Python",
                        "type": "fact",
                        "importance": 0.7,
                        "created_at": "2025-12-30T09:00:00Z"
                    }
                ]
            }
        }


class MemoryUpdate(BaseModel):
    """
    Structured output from LLM for safe memory updates
    
    Why this exists:
    - LLM can't directly write to vector DB (hallucination risk)
    - Provides type-safe interface for memory creation
    - Allows validation before persistence
    """
    new_memories: list[str] = Field(
        default_factory=list,
        description="List of new memory contents to store"
    )
    memory_type: Literal["semantic", "preference", "fact"] = Field(
        default="semantic",
        description="Category for all new memories in this batch"
    )
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score for all new memories"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "new_memories": [
                    "User wants to learn PydanticAI",
                    "User prefers practical examples"
                ],
                "memory_type": "preference",
                "importance": 0.8
            }
        }
