import openai
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType
from graph import get_graph, run_agent_workflow
from audit import AuditLog, FinancialAuditLog
from policy import compliance_policy, memory_retention_policy
import uuid


class LLMChatWithMemoryV2:
    """基于Pydantic + LangGraph的LLM Memory系统"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.1,
                 max_tokens: int = 1000,
                 audit_log_path: str = "audit.db",
                 graph_type: str = "base"):
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请提供OpenAI API密钥或通过环境变量OPENAI_API_KEY设置")
        
        openai.api_key = self.api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.graph_type = graph_type
        
        # 初始化审计日志
        self.audit_log = AuditLog(audit_log_path)
        
        # 获取图
        self.graph = get_graph(graph_type)
    
    def create_session(self, user_id: Optional[str] = None, context: str = "default") -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        # 创建初始状态
        if self.graph_type == "financial":
            initial_state = FinancialAgentState(
                session_id=session_id,
                user_id=user_id,
                context=context,
                compliance_level="retail",
                risk_level="medium"
            )
        else:
            initial_state = AgentState(
                session_id=session_id,
                user_id=user_id,
                context=context
            )
        
        # 记录初始状态
        self.audit_log.append_state(initial_state, "session_start")
        
        return session_id
    
    def chat_completion(self, 
                       session_id: str,
                       user_input: str,
                       context: Optional[str] = None,
                       system_prompt: Optional[str] = None,
                       save_memory: bool = True) -> Dict[str, Any]:
        """
        处理聊天完成请求
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            context: 上下文（可选）
            system_prompt: 系统提示词（可选）
            save_memory: 是否保存记忆
        
        Returns:
            包含响应和元数据的字典
        """
        
        # 获取当前状态（这里简化处理，实际应该持久化状态）
        current_state = self._get_current_state(session_id)
        
        # 更新上下文
        if context:
            current_state.context = context
        
        # 添加用户消息
        current_state.add_message(
            role=MessageRole.USER,
            content=user_input,
            message_type=MessageType.USER_INPUT
        )
        
        # 记录用户消息
        self.audit_log.append_message(session_id, current_state.get_latest_message())
        
        # 合规检查
        if not compliance_policy(current_state):
            return {
                "response": "抱歉，您的请求未能通过合规检查。请确保您的请求符合相关法规要求。",
                "status": "rejected",
                "compliance_flags": current_state.compliance_flags,
                "session_id": session_id
            }
        
        # 运行代理工作流
        final_state = run_agent_workflow(current_state, self.graph_type)
        
        # 获取助手响应
        assistant_messages = final_state.get_messages_by_role(MessageRole.ASSISTANT)
        if assistant_messages:
            response = assistant_messages[-1].content
        else:
            response = "抱歉，我无法生成合适的响应。"
        
        # 记录最终状态
        self.audit_log.append_state(final_state, "completion")
        
        return {
            "response": response,
            "status": final_state.status,
            "decision": final_state.decision,
            "step": final_state.step,
            "memory_count": len(final_state.memories),
            "compliance_flags": final_state.compliance_flags,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_current_state(self, session_id: str) -> AgentState:
        """获取当前状态（简化版，实际应该持久化）"""
        # 这里创建新的状态，实际应该基于session_id从存储中恢复
        if self.graph_type == "financial":
            return FinancialAgentState(
                session_id=session_id,
                context="financial_advisory",
                compliance_level="retail"
            )
        else:
            return AgentState(session_id=session_id)
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return self.audit_log.get_session_history(session_id, limit)
    
    def get_compliance_report(self, session_id: str) -> Dict[str, Any]:
        """获取合规报告"""
        return self.audit_log.get_compliance_report(session_id)
    
    def verify_session_integrity(self, session_id: str) -> bool:
        """验证会话完整性"""
        return self.audit_log.verify_state_integrity(session_id)
    
    def search_memories(self, session_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索记忆"""
        # 获取状态
        state = self._get_current_state(session_id)
        
        # 搜索相关记忆
        relevant_memories = []
        for memory in state.memories.values():
            if query.lower() in memory.content.lower():
                relevant_memories.append({
                    "id": memory.id,
                    "content": memory.content,
                    "context": memory.context,
                    "timestamp": memory.timestamp.isoformat(),
                    "message_type": memory.message_type
                })
        
        # 按时间排序
        relevant_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return relevant_memories[:limit]
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """关闭会话"""
        # 获取最终状态
        state = self._get_current_state(session_id)
        state.set_status("complete")
        
        # 记录会话结束
        self.audit_log.append_state(state, "session_end")
        
        return {
            "session_id": session_id,
            "status": "closed",
            "total_steps": state.step,
            "total_memories": len(state.memories),
            "compliance_status": "compliant" if state.is_compliant() else "non_compliant"
        }


