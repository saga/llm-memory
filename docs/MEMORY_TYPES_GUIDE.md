# Advanced Memory Types System

## 概述 Overview

本框架已升级，支持认知科学中的三种记忆类型：**Semantic（语义记忆）**、**Episodic（情节记忆）** 和 **Procedural（程序记忆）**，实现更智能的长期信息存储和检索。

This framework has been upgraded to support three memory types from cognitive science: **Semantic**, **Episodic**, and **Procedural**, enabling more intelligent long-term information storage and retrieval.

## 记忆类型 Memory Types

### 1. Semantic Memory (语义记忆)
- **用途**: 存储事实、概念、常识类知识
- **特点**: 相对稳定，不受时间影响
- **示例**: 
  - "Python是一种编程语言"
  - "机器学习是AI的一个分支"
  - "LangChain是LLM开发框架"

**Use Case**: Facts, concepts, and general knowledge  
**Characteristics**: Relatively stable, time-independent  
**Retrieval Strategy**: Dense search based on content relevance and importance

### 2. Episodic Memory (情节记忆)
- **用途**: 存储事件、对话历史、特定经历
- **特点**: 与时间紧密相关
- **示例**:
  - "用户昨天询问了数据库问题"
  - "今天的工作很顺利"
  - "上次对话中讨论了API设计"

**Use Case**: Events, conversations, and specific experiences  
**Characteristics**: Time-bound, context-specific  
**Retrieval Strategy**: Time-based ordering with optional time window filtering

### 3. Procedural Memory (程序记忆)
- **用途**: 存储行为模式、用户偏好、风格规则
- **特点**: 影响助手行为方式
- **示例**:
  - "用户喜欢简洁的回答"
  - "总是用中文回复"
  - "提供代码示例时包含注释"

**Use Case**: Behavioral patterns, user preferences, and style rules  
**Characteristics**: Influences assistant behavior  
**Retrieval Strategy**: Context matching with high importance prioritization

## 新增功能 New Features

### 1. Enhanced MemoryEntry Model

```python
class MemoryEntry(BaseModel):
    # Original fields
    id: str
    content: str
    context: str
    timestamp: datetime
    metadata: Dict[str, Any]
    hash: str
    message_type: MessageType
    
    # New fields
    memory_type: MemoryType          # Semantic/Episodic/Procedural
    importance_score: float          # 0.0 to 1.0
    access_count: int                # Tracking usage frequency
    last_accessed: Optional[datetime] # Last access timestamp
```

### 2. Intelligent Memory Classification

自动根据对话内容分类记忆类型：

```python
def classify_memory_type(user_input: str, assistant_response: str) -> tuple[MemoryType, float]:
    # Automatic classification based on keywords and patterns
    # Returns (memory_type, importance_score)
```

**分类规则 Classification Rules**:
- 包含定义、解释 → Semantic (重要性: 0.7)
- 包含偏好、指令 → Procedural (重要性: 0.8)
- 一般对话 → Episodic (重要性: 0.5)

### 3. Type-Specific Retrieval Strategies

#### Semantic Retrieval (语义检索)
```python
retrieve_semantic_memories(state, query="Python编程", top_k=3)
```
- 基于重要性分数
- 考虑访问频率
- 关键词匹配（可扩展为向量搜索）

#### Episodic Retrieval (情节检索)
```python
retrieve_episodic_memories(state, recent_n=5, max_age_hours=24)
```
- 时间排序（最新优先）
- 可选时间窗口过滤
- 支持摘要功能

#### Procedural Retrieval (程序检索)
```python
retrieve_procedural_memories(state, context="default")
```
- 上下文匹配
- 重要性排序
- 返回所有相关规则

#### Mixed Retrieval (混合检索)
```python
retrieve_mixed_memories(state, query="如何编程", top_k=5)
```
- 智能平衡三种类型
- 配比: 40% Semantic + 40% Episodic + 20% Procedural

### 4. Memory Statistics

```python
stats = state.get_memory_stats()
# {
#     "total": 10,
#     "by_type": {
#         "semantic": 3,
#         "episodic": 5,
#         "procedural": 2
#     },
#     "avg_importance": 0.65,
#     "most_accessed": {...}
# }
```

## 使用示例 Usage Examples

### 基础使用 Basic Usage

```python
from framework.state import AgentState, MemoryType
from framework.nodes import create_memory_entry

# Create semantic memory (fact)
memory = create_memory_entry(
    content="Python是一种高级编程语言",
    context="default",
    message_type="user_input",
    memory_type=MemoryType.SEMANTIC,
    importance_score=0.9
)
state.add_memory(memory)

# Create procedural memory (preference)
memory = create_memory_entry(
    content="用户偏好简洁的回答",
    context="default",
    message_type="user_input",
    memory_type=MemoryType.PROCEDURAL,
    importance_score=0.85
)
state.add_memory(memory)
```

