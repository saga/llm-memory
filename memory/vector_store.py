"""
Vector Store Abstraction - Chroma wrapper

Design Principles:
1. Don't leak Chroma details to upper layers
2. Easy to swap to pgvector/Milvus/Pinecone later
3. Clean interface for add/search operations
4. Handle all embedding/metadata complexity here
"""

import chromadb
from chromadb.config import Settings
from typing import Any


class VectorStore:
    """
    Vector database abstraction layer
    
    Why this exists:
    - Isolates vector DB implementation from business logic
    - Provides clean interface for memory operations
    - Makes switching vector DBs trivial (change this file only)
    
    Current implementation: ChromaDB
    Future options: pgvector, Milvus, Pinecone, Weaviate
    """
    
    def __init__(self, persist_dir: str = "./chroma_db"):
        """
        Initialize vector store
        
        Args:
            persist_dir: Directory for ChromaDB persistence
        """
        self.persist_dir = persist_dir
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_dir,
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="memory",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity for embeddings
        )
    
    def add(
        self,
        id: str,
        text: str,
        embedding: list[float],
        metadata: dict[str, Any]
    ) -> None:
        """
        Add a single memory to vector store
        
        Args:
            id: Unique identifier
            text: Original text content
            embedding: Vector representation
            metadata: Additional metadata (type, importance, timestamp, etc.)
        """
        self.collection.add(
            ids=[id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata]
        )
    
    def add_batch(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]]
    ) -> None:
        """
        Batch add memories for efficiency
        
        Use this for:
        - Initial data loading
        - Bulk imports
        - Snapshot restores
        """
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def search(
        self,
        embedding: list[float],
        k: int = 5,
        filter_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Semantic search for relevant memories
        
        Args:
            embedding: Query vector
            k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"type": "preference"})
        
        Returns:
            Dictionary with ids, documents, metadatas, distances
        """
        query_params = {
            "query_embeddings": [embedding],
            "n_results": k
        }
        
        if filter_metadata:
            query_params["where"] = filter_metadata
        
        return self.collection.query(**query_params)
    
    def delete(self, id: str) -> None:
        """
        Delete a memory by ID
        
        Use cases:
        - User requests memory deletion
        - Expired memories cleanup
        - GDPR compliance
        """
        self.collection.delete(ids=[id])
    
    def delete_batch(self, ids: list[str]) -> None:
        """Batch delete for efficiency"""
        self.collection.delete(ids=ids)
    
    def count(self) -> int:
        """Get total number of memories"""
        return self.collection.count()
    
    def reset(self) -> None:
        """
        Clear all memories (use with caution!)
        
        Use cases:
        - Testing
        - Fresh start
        - Data corruption recovery
        """
        self.client.delete_collection(name="memory")
        self.collection = self.client.get_or_create_collection(
            name="memory",
            metadata={"hnsw:space": "cosine"}
        )


class VectorStoreConfig:
    """
    Configuration for vector store
    
    Separates config from implementation
    Makes testing/deployment easier
    """
    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        collection_name: str = "memory",
        similarity_metric: str = "cosine"
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.similarity_metric = similarity_metric
