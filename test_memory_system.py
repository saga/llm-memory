import unittest
import tempfile
import os
import json
from memory_system import DeterministicMemoryStore, MemoryEntry, LLMChatWithMemory
from chat_api import CompletionChatAPI


class TestMemorySystem(unittest.TestCase):
    """测试记忆系统"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "test_memory.json")
        self.memory_store = DeterministicMemoryStore(self.memory_path)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.memory_path):
            os.remove(self.memory_path)
        os.rmdir(self.temp_dir)
    
    def test_memory_entry_creation(self):
        """测试记忆条目创建"""
        entry = MemoryEntry(
            id="test_id",
            content="测试内容",
            context="测试上下文",
            timestamp=1234567890.0,
            metadata={"type": "test"},
            hash="test_hash"
        )
        
        self.assertEqual(entry.id, "test_id")
        self.assertEqual(entry.content, "测试内容")
        self.assertEqual(entry.context, "测试上下文")
        self.assertEqual(entry.metadata["type"], "test")
    
    def test_add_memory(self):
        """测试添加记忆"""
        memory_id = self.memory_store.add_memory(
            content="用户询问风险评估",
            context="financial_advisory",
            metadata={"type": "user_input"}
        )
        
        self.assertIsNotNone(memory_id)
        self.assertIn(memory_id, self.memory_store.memories)
        self.assertIn("financial_advisory", self.memory_store.context_index)
    
    def test_duplicate_memory_handling(self):
        """测试重复记忆处理"""
        content = "相同的内容"
        context = "相同的上下文"
        
        id1 = self.memory_store.add_memory(content, context)
        id2 = self.memory_store.add_memory(content, context)
        
        # 应该返回相同的ID（避免重复）
        self.assertEqual(id1, id2)
        self.assertEqual(len(self.memory_store.memories), 1)
    
    def test_search_memories(self):
        """测试记忆搜索"""
        # 添加测试数据
        self.memory_store.add_memory("风险评估问题", "financial_advisory", {"type": "user_input"})
        self.memory_store.add_memory("投资建议", "financial_advisory", {"type": "assistant_response"})
        self.memory_store.add_memory("其他话题", "general", {"type": "user_input"})
        
        # 搜索
        results = self.memory_store.search_memories("风险", "financial_advisory")
        self.assertEqual(len(results), 1)
        self.assertIn("风险", results[0].content)
    
    def test_memory_persistence(self):
        """测试记忆持久化"""
        # 添加记忆
        original_id = self.memory_store.add_memory("测试持久化", "test_context")
        
        # 创建新的存储实例（模拟重启）
        new_store = DeterministicMemoryStore(self.memory_path)
        
        # 验证记忆被恢复
        self.assertIn(original_id, new_store.memories)
        self.assertEqual(new_store.memories[original_id].content, "测试持久化")


class TestLLMChatWithMemory(unittest.TestCase):
    """测试带记忆的LLM聊天系统"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "test_chat_memory.json")
        self.memory_store = DeterministicMemoryStore(self.memory_path)
        self.chat_system = LLMChatWithMemory(self.memory_store)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.memory_path):
            os.remove(self.memory_path)
        os.rmdir(self.temp_dir)
    
    def test_context_switching(self):
        """测试上下文切换"""
        self.chat_system.set_context("context1")
        self.assertEqual(self.chat_system.current_context, "context1")
        
        self.chat_system.set_context("context2")
        self.assertEqual(self.chat_system.current_context, "context2")
    
    def test_memory_from_interaction(self):
        """测试从交互中添加记忆"""
        self.chat_system.add_memory_from_interaction(
            user_input="用户问题",
            assistant_response="助手回答",
            metadata={"test": True}
        )
        
        # 验证记忆被添加
        self.assertEqual(len(self.memory_store.memories), 2)  # 用户输入和助手回复
    
    def test_relevant_context_retrieval(self):
        """测试相关上下文检索"""
        # 添加测试记忆
        self.chat_system.add_memory_from_interaction(
            "风险评估问题",
            "基于您的风险承受能力，建议..."
        )
        
        # 获取相关上下文
        context = self.chat_system.get_relevant_context("风险")
        self.assertIn("风险评估问题", context)
        self.assertIn("风险承受能力", context)
    
    def test_prompt_formatting_with_memory(self):
        """测试带记忆提示词格式化"""
        # 添加记忆
        self.chat_system.add_memory_from_interaction(
            "之前的问题",
            "之前的回答"
        )
        
        # 格式化提示词
        formatted = self.chat_system.format_prompt_with_memory("新问题")
        self.assertIn("之前的相关对话记忆", formatted)
        self.assertIn("新问题", formatted)