### 自动分类 Automatic Classification

```python
from framework.nodes import classify_memory_type

user_msg = "什么是机器学习？"
assistant_msg = "机器学习是AI的一个分支..."

memory_type, importance = classify_memory_type(user_msg, assistant_msg)
# Returns: (MemoryType.SEMANTIC, 0.7)
```

### 智能检索 Intelligent Retrieval

```python
from framework.nodes import retrieve_mixed_memories

# Retrieve relevant memories for current query
memories = retrieve_mixed_memories(
    state,
    query="如何用Python编程",
    top_k=5
)

# Automatically balances semantic, episodic, and procedural memories
```

## 工作流集成 Workflow Integration

框架的核心节点已更新以支持新的记忆系统：

### Updated Nodes

1. **memory_recall_node**: 使用混合检索策略
2. **memory_storage_node**: 自动分类和存储
3. **create_memory_entry**: 支持新字段

### Example Workflow

```python
from framework.graph import create_simple_base_graph
from framework.state import AgentState, MessageRole

state = AgentState(session_id="user_session")
state.add_message(MessageRole.USER, "什么是人工智能？这很重要")

graph = create_simple_base_graph()
final_state = graph.invoke(state, max_steps=10)

# Memory automatically created and classified
stats = final_state.get_memory_stats()
print(f"Memories created: {stats['total']}")
print(f"Type breakdown: {stats['by_type']}")
```

## 运行演示 Running the Demo

```bash
# Run the comprehensive demo
python memory_types_demo.py
```

演示内容包括：
1. 自动记忆分类
2. 分类检索策略
3. 混合检索
4. 完整工作流
5. 统计分析

## 高级配置 Advanced Configuration

### Custom Classification Rules

可以扩展 `classify_memory_type` 函数以使用LLM进行更智能的分类：

```python
def classify_memory_type_with_llm(user_input: str, assistant_response: str):
    # Call LLM to classify memory type
    # Return (MemoryType, importance_score)
    pass
```

### Embedding-Based Semantic Search

可以增强语义检索使用向量嵌入：

```python
def retrieve_semantic_memories_with_embeddings(state, query, top_k=3):
    # Use embeddings for similarity search
    # More accurate than keyword matching
    pass
```

### Time-Based Episodic Summarization

可以实现情节记忆的自动摘要：

```python
def summarize_episodic_memories(memories: List[MemoryEntry]) -> str:
    # Summarize long conversation history
    # Reduce context window usage
    pass
```

## 最佳实践 Best Practices

1. **重要性评分 Importance Scoring**
   - 用户明确表示重要的信息 → 0.8-1.0
   - 偏好和规则 → 0.7-0.9
   - 事实知识 → 0.6-0.8
   - 一般对话 → 0.3-0.6

2. **记忆类型选择 Memory Type Selection**
   - 定义、解释 → Semantic
   - 偏好、指令 → Procedural
   - 事件、经历 → Episodic

3. **检索策略 Retrieval Strategy**
   - 知识问答 → Semantic retrieval
   - 对话理解 → Mixed retrieval
   - 行为一致性 → Procedural retrieval

4. **性能优化 Performance Optimization**
   - 定期清理低重要性的旧记忆
   - 使用访问频率优化检索
   - 考虑记忆容量限制

## API Reference

### Core Functions

- `create_memory_entry()`: 创建记忆条目
- `classify_memory_type()`: 自动分类
- `retrieve_semantic_memories()`: 语义检索
- `retrieve_episodic_memories()`: 情节检索
- `retrieve_procedural_memories()`: 程序检索
- `retrieve_mixed_memories()`: 混合检索

### State Methods

- `state.get_memories_by_type()`: 按类型过滤记忆
- `state.get_memory_stats()`: 获取统计信息
- `state.add_memory()`: 添加记忆
- `memory.increment_access()`: 更新访问计数

## 迁移指南 Migration Guide

现有代码可以无缝升级，新字段使用默认值：

```python
# Old code still works
memory = create_memory_entry(
    content="...",
    context="default",
    message_type="user_input"
)
# Automatically uses: memory_type=EPISODIC, importance_score=0.5

# New code with enhanced features
memory = create_memory_entry(
    content="...",
    context="default",
    message_type="user_input",
    memory_type=MemoryType.SEMANTIC,  # Explicit type
    importance_score=0.9               # Custom importance
)
```

## 总结 Summary

这次升级实现了：
- ✅ 三种记忆类型分类系统
- ✅ 自动记忆分类
- ✅ 类型特定的检索策略
- ✅ 重要性评分机制
- ✅ 访问频率跟踪
- ✅ 统计分析功能
- ✅ 向后兼容

这使得系统能够：
- 更好地记住用户偏好和长期信息
- 根据查询类型智能检索相关记忆
- 平衡不同类型记忆的重要性
- 支持更复杂的对话场景
