# 项目记忆 - 重要约定和流程

## 🎯 核心原则

### 永远记住的工作流程

```
1. .\activate.ps1              # 激活虚拟环境
2. python your_script.py       # 运行脚本
3. deactivate                  # 完成后退出
```

---

## 📂 环境管理

### ✅ 正确方式

```bash
# 方式 1: 使用自动化脚本（推荐）
.\setup_and_run.ps1 simple_memory.py

# 方式 2: 手动激活
.\activate.ps1
python simple_memory.py
deactivate
```

### ❌ 错误方式

```bash
# ❌ 不要直接用全局 Python
python3.14 simple_memory.py

# ❌ 不要在未激活 venv 时安装包
pip install pydantic-ai

# ✅ 应该先激活
.\venv\Scripts\Activate.ps1
pip install pydantic-ai
```

---

## 🔑 环境变量

### 必须设置的变量

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# 检查是否设置
$env:OPENAI_API_KEY
```

### 可选的变量

```bash
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:GEMINI_API_KEY = "..."
```

---

## 📦 依赖管理

### 核心依赖（必装）

```
pydantic>=2.5.0
pydantic-ai>=0.0.8
```

### 可选依赖

```
openai>=1.0.0              # OpenAI 模型
anthropic>=0.18.0          # Claude 模型
google-generativeai        # Gemini 模型
fastapi>=0.111.0           # API 服务
uvicorn>=0.23.0            # ASGI 服务器
pytest>=7.0.0              # 测试
```

### 快速安装

```bash
# 激活环境后
pip install -r requirements.txt

# 或最小安装
pip install pydantic pydantic-ai openai
```

---

## 🚀 常用命令速查

### 环境管理

```bash
# 创建 venv
python -m venv venv

# 激活 venv (Windows)
.\venv\Scripts\Activate.ps1

# 快速激活
.\activate.ps1

# 退出
deactivate
```

### 运行脚本

```bash
# 推荐：一键运行
.\setup_and_run.ps1 <script_name>

# 手动运行
.\activate.ps1
python <script_name>
```

### 可用的演示脚本

```bash
python simple_memory.py         # 极简版演示（推荐入门）
python comparison.py            # 新旧系统对比
python pydantic_ai_demo.py      # 完整功能演示

# 旧演示已移至 legacy/ 目录
# legacy/memory_types_demo.py   # 不推荐
# legacy/summarization_demo.py  # 不推荐
```

### 测试

```bash
pytest tests/ -v                # 运行所有测试
pytest tests/test_framework.py  # 运行特定测试
pytest --cov=framework tests/   # 带覆盖率
```

---

## 📁 项目结构记忆

### 核心模块（PydanticAI 版本） ⭐

```
framework/
├── state.py              # 数据模型 (MemoryEntry, AgentState)
├── pydantic_agent.py     # ⭐ PydanticAI 实现（新系统）
└── summarization.py      # 记忆压缩

简化文件:
simple_memory.py          # ⭐ 最简实现（150 行）
```

### 已归档（legacy/ 目录）

```
legacy/
├── graph.py              # 📦 旧状态机（已废弃）
├── nodes.py              # 📦 旧节点（已废弃）
├── memory_types_demo.py  # 📦 旧演示
└── summarization_demo.py # 📦 旧演示
```

**重要：不要再使用 legacy/ 中的代码！**

### 环境配置

```
venv/                     # 虚拟环境（不提交到 git）
requirements.txt          # 依赖清单
.gitignore               # Git 忽略规则
.env                     # 环境变量（不提交到 git）
```

### 文档

```
SETUP.md                 # ⭐ 环境设置指南
README_PYDANTICAI.md     # ⭐ 主文档
QUICKSTART_PYDANTICAI.md # 快速开始
PYDANTIC_AI_MIGRATION.md # 迁移指南
BEFORE_AFTER_COMPARISON.md # 代码对比
MEMORY_TYPES_GUIDE.md    # 记忆类型
SUMMARIZATION_GUIDE.md   # 压缩策略
PROJECT_MEMORY.md        # 📍 你现在在这里
```

---

## 🔍 问题排查清单

### 问题 1: ModuleNotFoundError

```bash
# 症状
ModuleNotFoundError: No module named 'pydantic'

