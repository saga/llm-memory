"""
Memory Summarization - Compress conversation history

Why this exists:
- LLMs have context limits
- Not all chat history should become long-term memory
- Need to distinguish: chat history vs. memory

Summarization use cases:
1. Compress long conversations into recent_summary
2. Extract key facts/preferences before storing as memory
3. Merge similar memories to reduce redundancy
"""

from typing import Any


class MemorySummarizer:
    """
    Handles conversation and memory summarization
    
    Principles:
    - Chat history ≠ Memory
    - Summarize before storing (avoid noise)
    - Use LLM for intelligent compression
    """
    
    def __init__(self, llm_client: Any):
        """
        Args:
            llm_client: LLM for summarization (e.g., OpenAI client)
        """
        self.llm = llm_client
    
    def summarize_conversation(
        self,
        messages: list[dict[str, str]],
        max_length: int = 200
    ) -> str:
        """
        Compress conversation history into a summary
        
        Use case:
        - Store in MemoryState.recent_summary
        - Provide context without full history
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            max_length: Target summary length in words
        
        Returns:
            Compressed summary
        """
        if not messages:
            return ""
        
        # Build prompt for summarization
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        prompt = f"""Summarize the following conversation concisely (max {max_length} words).
Focus on:
- Key topics discussed
- Important decisions or preferences
- Actionable items

Conversation:
{conversation_text}

Summary:"""
        
        # Call LLM (pseudo-code, adapt to your LLM client)
        try:
            response = self.llm.generate(prompt, max_tokens=max_length * 2)
            return response.strip()
        except Exception as e:
            # Fallback: return last few messages
            return conversation_text[:500] + "..."
    
    def extract_memories_from_conversation(
        self,
        messages: list[dict[str, str]]
    ) -> list[str]:
        """
        Extract memorable facts/preferences from conversation
        
        Use case:
        - Before storing to vector DB, filter out noise
        - Only store what's worth remembering
        
        Returns:
            List of memory-worthy statements
        """
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        prompt = f"""From the following conversation, extract key facts, preferences, or decisions worth remembering long-term.

Format: Return a JSON list of strings.

Conversation:
{conversation_text}

Memorable items (JSON list):"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=500)
            # Parse JSON response
            import json
            memories = json.loads(response)
            return memories if isinstance(memories, list) else []
        except Exception:
            return []
    
    def merge_similar_memories(
        self,
        memories: list[str],
        similarity_threshold: float = 0.9
    ) -> list[str]:
        """
        Merge redundant memories to reduce storage
        
        Use case:
        - User says "I like Python" multiple times
        - Should store once, not duplicate
        
        Future improvement:
        - Use embeddings for semantic similarity
        - Current: Simple string matching
        """
        # TODO: Implement with embedding-based similarity
        # For now, simple deduplication
        unique_memories = list(set(memories))
        return unique_memories
