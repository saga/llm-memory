"""
Demo: Advanced Memory Types System
Demonstrates the use of Semantic, Episodic, and Procedural memory types
with intelligent retrieval strategies.
"""

from framework.state import AgentState, MessageRole, MemoryType
from framework.nodes import (
    create_memory_entry, 
    retrieve_semantic_memories,
    retrieve_episodic_memories,
    retrieve_procedural_memories,
    retrieve_mixed_memories,
    classify_memory_type
)
from framework.graph import create_simple_base_graph
from datetime import datetime
import time


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_memory(memory, index=None):
    prefix = f"[{index}] " if index is not None else ""
    print(f"{prefix}ID: {memory.id}")
    print(f"    类型: {memory.memory_type} | 重要性: {memory.importance_score:.2f}")
    print(f"    访问次数: {memory.access_count} | 时间: {memory.timestamp.strftime('%H:%M:%S')}")
    print(f"    内容: {memory.content[:100]}...")
    print()


def demo_memory_classification():
    """Demo 1: Automatic memory type classification"""
    print_section("Demo 1: 自动记忆类型分类")
    
    test_cases = [
        ("什么是机器学习？", "机器学习是人工智能的一个分支..."),
        ("我喜欢简洁的回答", "好的，我会提供简洁的回答"),
        ("今天天气不错", "是的，今天的天气很好"),
        ("请总是用中文回复我", "明白了，我会用中文回复"),
        ("解释一下Python是什么", "Python是一种高级编程语言...")
    ]
    
    for user_input, assistant_response in test_cases:
        memory_type, importance = classify_memory_type(user_input, assistant_response)
        print(f"用户: {user_input}")
        print(f"  → 分类: {memory_type.value} (重要性: {importance:.2f})")
        print()


def demo_type_specific_retrieval():
    """Demo 2: Type-specific memory retrieval"""
    print_section("Demo 2: 分类检索策略")
    
    state = AgentState(session_id="demo_session_2")
    
    # Add semantic memories (facts)
    semantic_memories = [
        ("Python是一种高级编程语言", 0.9),
        ("机器学习是AI的一个分支", 0.8),
        ("LangChain是LLM开发框架", 0.7),
    ]
    
    for content, importance in semantic_memories:
        mem = create_memory_entry(
            content=content,
            context="default",
            message_type="user_input",
            memory_type=MemoryType.SEMANTIC,
            importance_score=importance
        )
        state.add_memory(mem)
    
    # Add episodic memories (conversations)
    time.sleep(0.1)  # Small delay for timestamp differentiation
    episodic_memories = [
        "用户询问了天气情况",
        "用户分享了今天的工作进展",
        "用户询问了晚餐建议",
    ]
    
    for content in episodic_memories:
        mem = create_memory_entry(
            content=content,
            context="default",
            message_type="user_input",
            memory_type=MemoryType.EPISODIC,
            importance_score=0.5
        )
        state.add_memory(mem)
        time.sleep(0.05)
    
    # Add procedural memories (preferences)
    procedural_memories = [
        ("用户偏好简洁的回答", 0.9),
        ("用户希望使用中文", 0.95),
    ]
    
    for content, importance in procedural_memories:
        mem = create_memory_entry(
            content=content,
            context="default",
            message_type="user_input",
            memory_type=MemoryType.PROCEDURAL,
            importance_score=importance
        )
        state.add_memory(mem)
    
    # Retrieve by type
    print("\n📚 语义记忆检索 (事实/知识):")
    semantic_results = retrieve_semantic_memories(state, query="Python 编程", top_k=3)
    for i, mem in enumerate(semantic_results, 1):
        print_memory(mem, i)
    
    print("📖 情节记忆检索 (最近对话):")
    episodic_results = retrieve_episodic_memories(state, recent_n=3)
    for i, mem in enumerate(episodic_results, 1):
        print_memory(mem, i)
    
    print("⚙️  程序记忆检索 (用户偏好):")
    procedural_results = retrieve_procedural_memories(state)
    for i, mem in enumerate(procedural_results, 1):
        print_memory(mem, i)


