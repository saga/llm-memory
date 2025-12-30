import unittest
import tempfile
import os
import json
from datetime import datetime
from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType, MemoryEntry
from audit import AuditLog, FinancialAuditLog
from nodes import planner_node, memory_recall_node, decision_node, create_memory_entry
from policy import compliance_policy, memory_retention_policy, next_step_policy
from graph import create_base_graph, run_agent_workflow


class TestPydanticState(unittest.TestCase):
    """测试Pydantic状态模型"""
    
    def test_message_creation(self):
        """测试消息创建"""
        message = Message(
            role=MessageRole.USER,
            content="测试消息",
            message_type=MessageType.USER_INPUT
        )
        
        self.assertEqual(message.role, MessageRole.USER)
        self.assertEqual(message.content, "测试消息")
        self.assertIsInstance(message.timestamp, datetime)
    
    def test_agent_state_validation(self):
        """测试代理状态验证"""
        # 有效状态
        state = AgentState(
            session_id="test_session",
            step=0,
            status="idle"
        )
        self.assertEqual(state.session_id, "test_session")
        
        # 无效步骤数应该抛出异常
        with self.assertRaises(ValueError):
            AgentState(session_id="test", step=-1)
    
    def test_financial_agent_state(self):
        """测试金融代理状态"""
        financial_state = FinancialAgentState(
            session_id="financial_test",
            compliance_level="retail",
            risk_level="medium"
        )
        
        self.assertEqual(financial_state.compliance_level, "retail")
        self.assertEqual(financial_state.risk_level, "medium")
    
    def test_memory_entry_creation(self):
        """测试记忆条目创建"""
        memory = MemoryEntry(
            id="test_memory_id",
            content="测试记忆内容",
            context="test_context",
            hash="test_hash"
        )
        
        self.assertEqual(memory.id, "test_memory_id")
        self.assertEqual(memory.content, "测试记忆内容")
        self.assertEqual(memory.context, "test_context")


