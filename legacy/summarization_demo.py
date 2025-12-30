"""
Demo: Memory Summarization and Compression
Demonstrates how the framework automatically compresses memories to control
token costs and improve recall quality.
"""

from framework.state import AgentState, MessageRole, MemoryType, SummarizationTrigger, MessageType
from framework.nodes import create_memory_entry, memory_summarization_node
from framework.summarization import (
    SummarizationConfig,
    should_trigger_summarization,
    select_memories_for_summarization,
    compress_memories,
    get_compression_stats
)
from framework.graph import create_simple_base_graph
from datetime import datetime, timedelta
import time


def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_memory_summary(memory):
    """Print a concise memory summary."""
    summarized_marker = " [Summary]" if memory.is_summarized else ""
    print(f"  ID: {memory.id}{summarized_marker}")
    print(f"  Type: {memory.memory_type} | Importance: {memory.importance_score:.2f}")
    print(f"  Tokens: ~{memory.estimate_tokens()} | Time: {memory.timestamp.strftime('%H:%M:%S')}")
    if memory.is_summarized and memory.source_memory_ids:
        print(f"  Consolidated from: {len(memory.source_memory_ids)} memories")
    content_preview = memory.content[:120].replace('\n', ' ')
    print(f"  Content: {content_preview}...")
    print()


def demo_basic_summarization():
    """Demo 1: Basic memory summarization"""
    print_section("Demo 1: Basic Memory Summarization")
    
    state = AgentState(session_id="demo_summary_1")
    
    # Create multiple episodic memories
    conversations = [
        "User asked about Python basics",
        "Discussed the difference between lists and tuples",
        "User asked about function definitions",
        "Explained the concept of decorators",
        "User shared today's learning progress",
        "Discussed code optimization techniques",
    ]
    
    print("Creating 6 episodic memories...\n")
    for i, content in enumerate(conversations):
        mem = create_memory_entry(
            content=content,
            context="default",
            message_type=MessageType.USER_INPUT,
            memory_type=MemoryType.EPISODIC,
            importance_score=0.5
        )
        state.add_memory(mem)
        time.sleep(0.01)
    
    print(f"Initial memory count: {len(state.memories)}")
    print(f"Initial token estimate: {sum(m.estimate_tokens() for m in state.memories.values())}\n")
    
    # Manual summarization
    config = SummarizationConfig(
        min_memories_to_summarize=3,
        preserve_recent_count=2,
        preserve_high_importance=False
    )
    
    new_state, stats = compress_memories(state, config=config)
    
    print(f"After compression: {len(new_state.memories)} memories")
    print(f"After compression tokens: {sum(m.estimate_tokens() for m in new_state.memories.values())}")
    print(f"\nCompression stats:")
    print(f"  Compressed memories: {stats['memories_compressed']}")
    print(f"  Original tokens: {stats['original_tokens']}")
    print(f"  New tokens: {stats['new_tokens']}")
    print(f"  Tokens saved: {stats['tokens_saved']}")
    print(f"  Compression ratio: {stats['compression_ratio']}%")
    
    print("\nCompressed memories:")
    for mem in new_state.memories.values():
        print_memory_summary(mem)