def demo_mixed_retrieval():
    """Demo 3: Intelligent mixed retrieval"""
    print_section("Demo 3: 智能混合检索")
    
    state = AgentState(session_id="demo_session_3")
    
    # Populate with diverse memories
    memories_data = [
        ("Python支持面向对象编程", MemoryType.SEMANTIC, 0.8, 5),
        ("用户昨天问了关于数据库的问题", MemoryType.EPISODIC, 0.5, 2),
        ("用户喜欢看到代码示例", MemoryType.PROCEDURAL, 0.9, 8),
        ("FastAPI是现代Python Web框架", MemoryType.SEMANTIC, 0.7, 3),
        ("用户今天学习了新的算法", MemoryType.EPISODIC, 0.6, 1),
        ("用户偏好详细的解释", MemoryType.PROCEDURAL, 0.85, 6),
    ]
    
    for content, mem_type, importance, access_count in memories_data:
        mem = create_memory_entry(
            content=content,
            context="default",
            message_type="user_input",
            memory_type=mem_type,
            importance_score=importance
        )
        # Simulate access history
        for _ in range(access_count):
            mem.increment_access()
        state.add_memory(mem)
    
    # Mixed retrieval
    query = "如何用Python编写代码"
    print(f"查询: '{query}'\n")
    
    mixed_results = retrieve_mixed_memories(state, query=query, top_k=5)
    print(f"检索到 {len(mixed_results)} 条记忆（智能混合）:\n")
    
    for i, mem in enumerate(mixed_results, 1):
        print_memory(mem, i)


def demo_full_workflow():
    """Demo 4: Full workflow with memory statistics"""
    print_section("Demo 4: 完整工作流程")
    
    state = AgentState(session_id="demo_session_4", user_id="user_123")
    
    # Simulate conversation with automatic classification
    conversations = [
        ("什么是LangChain？", MessageRole.USER),
        ("LangChain是一个用于开发LLM应用的框架", MessageRole.ASSISTANT),
        ("我喜欢简洁的解释", MessageRole.USER),
        ("好的，我会提供简洁的回答", MessageRole.ASSISTANT),
        ("今天的工作很顺利", MessageRole.USER),
        ("很高兴听到这个消息！", MessageRole.ASSISTANT),
    ]
    
    # Add messages and create memories
    for content, role in conversations:
        state.add_message(role, content)
        
        # Create memory after each user-assistant pair
        if role == MessageRole.ASSISTANT:
            user_msg = state.get_messages_by_role(MessageRole.USER)[-1]
            assistant_msg = state.get_messages_by_role(MessageRole.ASSISTANT)[-1]
            
            memory_type, importance = classify_memory_type(
                user_msg.content,
                assistant_msg.content
            )
            
            mem = create_memory_entry(
                content=f"用户: {user_msg.content}\\n助手: {assistant_msg.content}",
                context="default",
                message_type="user_input",
                memory_type=memory_type,
                importance_score=importance
            )
            state.add_memory(mem)
    
    # Display statistics
    stats = state.get_memory_stats()
    print("\n📊 记忆统计:")
    print(f"  总记忆数: {stats['total']}")
    print(f"  语义记忆: {stats['by_type']['semantic']}")
    print(f"  情节记忆: {stats['by_type']['episodic']}")
    print(f"  程序记忆: {stats['by_type']['procedural']}")
    print(f"  平均重要性: {stats['avg_importance']}")
    
    print("\n📝 所有记忆:")
    for mem in state.memories.values():
        print_memory(mem)


def demo_graph_integration():
    """Demo 5: Integration with the graph workflow"""
    print_section("Demo 5: 图工作流集成")
    
    state = AgentState(session_id="demo_session_5")
    state.add_message(MessageRole.USER, "什么是人工智能？这很重要")
    
    # Run through the graph
    graph = create_simple_base_graph()
    final_state = graph.invoke(state, max_steps=10)
    
    print(f"\n工作流完成！执行步骤: {final_state.step}")
    print(f"状态: {final_state.status}")
    print(f"\n消息数: {len(final_state.messages)}")
    print(f"记忆数: {len(final_state.memories)}")
    
    # Show created memories
    print("\n💾 存储的记忆:")
    for mem in final_state.memories.values():
        print_memory(mem)
    
    # Show memory stats
    stats = final_state.get_memory_stats()
    print("\n📊 记忆统计:")
    print(f"  总计: {stats['total']}")
    print(f"  类型分布: {stats['by_type']}")


if __name__ == "__main__":
    print("\n" + "🧠" * 30)
    print("   LLM Memory System - Advanced Memory Types Demo")
    print("🧠" * 30)
    
    demo_memory_classification()
    demo_type_specific_retrieval()
    demo_mixed_retrieval()
    demo_full_workflow()
    demo_graph_integration()
    
    print_section("✅ 所有演示完成")
    print("\n主要特性:")
    print("  ✓ 三种记忆类型: Semantic, Episodic, Procedural")
    print("  ✓ 自动记忆分类")
    print("  ✓ 类型特定的检索策略")
    print("  ✓ 智能混合检索")
    print("  ✓ 重要性评分和访问追踪")
    print("  ✓ 完整的统计分析")
    print()
