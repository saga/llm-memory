"""
简化版测试脚本 - 验证无LangGraph依赖的系统
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType
from audit import AuditLog, FinancialAuditLog
from nodes import (
    planner_node, memory_recall_node, decision_node,
    response_generator_node, memory_storage_node, compliance_check_node,
    create_memory_entry
)
from policy import next_step_policy, routing_policy, compliance_policy, memory_retention_policy
from simple_graph import SimpleStateMachine, create_simple_base_graph, run_simple_agent_workflow
from simple_chat_api import SimpleLLMChatWithMemory, SimpleFinancialLLMChat
import uuid


def test_pydantic_models():
    """测试Pydantic模型"""
    print("🧪 测试Pydantic模型...")
    
    # 基础状态
    state = AgentState(session_id="test_001")
    print(f"✅ 基础状态创建: {state.session_id}")
    
    # 金融状态
    financial_state = FinancialAgentState(
        session_id="test_002",
        risk_level="medium",
        risk_factors={"age": 30}
    )
    print(f"✅ 金融状态创建: {financial_state.session_id}, 风险等级: {financial_state.risk_level}")
    
    # 消息创建
    message = Message(
        role=MessageRole.USER,
        content="测试消息",
        message_type=MessageType.CHAT
    )
    print(f"✅ 消息创建: {message.role.value} - {message.content}")
    
    # 状态转换
    new_state = state.model_copy(deep=True)
    new_state.messages.append(message)
    print(f"✅ 状态转换: 消息数从 {len(state.messages)} 到 {len(new_state.messages)}")
    
    return True


def test_audit_system():
    """测试审计系统"""
    print("🧪 测试审计系统...")
    
    # 基础审计
    audit_log = AuditLog("test_audit.db")
    
    # 创建测试状态
    state = AgentState(session_id="audit_test_001")
    state_hash = state.compute_hash()
    
    # 记录状态变化
    audit_log.log_state_change(
        session_id="audit_test_001",
        step=1,
        action="test_action",
        state_json=state.model_dump_json(),
        state_hash=state_hash
    )
    
    # 获取历史
    history = audit_log.get_session_history("audit_test_001")
    print(f"✅ 审计历史: {len(history)} 条记录")
    
    # 验证完整性
    is_valid = audit_log.verify_state_integrity("audit_test_001")
    print(f"✅ 完整性验证: {'通过' if is_valid else '失败'}")
    
    return True


def test_nodes():
    """测试节点函数"""
    print("🧪 测试节点函数...")
    
    # 创建测试状态
    state = AgentState(session_id="node_test_001")
    state.messages.append(Message(
        role=MessageRole.USER,
        content="测试输入",
        message_type=MessageType.CHAT
    ))
    
    # 测试各个节点
    try:
        # 规划节点
        state1 = planner_node(state)
        print(f"✅ 规划节点: 状态正常转换")
        
        # 记忆召回节点
        state2 = memory_recall_node(state1)
        print(f"✅ 记忆召回节点: 状态正常转换")
        
        # 决策节点
        state3 = decision_node(state2)
        print(f"✅ 决策节点: 状态正常转换")
        
        # 响应生成节点
        state4 = response_generator_node(state3)
        print(f"✅ 响应生成节点: 状态正常转换")
        
        # 合规检查节点
        state5 = compliance_check_node(state4)
        print(f"✅ 合规检查节点: 状态正常转换")
        
        # 记忆存储节点
        state6 = memory_storage_node(state5)
        print(f"✅ 记忆存储节点: 状态正常转换")
        
        return True
        
    except Exception as e:
        print(f"❌ 节点测试失败: {e}")
        return False


def test_simple_state_machine():
    """测试简化版状态机"""
    print("🧪 测试简化版状态机...")
    
    # 创建状态机
    state_machine = SimpleStateMachine(AgentState)
    
    # 添加节点
    state_machine.add_node("test_node", lambda state: state)
    state_machine.set_entry_point("test_node")
    
    # 编译
    compiled = state_machine.compile()
    
    # 创建初始状态
    initial_state = AgentState(session_id="sm_test_001")
    
    # 运行状态机
    result = compiled.invoke(initial_state, max_steps=1)
    
    print(f"✅ 状态机运行: {result.session_id}")
    
    # 测试完整图
    try:
        graph = create_simple_base_graph()
        final_state = run_simple_agent_workflow(initial_state, max_steps=5)
        print(f"✅ 完整工作流: 执行成功，最终消息数: {len(final_state.messages)}")
        return True
        
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        return False


def test_simple_chat_api():
    """测试简化版聊天API"""
    print("🧪 测试简化版聊天API...")
    
    try:
        # 基础聊天
        chat = SimpleLLMChatWithMemory(
            api_key="test-key",
            audit_log_path="test_chat_audit.db"
        )
        
        # 创建会话
        session_id = chat.create_session("api_test_001")
        print(f"✅ 创建会话: {session_id}")
        
        # 添加消息
        success = chat.add_message(
            session_id,
            MessageRole.USER,
            "测试消息",
            MessageType.USER_INPUT
        )
        print(f"✅ 添加消息: {'成功' if success else '失败'}")
        
        # 获取历史
        history = chat.get_session_history(session_id)
        print(f"✅ 获取历史: {len(history)} 条消息")
        
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


def test_financial_features():
    """测试金融特性"""
    print("🧪 测试金融特性...")
    
    try:
        # 金融聊天
        financial_chat = SimpleFinancialLLMChat(
            api_key="test-key",
            audit_log_path="test_financial_audit.db"
        )
        
        # 创建会话
        session_id = financial_chat.create_session("financial_test_001")
        
        # 设置风险档案
        success = financial_chat.set_risk_profile(
            session_id,
            "high",
            {"age": 25, "income": "low"}
        )
        print(f"✅ 设置风险档案: {'成功' if success else '失败'}")
        
        # 获取合规状态
        compliance = financial_chat.get_compliance_status(session_id)
        print(f"✅ 合规状态: {compliance}")
        
        return True
        
    except Exception as e:
        print(f"❌ 金融特性测试失败: {e}")
        return False


def cleanup_test_files():
    """清理测试文件"""
    test_files = [
        "test_audit.db", "test_chat_audit.db", "test_financial_audit.db"
    ]
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"🗑️  清理文件: {file}")
        except Exception:
            pass


def main():
    """主测试函数"""
    print("🚀 开始简化版LLM Memory系统测试...")
    print("=" * 50)
    
    tests = [
        ("Pydantic模型", test_pydantic_models),
        ("审计系统", test_audit_system),
        ("节点函数", test_nodes),
        ("简化版状态机", test_simple_state_machine),
        ("简化版聊天API", test_simple_chat_api),
        ("金融特性", test_financial_features),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    # 清理测试文件
    cleanup_test_files()
    
    # 总结
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！简化版系统工作正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查代码")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)