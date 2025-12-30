# Framework 精简方案

## 🎯 精简分析

### 当前 framework 结构

```
framework/
├── state.py              # ✅ 保留 - 核心数据模型
├── summarization.py      # ✅ 保留 - 压缩功能
├── pydantic_agent.py     # ✅ 保留 - 新系统
├── policy.py             # ⚠️ 可删除 - 功能简单，可整合
├── graph.py              # ❌ 可删除 - 已被 pydantic_agent 替代
└── nodes.py              # ❌ 可删除 - 已被 pydantic_agent 替代
```

---

## 📊 详细分析

### 1. graph.py (150 lines) - ❌ 建议删除

**功能：** 自定义状态机实现

**现状：**
- 已被 `pydantic_agent.py` 完全替代
- 使用的地方：
  - `memory_types_demo.py` (旧演示)
  - `summarization_demo.py` (旧演示)
  - `tests/test_framework.py` (旧测试)
  - 文档示例

**精简方案：**
- ✅ 删除 `graph.py`
- ✅ 将旧演示移到 `legacy/` 目录
- ✅ 更新测试使用 PydanticAI

---

### 2. nodes.py (368 lines) - ❌ 建议删除

**功能：** 手动节点函数

**现状：**
- 已被 `pydantic_agent.py` 的 tools 替代
- 使用的地方同上

**精简方案：**
- ✅ 删除 `nodes.py`
- ✅ 旧演示移到 `legacy/`

---

### 3. policy.py (24 lines) - ⚠️ 可整合

**功能：** 简单的路由和保留策略

**现状：**
- 功能非常简单
- 几乎没有被使用
- 可以直接整合到需要的地方

**精简方案：**
- ✅ 删除独立文件
- ✅ 如需要，整合到 `summarization.py` 或 `pydantic_agent.py`

---

### 4. state.py - ✅ 保留

**功能：** 核心数据模型 (MemoryEntry, AgentState, MemoryType)

**原因：**
- 被所有模块使用
- 定义了数据结构
- PydanticAI 也依赖它

---

### 5. summarization.py - ✅ 保留

**功能：** 记忆压缩和摘要

**原因：**
- 独立的业务逻辑模块
- 被 PydanticAI 版本使用
- 功能完整且必要

---

### 6. pydantic_agent.py - ✅ 保留

**功能：** 新的 PydanticAI 实现

**原因：**
- 这是新系统的核心
- 替代了 graph.py + nodes.py

---

## 🚀 精简执行计划

### Phase 1: 创建 legacy 目录

```bash
mkdir legacy
mv memory_types_demo.py legacy/
mv summarization_demo.py legacy/
mv manual_test.py legacy/
```

### Phase 2: 删除旧文件

```bash
# 移动到 legacy（保留备份）
mv framework/graph.py legacy/
mv framework/nodes.py legacy/
rm framework/policy.py  # 功能简单，不保留
```

### Phase 3: 更新引用

```bash
# 更新 tests/test_framework.py
# 使用 pydantic_agent 的测试

# 更新文档中的旧引用
# 指向 legacy/ 或 pydantic_agent
```

### Phase 4: 清理

```bash
rm -rf framework/__pycache__
```

---

## 📉 精简效果

### 代码量对比

**精简前：**
```
framework/
  graph.py              150 lines
  nodes.py              368 lines
  policy.py              24 lines
  state.py              150 lines
  summarization.py      350 lines
  pydantic_agent.py     200 lines
  ────────────────────────────────
  总计                 1,242 lines
```

**精简后：**
```
framework/
  state.py              150 lines
  summarization.py      350 lines
  pydantic_agent.py     200 lines
  ────────────────────────────────
  总计                  700 lines
```

**减少：542 lines (-44%)**

---

## ✅ 最终结构

```
llm-memory/
├── framework/
│   ├── state.py              # 核心数据模型
│   ├── summarization.py      # 压缩功能
│   └── pydantic_agent.py     # PydanticAI 实现
├── legacy/                    # 旧代码归档
│   ├── graph.py              # 旧状态机
│   ├── nodes.py              # 旧节点
│   ├── memory_types_demo.py  # 旧演示
│   └── summarization_demo.py # 旧演示
├── simple_memory.py           # 极简实现
├── pydantic_ai_demo.py        # 新演示
└── comparison.py              # 对比演示
```

---

## 💡 建议

### 立即执行（安全）

1. ✅ 创建 `legacy/` 目录
2. ✅ 移动旧演示到 `legacy/`
3. ✅ 移动 `graph.py` 和 `nodes.py` 到 `legacy/`

### 谨慎考虑（可选）

1. ⚠️ 删除 `policy.py`（功能很少使用）
2. ⚠️ 更新测试文件（需要重写）

### 不要删除

1. ✅ `state.py` - 核心依赖
2. ✅ `summarization.py` - 业务逻辑
3. ✅ `pydantic_agent.py` - 新系统

---

## 🎯 执行命令

```powershell
# 1. 创建归档目录
New-Item -ItemType Directory -Path legacy

# 2. 移动旧演示
Move-Item memory_types_demo.py legacy/
Move-Item summarization_demo.py legacy/
Move-Item manual_test.py legacy/

# 3. 移动旧框架代码
Move-Item framework/graph.py legacy/
Move-Item framework/nodes.py legacy/

# 4. 删除简单文件
Remove-Item framework/policy.py

# 5. 清理缓存
Remove-Item -Recurse framework/__pycache__

# Done!
```

---

## 📝 需要更新的文件

### 测试文件

```python
# tests/test_framework.py
# 从:
from framework.graph import create_simple_base_graph
from framework.nodes import planner_node

# 改为:
from framework.pydantic_agent import MemoryAgentWorkflow
```

### 文档

- `MEMORY_TYPES_GUIDE.md` - 更新示例代码
- `SUMMARIZATION_GUIDE.md` - 更新示例代码
- `FRAMEWORK_UPDATES.md` - 标注为 legacy

---

**总结：可以安全删除 542 行旧代码（44%），保留 700 行核心功能**
