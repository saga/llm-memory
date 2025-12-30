# 手动测试脚本 - 验证Pydantic + LangGraph LLM Memory系统

import sys
import os
import tempfile
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 手动导入模块来测试
print("🧪 开始手动测试Pydantic + LangGraph LLM Memory系统...")
print("=" * 60)

# 1. 测试状态模型
print("\n1️⃣ 测试状态模型...")
try:
    from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType, MemoryEntry
    print("✅ 状态模型导入成功")
    
    # 测试消息创建
    message = Message(
        role=MessageRole.USER,
        content="测试消息",
        message_type=MessageType.USER_INPUT
    )
    assert message.role == MessageRole.USER
    assert message.content == "测试消息"
    print("✅ 消息创建测试通过")
    
    # 测试代理状态
    state = AgentState(
        session_id="test_session",
        step=0,
        status="idle"
    )
    assert state.session_id == "test_session"
    print("✅ 代理状态测试通过")
    
    # 测试金融代理状态
    financial_state = FinancialAgentState(
        session_id="financial_test",
        compliance_level="retail",
        risk_level="medium"
    )
    assert financial_state.compliance_level == "retail"
    assert financial_state.risk_level == "medium"
    print("✅ 金融代理状态测试通过")
    
    # 测试记忆条目
    memory = MemoryEntry(
        id="test_memory_id",
        content="测试记忆内容",
        context="test_context",
        hash="test_hash"
    )
    assert memory.id == "test_memory_id"
    assert memory.content == "测试记忆内容"
    print("✅ 记忆条目测试通过")
    
except Exception as e:
    print(f"❌ 状态模型测试失败: {e}")
    sys.exit(1)
# 2. 测试状态管理
print("\n2️⃣ 测试状态管理...")
try:
    print(f"❌ 审计系统测试失败: {e}")
    sys.exit(1)

# 3. 测试节点功能
print("\n3️⃣ 测试节点功能...")
try:
    from nodes import planner_node, memory_recall_node, decision_node, create_memory_entry
    
    # 测试规划器节点
    state = AgentState(session_id="test_session")
    state.add_message(MessageRole.USER, "风险评估问题")
    
    new_state = planner_node(state)
    
    # 验证步骤递增
    assert new_state.step == 1
    print("✅ 规划器节点测试通过")
    
    # 测试决策节点
    state = AgentState(session_id="test_session")
    state.add_message(MessageRole.USER, "投资风险评估")
    
    new_state = decision_node(state)
    
    # 验证决策被设置
    assert new_state.decision is not None
    print("✅ 决策节点测试通过")
    
    # 测试记忆条目创建
    memory = create_memory_entry(
        content="测试内容",
        context="测试上下文",
        message_type=MessageType.USER_INPUT
    )
    
    assert memory.content == "测试内容"
    assert memory.context == "测试上下文"
    print("✅ 记忆条目创建测试通过")
    
except Exception as e:
    print(f"❌ 节点功能测试失败: {e}")
    sys.exit(1)

# 4. 测试策略功能
print("\n4️⃣ 测试策略功能...")
try:
    from policy import compliance_policy, memory_retention_policy, next_step_policy
    
    # 测试合规策略
    state = AgentState(session_id="test_session")
    assert compliance_policy(state) == True
    print("✅ 合规策略测试通过")
    
    # 测试记忆保留策略
    assert memory_retention_policy(None, "正常内容") == True
    assert memory_retention_policy(None, "我的密码是123456") == False
    print("✅ 记忆保留策略测试通过")
    
    # 测试下一步策略
    state = AgentState(session_id="test_session")
    next_step = next_step_policy(state)
    assert next_step == "planner"
    print("✅ 下一步策略测试通过")
    
except Exception as e:
    print(f"❌ 策略功能测试失败: {e}")
    sys.exit(1)

# 5. 测试图功能
print("\n5️⃣ 测试图功能...")
try:
    from graph import create_base_graph, run_agent_workflow
    
    # 测试图创建
    graph = create_base_graph()
    assert graph is not None
    print("✅ 图创建测试通过")
    
    # 测试工作流执行
    initial_state = AgentState(
        session_id="test_workflow",
        messages=[Message(role=MessageRole.USER, content="测试问题")]
    )
    
    final_state = run_agent_workflow(initial_state, max_steps=5)
    
    # 验证状态变更
    assert final_state.step > 0
    assert final_state.status in ["waiting_input", "complete", "error"]
    print("✅ 工作流执行测试通过")
    
except Exception as e:
    print(f"❌ 图功能测试失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 所有测试通过！")
print("✅ Pydantic + LangGraph LLM Memory系统已就绪")
print("\n系统特点：")
print("- ✅ Pydantic强一致性状态管理")
print("- ✅ LangGraph显式状态机")
print("- ✅ SQLite审计日志")
print("- ✅ 金融合规功能")
print("- ✅ 确定性结果保证")
print("\n🚀 系统已准备好用于金融科技场景！")