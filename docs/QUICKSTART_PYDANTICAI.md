# PydanticAI 快速开始指南

## 🚀 快速安装

### 推荐方式：使用自动化脚本

```bash
# Windows PowerShell - 一键设置并运行
.\setup_and_run.ps1 pydantic_ai_demo.py

# 这会自动：
# 1. 创建 venv（如果不存在）
# 2. 激活虚拟环境
# 3. 安装依赖
# 4. 运行脚本
```

### 手动方式

#### 1. 创建并激活虚拟环境

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### 2. 安装依赖

```bash
# 安装核心依赖
pip install pydantic-ai

# 或者使用 requirements.txt
pip install -r requirements.txt

# 安装 LLM provider（根据需要选择）
pip install openai              # OpenAI GPT-4
pip install anthropic           # Anthropic Claude
pip install google-generativeai # Google Gemini
```

#### 3. 配置 API Key

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Linux/Mac
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

或创建 `.env` 文件：
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

> 📖 **完整设置指南**: [SETUP.md](SETUP.md)  
> 💡 **快速激活**: `.\activate.ps1`

### 3. 运行示例

```bash
# 运行完整演示
python pydantic_ai_demo.py

# 运行简单测试
python -c "
import asyncio
from framework.pydantic_agent import MemoryAgentWorkflow

async def main():
    workflow = MemoryAgentWorkflow()
    session_id = workflow.create_session()
    response = await workflow.chat(session_id, 'Hello!')
    print(response)

asyncio.run(main())
"
```

---

## 📖 基础使用

### 创建会话

```python
from framework.pydantic_agent import MemoryAgentWorkflow

# 创建 workflow
workflow = MemoryAgentWorkflow(
    model='openai:gpt-4o-mini',  # 或 'anthropic:claude-3-5-sonnet-latest'
    enable_summarization=True
)

# 创建会话
session_id = workflow.create_session()
```

### 对话

```python
# 发送消息
response = await workflow.chat(session_id, "My favorite color is blue")

# AI 会自动记住
response = await workflow.chat(session_id, "What's my favorite color?")
# Response: "Your favorite color is blue"
```

### 使用记忆工具

```python
# 存储特定类型的记忆
await workflow.chat(session_id, "Store as semantic: Python is a programming language")
await workflow.chat(session_id, "Store as procedural: I prefer short answers")

# 检索记忆
await workflow.chat(session_id, "Recall all semantic memories")

# 查看统计
await workflow.chat(session_id, "Show me memory statistics")

# 手动压缩
await workflow.chat(session_id, "Compress old memories")
```

---

## 🔧 高级配置

### 自定义压缩策略

```python
from framework.summarization import SummarizationConfig, TriggerPolicy

config = SummarizationConfig(
    trigger_policy=TriggerPolicy.HYBRID,
    count_threshold=20,
    time_window_hours=24,
    token_threshold=2000,
    preserve_recent=5,
    preserve_important=3
)

workflow = MemoryAgentWorkflow(
    enable_summarization=True,
    summarization_config=config
)
```

### 切换模型

```python
# OpenAI
workflow = MemoryAgentWorkflow(model='openai:gpt-4o')

# Anthropic Claude
workflow = MemoryAgentWorkflow(model='anthropic:claude-3-5-sonnet-latest')

# Google Gemini
workflow = MemoryAgentWorkflow(model='gemini:gemini-1.5-pro')

# Local (Ollama)
workflow = MemoryAgentWorkflow(model='ollama:llama3.1')
```

### 获取会话状态

```python
# 获取完整状态
state = workflow.get_session_state(session_id)
print(f"Messages: {len(state.messages)}")
print(f"Memories: {len(state.memories)}")

# 获取统计信息
stats = workflow.get_session_stats(session_id)
print(stats['memory_stats'])
```

---

## 🧪 测试

### 单元测试示例

