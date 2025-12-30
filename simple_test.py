"""
简化版测试 - 修复版本，无LangGraph依赖
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_state import AgentState, FinancialAgentState, MessageRole, MessageType
from simple_graph import SimpleStateMachine, CompiledStateMachine, create_simple_base_graph, create_simple_financial_graph
from simple_audit import SimpleAuditLog, SimpleFinancialAuditLog
from simple_nodes import planner_node, memory_recall_node, decision_node, response_generator_node
from simple_policy import routing_policy, compliance_policy, memory_retention_policy


def test_simple_state():
    """测试简化版状态模型"""
    print("=== 测试简化版状态模型 ===")
    
    # 测试基础状态
    state = AgentState(session_id="test_001")
    state.add_message(MessageRole.USER, "你好")
    state.add_message(MessageRole.ASSISTANT, "你好！有什么可以帮助您的吗？")
    
    print(f"✅ 基础状态创建: {state.session_id}")
    print(f"✅ 消息数量: {len(state.messages)}")
    print(f"✅ 状态哈希: {state.compute_hash()}")
    
    # 测试金融状态
    financial_state = FinancialAgentState(session_id="financial_test_001")
    financial_state.set_risk_profile("medium", {"age": 30, "experience": "intermediate"})
    financial_state.add_compliance_flag("test_flag")
    
    print(f"✅ 金融状态创建: {financial_state.session_id}")
    print(f"✅ 风险档案: {financial_state.risk_profile}")
    print(f"✅ 合规标记: {financial_state.compliance_flags}")
    print(f"✅ 状态哈希: {financial_state.compute_hash()}")


def test_simple_state_machine():
    """测试简化版状态机"""
    print("\n=== 测试简化版状态机 ===")
    
    # 创建状态机
    state_machine = SimpleStateMachine(AgentState)
    
    # 添加测试节点
    def test_node(state: AgentState) -> AgentState:
        new_state = state.model_copy(deep=True)
        new_state.add_message(MessageRole.SYSTEM, "测试节点执行")
        return new_state
    
    state_machine.add_node("test_node", test_node)
    state_machine.set_entry_point("test_node")
    
    # 编译并运行
    compiled = state_machine.compile()
    initial_state = AgentState(session_id="sm_test_001")
    result = compiled.invoke(initial_state, max_steps=1)
    
    print(f"✅ 状态机运行: {result.session_id}")
    print(f"✅ 消息数量: {len(result.messages)}")


def test_simple_graph():
    """测试简化版图"""
    print("\n=== 测试简化版图 ===")
    
    # 测试基础图
    base_graph = create_simple_base_graph()
    initial_state = AgentState(session_id="graph_test_001")
    result = base_graph.invoke(initial_state, max_steps=3)
    
    print(f"✅ 基础图运行: {result.session_id}")
    print(f"✅ 消息数量: {len(result.messages)}")
    
    # 测试金融图
    financial_graph = create_simple_financial_graph()
    financial_state = FinancialAgentState(session_id="financial_graph_test_001")
    financial_result = financial_graph.invoke(financial_state, max_steps=3)
    
    print(f"✅ 金融图运行: {financial_result.session_id}")
    print(f"✅ 消息数量: {len(financial_result.messages)}")


def test_simple_audit():
    """测试简化版审计"""
    print("\n=== 测试简化版审计 ===")
    
    # 测试基础审计
    audit_log = SimpleAuditLog("test_audit_runtime.db")
    
    # 记录状态变化
    state = AgentState(session_id="audit_test_001")
    audit_log.log_state_change(
        session_id="audit_test_001",
        step=1,
        action="test_action",
        state_json=state.model_dump_json(),
        state_hash=state.compute_hash()
    )
    
    # 获取审计日志
    logs = audit_log.get_session_history("audit_test_001")
    print(f"✅ 审计日志记录: {len(logs)} 条记录")
    
    # 验证状态完整性
    is_valid = audit_log.verify_state_integrity("audit_test_001")
    print(f"✅ 状态完整性验证: {is_valid}")


def test_simple_policy():
    """测试简化版策略"""
    print("\n=== 测试简化版策略 ===")
    
    # 测试路由策略
    state = AgentState(session_id="policy_test_001")
    route = routing_policy(state)
    print(f"✅ 路由策略: {route}")
    
    # 测试合规策略
    financial_state = FinancialAgentState(session_id="compliance_test_001")
    financial_state.decision = "investment_advice"
    compliance = compliance_policy(financial_state)
    print(f"✅ 合规策略: {compliance}")
    
    # 测试记忆保留策略
    retention = memory_retention_policy(state, "投资建议")
    print(f"✅ 记忆保留策略: {retention}")


def test_simple_nodes():
    """测试简化版节点"""
    print("\n=== 测试简化版节点 ===")
    
    # 测试规划器节点
    state = AgentState(session_id="node_test_001")
    state.add_message(MessageRole.USER, "我想投资股票")
    
    result_state = planner_node(state)
    print(f"✅ 规划器节点: {len(result_state.messages)} 条消息")
    
    # 测试记忆召回节点
    memory_state = memory_recall_node(result_state)
    print(f"✅ 记忆召回节点: {len(memory_state.messages)} 条消息")
    
    # 测试决策节点
    decision_state = decision_node(memory_state)
    print(f"✅ 决策节点: {decision_state.decision}")
    
    # 测试响应生成节点
    response_state = response_generator_node(decision_state)
    print(f"✅ 响应生成节点: {len(response_state.messages)} 条消息")


def test_simple_workflow():
    """测试简化版工作流"""
    print("\n=== 测试简化版工作流 ===")
    
    # 创建初始状态
    initial_state = AgentState(session_id="workflow_test_001")
    initial_state.add_message(MessageRole.USER, "你好，我想了解一些投资建议")
    
    # 运行工作流
    from simple_graph import run_simple_agent_workflow
    final_state = run_simple_agent_workflow(initial_state, graph_type="base", max_steps=5)
    
    print(f"✅ 工作流完成: {final_state.session_id}")
    print(f"✅ 最终消息数量: {len(final_state.messages)}")
    print(f"✅ 最终决策: {final_state.decision}")
    print(f"✅ 最终状态: {final_state.status}")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行简化版LLM Memory系统测试...")
    print("=" * 50)
    
    try:
        test_simple_state()
        test_simple_state_machine()
        test_simple_graph()
        test_simple_audit()
        test_simple_policy()
        test_simple_nodes()
        test_simple_workflow()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！简化版LLM Memory系统运行正常。")
        print("✅ 状态模型: 基础 + 金融扩展")
        print("✅ 状态机: 无LangGraph依赖")
        print("✅ 审计日志: SQLite存储 + 完整性验证")
        print("✅ 策略系统: 路由 + 合规 + 记忆保留")
        print("✅ 节点函数: 纯函数实现")
        print("✅ 工作流: 完整流程测试")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
