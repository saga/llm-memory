import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.state import AgentState, MessageRole, MessageType
from framework.graph import SimpleStateMachine, CompiledStateMachine, create_simple_base_graph
from framework.nodes import planner_node, memory_recall_node, decision_node, response_generator_node
from framework.policy import routing_policy, memory_retention_policy


def test_simple_state():
    state = AgentState(session_id="test_001")
    state.add_message(MessageRole.USER, "你好")
    state.add_message(MessageRole.ASSISTANT, "你好！有什么可以帮助您的吗？")
    assert state.session_id == "test_001"
    assert len(state.messages) == 2
    assert isinstance(state.compute_hash(), str)


def test_simple_state_machine():
    sm = SimpleStateMachine(AgentState)
    def test_node(s: AgentState) -> AgentState:
        ns = s.model_copy(deep=True)
        ns.add_message(MessageRole.SYSTEM, "测试节点执行")
        return ns
    sm.add_node("test_node", test_node)
    sm.set_entry_point("test_node")
    compiled = sm.compile()
    initial_state = AgentState(session_id="sm_test_001")
    result = compiled.invoke(initial_state, max_steps=1)
    assert result.session_id == "sm_test_001"
    assert len(result.messages) == 1


def test_simple_graph_and_nodes():
    base_graph = create_simple_base_graph()
    initial_state = AgentState(session_id="graph_test_001")
    result = base_graph.invoke(initial_state, max_steps=3)
    assert result.session_id == "graph_test_001"
    # run nodes individually
    s = AgentState(session_id="node_test_001")
    s.add_message(MessageRole.USER, "我想投资股票")
    s1 = planner_node(s)
    s2 = memory_recall_node(s1)
    s3 = decision_node(s2)
    s4 = response_generator_node(s3)
    assert len(s4.messages) >= 1


def test_simple_audit(tmp_path):
    db_path = tmp_path / "test_audit_runtime.db"
    audit_log = SimpleAuditLog(str(db_path))
    state = AgentState(session_id="audit_test_001")
    audit_log.log_state_change(
        session_id="audit_test_001",
        step=1,
        action="test_action",
        state_json=state.model_dump_json(),
        state_hash=state.compute_hash()
    )
    logs = audit_log.get_session_history("audit_test_001")
    assert isinstance(logs, list)
    assert len(logs) >= 1
    assert audit_log.verify_state_integrity("audit_test_001") is True


def test_simple_policy():
    state = AgentState(session_id="policy_test_001")
    route = routing_policy(state)
    retention = memory_retention_policy(state, "投资建议")
    assert route in ("continue", "end", "error")
    assert retention["retain"] is True
