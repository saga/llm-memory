"""
Embedding Service - Unified embedding interface

Design principles:
1. Abstract away embedding model implementation
2. Easy to swap providers (OpenAI, Cohere, HuggingFace, etc.)
3. Support local and remote models
4. Cache embeddings for efficiency

Current implementation: OpenAI
Future options: Cohere, sentence-transformers, FastEmbed, etc.
"""

import os
from typing import Any
import hashlib
import json


class Embedder:
    """
    Embedding service interface
    
    Why this exists:
    - Centralize embedding logic
    - Easy provider switching
    - Caching support
    - Consistent interface for all models
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        cache_enabled: bool = True
    ):
        """
        Initialize embedder
        
        Args:
            provider: "openai", "cohere", "huggingface", "local"
            model: Model identifier
            api_key: API key (if needed)
            cache_enabled: Enable embedding caching
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.cache_enabled = cache_enabled
        self._cache: dict[str, list[float]] = {}
        
        # Initialize client based on provider
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        elif provider == "cohere":
            # Future: import cohere
            raise NotImplementedError("Cohere provider not yet implemented")
        elif provider == "huggingface":
            # Future: from sentence_transformers import SentenceTransformer
            raise NotImplementedError("HuggingFace provider not yet implemented")
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for text
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        # Check cache
        if self.cache_enabled:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Generate embedding
        embedding = self._generate_embedding(text)
        
        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = embedding
        
        return embedding
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (more efficient)
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        # Check cache for each text
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            if self.cache_enabled:
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    results.append(self._cache[cache_key])
                    continue
            
            uncached_texts.append(text)
            uncached_indices.append(i)
            results.append(None)  # Placeholder
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            uncached_embeddings = self._generate_embeddings_batch(uncached_texts)
            
            # Fill in results and cache
            for idx, embedding in zip(uncached_indices, uncached_embeddings):
                results[idx] = embedding
                if self.cache_enabled:
                    cache_key = self._get_cache_key(texts[idx])
                    self._cache[cache_key] = embedding
        
        return results
    
    def _generate_embedding(self, text: str) -> list[float]:
        """Generate single embedding (provider-specific)"""
        if self.provider == "openai":
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def _generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate batch embeddings (provider-specific)"""
        if self.provider == "openai":
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        # Use hash to handle long texts
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{self.provider}:{self.model}:{text_hash}"
    
    def clear_cache(self):
        """Clear embedding cache"""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached embeddings"""
        return len(self._cache)


# Factory function for easy initialization
def create_embedder(
    provider: str = "openai",
    model: str | None = None,
    **kwargs
) -> Embedder:
    """
    Create embedder with provider-specific defaults
    
    Args:
        provider: Embedding provider
        model: Model name (uses provider default if None)
        **kwargs: Additional arguments
    
    Returns:
        Configured Embedder instance
    """
    # Provider-specific defaults
    defaults = {
        "openai": "text-embedding-3-small",  # Cheaper and faster
        "cohere": "embed-english-v3.0",
        "huggingface": "sentence-transformers/all-MiniLM-L6-v2"
    }
    
    if model is None:
        model = defaults.get(provider, "default")
    
    return Embedder(provider=provider, model=model, **kwargs)


# Export
__all__ = ["Embedder", "create_embedder"]