class TestDeterministicBehavior(unittest.TestCase):
    """测试确定性行为"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "deterministic_test.json")
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.memory_path):
            os.remove(self.memory_path)
        os.rmdir(self.temp_dir)
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        store1 = DeterministicMemoryStore(self.memory_path)
        hash1 = store1._generate_hash("相同内容", "相同上下文")
        
        # 创建新实例
        store2 = DeterministicMemoryStore(self.memory_path)
        hash2 = store2._generate_hash("相同内容", "相同上下文")
        
        # 哈希应该相同
        self.assertEqual(hash1, hash2)
    
    def test_id_consistency(self):
        """测试ID一致性"""
        store1 = DeterministicMemoryStore(self.memory_path)
        id1 = store1._generate_id("相同内容", "相同上下文", 1234567890.0)
        
        # 创建新实例
        store2 = DeterministicMemoryStore(self.memory_path)
        id2 = store2._generate_id("相同内容", "相同上下文", 1234567890.0)
        
        # ID应该相同
        self.assertEqual(id1, id2)
    
    def test_memory_deduplication(self):
        """测试记忆去重"""
        store = DeterministicMemoryStore(self.memory_path)
        
        # 多次添加相同内容
        id1 = store.add_memory("重复内容", "重复上下文")
        id2 = store.add_memory("重复内容", "重复上下文")
        id3 = store.add_memory("重复内容", "重复上下文")
        
        # 应该只保留一个
        self.assertEqual(id1, id2)
        self.assertEqual(id2, id3)
        self.assertEqual(len(store.memories), 1)


class TestFinancialUseCase(unittest.TestCase):
    """测试金融场景用例"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_path = os.path.join(self.temp_dir, "financial_test.json")
        self.memory_store = DeterministicMemoryStore(self.memory_path)
        self.chat_system = LLMChatWithMemory(self.memory_store)
        self.chat_system.set_context("financial_advisory")
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.memory_path):
            os.remove(self.memory_path)
        os.rmdir(self.temp_dir)
    
    def test_risk_assessment_memory(self):
        """测试风险评估记忆"""
        # 模拟风险评估对话
        self.chat_system.add_memory_from_interaction(
            "我的风险承受能力如何？",
            "根据您的年龄、收入、投资经验等因素，您的风险承受能力属于中等水平...",
            metadata={"category": "risk_assessment", "risk_level": "medium"}
        )
        
        # 搜索风险相关内容
        memories = self.memory_store.search_memories("风险承受")
        self.assertEqual(len(memories), 1)
        self.assertIn("中等水平", memories[0].content)
    
    def test_investment_recommendation_context(self):
        """测试投资建议上下文"""
        # 添加用户风险信息
        self.memory_store.add_memory(
            "用户风险承受能力：中等",
            "financial_advisory",
            {"type": "risk_profile", "level": "moderate"}
        )
        
        # 获取投资建议上下文
        context = self.chat_system.get_relevant_context("投资")
        self.assertIn("风险承受能力", context)
    
    def test_compliance_metadata(self):
        """测试合规元数据"""
        # 添加带合规信息的记忆
        self.memory_store.add_memory(
            "投资建议：分散投资",
            "financial_advisory",
            {
                "type": "recommendation",
                "compliance": {
                    "disclaimer": "投资有风险，决策需谨慎",
                    "regulation": "符合相关法规",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
        )
        
        # 验证元数据被保存
        memories = self.memory_store.search_memories("分散投资")
        self.assertEqual(len(memories), 1)
        self.assertIn("compliance", memories[0].metadata)
        self.assertIn("投资有风险", memories[0].metadata["compliance"]["disclaimer"])


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestMemorySystem,
        TestLLMChatWithMemory,
        TestDeterministicBehavior,
        TestFinancialUseCase
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("运行LLM Memory系统测试...")
    success = run_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败！")
        exit(1)