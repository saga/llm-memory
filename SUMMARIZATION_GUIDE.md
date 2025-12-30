# Memory Summarization & Compression

## 概述 Overview

随着对话变长，会产生大量冗余信息，导致Token成本上升和检索质量下降。本框架引入了**Memory Summarization（记忆摘要）**和**Compression（压缩）**机制，通过智能合并和摘要历史记录来优化长期记忆管理。

As conversations grow longer, redundant information accumulates, leading to increased token costs and reduced retrieval quality. This framework introduces **Memory Summarization** and **Compression** mechanisms to optimize long-term memory management through intelligent consolidation and summarization of historical records.

## 核心优势 Key Benefits

### 1. 控制Token成本 Control Token Costs
- 自动压缩冗余记忆，减少存储空间
- 降低LLM调用时的上下文开销
- 典型压缩率：40-70%

### 2. 提高召回质量 Improve Recall Quality
- 摘要比原始文本信息密度更高
- 去除冗余，保留关键信息
- 更好的语义一致性

### 3. 支持长期对话 Enable Long-term Conversations
- 无限期保持对话历史
- 避免记忆爆炸问题
- 保持系统性能稳定

### 4. 灵活的策略 Flexible Policies
- 多种触发条件（时间/数量/Token）
- 可自定义保留规则
- 支持手动和自动模式

## 架构设计 Architecture

### 新增字段 New Fields

#### MemoryEntry 扩展
```python
class MemoryEntry(BaseModel):
    # ... existing fields ...
    
    # Summarization fields
    is_summarized: bool = False              # 是否已摘要
    original_content: Optional[str] = None   # 原始内容（如已摘要）
    summarized_at: Optional[datetime] = None # 摘要时间
    source_memory_ids: List[str] = []        # 源记忆IDs（合并时）
    token_estimate: Optional[int] = None     # Token估计
```

#### 新增枚举类型
```python
class SummarizationTrigger(str, Enum):
    TIME_BASED = "time_based"      # 基于时间
    COUNT_BASED = "count_based"    # 基于数量
    TOKEN_BASED = "token_based"    # 基于Token
    MANUAL = "manual"              # 手动触发
    HYBRID = "hybrid"              # 混合策略
```

### 摘要配置 Summarization Configuration

```python
class SummarizationConfig:
    trigger: SummarizationTrigger = HYBRID
    max_episodic_age_hours: float = 24.0        # 最大年龄（小时）
    max_episodic_count: int = 20                # 最大情节记忆数
    max_total_tokens: int = 4000                # Token上限
    min_memories_to_summarize: int = 3          # 最小摘要数量
    preserve_recent_count: int = 5              # 保留最近N条
    preserve_high_importance: bool = True       # 保留高重要性
    importance_threshold: float = 0.8           # 重要性阈值
```

## 触发策略 Trigger Strategies

### 1. 基于数量 Count-Based
```python
config = SummarizationConfig(
    trigger=SummarizationTrigger.COUNT_BASED,
    max_episodic_count=20  # 超过20条情节记忆时触发
)
```

**使用场景**：对话密集型应用，需要控制记忆条目数量

### 2. 基于时间 Time-Based
```python
config = SummarizationConfig(
    trigger=SummarizationTrigger.TIME_BASED,
    max_episodic_age_hours=24  # 超过24小时的记忆触发摘要
)
```

**使用场景**：长期运行的系统，定期归档旧记忆

### 3. 基于Token Token-Based
```python
config = SummarizationConfig(
    trigger=SummarizationTrigger.TOKEN_BASED,
    max_total_tokens=4000  # 总Token超过4000时触发
)
```

**使用场景**：严格控制成本的场景

### 4. 混合策略 Hybrid (推荐)
```python
config = SummarizationConfig(
    trigger=SummarizationTrigger.HYBRID,
    max_episodic_count=20,
    max_episodic_age_hours=24,
    max_total_tokens=4000
)
```

**使用场景**：生产环境，综合多个条件判断

## 使用方法 Usage

### 基础用法 Basic Usage

