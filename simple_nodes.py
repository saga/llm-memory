"""
简化版节点函数 - 修复版本
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json
import uuid
from simple_state import AgentState, FinancialAgentState, Message, MessageRole, MessageType, MemoryEntry


def planner_node(state: AgentState) -> AgentState:
    """规划节点：分析用户输入，确定处理策略"""
    new_state = state.model_copy(deep=True)
    
    # 获取最新消息
    latest_message = new_state.get_latest_message()
    if not latest_message or latest_message.role != MessageRole.USER:
        return new_state
    
    # 分析用户意图
    user_input = latest_message.content.lower()
    
    # 简单的意图识别
    if any(word in user_input for word in ["投资", "理财", "股票", "基金", "风险"]):
        new_state.decision = "investment_advice"
    elif any(word in user_input for word in ["记忆", "记住", "回忆"]):
        new_state.decision = "memory_operation"
    elif any(word in user_input for word in ["帮助", "协助"]):
        new_state.decision = "general_help"
    else:
        new_state.decision = "general_chat"
    
    # 添加系统思考消息
    new_state.add_message(
        role=MessageRole.SYSTEM,
        content=f"检测到用户意图: {new_state.decision}",
        message_type=MessageType.SYSTEM_MESSAGE
    )
    
    new_state.increment_step()
    return new_state


def memory_recall_node(state: AgentState) -> AgentState:
    """记忆召回节点：从长期记忆中召回相关信息"""
    new_state = state.model_copy(deep=True)
    
    # 获取最新消息
    latest_message = new_state.get_latest_message()
    if not latest_message:
        return new_state
    
    # 简单的记忆召回逻辑
    recalled_memories = []
    
    # 基于关键词召回
    user_input = latest_message.content
    for memory_id, memory in new_state.memories.items():
        # 简单的关键词匹配
        if any(word in user_input for word in memory.content.split()[:5]):
            recalled_memories.append(memory)
    
    # 添加召回的记忆到状态
    if recalled_memories:
        new_state.add_message(
            role=MessageRole.SYSTEM,
            content=f"召回 {len(recalled_memories)} 条相关记忆",
            message_type=MessageType.MEMORY_RECALL,
            metadata={"recalled_count": len(recalled_memories)}
        )
    
    new_state.increment_step()
    return new_state


def decision_node(state: AgentState) -> AgentState:
    """决策节点：基于当前状态做出处理决策"""
    new_state = state.model_copy(deep=True)
    
    # 基于之前的决策和状态做出选择
    if new_state.decision == "investment_advice":
        # 投资建议需要额外的风险评估
        new_state.set_status("processing")
        new_state.add_compliance_flag("investment_advice_requested")
    elif new_state.decision == "memory_operation":
        # 记忆操作
        new_state.set_status("processing")
    else:
        # 一般聊天
        new_state.set_status("processing")
    
    new_state.increment_step()
    return new_state


def response_generator_node(state: AgentState) -> AgentState:
    """响应生成节点：生成助手回复"""
    new_state = state.model_copy(deep=True)
    
    # 获取用户输入
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    if not user_messages:
        return new_state
    
    latest_user_message = user_messages[-1]
    
    # 基于决策生成响应
    if new_state.decision == "investment_advice":
        response_content = generate_investment_response(new_state, latest_user_message.content)
    elif new_state.decision == "memory_operation":
        response_content = generate_memory_response(new_state, latest_user_message.content)
    else:
        response_content = generate_general_response(new_state, latest_user_message.content)
    
    # 添加助手回复
    new_state.add_message(
        role=MessageRole.ASSISTANT,
        content=response_content,
        message_type=MessageType.ASSISTANT_RESPONSE
    )
    
    new_state.increment_step()
    return new_state


def compliance_check_node(state: AgentState) -> AgentState:
    """合规检查节点：检查回复是否符合规定"""
    new_state = state.model_copy(deep=True)
    
    # 获取最新的助手回复
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    if not assistant_messages:
        return new_state
    
    latest_response = assistant_messages[-1]
    
    # 基础合规检查
    compliance_flags = []
    
    # 检查是否包含投资建议
    if new_state.decision == "investment_advice":
        compliance_flags.append("investment_advice")
        
        # 检查是否包含风险披露
        if "风险" not in latest_response.content:
            compliance_flags.append("missing_risk_disclosure")
    
    # 检查是否包含保证性语言
    if any(word in latest_response.content for word in ["保证", "确保", "一定", "100%"]):
        compliance_flags.append("guarantee_language")
    
    # 更新合规标记
    for flag in compliance_flags:
        new_state.add_compliance_flag(flag)
    
    # 如果需要添加风险披露
    if "missing_risk_disclosure" in compliance_flags:
        # 在回复后添加风险披露
        risk_disclosure = "\n\n【重要声明】投资有风险，过往业绩不代表未来表现。请根据自身情况谨慎投资，如有疑问请咨询专业投资顾问。"
        latest_response.content += risk_disclosure
    
    new_state.increment_step()
    return new_state


def memory_storage_node(state: AgentState) -> AgentState:
    """记忆存储节点：存储重要的对话信息"""
    new_state = state.model_copy(deep=True)
    
    # 获取最新消息
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    
    if user_messages and assistant_messages:
        # 创建记忆条目
        memory_content = f"用户: {user_messages[-1].content}\n助手: {assistant_messages[-1].content}"
        
        memory_entry = create_memory_entry(
            content=memory_content,
            context=new_state.context,
            message_type=MessageType.USER_INPUT,
            metadata={
                "decision": new_state.decision,
                "risk_level": new_state.risk_level,
                "compliance_flags": new_state.compliance_flags
            }
        )
        
        # 存储记忆
        new_state.add_memory(memory_entry)
    
    new_state.increment_step()
    return new_state


def create_memory_entry(content: str, context: str, message_type: MessageType, 
                       metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
    """创建记忆条目"""
    # 生成确定性ID
    memory_id = hashlib.md5(f"{content}_{context}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    # 计算哈希
    memory_hash = hashlib.sha256(f"{content}_{context}".encode()).hexdigest()
    
    # 时间戳
    timestamp = datetime.utcnow()
    
    return MemoryEntry(
        id=memory_id,
        content=content,
        context=context,
        timestamp=timestamp,
        metadata=metadata or {},
        hash=memory_hash,
        message_type=message_type
    )


def generate_investment_response(state: AgentState, user_input: str) -> str:
    """生成投资建议响应"""
    # 基础的投资建议模板
    response = "基于您的风险承受能力评估，"
    
    if state.risk_level == "low":
        response += "建议您选择低风险的投资产品，如货币基金、国债等。"
    elif state.risk_level == "medium":
        response += "可以考虑中等风险的投资组合，如混合型基金、债券基金等。"
    else:
        response += "您可以考虑较高风险的投资产品，如股票型基金、ETF等。"
    
    response += "\n\n在进行任何投资决策前，请注意以下重要事项："
    response += "\n1. 投资有风险，过往业绩不代表未来表现"
    response += "\n2. 请根据您的实际情况谨慎投资"
    response += "\n3. 建议分散投资以降低风险"
    response += "\n4. 如有疑问，请咨询专业投资顾问"
    
    response += "\n\n免责声明：本建议仅供参考，不构成投资建议。投资有风险，决策需谨慎。"
    
    return response


def generate_memory_response(state: AgentState, user_input: str) -> str:
    """生成记忆操作响应"""
    if "记住" in user_input:
        return "我会记住这个信息，在后续对话中会考虑相关内容。"
    elif "回忆" in user_input:
        memory_count = len(state.memories)
        return f"我已召回{memory_count}条相关记忆，会结合这些信息为您提供更好的服务。"
    else:
        return "我理解您关于记忆的需求，会继续学习和改进。"


def generate_general_response(state: AgentState, user_input: str) -> str:
    """生成一般聊天响应"""
    return "我理解您的问题。作为AI助手，我会尽力为您提供准确和有用的信息。如果您有具体的投资或理财问题，我也很乐意为您提供建议。"