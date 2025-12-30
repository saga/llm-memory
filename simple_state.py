"""
简化版状态模型 - 修复版本
"""
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import hashlib
import json


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    USER_INPUT = "user_input"
    ASSISTANT_RESPONSE = "assistant_response"
    SYSTEM_MESSAGE = "system_message"
    MEMORY_RECALL = "memory_recall"


class Message(BaseModel):
    """消息模型，确保消息格式的一致性"""
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.USER_INPUT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
        use_enum_values = True


class MemoryEntry(BaseModel):
    """记忆条目，强类型保证"""
    id: str
    content: str
    context: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    hash: str
    message_type: MessageType = MessageType.USER_INPUT
    
    class Config:
        validate_assignment = True
        use_enum_values = True


class AgentState(BaseModel):
    """代理状态，核心状态模型"""
    
    # 短期记忆（对话历史）
    messages: List[Message] = Field(default_factory=list)
    
    # 长期记忆（事实和知识）
    memories: Dict[str, MemoryEntry] = Field(default_factory=dict)
    
    # 强事实（确定性知识）
    facts: Dict[str, str] = Field(default_factory=dict)
    
    # 控制状态
    step: int = Field(default=0, ge=0)
    status: Literal["idle", "processing", "waiting_input", "error", "complete"] = "idle"
    decision: Optional[str] = None
    
    # 审计信息
    session_id: str = Field(default="")
    user_id: Optional[str] = None
    context: str = Field(default="default")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # 合规和风险控制
    risk_level: Literal["low", "medium", "high"] = "low"
    compliance_flags: List[str] = Field(default_factory=list)
    
    class Config:
        validate_assignment = True
        use_enum_values = True
    
    @field_validator('step')
    def validate_step(cls, v):
        if v < 0:
            raise ValueError('step must be non-negative')
        return v
    
    def compute_hash(self) -> str:
        """计算状态哈希值"""
        state_dict = self.model_dump(exclude={'last_updated'})
        state_json = json.dumps(state_dict, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()
    
    def add_message(self, role: MessageRole, content: str, 
                   message_type: MessageType = MessageType.USER_INPUT,
                   metadata: Optional[Dict[str, Any]] = None) -> Message:
        """添加消息并返回消息对象"""
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_updated = datetime.utcnow()
        return message
    
    def add_fact(self, key: str, value: str) -> None:
        """添加确定性事实"""
        self.facts[key] = value
        self.last_updated = datetime.utcnow()
    
    def get_fact(self, key: str) -> Optional[str]:
        """获取事实"""
        return self.facts.get(key)
    
    def add_memory(self, memory: MemoryEntry) -> None:
        """添加记忆"""
        self.memories[memory.id] = memory
        self.last_updated = datetime.utcnow()
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取记忆"""
        return self.memories.get(memory_id)
    
    def get_messages_by_role(self, role: MessageRole) -> List[Message]:
        """按角色获取消息"""
        return [msg for msg in self.messages if msg.role == role]
    
    def get_latest_message(self) -> Optional[Message]:
        """获取最新消息"""
        return self.messages[-1] if self.messages else None
    
    def increment_step(self) -> int:
        """递增步骤计数器"""
        self.step += 1
        self.last_updated = datetime.utcnow()
        return self.step
    
    def set_status(self, status: Literal["idle", "processing", "waiting_input", "error", "complete"]) -> None:
        """设置状态"""
        self.status = status
        self.last_updated = datetime.utcnow()
    
    def add_compliance_flag(self, flag: str) -> None:
        """添加合规标记"""
        if flag not in self.compliance_flags:
            self.compliance_flags.append(flag)
    
    def is_compliant(self) -> bool:
        """检查是否合规"""
        return len(self.compliance_flags) == 0 or all(
            flag.startswith("approved:") for flag in self.compliance_flags
        )
    
    def get_audit_info(self) -> Dict[str, Any]:
        """获取审计信息"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "step": self.step,
            "status": self.status,
            "message_count": len(self.messages),
            "memory_count": len(self.memories),
            "fact_count": len(self.facts),
            "risk_level": self.risk_level,
            "compliance_flags": self.compliance_flags,
            "last_updated": self.last_updated.isoformat(),
            "context": self.context
        }


class FinancialAgentState(AgentState):
    """金融专用代理状态，扩展基础状态"""
    
    # 金融特定字段
    risk_profile: Dict[str, Any] = Field(default_factory=dict)
    portfolio_info: Dict[str, Any] = Field(default_factory=dict)
    regulatory_context: str = Field(default="")
    compliance_level: Literal["retail", "professional", "institutional"] = "retail"
    
    # 金融风险控制
    investment_limit: Optional[float] = Field(default=None, ge=0)
    approved_products: List[str] = Field(default_factory=list)
    restricted_products: List[str] = Field(default_factory=list)
    
    # 审计追踪
    risk_disclosures: List[str] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    
    def set_risk_profile(self, risk_level: str, factors: Dict[str, Any]) -> None:
        """设置风险画像"""
        self.risk_profile = {
            "level": risk_level,
            "factors": factors,
            "assessed_at": datetime.utcnow().isoformat()
        }
        self.add_fact("risk_level", risk_level)
        self.last_updated = datetime.utcnow()
    
    def can_recommend_product(self, product_type: str) -> bool:
        """检查是否可以推荐产品"""
        if product_type in self.restricted_products:
            return False
        if self.approved_products and product_type not in self.approved_products:
            return False
        return True
    
    def add_risk_disclosure(self, disclosure: str) -> None:
        """添加风险披露"""
        if disclosure not in self.risk_disclosures:
            self.risk_disclosures.append(disclosure)
    
    def add_audit_entry(self, entry_type: str, details: Dict[str, Any]) -> None:
        """添加审计条目"""
        self.audit_trail.append({
            "type": entry_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_financial_audit_info(self) -> Dict[str, Any]:
        """获取金融审计信息"""
        base_info = self.get_audit_info()
        return {
            **base_info,
            "risk_profile": self.risk_profile,
            "compliance_level": self.compliance_level,
            "investment_limit": self.investment_limit,
            "regulatory_context": self.regulatory_context,
            "portfolio_info_keys": list(self.portfolio_info.keys()),
            "risk_disclosures": self.risk_disclosures,
            "audit_trail_count": len(self.audit_trail)
        }