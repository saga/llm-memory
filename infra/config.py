"""
Configuration Management

Centralize all configuration:
- Environment variables
- Model settings
- Vector store settings
- API settings

Follows 12-factor app principles
"""

import os
from typing import Any
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Embedding service configuration"""
    provider: str = Field(default="openai", description="Embedding provider")
    model: str = Field(default="text-embedding-3-small", description="Embedding model")
    api_key: str | None = Field(default=None, description="API key (or from env)")
    cache_enabled: bool = Field(default=True, description="Enable embedding cache")
    
    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Load from environment variables"""
        return cls(
            provider=os.getenv("EMBEDDING_PROVIDER", "openai"),
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY"),
            cache_enabled=os.getenv("EMBEDDING_CACHE", "true").lower() == "true"
        )


class VectorStoreConfig(BaseModel):
    """Vector store configuration"""
    persist_dir: str = Field(default="./chroma_db", description="Persistence directory")
    collection_name: str = Field(default="memory", description="Collection name")
    similarity_metric: str = Field(default="cosine", description="Similarity metric")
    
    @classmethod
    def from_env(cls) -> "VectorStoreConfig":
        """Load from environment variables"""
        return cls(
            persist_dir=os.getenv("VECTOR_STORE_DIR", "./chroma_db"),
            collection_name=os.getenv("COLLECTION_NAME", "memory"),
            similarity_metric=os.getenv("SIMILARITY_METRIC", "cosine")
        )


class AgentConfig(BaseModel):
    """Agent configuration"""
    model: str = Field(default="openai:gpt-4", description="LLM model")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1000, description="Max response tokens")
    max_retries: int = Field(default=2, description="Retry attempts on failure")
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load from environment variables"""
        return cls(
            model=os.getenv("AGENT_MODEL", "openai:gpt-4"),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "1000")),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "2"))
        )


class MemoryConfig(BaseModel):
    """Memory system configuration"""
    max_active_memories: int = Field(default=10, description="Max memories per query")
    retention_days: int = Field(default=90, description="Default retention period")
    importance_threshold: float = Field(default=0.3, description="Min importance to keep")
    
    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """Load from environment variables"""
        return cls(
            max_active_memories=int(os.getenv("MAX_ACTIVE_MEMORIES", "10")),
            retention_days=int(os.getenv("RETENTION_DAYS", "90")),
            importance_threshold=float(os.getenv("IMPORTANCE_THRESHOLD", "0.3"))
        )


class APIConfig(BaseModel):
    """API server configuration"""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    log_level: str = Field(default="info", description="Logging level")
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load from environment variables"""
        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            reload=os.getenv("API_RELOAD", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "info")
        )


class SnapshotConfig(BaseModel):
    """S3 snapshot configuration"""
    s3_bucket: str | None = Field(default=None, description="S3 bucket name")
    s3_prefix: str = Field(default="memory-snapshots", description="S3 key prefix")
    snapshot_interval_hours: int = Field(default=24, description="Snapshot frequency")
    
    @classmethod
    def from_env(cls) -> "SnapshotConfig":
        """Load from environment variables"""
        return cls(
            s3_bucket=os.getenv("S3_BUCKET"),
            s3_prefix=os.getenv("S3_PREFIX", "memory-snapshots"),
            snapshot_interval_hours=int(os.getenv("SNAPSHOT_INTERVAL", "24"))
        )


class Config(BaseModel):
    """
    Complete system configuration
    
    Usage:
        # Load from environment
        config = Config.from_env()
        
        # Or create manually
        config = Config(
            embedding=EmbeddingConfig(provider="openai"),
            agent=AgentConfig(model="openai:gpt-4")
        )
    """
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    snapshot: SnapshotConfig = Field(default_factory=SnapshotConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load complete configuration from environment"""
        return cls(
            embedding=EmbeddingConfig.from_env(),
            vector_store=VectorStoreConfig.from_env(),
            agent=AgentConfig.from_env(),
            memory=MemoryConfig.from_env(),
            api=APIConfig.from_env(),
            snapshot=SnapshotConfig.from_env()
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()


# Global config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """
    Get global configuration instance
    
    Loads from environment on first call
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config():
    """Reload configuration from environment"""
    global _config
    _config = Config.from_env()


# Export
__all__ = [
    "Config",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "AgentConfig",
    "MemoryConfig",
    "APIConfig",
    "SnapshotConfig",
    "get_config",
    "reload_config",
]
