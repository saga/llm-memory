"""
Memory Manager - Core business logic for memory operations

This is the most important module:
- Orchestrates vector store, embeddings, and scoring
- Implements memory lifecycle (create, retrieve, update, delete)
- Handles scoring logic (importance, recency, relevance)
- Enforces memory retention policies

Design principle: This module should outlive the Agent.
"""

from uuid import uuid4
from datetime import datetime
import time
from typing import Any

from memory.models import MemoryItem, MemoryUpdate
from memory.vector_store import VectorStore


class MemoryManager:
    """
    Central memory management system
    
    Responsibilities:
    1. Write memories to vector store (with embeddings)
    2. Retrieve relevant memories (semantic search + scoring)
    3. Score and filter memories (importance + recency + relevance)
    4. Enforce retention policies
    
    NOT responsible for:
    - LLM interactions (that's Agent's job)
    - API endpoints (that's API layer's job)
    - Prompt engineering (that's Agent's job)
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Any,  # Type: callable that takes str and returns list[float]
        max_active_memories: int = 10
    ):
        """
        Initialize memory manager
        
        Args:
            vector_store: Vector database instance
            embedder: Embedding function (infra.embedding.Embedder)
            max_active_memories: Max memories to return in one query
        """
        self.store = vector_store
        self.embedder = embedder
        self.max_active_memories = max_active_memories
    
    def write_memory(
        self,
        text: str,
        memory_type: str,
        importance: float = 0.5,
        user_id: str | None = None
    ) -> str:
        """
        Write a single memory to vector store
        
        Process:
        1. Generate embedding
        2. Create metadata
        3. Store in vector DB
        
        Args:
            text: Memory content
            memory_type: semantic, preference, or fact
            importance: 0.0 to 1.0
            user_id: Optional user identifier for multi-user systems
        
        Returns:
            Memory ID
        """
        memory_id = uuid4().hex
        
        # Generate embedding
        embedding = self.embedder.embed(text)
        
        # Prepare metadata
        metadata = {
            "type": memory_type,
            "importance": importance,
            "created_at": time.time(),  # Unix timestamp for easy calculation
        }
        
        if user_id:
            metadata["user_id"] = user_id
        
        # Store in vector DB
        self.store.add(
            id=memory_id,
            text=text,
            embedding=embedding,
            metadata=metadata
        )
        
        return memory_id
    
    def write_memories_batch(
        self,
        memory_updates: list[MemoryUpdate],
        user_id: str | None = None
    ) -> list[str]:
        """
        Batch write memories (more efficient than one-by-one)
        
        Use case:
        - Agent produces multiple memories in one turn
        - Initial data import
        """
        memory_ids = []
        
        for update in memory_updates:
            for text in update.new_memories:
                mem_id = self.write_memory(
                    text=text,
                    memory_type=update.memory_type,
                    importance=update.importance,
                    user_id=user_id
                )
                memory_ids.append(mem_id)
        
        return memory_ids
    
    def retrieve(
        self,
        query: str,
        k: int | None = None,
        memory_type: str | None = None,
        user_id: str | None = None
    ) -> list[MemoryItem]:
        """
        Retrieve relevant memories
        
        Process:
        1. Generate query embedding
        2. Semantic search in vector DB
        3. Score and filter results
        4. Return top-k memories
        
        Args:
            query: User input or context
            k: Number of memories to retrieve (default: max_active_memories)
            memory_type: Filter by type (optional)
            user_id: Filter by user (optional)
        
        Returns:
            List of MemoryItems, sorted by relevance score
        """
        k = k or self.max_active_memories
        
        # Generate query embedding
        query_embedding = self.embedder.embed(query)
        
        # Build metadata filter
        filter_metadata = {}
        if memory_type:
            filter_metadata["type"] = memory_type
        if user_id:
            filter_metadata["user_id"] = user_id
        
        # Search vector DB (retrieve more than k for scoring)
        raw_results = self.store.search(
            embedding=query_embedding,
            k=k * 2,  # Over-retrieve for better scoring
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Score and filter
        scored_memories = self._score_and_filter(raw_results)
        
        # Return top-k
        return scored_memories[:k]
    
    def _score_and_filter(
        self,
        raw_results: dict[str, Any]
    ) -> list[MemoryItem]:
        """
        Score memories using multiple signals
        
        Signals:
        1. Relevance: Vector similarity (from Chroma)
        2. Importance: User/system assigned importance
        3. Recency: How recent the memory is
        
        Formula (can be tuned):
            final_score = relevance * 0.5 + importance * 0.3 + recency * 0.2
        
        Future improvements:
        - Add type-specific weighting
        - Add access frequency
        - Add rerank model (e.g., Cohere rerank)
        """
        ids = raw_results["ids"][0] if raw_results["ids"] else []
        documents = raw_results["documents"][0] if raw_results["documents"] else []
        metadatas = raw_results["metadatas"][0] if raw_results["metadatas"] else []
        distances = raw_results["distances"][0] if raw_results["distances"] else []
        
        if not ids:
            return []
        
        scored_memories = []
        current_time = time.time()
        
        for i, (mem_id, doc, metadata, distance) in enumerate(
            zip(ids, documents, metadatas, distances)
        ):
            # Relevance score (convert distance to similarity)
            # Assuming cosine distance [0, 2], convert to similarity [0, 1]
            relevance = 1 - (distance / 2)
            
            # Importance score (from metadata)
            importance = metadata.get("importance", 0.5)
            
            # Recency score (exponential decay)
            created_at = metadata.get("created_at", current_time)
            age_hours = (current_time - created_at) / 3600
            recency = max(0.0, 1.0 - (age_hours / 720))  # Decay over 30 days
            
            # Combined score (tunable weights)
            final_score = (
                relevance * 0.5 +
                importance * 0.3 +
                recency * 0.2
            )
            
            # Create MemoryItem
            memory_item = MemoryItem(
                id=mem_id,
                content=doc,
                type=metadata.get("type", "semantic"),
                importance=importance,
                created_at=datetime.fromtimestamp(created_at)
            )
            
            scored_memories.append((final_score, memory_item))
        
        # Sort by score (descending)
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # Return only MemoryItems (drop scores)
        return [item for score, item in scored_memories]
    
    def delete_memory(self, memory_id: str) -> None:
        """
        Delete a specific memory
        
        Use cases:
        - User requests deletion
        - GDPR compliance
        - Memory quality issues
        """
        self.store.delete(memory_id)
    
    def delete_old_memories(
        self,
        days_old: int = 90,
        user_id: str | None = None
    ) -> int:
        """
        Delete memories older than specified days
        
        Retention policy implementation
        
        Args:
            days_old: Delete memories older than this
            user_id: Optional user filter
        
        Returns:
            Number of deleted memories
        """
        # TODO: Implement with metadata filtering
        # Requires ChromaDB metadata query support
        pass
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get memory statistics
        
        Useful for:
        - Monitoring
        - Debugging
        - User dashboards
        """
        return {
            "total_memories": self.store.count(),
            "persist_dir": self.store.persist_dir
        }
