"""
PydanticAI Demo - Simplified Memory System
Shows how PydanticAI makes the framework cleaner and easier to use
"""

import asyncio
from framework.pydantic_agent import MemoryAgentWorkflow
from framework.state import MemoryType


async def demo_basic_usage():
    """Demo 1: Basic agent usage"""
    print("=" * 70)
    print("  Demo 1: Basic PydanticAI Agent Usage")
    print("=" * 70 + "\n")
    
    # Create workflow
    workflow = MemoryAgentWorkflow(enable_summarization=False)
    session_id = workflow.create_session()
    
    print(f"Session created: {session_id}\n")
    
    # Simple conversation
    conversations = [
        "Hi! My name is Alice and I love Python programming.",
        "What's my name?",
        "What do I like?",
    ]
    
    for user_input in conversations:
        print(f"User: {user_input}")
        response = await workflow.chat(session_id, user_input)
        print(f"Assistant: {response}\n")
    
    # Show stats
    stats = workflow.get_session_stats(session_id)
    print(f"Session stats: {stats['memory_stats']}\n")


async def demo_with_tools():
    """Demo 2: Using agent tools explicitly"""
    print("=" * 70)
    print("  Demo 2: Explicit Tool Usage")
    print("=" * 70 + "\n")
    
    workflow = MemoryAgentWorkflow(enable_summarization=False)
    session_id = workflow.create_session()
    
    # Ask agent to use tools
    commands = [
        "Store this as a semantic memory: Python is a high-level programming language",
        "Store this as a procedural memory: I prefer concise answers",
        "Recall all semantic memories",
        "Show me memory statistics",
    ]
    
    for cmd in commands:
        print(f"User: {cmd}")
        response = await workflow.chat(session_id, cmd)
        print(f"Assistant: {response}\n")


async def demo_auto_summarization():
    """Demo 3: Automatic memory compression"""
    print("=" * 70)
    print("  Demo 3: Auto-Summarization")
    print("=" * 70 + "\n")
    
    workflow = MemoryAgentWorkflow(enable_summarization=True)
    session_id = workflow.create_session()
    
    # Generate many conversations to trigger summarization
    print("Generating conversation to trigger auto-summarization...\n")
    
    topics = [
        "Tell me about machine learning",
        "What is deep learning?",
        "Explain neural networks",
        "What are transformers?",
        "Tell me about GPT",
        "What is attention mechanism?",
        "Explain BERT",
        "What is NLP?",
        "Tell me about tokenization",
        "What are embeddings?",
    ]
    
    for i, topic in enumerate(topics, 1):
        print(f"[{i}/10] User: {topic}")
        response = await workflow.chat(session_id, topic)
        print(f"Assistant: {response[:100]}...\n")
    
    # Check if summarization was triggered
    stats = workflow.get_session_stats(session_id)
    print(f"\nFinal memory stats:")
    print(f"  Total memories: {stats['memory_stats']['total']}")
    print(f"  Summarized: {stats['memory_stats']['summarized_memories']}")
    
    # Ask about compression
    print(f"\nUser: How many memories do you have now?")
    response = await workflow.chat(session_id, "How many memories do you have now?")
    print(f"Assistant: {response}")


async def demo_memory_types():
    """Demo 4: Working with different memory types"""
    print("\n" + "=" * 70)
    print("  Demo 4: Memory Types")
    print("=" * 70 + "\n")
    
    workflow = MemoryAgentWorkflow(enable_summarization=False)
    session_id = workflow.create_session()
    
    # Store different types
    print("Storing different memory types...\n")
    
    memory_commands = [
        ("Store as semantic: The capital of France is Paris", "fact"),
        ("Store as procedural: Always greet me with 'Hello'", "preference"),
        ("Store as episodic: We discussed Python today", "event"),
        ("Recall semantic memories", "recall"),
        ("Recall procedural memories", "recall"),
        ("Show memory statistics", "stats"),
    ]
    
    for cmd, label in memory_commands:
        print(f"User [{label}]: {cmd}")
        response = await workflow.chat(session_id, cmd)
        print(f"Assistant: {response}\n")


async def demo_simplified_api():
    """Demo 5: Compare old vs new API"""
    print("=" * 70)
    print("  Demo 5: Simplified API Comparison")
    print("=" * 70 + "\n")
    
    print("OLD WAY (Manual node management):")
    print("  1. Create state")
    print("  2. Call planner_node(state)")
    print("  3. Call memory_recall_node(state)")
    print("  4. Call decision_node(state)")
    print("  5. Call response_generator_node(state)")
    print("  6. Call memory_storage_node(state)")
    print("  7. Handle routing manually")
    print("  8. Manage state transitions")
    print()
    
    print("NEW WAY (PydanticAI):")
    print("  1. Create workflow")
    print("  2. workflow.chat(session_id, message)")
    print("  3. Done! ✨")
    print()
    
    # Show it in action
    print("Example:\n")
    
    workflow = MemoryAgentWorkflow()
    session_id = workflow.create_session()
    
    print("# Just 3 lines of code!")
    print("workflow = MemoryAgentWorkflow()")
    print("session_id = workflow.create_session()")
    print("response = await workflow.chat(session_id, 'Hello!')")
    print()
    
    response = await workflow.chat(session_id, "Hello! I'm testing the new API.")
    print(f"Response: {response}")


async def main():
    """Run all demos"""
    print("\n" + "🚀" * 35)
    print("   PydanticAI Memory Agent - Simplified Framework Demo")
    print("🚀" * 35 + "\n")
    
    await demo_basic_usage()
    await demo_with_tools()
    await demo_auto_summarization()
    await demo_memory_types()
    await demo_simplified_api()
    
    print("\n" + "=" * 70)
    print("  ✅ All Demos Complete")
    print("=" * 70)
    
    print("\n📊 Key Simplifications:")
    print("  ✓ Agent-based architecture (vs manual nodes)")
    print("  ✓ Built-in tool system (vs custom functions)")
    print("  ✓ Automatic context management")
    print("  ✓ Type-safe with Pydantic")
    print("  ✓ Async-first design")
    print("  ✓ Simplified API (3 lines vs 20+)")
    print("  ✓ Dependency injection")
    print("  ✓ Easy testing and mocking")
    
    print("\n💡 Benefits:")
    print("  • Less boilerplate code (~60% reduction)")
    print("  • Better separation of concerns")
    print("  • Easier to extend and maintain")
    print("  • Built-in best practices")
    print("  • Production-ready patterns")
    print()


if __name__ == "__main__":
    asyncio.run(main())