def demo_trigger_policies():
    """Demo 2: Different summarization trigger policies"""
    print_section("Demo 2: Trigger Policies")
    
    # Count-based trigger
    print("Count-based trigger\n")
    state = AgentState(session_id="demo_count")
    
    for i in range(25):
        mem = create_memory_entry(
            content=f"Conversation record {i+1}",
            context="default",
            message_type=MessageType.USER_INPUT,
            memory_type=MemoryType.EPISODIC,
            importance_score=0.5
        )
        state.add_memory(mem)
    
    config_count = SummarizationConfig(
        trigger=SummarizationTrigger.COUNT_BASED,
        max_episodic_count=20,
        min_memories_to_summarize=3
    )
    
    should_trigger, reason = should_trigger_summarization(state, config_count)
    print(f"Memory count: {len(state.get_memories_by_type(MemoryType.EPISODIC))}")
    print(f"Should trigger: {should_trigger} (reason: {reason})")
    
    # Token-based trigger
    print("\n\nToken-based trigger\n")
    state2 = AgentState(session_id="demo_token")
    
    for i in range(10):
        mem = create_memory_entry(
            content=f"This is a longer conversation record " * 50,
            context="default",
            message_type=MessageType.USER_INPUT,
            memory_type=MemoryType.EPISODIC,
            importance_score=0.5
        )
        state2.add_memory(mem)
    
    config_token = SummarizationConfig(
        trigger=SummarizationTrigger.TOKEN_BASED,
        max_total_tokens=2000,
        min_memories_to_summarize=3
    )
    
    total_tokens = sum(m.estimate_tokens() for m in state2.get_memories_by_type(MemoryType.EPISODIC))
    should_trigger2, reason2 = should_trigger_summarization(state2, config_token)
    print(f"Total tokens: {total_tokens}")
    print(f"Token limit: {config_token.max_total_tokens}")
    print(f"Should trigger: {should_trigger2} (reason: {reason2})")


def demo_compression_stats():
    """Demo 3: Compression statistics over time"""
    print_section("Demo 3: Long-term Compression")
    
    state = AgentState(session_id="demo_longterm")
    
    config = SummarizationConfig(
        max_episodic_count=10,
        preserve_recent_count=3,
        min_memories_to_summarize=3
    )
    
    print("Simulating long conversation...\n")
    
    for round_num in range(1, 4):
        print(f"--- Round {round_num} (adding 8 memories) ---")
        
        # Add memories
        for i in range(8):
            mem = create_memory_entry(
                content=f"Round {round_num} conversation {i+1}: discussing technical topics",
                context="default",
                message_type=MessageType.USER_INPUT,
                memory_type=MemoryType.EPISODIC,
                importance_score=0.5
            )
            state.add_memory(mem)
            time.sleep(0.01)
        
        before_count = len(state.memories)
        before_tokens = sum(m.estimate_tokens() for m in state.memories.values())
        
        # Check and compress
        state, stats = compress_memories(state, config=config)
        
        after_count = len(state.memories)
        after_tokens = sum(m.estimate_tokens() for m in state.memories.values())
        
        print(f"  Memories: {before_count} -> {after_count}")
        print(f"  Tokens: {before_tokens} -> {after_tokens}")
        
        if stats['triggered']:
            print(f"  Compression triggered: {stats['memories_compressed']} -> 1 summary")
            print(f"    Saved: {stats['tokens_saved']} tokens ({stats['compression_ratio']}%)")
        else:
            print(f"  Not triggered: {stats['reason']}")
        
        print()
    
    # Final statistics
    compression_stats = get_compression_stats(state)
    print("\nFinal compression stats:")
    print(f"  Total memories: {compression_stats['total_memories']}")
    print(f"  Summarized memories: {compression_stats['summarized_memories']}")
    print(f"  Summarization rate: {compression_stats['summarization_rate']}%")
    print(f"  Total tokens: {compression_stats['total_tokens']}")
    print(f"  Estimated savings: {compression_stats['estimated_tokens_saved']} tokens")
    print(f"  Average compression ratio: {compression_stats['average_compression_ratio']}%")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   Memory Summarization & Compression Demo")
    print("=" * 70)
    
    demo_basic_summarization()
    demo_trigger_policies()
    demo_compression_stats()
    
    print_section("All Demos Complete")
    print("\nKey Features:")
    print("  - Multiple trigger strategies (count/time/token/hybrid)")
    print("  - Selective preservation (recent/important)")
    print("  - Intelligent summary generation")
    print("  - Automatic token optimization")
    print("  - Seamless workflow integration")
    print("\nBenefits:")
    print("  - Control token costs - reduce LLM call overhead")
    print("  - Improve recall quality - summaries have higher information density")
    print("  - Long-term conversation support - infinite memory without explosion")
    print()
