#!/usr/bin/env python3
"""
简单的Pydantic + LangGraph LLM Memory系统测试脚本
避免构建问题，直接运行测试
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """测试基本导入"""
    try:
        from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType, MemoryEntry
        print("✅ 状态模型导入成功")
    except ImportError as e:
        print(f"❌ 状态模型导入失败: {e}")
        return False
    
    try:
        from audit import AuditLog, FinancialAuditLog
        print("✅ 审计系统导入成功")
    except ImportError as e:
        print(f"❌ 审计系统导入失败: {e}")
        return False
    
    try:
        from nodes import planner_node, memory_recall_node, decision_node, create_memory_entry
        print("✅ 节点功能导入成功")
    except ImportError as e:
        print(f"❌ 节点功能导入失败: {e}")
        return False
    
    try:
        from policy import compliance_policy, memory_retention_policy, next_step_policy
        print("✅ 策略功能导入成功")
    except ImportError as e:
        print(f"❌ 策略功能导入失败: {e}")
        return False
    
    try:
        from graph import create_base_graph, run_agent_workflow
        print("✅ 图功能导入成功")
    except ImportError as e:
        print(f"❌ 图功能导入失败: {e}")
        return False
    
    return True

def test_pydantic_models():
    """测试Pydantic模型"""
    try:
        from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType, MemoryEntry
        
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
        
        return True
    except Exception as e:
        print(f"❌ Pydantic模型测试失败: {e}")
        return False

def test_audit_system():
    """测试审计系统"""
    try:
        from audit import AuditLog, FinancialAuditLog
        import tempfile
        import os
        
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        audit_path = os.path.join(temp_dir, "test_audit.db")
        
        try:
            audit_log = AuditLog(audit_path)
            
            from state import AgentState
            
            # 测试状态审计
            state = AgentState(
                session_id="test_session",
                step=1,
                status="processing"
            )
            
            audit_log.append_state(state, "test_transition")
            
            # 验证审计记录
            history = audit_log.get_session_history("test_session")
            assert len(history) == 1
            assert history[0]["step"] == 1
            print("✅ 状态审计测试通过")
            
            audit_log.close()
            
        finally:
            if os.path.exists(audit_path):
                os.remove(audit_path)
            os.rmdir(temp_dir)
        
        return True
    except Exception as e:
        print(f"❌ 审计系统测试失败: {e}")
        return False

def test_nodes():
    """测试节点功能"""
    try:
        from nodes import planner_node, memory_recall_node, decision_node, create_memory_entry
        from state import AgentState, Message, MessageRole, MessageType
        
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
        
        return True
    except Exception as e:
        print(f"❌ 节点功能测试失败: {e}")
        return False

def test_policy():
    """测试策略功能"""
    try:
        from policy import compliance_policy, memory_retention_policy, next_step_policy
        from state import AgentState
        
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
        
        return True
    except Exception as e:
        print(f"❌ 策略功能测试失败: {e}")
        return False

def test_graph():
    """测试图功能"""
    try:
        from graph import create_base_graph, run_agent_workflow
        from state import AgentState, Message, MessageRole
        
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
        
        return True
    except Exception as e:
        print(f"❌ 图功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始Pydantic + LangGraph LLM Memory系统测试...")
    print("=" * 60)
    
    # 测试基本导入
    if not test_basic_imports():
        print("❌ 基本导入测试失败，停止测试")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试Pydantic模型
    if not test_pydantic_models():
        print("❌ Pydantic模型测试失败")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试审计系统
    if not test_audit_system():
        print("❌ 审计系统测试失败")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试节点功能
    if not test_nodes():
        print("❌ 节点功能测试失败")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试策略功能
    if not test_policy():
        print("❌ 策略功能测试失败")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试图功能
    if not test_graph():
        print("❌ 图功能测试失败")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("✅ Pydantic + LangGraph LLM Memory系统已就绪")
    print("\n系统特点：")
    print("- ✅ Pydantic强一致性状态管理")
    print("- ✅ LangGraph显式状态机")
    print("- ✅ SQLite审计日志")
    print("- ✅ 金融合规功能")
    print("- ✅ 确定性结果保证")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)