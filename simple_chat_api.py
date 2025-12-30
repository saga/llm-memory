import openai
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from simple_state import AgentState, FinancialAgentState, Message, MessageRole, MessageType
from simple_graph import run_simple_agent_workflow  # 改用简化版
from simple_audit import SimpleAuditLog, SimpleFinancialAuditLog
from simple_policy import compliance_policy, memory_retention_policy
import uuid


class SimpleLLMChatWithMemory:
    """简化版LLM Memory系统 - 不依赖LangGraph"""
    
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
        if graph_type == "financial":
            self.audit_log = SimpleFinancialAuditLog(audit_log_path)
        else:
            self.audit_log = SimpleAuditLog(audit_log_path)
            
        # 会话存储
        self.sessions: Dict[str, AgentState] = {}
    
    def create_session(self, session_id: str = None) -> str:
        """创建新会话"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        if self.graph_type == "financial":
            initial_state = FinancialAgentState(session_id=session_id)
        else:
            initial_state = AgentState(session_id=session_id)
            
        self.sessions[session_id] = initial_state
        return session_id
    
    def get_session(self, session_id: str) -> Optional[AgentState]:
        """获取会话状态"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: MessageRole, content: str, 
                   message_type: MessageType = MessageType.USER_INPUT) -> bool:
        """添加消息到会话"""
        session = self.get_session(session_id)
        if not session:
            return False
            
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            timestamp=datetime.now()
        )
        
        session.messages.append(message)
        return True
    
    def get_chat_completion(self, session_id: str, user_input: str) -> str:
        """获取聊天完成，带记忆功能"""
        # 添加用户消息
        self.add_message(session_id, MessageRole.USER, user_input)
        
        # 获取当前会话状态
        current_state = self.get_session(session_id)
        if not current_state:
            raise ValueError(f"会话 {session_id} 不存在")
        
        # 记录审计日志
        self.audit_log.log_state_change(
            session_id=session_id,
            step=len(current_state.messages),
            action="chat_completion",
            state_json=current_state.model_dump_json(),
            state_hash=current_state.compute_hash()
        )
        
        # 使用简化版工作流
        final_state = run_simple_agent_workflow(
            current_state,
            graph_type=self.graph_type,
            max_steps=10
        )
        
        # 更新会话状态
        self.sessions[session_id] = final_state
        
        # 返回最后一条助手消息
        for msg in reversed(final_state.messages):
            if msg.role == MessageRole.ASSISTANT:
                return msg.content
                
        return "抱歉，我没有生成有效的回复。"
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        session = self.get_session(session_id)
        if not session:
            return []
            
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "type": msg.message_type.value,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]
    
    def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


class SimpleFinancialLLMChat(SimpleLLMChatWithMemory):
    """简化版金融专用LLM Memory系统"""
    
    def __init__(self, **kwargs):
        kwargs['graph_type'] = 'financial'
        super().__init__(**kwargs)
    
    def set_risk_profile(self, session_id: str, risk_level: str, 
                        factors: Optional[Dict[str, Any]] = None) -> bool:
        """设置用户风险档案"""
        session = self.get_session(session_id)
        if not session or not isinstance(session, FinancialAgentState):
            return False
            
        session.set_risk_profile(risk_level, factors or {})
        
        # 记录审计日志
        self.audit_log.log_state_change(
            session_id=session_id,
            step=len(session.messages),
            action="set_risk_profile",
            state_json=session.model_dump_json(),
            state_hash=session.compute_hash(),
            metadata={"risk_level": risk_level, "factors": factors}
        )
        
        return True
    
    def get_compliance_status(self, session_id: str) -> Dict[str, Any]:
        """获取合规状态"""
        session = self.get_session(session_id)
        if not session or not isinstance(session, FinancialAgentState):
            return {"error": "会话不存在或类型错误"}
            
        return {
            "compliance_flags": session.compliance_flags,
            "risk_disclosures": session.risk_disclosures,
            "audit_trail": session.audit_trail,
            "risk_profile": session.risk_profile
        }