#### 手动压缩
```python
from framework.summarization import compress_memories, SummarizationConfig

state = AgentState(session_id="session_123")
# ... add memories ...

config = SummarizationConfig(
    preserve_recent_count=5,
    min_memories_to_summarize=3
)

new_state, stats = compress_memories(state, config=config)

print(f"压缩了 {stats['memories_compressed']} 条记忆")
print(f"节省 {stats['tokens_saved']} tokens")
print(f"压缩率 {stats['compression_ratio']}%")
```

#### 自动压缩（工作流集成）
```python
from framework.graph import create_simple_base_graph

# 创建启用摘要的工作流
graph = create_simple_base_graph(enable_summarization=True)

state = AgentState(session_id="session_123")
state.add_message(MessageRole.USER, "你好")

# 工作流会自动检查并执行压缩
final_state = graph.invoke(state, max_steps=10)
```

### 高级配置 Advanced Configuration

#### 选择性保留策略
```python
config = SummarizationConfig(
    preserve_recent_count=5,          # 保留最近5条
    preserve_high_importance=True,    # 保留重要记忆
    importance_threshold=0.8,         # 重要性阈值
    min_memories_to_summarize=3       # 至少3条才摘要
)
```

**保留规则**：
1. 最近的N条记忆（默认5条）
2. 重要性≥阈值的记忆（默认0.8）
3. 非Episodic类型的记忆（Semantic和Procedural通常保留）

#### 检查是否应触发摘要
```python
from framework.summarization import should_trigger_summarization

should_trigger, reason = should_trigger_summarization(state, config)

if should_trigger:
    print(f"应触发摘要，原因: {reason}")
    # reason可能是: "count_exceeded", "time_exceeded", "token_limit_exceeded"
```

#### 手动选择要摘要的记忆
```python
from framework.summarization import select_memories_for_summarization

memories_to_summarize = select_memories_for_summarization(state, config)
print(f"将摘要 {len(memories_to_summarize)} 条记忆")
```

### 压缩统计 Compression Statistics

```python
from framework.summarization import get_compression_stats

stats = get_compression_stats(state)

print(f"总记忆数: {stats['total_memories']}")
print(f"摘要记忆数: {stats['summarized_memories']}")
print(f"摘要率: {stats['summarization_rate']}%")
print(f"总Token数: {stats['total_tokens']}")
print(f"节省Token数: {stats['estimated_tokens_saved']}")
print(f"平均压缩率: {stats['average_compression_ratio']}%")
```

## 摘要方法 Summarization Methods

### 当前实现：提取式摘要 Extractive Summarization

当前版本使用简单的提取式摘要（不需要LLM）：

```python
def _extractive_summarize(memories: List[MemoryEntry]) -> str:
    # 1. 时间范围
    # 2. 提取高重要性/高访问频率的关键记忆
    # 3. 生成结构化摘要
```

**示例输出**：
```
[摘要] 6条对话记录 (2025-12-30 10:00 - 12:30)
  1. 用户询问了Python装饰器的概念...
  2. 讨论了装饰器的参数传递...
  3. 用户分享了学习心得...
  ... 还有 3 条相关对话
```

### 未来扩展：LLM摘要 LLM-based Summarization

框架预留了LLM摘要接口：

```python
def _llm_summarize(memories: List[MemoryEntry]) -> str:
    """
    调用LLM生成高质量摘要
    
    提示词示例：
    请总结以下对话历史，保留关键信息和重要细节：
    
    {conversation_history}
    
    总结应该：
    1. 简洁但信息密度高
    2. 保留用户的关键需求和偏好
    3. 保留重要的事实和决策
    """
    # 实现LLM调用
```

**启用LLM摘要**：
```python
new_state, stats = compress_memories(
    state,
    config=config,
    use_llm=True  # 启用LLM摘要
)
```

## 工作流集成 Workflow Integration

### 添加摘要节点

摘要节点已集成到框架的工作流中：

```python
# framework/nodes.py
def memory_summarization_node(state: AgentState, auto_trigger: bool = True) -> AgentState:
    """定期压缩和摘要记忆以控制Token成本"""
    # 自动检查和执行压缩
    # 记录压缩事件到系统消息
```

### 工作流配置

