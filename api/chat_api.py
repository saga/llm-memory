"""
Chat API - HTTP interface for memory-enhanced chat

This is the orchestration layer that ties everything together:
1. Retrieve memories from vector DB
2. Pass to agent
3. Get response
4. Persist new memories

Design principle: Keep it thin. Business logic belongs in memory/ and agent/.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any
import os

from memory import VectorStore, MemoryManager, MemoryState
from agent import create_memory_agent
from infra import create_embedder, get_config


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request"""
    user_input: str = Field(description="User message")
    user_id: str | None = Field(default=None, description="User identifier (for multi-user)")
    session_id: str | None = Field(default=None, description="Session identifier")


class ChatResponse(BaseModel):
    """Chat response"""
    response: str = Field(description="Assistant response")
    memories_created: int = Field(description="Number of new memories created")
    memories_retrieved: int = Field(description="Number of memories used")


class MemoryStatsResponse(BaseModel):
    """Memory statistics"""
    total_memories: int
    persist_dir: str


# Initialize FastAPI app
app = FastAPI(
    title="LLM Memory System API",
    description="Production-grade LLM with long-term memory",
    version="2.0.0"
)


# Global instances (initialized on startup)
config = None
embedder = None
vector_store = None
memory_manager = None
agent = None


@app.on_event("startup")
async def startup():
    """Initialize system on startup"""
    global config, embedder, vector_store, memory_manager, agent
    
    # Load configuration
    config = get_config()
    
    # Initialize embedder
    embedder = create_embedder(
        provider=config.embedding.provider,
        model=config.embedding.model
    )
    
    # Initialize vector store
    vector_store = VectorStore(
        persist_dir=config.vector_store.persist_dir
    )
    
    # Initialize memory manager
    memory_manager = MemoryManager(
        vector_store=vector_store,
        embedder=embedder,
        max_active_memories=config.memory.max_active_memories
    )
    
    # Initialize agent
    agent = create_memory_agent(
        model=config.agent.model
    )
    
    print("✅ System initialized successfully")
    print(f"📊 Total memories: {vector_store.count()}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint - THE MOST IMPORTANT FUNCTION
    
    This is the complete flow:
    1. Retrieve relevant memories from vector DB
    2. Create agent state with memories
    3. Run agent
    4. Persist new memories
    5. Return response
    
    Critical: Memory persistence happens AFTER agent run (not during)
    """
    try:
        # Step 1: Retrieve relevant memories
        retrieved_memories = memory_manager.retrieve(
            query=request.user_input,
            user_id=request.user_id
        )
        
        # Step 2: Create agent state
        state = MemoryState(
            active_memories=retrieved_memories
        )
        
        # Step 3: Run agent
        result = agent.run_sync(
            request.user_input,
            deps=state
        )
        
        # Step 4: Persist new memories
        # Extract memories that were added during agent run
        initial_count = len(retrieved_memories)
        final_count = len(state.active_memories)
        new_memories = state.active_memories[initial_count:]
        
        # Write new memories to vector DB
        for memory in new_memories:
            memory_manager.write_memory(
                text=memory.content,
                memory_type=memory.type,
                importance=memory.importance,
                user_id=request.user_id
            )
        
        # Step 5: Return response
        return ChatResponse(
            response=result.data,
            memories_created=len(new_memories),
            memories_retrieved=initial_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=MemoryStatsResponse)
async def get_stats() -> MemoryStatsResponse:
    """Get memory system statistics"""
    stats = memory_manager.get_stats()
    return MemoryStatsResponse(**stats)


@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory"""
    try:
        memory_manager.delete_memory(memory_id)
        return {"message": f"Memory {memory_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_all_memories():
    """
    Reset all memories (use with caution!)
    
    For testing/development only
    """
    try:
        vector_store.reset()
        return {"message": "All memories cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "total_memories": vector_store.count() if vector_store else 0
    }


# Run with: uvicorn api.chat_api:app --reload
if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "api.chat_api:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.api.log_level
    )
