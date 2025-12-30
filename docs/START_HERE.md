# 🎯 快速开始 - 30 秒上手指南

## ✨ 一键运行（推荐）

```powershell
# 自动设置并运行演示
.\setup_and_run.ps1 comparison.py
```

**这个命令会自动：**
- ✅ 创建虚拟环境（如果不存在）
- ✅ 激活环境
- ✅ 安装依赖
- ✅ 运行脚本

---

## 📖 手动运行

### 步骤 1: 激活环境

```powershell
.\activate.ps1
```

### 步骤 2: 运行演示

```powershell
# 查看新旧系统对比
python comparison.py

# 查看极简实现（150 行）
python simple_memory.py

# 查看完整演示（需要 API Key）
$env:OPENAI_API_KEY = "sk-..."
python pydantic_ai_demo.py
```

### 步骤 3: 完成后退出

```powershell
deactivate
```

---

## 📚 重要文档

| 文档 | 用途 |
|------|------|
| **PROJECT_MEMORY.md** | 📍 **项目约定和记忆** - 永远先看这个 |
| SETUP.md | 环境设置详细指南 |
| BEFORE_AFTER_COMPARISON.md | 真实代码对比分析 |
| README_PYDANTICAI.md | 完整功能文档 |
| QUICKSTART_PYDANTICAI.md | 快速入门教程 |

---

## 🎯 核心文件

### 新系统（PydanticAI - 推荐）

```
simple_memory.py              # ⭐ 150 行极简实现
framework/pydantic_agent.py   # 200 行完整实现
```

### 旧系统（已废弃）

```
framework/graph.py            # ⚠️ 状态机（518 行）
framework/nodes.py            # ⚠️ 手动节点
```

---

## 💡 永远记住

### 工作流程

```powershell
.\activate.ps1        # 1. 激活环境
python script.py      # 2. 运行脚本
deactivate           # 3. 退出环境
```

### 或者一键启动

```powershell
.\setup_and_run.ps1 <script_name>
```

---

## 🎉 已完成的工作

✅ **代码简化 60%**（888 → 350 lines）  
✅ **环境自动化**（setup_and_run.ps1 + activate.ps1）  
✅ **项目记忆文档**（PROJECT_MEMORY.md）  
✅ **完整文档系统**（7 个指南文档）  
✅ **对比演示**（comparison.py）  

---

**现在开始：**

```powershell
.\setup_and_run.ps1 comparison.py
```

**查看约定：**

```powershell
cat PROJECT_MEMORY.md
```
