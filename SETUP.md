# Setup Guide - Virtual Environment

## 🔧 环境设置（必读）

### 1. 创建虚拟环境

```bash
# Windows PowerShell
python3.14 -m venv venv

# 或使用系统默认 Python
python -m venv venv
```

### 2. 激活虚拟环境

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 激活环境后
pip install -r requirements.txt

# 或最小依赖
pip install pydantic pydantic-ai
```

### 4. 设置 API Key

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# Linux/Mac
export OPENAI_API_KEY="sk-..."
```

---

## 🚀 快速启动（推荐）

### 使用自动化脚本

```bash
# Windows
.\setup_and_run.ps1

# 或手动
.\venv\Scripts\Activate.ps1
python simple_memory.py
```

---

## 📝 常用命令（记忆清单）

```bash
# 1. 激活环境
.\venv\Scripts\Activate.ps1

# 2. 运行演示
python pydantic_ai_demo.py
python simple_memory.py
python comparison.py

# 3. 运行测试
pytest tests/ -v

# 4. 退出环境
deactivate
```

---

## 🔍 环境检查

```bash
# 确认在 venv 中
where python
# 应该输出: D:\temp\llm-memory\venv\Scripts\python.exe

# 查看已安装包
pip list

# 验证 pydantic-ai
python -c "import pydantic_ai; print(pydantic_ai.__version__)"
```

---

## ⚠️ 常见问题

### 问题 1: 无法激活 venv

```bash
# 如果遇到执行策略错误
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 2: 找不到 pydantic

```bash
# 确保先激活 venv
.\venv\Scripts\Activate.ps1
# 然后再安装
pip install pydantic pydantic-ai
```

### 问题 3: OPENAI_API_KEY 未设置

```bash
# 临时设置
$env:OPENAI_API_KEY = "sk-..."

# 或创建 .env 文件
echo 'OPENAI_API_KEY=sk-...' > .env
```

---

## 📂 项目记忆

**永远记住这个流程：**

```
1. .\venv\Scripts\Activate.ps1
2. python your_script.py
3. deactivate (结束时)
```

**不要直接运行：**
```
❌ python3.14 simple_memory.py  # 可能用的是全局环境
✅ .\venv\Scripts\Activate.ps1 → python simple_memory.py
```
