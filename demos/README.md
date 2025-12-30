# Demos - 演示示例

本目录包含所有演示脚本，展示 LLM Memory System 的各种功能。

---

## 🚀 快速运行

```bash
# 使用自动化脚本（推荐）
.\setup_and_run.ps1 simple_memory.py
.\setup_and_run.ps1 comparison.py
.\setup_and_run.ps1 pydantic_ai_demo.py

# 或手动运行
.\activate.ps1
python demos/simple_memory.py
python demos/comparison.py
python demos/pydantic_ai_demo.py
```

---

## 📱 演示列表

### ⭐ 推荐入门

**`simple_memory.py`** - 极简实现（150 lines）
- 展示如何用 PydanticAI 实现完整的记忆系统
- Memory = Typed State 概念
- 自动化工具调用
- 代码量对比分析

**用途：** 理解核心概念，学习最佳实践

```bash
.\setup_and_run.ps1 simple_memory.py
```

---

### 🔍 系统对比

**`comparison.py`** - 新旧系统对比
- 新旧架构并排对比
- 代码量统计（518 → 200 lines）
- 功能对比表格
- 真实使用场景
- 迁移建议

**用途：** 理解 PydanticAI 的价值

```bash
.\setup_and_run.ps1 comparison.py
```

---

### 🎨 完整演示

**`pydantic_ai_demo.py`** - 完整功能演示
- 基础对话流程
- 显式工具使用
- 自动压缩演示
- 不同记忆类型
- API 简化对比

**用途：** 查看所有功能的实际运行

**需要：** OpenAI API Key

```bash
$env:OPENAI_API_KEY = "sk-..."
.\setup_and_run.ps1 pydantic_ai_demo.py
```

---

## 📊 演示特性对比

| 演示 | 代码行数 | API Key | 用途 | 难度 |
|------|----------|---------|------|------|
| `simple_memory.py` | 150 | ❌ | 学习核心概念 | ⭐ |
| `comparison.py` | 300 | ❌ | 理解价值 | ⭐ |
| `pydantic_ai_demo.py` | 400 | ✅ | 查看完整功能 | ⭐⭐ |

---

## 💡 学习路径

### 第一步：理解核心概念
```bash
python demos/simple_memory.py
```
学习：Memory = Typed State, 工具自动调用

### 第二步：对比新旧系统
```bash
python demos/comparison.py
```
理解：为什么 PydanticAI 更好

### 第三步：实际运行
```bash
$env:OPENAI_API_KEY = "sk-..."
python demos/pydantic_ai_demo.py
```
体验：完整功能

### 第四步：开发自己的应用
参考 `simple_memory.py` 的实现

---

## 🔗 相关文档

- [../docs/QUICKSTART_PYDANTICAI.md](../docs/QUICKSTART_PYDANTICAI.md) - 快速入门
- [../docs/README_PYDANTICAI.md](../docs/README_PYDANTICAI.md) - 完整文档
- [../docs/BEFORE_AFTER_COMPARISON.md](../docs/BEFORE_AFTER_COMPARISON.md) - 代码对比
- [../docs/PROJECT_MEMORY.md](../docs/PROJECT_MEMORY.md) - 项目约定

---

## 🎯 快速命令

```bash
# 查看所有演示
Get-ChildItem demos/*.py

# 运行特定演示
.\setup_and_run.ps1 <demo_name>.py

# 激活环境后运行
.\activate.ps1
python demos/<demo_name>.py
```