# 原因
未激活 venv 或未安装依赖

# 解决
.\activate.ps1
pip install -r requirements.txt
```

### 问题 2: 脚本执行策略错误

```bash
# 症状
无法加载文件，因为在此系统上禁止运行脚本

# 解决
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 3: API Key 未设置

```bash
# 症状
Error: OPENAI_API_KEY not set

# 解决
$env:OPENAI_API_KEY = "sk-..."

# 或创建 .env 文件
echo 'OPENAI_API_KEY=sk-...' > .env
```

### 问题 4: venv 损坏

```bash
# 删除重建
Remove-Item -Recurse -Force venv
python -m venv venv
.\activate.ps1
pip install -r requirements.txt
```

---

## 🎓 开发约定

### 代码风格

1. **优先使用 PydanticAI**
   - 新功能用 `pydantic_agent.py`
   - 不要再扩展 `graph.py` 和 `nodes.py`

2. **类型安全**
   - 使用 Pydantic models
   - 添加类型提示
   - 验证输入输出

3. **工具模式**
   ```python
   @memory_agent.tool
   async def new_feature(ctx: RunContext[MemoryDeps], param: str) -> str:
       """清晰的 docstring"""
       # 实现
       return result
   ```

### Git 约定

1. **不提交的文件**
   ```
   venv/          # 虚拟环境
   __pycache__/   # Python 缓存
   .env           # 环境变量
   *.log          # 日志文件
   memories.json  # 运行时数据
   ```

2. **提交前检查**
   ```bash
   # 运行测试
   pytest tests/ -v
   
   # 检查格式
   black framework/ --check
   
   # 类型检查
   mypy framework/
   ```

---

## 📊 性能基线

### 代码量对比

```
旧系统:
  graph.py + nodes.py     ~518 lines
  API 层                  ~100 lines
  总计                    ~888 lines

新系统 (PydanticAI):
  simple_memory.py        ~150 lines
  pydantic_agent.py       ~200 lines
  总计                    ~350 lines

节省: 60% 代码量
```

### 运行性能

```
单次对话延迟:
  GPT-4o-mini:   ~1-2s
  Claude-Haiku:  ~1-2s
  Gemini-Flash: ~0.5-1s

压缩效果:
  token 节省:    40-70%
  memory 减少:   60-80%
```

---

## 🎯 下一步计划

### 短期（1周）
- [ ] 完成单元测试覆盖
- [ ] 添加集成测试
- [ ] 性能基准测试

### 中期（1月）
- [ ] 向量检索集成（可选）
- [ ] 多模型支持完善
- [ ] 监控和日志

### 长期
- [ ] 分布式 memory 支持
- [ ] 插件系统
- [ ] 可视化工具

---

## 💡 快速参考

### 最常用的 3 个命令

```bash
1. .\activate.ps1                  # 激活环境
2. python simple_memory.py         # 运行演示
3. deactivate                      # 退出环境
```

### 新手第一次运行

```bash
# Step 1: 一键启动
.\setup_and_run.ps1 simple_memory.py

# Step 2: 查看文档
cat QUICKSTART_PYDANTICAI.md

# Step 3: 尝试修改
# 编辑 simple_memory.py，添加你的功能

# Step 4: 运行测试
pytest tests/ -v
```

---

## 🔗 相关资源

- [PydanticAI 官方文档](https://ai.pydantic.dev/)
- [Pydantic v2 文档](https://docs.pydantic.dev/latest/)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [项目仓库](https://github.com/saga/llm-memory)

---

**📌 记住：永远先激活 venv，再运行脚本！**

```bash
.\activate.ps1  # 这是你的肌肉记忆
```
