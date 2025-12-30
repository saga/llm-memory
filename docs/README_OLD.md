# 🧠 LLM Memory System

**简洁、类型安全、生产就绪的 LLM 长期记忆系统**

---

## 🚀 快速开始

```bash
# 一键启动
.\setup_and_run.ps1 simple_memory.py

# 或查看快速开始指南
cat docs/START_HERE.md
```

---

## 📚 文档

所有文档已移至 **`docs/`** 目录：

| 文档 | 描述 |
|------|------|
| **[docs/START_HERE.md](docs/START_HERE.md)** | ⭐ 30 秒快速开始 |
| [docs/SETUP.md](docs/SETUP.md) | 环境设置完整指南 |
| [docs/README_PYDANTICAI.md](docs/README_PYDANTICAI.md) | 主文档 - 完整功能介绍 |
| [docs/QUICKSTART_PYDANTICAI.md](docs/QUICKSTART_PYDANTICAI.md) | 快速入门教程 |
| [docs/PROJECT_MEMORY.md](docs/PROJECT_MEMORY.md) | 项目约定和记忆 |
| [docs/PYDANTIC_AI_MIGRATION.md](docs/PYDANTIC_AI_MIGRATION.md) | 迁移指南 |
| [docs/BEFORE_AFTER_COMPARISON.md](docs/BEFORE_AFTER_COMPARISON.md) | 代码对比分析 |

---

## 🎨 演示示例

所有演示已移至 **`demos/`** 目录：

```bash
# 极简实现演示（推荐入门）
.\setup_and_run.ps1 simple_memory.py

# 新旧系统对比
.\setup_and_run.ps1 comparison.py

# 完整功能演示
.\setup_and_run.ps1 pydantic_ai_demo.py
```

---

## 📁 项目结构

```
llm-memory/
├── demos/                      # 📱 演示示例
│   ├── simple_memory.py       # ⭐ 极简实现（150 lines）
│   ├── pydantic_ai_demo.py    # 完整功能演示
│   ├── comparison.py          # 新旧系统对比
│   ├── simple_demo.py         # 基础演示
│   └── financial_demo.py      # 金融场景演示
│
├── docs/                       # 📖 文档
│   ├── START_HERE.md          # ⭐ 快速开始
│   ├── SETUP.md               # 环境设置
│   ├── README_PYDANTICAI.md   # 主文档
│   ├── PROJECT_MEMORY.md      # 项目记忆
│   └── ...更多文档...
│
├── framework/                  # 🎯 核心框架
│   ├── state.py               # 数据模型
│   ├── summarization.py       # 压缩功能
│   └── pydantic_agent.py      # PydanticAI 实现
│
├── legacy/                     # 📦 旧代码归档
│   └── ...已废弃的代码...
│
├── tests/                      # 🧪 测试
├── app/                        # 🌐 API 应用
├── activate.ps1                # 快速激活脚本
└── setup_and_run.ps1          # 一键启动脚本
```

---

## ✨ 核心特性

- **多种记忆类型**：语义（事实）、情景（事件）、程序性（偏好）
- **智能召回**：基于记忆类型的优化检索策略
- **自动压缩**：4 种触发策略，节省 40-70% tokens
- **60% 代码减少**：从 888 行降至 350 行
- **完全类型安全**：Pydantic v2 验证
- **3 行 API**：创建、会话、聊天

---

## 💡 使用示例

```python
from framework.pydantic_agent import MemoryAgentWorkflow
import asyncio

async def main():
    # 3 行开始使用
    workflow = MemoryAgentWorkflow()
    session_id = workflow.create_session()
    response = await workflow.chat(session_id, "Hello!")
    print(response)

asyncio.run(main())
```

---

## 📊 代码简化效果

| 指标 | 旧系统 | 新系统 | 改进 |
|------|--------|--------|------|
| 核心代码 | 888 lines | 350 lines | **-60%** |
| API 复杂度 | 7-8 steps | 3 lines | **-80%** |
| Framework | 6 files | 3 files | **-50%** |

---

## 🎯 立即开始

1. **查看快速指南**
   ```bash
   cat docs/START_HERE.md
   ```

2. **运行演示**
   ```bash
   .\setup_and_run.ps1 simple_memory.py
   ```

3. **阅读完整文档**
   ```bash
   cat docs/README_PYDANTICAI.md
   ```

---

## 📄 许可

MIT License

---

**更多信息请查看 [docs/](docs/) 目录**
