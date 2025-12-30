# LLM Memory System - Pydantic + LangGraph Implementation

基于Pydantic + LangGraph范式的LLM Memory系统，专为金融科技场景设计，确保确定性结果和审计友好。

## 核心特性

### 🔒 强一致性保证
- **Pydantic State**: 强类型状态模型，防止脏写
- **确定性执行**: 每个节点都是纯函数，无隐式状态修改
- **版本控制**: 状态变更可追踪，支持完整replay

### 📊 审计友好
- **Append-only存储**: SQLite审计日志，不可篡改
- **合规检查**: 内置金融合规规则
- **状态完整性验证**: 哈希校验确保数据完整性

### 🧠 智能记忆
- **上下文感知**: 基于对话上下文检索相关记忆
- **确定性ID**: 相同内容生成相同ID，避免重复
- **敏感信息过滤**: 自动过滤密码等敏感信息

### 🏦 金融专用
- **风险评估**: 内置风险承受能力评估
- **投资建议合规**: 符合金融监管要求
- **产品限制**: 支持投资产品白名单/黑名单

## 系统架构

```
Agent Runtime
├── LangGraph
│   ├── Node = 纯函数
│   ├── Edge = Policy  
│   └── State = Pydantic Model
├── Pydantic
│   ├── State Schema
│   ├── Validation
│   └── Versioning
└── Audit / Persistence
    └── SQLite（append-only）
```

## 快速开始

### 1. 安装依赖

```bash
pip install openai langgraph pydantic python-dotenv
```

### 2. 设置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
```

### 3. 基础使用

```python
from chat_api_v2 import LLMChatWithMemoryV2

# 初始化系统
chat = LLMChatWithMemoryV2(
    model="gpt-3.5-turbo",
    temperature=0.1,  # 低温度确保确定性
    audit_log_path="audit.db"
)

# 创建会话
session_id = chat.create_session(
    user_id="user_001",
    context="financial_advisory"
)

# 发送消息
result = chat.chat_completion(
    session_id=session_id,
    user_input="我的风险承受能力如何？",
    system_prompt="你是一个专业的金融顾问"
)

print(result["response"])
```

### 4. 金融专用功能

```python
from chat_api_v2 import FinancialLLMChat

# 初始化金融专用系统
financial_chat = FinancialLLMChat()

# 设置风险画像
financial_chat.set_risk_profile(
    session_id=session_id,
    risk_level="medium",
    factors={
        "age": 35,
        "income": "stable",
        "investment_experience": "moderate"
    }
)

# 设置投资限制
financial_chat.set_investment_limit(session_id, 100000)
financial_chat.add_approved_products(session_id, ["mutual_funds", "bonds"])
financial_chat.add_restricted_products(session_id, ["derivatives", "crypto"])
```

## 核心组件

### State Models (`state.py`)
- `AgentState`: 基础代理状态
- `FinancialAgentState`: 金融专用状态
- `Message`: 消息模型
- `MemoryEntry`: 记忆条目

### Nodes (`nodes.py`)
- `planner_node`: 规划器节点
- `memory_recall_node`: 记忆召回节点
- `decision_node`: 决策节点
- `response_generator_node`: 响应生成节点
- `memory_storage_node`: 记忆存储节点
- `compliance_check_node`: 合规检查节点

### Policy (`policy.py`)
- `next_step_policy`: 下一步决策策略
- `compliance_policy`: 合规检查策略
- `memory_retention_policy`: 记忆保留策略
- `risk_assessment_policy`: 风险评估策略

### Audit (`audit.py`)
- `AuditLog`: 基础审计日志
- `FinancialAuditLog`: 金融专用审计日志

### Graph (`graph.py`)
- 状态机定义和编译
- 工作流执行

## 审计功能

### 会话历史
```python
history = chat.get_session_history(session_id, limit=50)
for step in history:
    print(f"步骤 {step['step']}: {step['transition_type']}")
```

### 合规报告
```python
report = chat.get_compliance_report(session_id)
print(f"总检查数: {report['total_checks']}")
print(f"通过检查: {report['passed_checks']}")
print(f"失败检查: {report['failed_checks']}")
```

### 完整性验证
```python
integrity = chat.verify_session_integrity(session_id)
print(f"会话完整性: {'✅ 通过' if integrity else '❌ 失败'}")
```

## 记忆搜索

```python
# 搜索相关记忆
memories = chat.search_memories(session_id, "风险", limit=5)
for memory in memories:
    print(f"[{memory['timestamp']}] {memory['content']}")
```

## 确定性保证

### 1. 确定性ID生成
```python
# 相同内容生成相同ID
memory_id = hashlib.md5(f"{content}|{context}|{timestamp}".encode()).hexdigest()
```

### 2. 低温度设置
```python
temperature=0.1  # 确保LLM响应的一致性
```

### 3. 纯函数节点
```python
def planner_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)  # 不修改原状态
    # ... 处理逻辑
    return new_state
```

## 测试

运行测试套件：
```bash
python test_memory_system.py
```

## 生产部署建议

### 1. 状态持久化
- 使用Redis或PostgreSQL持久化状态
- 实现状态恢复机制

### 2. 水平扩展
- 状态存储在共享存储中
- 支持无状态服务部署

### 3. 监控告警
- 监控合规检查失败率
- 监控状态完整性验证失败

### 4. 备份策略
- 定期备份审计数据库
- 实现状态快照机制

## 合规要求

### 金融监管
- 风险充分披露
- 禁止收益保证
- 适当性管理

### 数据保护
- 敏感信息过滤
- 数据最小化原则
- 审计日志保护

## 扩展性

### 自定义节点
```python
def custom_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    # 自定义逻辑
    return new_state
```

### 自定义策略
```python
def custom_policy(state: AgentState) -> str:
    # 自定义决策逻辑
    return "next_node"
```

### 自定义状态
```python
class CustomAgentState(AgentState):
    custom_field: str = ""
    # 添加自定义字段和方法
```

## 许可证

MIT License