```python
# 方式1: 启用摘要的工作流
graph = create_simple_base_graph(enable_summarization=True)

# 方式2: 自定义工作流
builder = SimpleStateMachine()
builder.add_node("memory_storage", memory_storage_node)
builder.add_node("memory_summarization", memory_summarization_node)
builder.add_edge("memory_storage", "memory_summarization")
```

### 执行流程

```
planner → memory_recall → decision → response_generator 
    → memory_storage → memory_summarization → [check routing]
```

每次对话后，摘要节点会：
1. 检查是否满足触发条件
2. 如果满足，执行压缩
3. 记录压缩事件到系统消息
4. 更新状态

## 性能优化 Performance Optimization

### 1. Token估计 Token Estimation

```python
# 快速估计（~4字符/token）
token_count = memory.estimate_tokens()

# 精确计算（使用tokenizer）
import tiktoken
encoder = tiktoken.encoding_for_model("gpt-4")
token_count = len(encoder.encode(memory.content))
```

### 2. 批量压缩 Batch Compression

```python
# 一次处理多个会话
sessions = [state1, state2, state3]
results = []

for session_state in sessions:
    new_state, stats = compress_memories(session_state, config)
    results.append((new_state, stats))
```

### 3. 定时任务 Scheduled Compression

```python
import schedule

def compress_all_sessions():
    # 获取所有活跃会话
    # 执行压缩
    pass

# 每小时执行一次
schedule.every(1).hours.do(compress_all_sessions)
```

## 实际案例 Real-world Examples

### 案例1：客服系统
```python
# 配置：保留最近对话，归档旧对话
config = SummarizationConfig(
    trigger=SummarizationTrigger.HYBRID,
    max_episodic_count=15,
    max_episodic_age_hours=8,
    preserve_recent_count=5,
    preserve_high_importance=True,
    importance_threshold=0.9  # 保留高优先级问题
)
```

### 案例2：教育助手
```python
# 配置：保留知识点，压缩练习对话
config = SummarizationConfig(
    trigger=SummarizationTrigger.TOKEN_BASED,
    max_total_tokens=3000,
    preserve_recent_count=3,
    preserve_high_importance=True,
    importance_threshold=0.85
)

# 手动标记重要内容
for mem in state.memories.values():
    if is_knowledge_point(mem.content):
        mem.importance_score = 0.95  # 不会被压缩
```

### 案例3：代码助手
```python
# 配置：定期清理，保留代码片段
config = SummarizationConfig(
    trigger=SummarizationTrigger.HYBRID,
    max_episodic_count=20,
    max_episodic_age_hours=72,
    preserve_recent_count=10,  # 保留更多最近对话
    preserve_high_importance=True
)
```

## 监控与调试 Monitoring & Debugging

### 压缩事件日志

系统会自动记录压缩事件：

```python
# 查找压缩事件
compression_events = [
    msg for msg in state.messages
    if msg.role == MessageRole.SYSTEM and '记忆压缩' in msg.content
]

for event in compression_events:
    print(event.content)
    print(event.metadata)  # 包含详细统计信息
```

### 可视化统计

```python
import matplotlib.pyplot as plt

# 收集历史统计
history = []
for i in range(100):
    state.add_message(...)
    state, stats = compress_memories(state, config)
    history.append({
        'step': i,
        'total_memories': len(state.memories),
        'total_tokens': sum(m.estimate_tokens() for m in state.memories.values())
    })

# 绘制趋势
plt.plot([h['step'] for h in history], [h['total_tokens'] for h in history])
plt.xlabel('Conversation Steps')
plt.ylabel('Total Tokens')
plt.title('Memory Token Usage Over Time')
plt.show()
```

## 最佳实践 Best Practices

### 1. 配置选择

| 场景 | 推荐配置 |
|------|---------|
| 短期对话（<1天） | `max_episodic_count=15, preserve_recent_count=5` |
| 中期对话（1-7天） | `max_episodic_age_hours=24, preserve_recent_count=10` |
| 长期对话（>7天） | `max_total_tokens=3000, hybrid trigger` |
| 成本敏感 | `max_total_tokens=2000, token_based trigger` |

### 2. 重要性评分指南