```python
import pytest
from framework.pydantic_agent import MemoryAgentWorkflow

@pytest.mark.asyncio
async def test_basic_conversation():
    workflow = MemoryAgentWorkflow()
    session_id = workflow.create_session()
    
    # 存储名字
    response = await workflow.chat(session_id, "My name is Alice")
    
    # 检索名字
    response = await workflow.chat(session_id, "What's my name?")
    assert "Alice" in response

@pytest.mark.asyncio
async def test_memory_storage():
    workflow = MemoryAgentWorkflow()
    session_id = workflow.create_session()
    
    # 存储记忆
    await workflow.chat(
        session_id,
        "Store as semantic: The Earth orbits the Sun"
    )
    
    # 验证存储
    stats = workflow.get_session_stats(session_id)
    assert stats['memory_stats']['by_type']['semantic'] > 0

@pytest.mark.asyncio
async def test_auto_summarization():
    from framework.summarization import SummarizationConfig
    
    config = SummarizationConfig(count_threshold=5)
    workflow = MemoryAgentWorkflow(
        enable_summarization=True,
        summarization_config=config
    )
    
    session_id = workflow.create_session()
    
    # 生成足够的对话触发压缩
    for i in range(10):
        await workflow.chat(session_id, f"Message {i}")
    
    # 验证压缩发生
    stats = workflow.get_session_stats(session_id)
    assert stats['memory_stats']['summarized_memories'] > 0
```

运行测试：
```bash
pytest tests/ -v
```

---

## 🐛 调试技巧

### 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pydantic_ai")
```

### 检查工具调用

```python
# PydanticAI 会在日志中显示工具调用
# 查看 agent 选择了哪些工具以及传入了什么参数
```

### 查看内部状态

```python
state = workflow.get_session_state(session_id)

print("Messages:")
for msg in state.messages:
    print(f"  {msg.role}: {msg.content[:50]}...")

print("\nMemories:")
for mem in state.memories.values():
    print(f"  [{mem.memory_type.value}] {mem.content[:50]}...")
```

---

## 🔗 集成到现有项目

### FastAPI 集成

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from framework.pydantic_agent import MemoryAgentWorkflow

app = FastAPI()
workflow = MemoryAgentWorkflow()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    memory_stats: dict

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.session_id not in workflow.sessions:
        workflow.create_session(request.session_id)
    
    response = await workflow.chat(request.session_id, request.message)
    stats = workflow.get_session_stats(request.session_id)
    
    return ChatResponse(
        response=response,
        memory_stats=stats['memory_stats']
    )

@app.post("/sessions")
def create_session():
    session_id = workflow.create_session()
    return {"session_id": session_id}
```

运行服务器：
```bash
uvicorn your_app:app --reload
```

---

## 📚 更多资源

- [PydanticAI 官方文档](https://ai.pydantic.dev/)
- [迁移指南](PYDANTIC_AI_MIGRATION.md) - 从旧系统迁移
- [Memory Types Guide](MEMORY_TYPES_GUIDE.md) - 记忆类型详解
- [Summarization Guide](SUMMARIZATION_GUIDE.md) - 压缩策略详解

---

## ❓ 常见问题

**Q: 需要什么 Python 版本？**
A: Python 3.10+ （PydanticAI 要求）

**Q: 支持离线使用吗？**
A: 支持！使用 Ollama 本地模型：
```python
workflow = MemoryAgentWorkflow(model='ollama:llama3.1')
```

**Q: 如何持久化会话？**
A: 序列化 AgentState：
```python
import json

state = workflow.get_session_state(session_id)
# 保存
with open('session.json', 'w') as f:
    json.dump(state.model_dump(), f)

# 加载
with open('session.json', 'r') as f:
    data = json.load(f)
    state = AgentState(**data)
```

**Q: 性能如何？**
A: 单次对话延迟：
- GPT-4o-mini: ~1-2s
- Claude-3-Haiku: ~1-2s
- Gemini-1.5-flash: ~0.5-1s
- Ollama (local): ~0.5-3s (取决于硬件)

**Q: token 成本如何控制？**
A: 使用自动压缩：
```python
config = SummarizationConfig(
    token_threshold=1000,  # 超过 1000 tokens 触发压缩
    preserve_recent=3       # 保留最近 3 条
)
# 可以节省 40-70% tokens
```

---

## 🎉 开始使用

```bash
# 1. 安装
pip install pydantic-ai openai

# 2. 设置 API key
export OPENAI_API_KEY="sk-..."

# 3. 运行示例
python pydantic_ai_demo.py

# 4. 开始开发！
```

Happy coding! 🚀
