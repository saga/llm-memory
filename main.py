"""
Main Example - Complete chat flow demonstration

This shows the FULL production flow:
1. Initialize all components
2. Retrieve memories
3. Run agent
4. Persist memories
5. Repeat

This is production-ready code, not a toy demo.
"""

import os
from memory import VectorStore, MemoryManager, MemoryState
from agent import create_memory_agent
from infra import create_embedder


def main():
    """
    Complete chat example
    
    Flow:
    1. Setup: Initialize vector store, embedder, memory manager, agent
    2. Chat loop: Retrieve -> Agent -> Persist
    3. Stats: Show what was stored
    """
    
    print("=" * 60)
    print("🧠 LLM Memory System v2.0 - Production Architecture")
    print("=" * 60)
    
    # ===== Step 1: Initialize Components =====
    print("\n[1/5] Initializing components...")
    
    # Embedder (for vector search)
    embedder = create_embedder(
        provider="openai",
        model="text-embedding-3-small"
    )
    print("  ✅ Embedder: OpenAI text-embedding-3-small")
    
    # Vector Store (ChromaDB)
    vector_store = VectorStore(persist_dir="./chroma_db")
    print(f"  ✅ Vector Store: {vector_store.count()} memories")
    
    # Memory Manager (business logic)
    memory_manager = MemoryManager(
        vector_store=vector_store,
        embedder=embedder,
        max_active_memories=10
    )
    print("  ✅ Memory Manager: Ready")
    
    # Agent (PydanticAI)
    agent = create_memory_agent(model="openai:gpt-4")
    print("  ✅ Agent: PydanticAI with memory tools")
    
    # ===== Step 2: Example Conversation =====
    print("\n[2/5] Starting example conversation...")
    
    user_inputs = [
        "Hi! I'm learning Python and PydanticAI. I really love clean code.",
        "What's the best way to structure an LLM memory system?",
        "Can you remind me what I told you I'm learning?"
    ]
    
    for i, user_input in enumerate(user_inputs, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_input}")
        
        # ===== THE CORE FLOW =====
        
        # Step A: Retrieve relevant memories
        retrieved_memories = memory_manager.retrieve(
            query=user_input,
            user_id="demo_user"
        )
        print(f"\n📚 Retrieved {len(retrieved_memories)} memories:")
        for mem in retrieved_memories:
            print(f"  - [{mem.type}] {mem.content}")
        
        # Step B: Create agent state
        state = MemoryState(active_memories=retrieved_memories)
        
        # Step C: Run agent
        result = agent.run_sync(user_input, deps=state)
        
        print(f"\n🤖 Assistant: {result.data}")
        
        # Step D: Persist new memories
        initial_count = len(retrieved_memories)
        new_memories = state.active_memories[initial_count:]
        
        if new_memories:
            print(f"\n💾 Storing {len(new_memories)} new memories:")
            for mem in new_memories:
                memory_manager.write_memory(
                    text=mem.content,
                    memory_type=mem.type,
                    importance=mem.importance,
                    user_id="demo_user"
                )
                print(f"  - [{mem.type}] {mem.content} (importance: {mem.importance})")
    
    # ===== Step 3: Show Final Stats =====
    print("\n[3/5] Memory statistics:")
    stats = memory_manager.get_stats()
    print(f"  📊 Total memories: {stats['total_memories']}")
    print(f"  📁 Storage: {stats['persist_dir']}")
    
    # ===== Step 4: Architecture Summary =====
    print("\n[4/5] Architecture highlights:")
    print("  ✅ Vector DB: Isolated in memory/ layer")
    print("  ✅ Agent: Stateless, uses MemoryState")
    print("  ✅ Embedder: Swappable provider")
    print("  ✅ Memory writes: AFTER agent run (no hallucinations)")
    
    # ===== Step 5: What Makes This Production-Ready =====
    print("\n[5/5] Production-ready features:")
    print("  ✅ Layered architecture (agent/ memory/ infra/ api/)")
    print("  ✅ Clean separation: storage vs. logic vs. interface")
    print("  ✅ Type safety: Pydantic models everywhere")
    print("  ✅ Swappable: Change vector DB without touching agent")
    print("  ✅ Observable: Stats, logging, structured errors")
    print("  ✅ Testable: Each layer can be tested independently")
    
    print("\n" + "=" * 60)
    print("✨ Demo complete! This is the architecture that scales.")
    print("=" * 60)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  $env:OPENAI_API_KEY = 'sk-...'")
        exit(1)
    
    main()