class TestAuditSystem(unittest.TestCase):
    """测试审计系统"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_path = os.path.join(self.temp_dir, "test_audit.db")
        self.audit_log = AuditLog(self.audit_path)
    
    def tearDown(self):
        """清理测试环境"""
        self.audit_log.close()
        if os.path.exists(self.audit_path):
            os.remove(self.audit_path)
        os.rmdir(self.temp_dir)
    
    def test_state_audit(self):
        """测试状态审计"""
        state = AgentState(
            session_id="test_session",
            step=1,
            status="processing"
        )
        
        self.audit_log.append_state(state, "test_transition")
        
        # 验证审计记录
        history = self.audit_log.get_session_history("test_session")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["step"], 1)
    
    def test_message_audit(self):
        """测试消息审计"""
        message = Message(
            role=MessageRole.USER,
            content="测试消息",
            message_type=MessageType.USER_INPUT
        )
        
        self.audit_log.append_message("test_session", message)
        
        # 验证消息记录（需要直接查询数据库）
        cursor = self.audit_log.conn.execute(
            "SELECT content FROM message_log WHERE session_id = ?",
            ("test_session",)
        )
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "测试消息")
    
    def test_compliance_audit(self):
        """测试合规审计"""
        self.audit_log.append_compliance_check(
            "test_session",
            "risk_check",
            "PASS",
            {"details": "test details"}
        )
        
        report = self.audit_log.get_compliance_report("test_session")
        self.assertEqual(report["total_checks"], 1)
        self.assertEqual(report["passed_checks"], 1)
    
    def test_state_integrity_verification(self):
        """测试状态完整性验证"""
        state = AgentState(
            session_id="test_session",
            step=1,
            status="processing"
        )
        
        self.audit_log.append_state(state, "test_transition")
        
        # 验证完整性
        integrity = self.audit_log.verify_state_integrity("test_session")
        self.assertTrue(integrity)


class TestNodes(unittest.TestCase):
    """测试节点功能"""
    
    def test_planner_node(self):
        """测试规划器节点"""
        state = AgentState(session_id="test_session")
        state.add_message(MessageRole.USER, "风险评估问题")
        
        new_state = planner_node(state)
        
        # 验证步骤递增
        self.assertEqual(new_state.step, 1)
        
        # 验证添加了系统消息
        system_messages = [msg for msg in new_state.messages if msg.role == MessageRole.SYSTEM]
        self.assertGreater(len(system_messages), 0)
    
    def test_memory_recall_node(self):
        """测试记忆召回节点"""
        state = AgentState(session_id="test_session", context="financial")
        state.add_message(MessageRole.USER, "投资风险")
        
        # 添加一些记忆
        memory = MemoryEntry(
            id="test_memory",
            content="之前的风险评估",
            context="financial",
            hash="test_hash"
        )
        state.add_memory(memory)
        
        new_state = memory_recall_node(state)
        
        # 验证可能添加了记忆召回消息
        recall_messages = [msg for msg in new_state.messages 
                          if msg.message_type == MessageType.MEMORY_RECALL]
        # 由于关键词匹配，应该找到相关记忆
        self.assertGreater(len(recall_messages), 0)
    
    def test_decision_node(self):
        """测试决策节点"""
        state = AgentState(session_id="test_session")
        state.add_message(MessageRole.USER, "投资风险评估")
        
        new_state = decision_node(state)
        
        # 验证决策被设置
        self.assertIsNotNone(new_state.decision)
        self.assertIn("RISK", new_state.decision)
    
    def test_memory_entry_creation(self):
        """测试记忆条目创建"""
        memory = create_memory_entry(
            content="测试内容",
            context="测试上下文",
            message_type=MessageType.USER_INPUT
        )
        
        self.assertIsInstance(memory, MemoryEntry)
        self.assertEqual(memory.content, "测试内容")
        self.assertEqual(memory.context, "测试上下文")


class TestPolicy(unittest.TestCase):
    """测试策略功能"""
    
    def test_compliance_policy(self):
        """测试合规策略"""
        state = AgentState(session_id="test_session")
        
        # 基础合规检查应该通过
        self.assertTrue(compliance_policy(state))
        
        # 添加合规标记应该仍然通过
        state.add_compliance_flag("test_flag")
        self.assertFalse(compliance_policy(state))
    
    def test_memory_retention_policy(self):
        """测试记忆保留策略"""
        # 正常内容应该保留
        self.assertTrue(memory_retention_policy(None, "正常内容"))
        
        # 敏感信息应该过滤
        self.assertFalse(memory_retention_policy(None, "我的密码是123456"))
        self.assertFalse(memory_retention_policy(None, "身份证号110101199001011234"))
        
        # 违法内容应该过滤
        self.assertFalse(memory_retention_policy(None, "违法投资建议"))
    
    def test_next_step_policy(self):
        """测试下一步策略"""
        state = AgentState(session_id="test_session")
        
        # 初始状态应该返回planner
        next_step = next_step_policy(state)
        self.assertEqual(next_step, "planner")
        
        # 设置决策后应该返回相应步骤
        state.decision = "PERFORM_RISK_ASSESSMENT"
        next_step = next_step_policy(state)
        self.assertEqual(next_step, "risk_assessment")


class TestGraph(unittest.TestCase):
    """测试图功能"""
    
    def test_base_graph_creation(self):
        """测试基础图创建"""
        graph = create_base_graph()
        self.assertIsNotNone(graph)
    
    def test_workflow_execution(self):
        """测试工作流执行"""
        # 创建初始状态
        initial_state = AgentState(
            session_id="test_workflow",
            messages=[Message(role=MessageRole.USER, content="测试问题")]
        )
        
        # 运行工作流
        final_state = run_agent_workflow(initial_state, max_steps=5)
        
        # 验证状态变更
        self.assertGreater(final_state.step, 0)
        self.assertIn(final_state.status, ["waiting_input", "complete", "error"])


class TestFinancialFeatures(unittest.TestCase):
    """测试金融专用功能"""
    
    def test_financial_agent_state(self):
        """测试金融代理状态"""
        financial_state = FinancialAgentState(
            session_id="financial_test",
            compliance_level="retail",
            risk_level="medium",
            investment_limit=100000
        )
        
        # 设置风险画像
        financial_state.set_risk_profile("low", {"age": 60, "income": "retired"})
        self.assertEqual(financial_state.get_fact("risk_level"), "low")
        
        # 产品推荐检查
        self.assertTrue(financial_state.can_recommend_product("bonds"))
    
    def test_financial_audit_log(self):
        """测试金融审计日志"""
        temp_dir = tempfile.mkdtemp()
        audit_path = os.path.join(temp_dir, "financial_audit.db")
        
        try:
            financial_audit = FinancialAuditLog(audit_path)
            
            # 记录风险评估
            financial_audit.log_risk_assessment(
                "test_session",
                "medium",
                {"age": 35, "income": "stable"},
                "initial_assessment"
            )
            
            # 获取风险评估历史
            history = financial_audit.get_risk_assessment_history("test_session")
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["risk_level"], "medium")
            
        finally:
            financial_audit.close()
            if os.path.exists(audit_path):
                os.remove(audit_path)
            os.rmdir(temp_dir)


def run_all_tests():
    """运行所有测试"""
    test_classes = [
        TestPydanticState,
        TestAuditSystem,
        TestNodes,
        TestPolicy,
        TestGraph,
        TestFinancialFeatures
    ]
    
    # 创建测试套件
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("运行Pydantic + LangGraph LLM Memory系统测试...")
    success = run_all_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
        print("Pydantic + LangGraph LLM Memory系统已就绪")
    else:
        print("\n❌ 部分测试失败！")
        exit(1)