| 重要性 | 分数范围 | 内容类型 |
|--------|---------|---------|
| 非常重要 | 0.9-1.0 | 用户偏好、关键决策、重要事实 |
| 重要 | 0.7-0.9 | 有价值的信息、常用知识 |
| 一般 | 0.5-0.7 | 普通对话、中等价值 |
| 低重要性 | 0.3-0.5 | 闲聊、临时信息 |
| 可删除 | 0.0-0.3 | 冗余、过时信息 |

### 3. 触发时机

```python
# ✅ 推荐：混合策略
config = SummarizationConfig(
    trigger=SummarizationTrigger.HYBRID,
    max_episodic_count=20,      # 防止数量爆炸
    max_total_tokens=4000,      # 控制成本
    max_episodic_age_hours=24   # 定期归档
)

# ❌ 不推荐：过于激进
config = SummarizationConfig(
    max_episodic_count=5,  # 太少，会丢失上下文
    preserve_recent_count=1
)
```

### 4. 保留策略

```python
# ✅ 平衡保留
config = SummarizationConfig(
    preserve_recent_count=5,          # 保留足够上下文
    preserve_high_importance=True,    # 保留重要信息
    importance_threshold=0.8          # 合理阈值
)

# ❌ 过度保留
config = SummarizationConfig(
    preserve_recent_count=20,  # 太多，压缩效果差
    importance_threshold=0.3   # 太低，几乎都保留
)
```

## 运行演示 Run the Demo

```bash
python summarization_demo.py
```

演示内容包括：
1. 基础摘要功能
2. 不同触发策略
3. 选择性保留
4. 长期对话压缩
5. 工作流集成
6. 内容对比

## 未来扩展 Future Enhancements

### 1. LLM摘要集成
```python
# 使用OpenAI/Anthropic API生成高质量摘要
def llm_summarize_with_openai(memories):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "总结以下对话，保留关键信息..."
        }]
    )
    return response.choices[0].message.content
```

### 2. 层次化摘要
```python
# 多级摘要：日摘要 → 周摘要 → 月摘要
class HierarchicalSummarization:
    def create_daily_summary()
    def create_weekly_summary()
    def create_monthly_summary()
```

### 3. 主题聚类
```python
# 根据主题聚类后再摘要
from sklearn.cluster import KMeans
# 对记忆进行聚类
# 每个聚类独立摘要
```

### 4. 智能重要性学习
```python
# 使用ML模型学习重要性评分
class ImportancePredictor:
    def train(self, feedback_data)
    def predict_importance(self, memory)
```

## API Reference

### Core Functions

#### compress_memories
```python
def compress_memories(
    state: AgentState,
    config: Optional[SummarizationConfig] = None,
    use_llm: bool = False
) -> Tuple[AgentState, Dict[str, Any]]
```

#### should_trigger_summarization
```python
def should_trigger_summarization(
    state: AgentState,
    config: SummarizationConfig
) -> Tuple[bool, str]
```

#### select_memories_for_summarization
```python
def select_memories_for_summarization(
    state: AgentState,
    config: SummarizationConfig
) -> List[MemoryEntry]
```

#### get_compression_stats
```python
def get_compression_stats(
    state: AgentState
) -> Dict[str, Any]
```

### MemoryEntry Methods

#### estimate_tokens
```python
def estimate_tokens(self) -> int
    """估计Token数量（~4字符/token）"""
```

#### summarize
```python
def summarize(
    self,
    summary_content: str,
    source_ids: Optional[List[str]] = None
) -> None
    """标记为已摘要并存储原始内容"""
```

## 总结 Summary

Memory Summarization是生产环境LLM系统的必备功能：

✅ **成本控制**：减少40-70%的Token使用  
✅ **质量提升**：信息密度更高的摘要  
✅ **长期支持**：无限期对话历史  
✅ **灵活配置**：多种策略适应不同场景  
✅ **无缝集成**：自动化工作流  
✅ **可监控**：详细的统计和日志

这使得系统能够：
- 支持长期运行的对话系统
- 有效控制LLM调用成本
- 保持高质量的记忆检索
- 适应各种业务场景