class FinancialLLMChat(LLMChatWithMemoryV2):
    """金融专用LLM Memory系统"""
    
    def __init__(self, **kwargs):
        kwargs["graph_type"] = "financial"
        kwargs["audit_log_path"] = kwargs.get("audit_log_path", "financial_audit.db")
        super().__init__(**kwargs)
        
        # 使用金融专用审计日志
        self.audit_log = FinancialAuditLog(kwargs.get("audit_log_path", "financial_audit.db"))
    
    def set_risk_profile(self, session_id: str, risk_level: str, factors: Dict[str, Any]) -> None:
        """设置风险画像"""
        state = self._get_current_state(session_id)
        if isinstance(state, FinancialAgentState):
            state.set_risk_profile(risk_level, factors)
            
            # 记录风险评估
            self.audit_log.log_risk_assessment(
                session_id=session_id,
                risk_level=risk_level,
                risk_factors=factors,
                recommendation_type="initial_assessment"
            )
    
    def set_investment_limit(self, session_id: str, limit: float) -> None:
        """设置投资限额"""
        state = self._get_current_state(session_id)
        if isinstance(state, FinancialAgentState):
            state.investment_limit = limit
    
    def add_approved_products(self, session_id: str, products: List[str]) -> None:
        """添加批准产品"""
        state = self._get_current_state(session_id)
        if isinstance(state, FinancialAgentState):
            state.approved_products.extend(products)
    
    def add_restricted_products(self, session_id: str, products: List[str]) -> None:
        """添加限制产品"""
        state = self._get_current_state(session_id)
        if isinstance(state, FinancialAgentState):
            state.restricted_products.extend(products)


# 使用示例
def demo_financial_chat_v2():
    """演示金融聊天系统V2"""
    
    try:
        # 初始化金融专用聊天系统
        chat = FinancialLLMChat(
            model="gpt-3.5-turbo",
            temperature=0.1,
            audit_log_path="demo_financial_audit.db"
        )
        
        # 创建会话
        session_id = chat.create_session(
            user_id="demo_user_001",
            context="financial_advisory"
        )
        
        print(f"=== 金融LLM Memory系统演示 ===")
        print(f"会话ID: {session_id}")
        print("-" * 50)
        
        # 设置风险画像
        chat.set_risk_profile(
            session_id=session_id,
            risk_level="medium",
            factors={
                "age": 35,
                "income": "stable",
                "investment_experience": "moderate",
                "investment_goal": "balanced_growth"
            }
        )
        
        # 设置投资限制
        chat.set_investment_limit(session_id, 100000)
        chat.add_approved_products(session_id, ["mutual_funds", "bonds", "etfs"])
        chat.add_restricted_products(session_id, ["derivatives", "crypto", "leveraged_products"])
        
        # 模拟对话
        conversations = [
            "我的风险承受能力如何评估？",
            "基于我的情况，推荐什么理财产品？",
            "这些产品的预期收益率是多少？",
            "如何分散投资风险？"
        ]
        
        for i, user_input in enumerate(conversations):
            print(f"\n对话 {i+1}:")
            print(f"用户: {user_input}")
            
            result = chat.chat_completion(
                session_id=session_id,
                user_input=user_input,
                system_prompt="""你是一个专业的金融顾问。请提供准确、合规、风险可控的建议。
                回答必须：
                1. 基于事实和数据
                2. 考虑风险因素  
                3. 符合监管要求
                4. 适合用户的风险承受能力"""
            )
            
            print(f"助手: {result['response']}")
            print(f"状态: {result['status']}, 步骤: {result['step']}, 记忆数: {result['memory_count']}")
            if result['compliance_flags']:
                print(f"合规标记: {result['compliance_flags']}")
        
        # 搜索记忆
        print(f"\n搜索'风险'相关记忆:")
        memories = chat.search_memories(session_id, "风险", limit=3)
        for memory in memories:
            print(f"- {memory['content'][:100]}...")
        
        # 获取合规报告
        print(f"\n合规报告:")
        compliance_report = chat.get_compliance_report(session_id)
        print(f"总检查数: {compliance_report['total_checks']}")
        print(f"通过检查: {compliance_report['passed_checks']}")
        print(f"失败检查: {compliance_report['failed_checks']}")
        
        # 验证会话完整性
        integrity_check = chat.verify_session_integrity(session_id)
        print(f"\n会话完整性: {'✅ 通过' if integrity_check else '❌ 失败'}")
        
        # 关闭会话
        close_result = chat.close_session(session_id)
        print(f"\n会话关闭: {close_result}")
        
    except ValueError as e:
        print(f"初始化失败: {e}")
        print("请设置OPENAI_API_KEY环境变量")
        return


if __name__ == "__main__":
    demo_financial_chat_v2()