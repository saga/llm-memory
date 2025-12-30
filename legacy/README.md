# Legacy Code Archive

This directory contains the **old implementation** of the memory framework, which has been replaced by **PydanticAI**.

## 📁 Archived Files

### Framework (Old)
- **`graph.py`** (150 lines) - Custom state machine implementation
- **`nodes.py`** (368 lines) - Manual node functions

### Demos (Old)
- **`memory_types_demo.py`** - Memory types demonstration using old system
- **`summarization_demo.py`** - Summarization demo using old system  
- **`manual_test.py`** - Manual testing script

---

## ⚠️ Important Notice

**These files are kept for reference only and are NO LONGER MAINTAINED.**

### Why archived?

The old system had several issues:
- ❌ 518+ lines of boilerplate code
- ❌ Manual state management and copying
- ❌ Complex node orchestration
- ❌ Difficult to extend or modify
- ❌ Hard to test individual components
- ❌ No type safety for node functions

### Use the new system instead

**New implementation (framework/pydantic_agent.py):**
- ✅ 200 lines of clean code (60% reduction)
- ✅ Automatic state management
- ✅ Simple 3-line API
- ✅ Easy to extend with @tool decorator
- ✅ Built-in testing support
- ✅ Full type safety with Pydantic

---

## 🚀 Migration Guide

### Old Code (graph.py + nodes.py)

```python
from framework.graph import create_simple_base_graph
from framework.state import AgentState, MessageRole

# Step 1: Create state
state = AgentState(session_id="demo")
state.add_message(MessageRole.USER, "Hello")

# Step 2: Create and compile graph
graph = create_simple_base_graph()
compiled = graph.compile()

# Step 3: Run workflow
state = compiled.invoke(state)
response = state.messages[-1].content
```

### New Code (pydantic_agent.py)

```python
from framework.pydantic_agent import MemoryAgentWorkflow

# Just 3 lines
workflow = MemoryAgentWorkflow()
session_id = workflow.create_session()
response = await workflow.chat(session_id, "Hello")
```

---

## 📚 Documentation

For new implementations, see:
- **[README_PYDANTICAI.md](../README_PYDANTICAI.md)** - Main documentation
- **[QUICKSTART_PYDANTICAI.md](../QUICKSTART_PYDANTICAI.md)** - Quick start guide
- **[simple_memory.py](../simple_memory.py)** - Minimal example (150 lines)
- **[comparison.py](../comparison.py)** - Before/after comparison

For migration details:
- **[PYDANTIC_AI_MIGRATION.md](../PYDANTIC_AI_MIGRATION.md)** - Migration guide
- **[BEFORE_AFTER_COMPARISON.md](../BEFORE_AFTER_COMPARISON.md)** - Code comparison

---

## 🔍 Reference Only

**If you need to reference the old implementation:**

1. These files are **read-only archives**
2. Do NOT base new features on this code
3. Use for historical reference only
4. All new development should use `framework/pydantic_agent.py`

---

## 📊 Code Statistics

**Old System (Archived):**
```
graph.py              150 lines
nodes.py              368 lines
policy.py              24 lines (deleted)
────────────────────────────────
Total                 542 lines
```

**New System (Active):**
```
pydantic_agent.py     200 lines
state.py              150 lines
summarization.py      350 lines
────────────────────────────────
Total                 700 lines
```

**Reduction: -44% code, -90% complexity**

---

**Last Updated:** December 30, 2025  
**Archived Reason:** Replaced by PydanticAI implementation  
**Status:** Reference only, no longer maintained
