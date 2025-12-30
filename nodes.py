from state import AgentState, FinancialAgentState, Message, MessageRole, MessageType, MemoryEntry
from datetime import datetime
from typing import Dict, Any, Optional, List


def planner_node(state: AgentState) -> AgentState:
    """规划器节点：分析当前状态并制定计划"""
    new_state = state.model_copy(deep=True)
    new_state.increment_step()
    
    # 分析当前对话状态
    latest_message = new_state.get_latest_message()
    
    if latest_message:
        # 根据消息类型和内容制定计划
        if "风险" in latest_message.content or "risk" in latest_message.content.lower():
            new_state.add_message(
                role=MessageRole.SYSTEM,
                content="检测到风险评估需求，准备进行风险分析",
                message_type=MessageType.SYSTEM_MESSAGE,
                metadata={"plan_type": "risk_assessment"}
            )
        elif "投资" in latest_message.content or "investment" in latest_message.content.lower():
            new_state.add_message(
                role=MessageRole.SYSTEM,
                content="检测到投资建议需求，准备进行投资分析",
                message_type=MessageType.SYSTEM_MESSAGE,
                metadata={"plan_type": "investment_advice"}
            )
        else:
            new_state.add_message(
                role=MessageRole.SYSTEM,
                content="一般性对话，准备标准响应",
                message_type=MessageType.SYSTEM_MESSAGE,
                metadata={"plan_type": "general"}
            )
    
    new_state.set_status("processing")
    return new_state


def memory_recall_node(state: AgentState) -> AgentState:
    """记忆召回节点：检索相关记忆"""
    new_state = state.model_copy(deep=True)
    
    latest_message = new_state.get_latest_message()
    if not latest_message:
        return new_state
    
    # 简单的关键词匹配召回（可以扩展为向量搜索）
    query = latest_message.content
    relevant_memories = []
    
    for memory in new_state.memories.values():
        # 上下文匹配和关键词匹配
        if (memory.context == new_state.context and 
            any(keyword in query for keyword in ["风险", "投资", "产品", "收益"])):
            relevant_memories.append(memory)
    
    # 按时间排序，取最新的
    relevant_memories.sort(key=lambda x: x.timestamp, reverse=True)
    top_memories = relevant_memories[:3]  # 取前3个最相关的
    
    if top_memories:
        memory_context = "\n".join([
            f"[{mem.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {mem.content}"
            for mem in top_memories
        ])
        
        new_state.add_message(
            role=MessageRole.SYSTEM,
            content=f"相关历史记忆：\n{memory_context}",
            message_type=MessageType.MEMORY_RECALL,
            metadata={
                "recalled_memories": [mem.id for mem in top_memories],
                "recall_method": "keyword_matching"
            }
        )
    
    return new_state


def decision_node(state: AgentState) -> AgentState:
    """决策节点：基于事实和记忆做出决策"""
    new_state = state.model_copy(deep=True)
    
    # 获取系统消息（规划和记忆召回的结果）
    system_messages = [msg for msg in new_state.messages if msg.role == MessageRole.SYSTEM]
    
    decision_factors = []
    
    # 基于规划类型做决策
    for msg in system_messages:
        if msg.metadata.get("plan_type") == "risk_assessment":
            decision_factors.append("risk_analysis_required")
        elif msg.metadata.get("plan_type") == "investment_advice":
            decision_factors.append("investment_advice_required")
        elif msg.metadata.get("recalled_memories"):
            decision_factors.append("has_historical_context")
    
    # 基于事实做决策
    if new_state.facts.get("risk_level"):
        decision_factors.append(f"known_risk_{new_state.facts['risk_level']}")
    
    # 做出最终决策
    if "risk_analysis_required" in decision_factors:
        new_state.decision = "PERFORM_RISK_ASSESSMENT"
    elif "investment_advice_required" in decision_factors:
        new_state.decision = "PROVIDE_INVESTMENT_ADVICE"
    elif "has_historical_context" in decision_factors:
        new_state.decision = "USE_CONTEXTUAL_RESPONSE"
    else:
        new_state.decision = "GENERAL_RESPONSE"
    
    new_state.add_message(
        role=MessageRole.SYSTEM,
        content=f"决策结果: {new_state.decision}",
        message_type=MessageType.SYSTEM_MESSAGE,
        metadata={"decision_factors": decision_factors}
    )
    
    return new_state


def response_generator_node(state: AgentState) -> AgentState:
    """响应生成器节点：生成最终响应"""
    new_state = state.model_copy(deep=True)
    
    # 基于决策生成响应
    if new_state.decision == "PERFORM_RISK_ASSESSMENT":
        response = generate_risk_assessment_response(new_state)
    elif new_state.decision == "PROVIDE_INVESTMENT_ADVICE":
        response = generate_investment_advice_response(new_state)
    elif new_state.decision == "USE_CONTEXTUAL_RESPONSE":
        response = generate_contextual_response(new_state)
    else:
        response = generate_general_response(new_state)
    
    new_state.add_message(
        role=MessageRole.ASSISTANT,
        content=response,
        message_type=MessageType.ASSISTANT_RESPONSE,
        metadata={
            "decision": new_state.decision,
            "response_type": "generated"
        }
    )
    
    new_state.set_status("waiting_input")
    return new_state


def memory_storage_node(state: AgentState) -> AgentState:
    """记忆存储节点：存储重要的交互信息"""
    new_state = state.model_copy(deep=True)
    
    # 存储用户输入
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    if user_messages:
        latest_user_msg = user_messages[-1]
        memory_entry = create_memory_entry(
            content=latest_user_msg.content,
            context=new_state.context,
            message_type=MessageType.USER_INPUT,
            metadata={
                "session_id": new_state.session_id,
                "user_id": new_state.user_id,
                "timestamp": latest_user_msg.timestamp.isoformat()
            }
        )
        new_state.add_memory(memory_entry)
    
    # 存储助手响应
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    if assistant_messages:
        latest_assistant_msg = assistant_messages[-1]
        memory_entry = create_memory_entry(
            content=latest_assistant_msg.content,
            context=new_state.context,
            message_type=MessageType.ASSISTANT_RESPONSE,
            metadata={
                "session_id": new_state.session_id,
                "decision": new_state.decision,
                "response_type": latest_assistant_msg.metadata.get("response_type", "generated")
            }
        )
        new_state.add_memory(memory_entry)
    
    return new_state


def compliance_check_node(state: AgentState) -> AgentState:
    """合规检查节点：确保响应符合要求"""
    new_state = state.model_copy(deep=True)
    
    # 获取最新的助手响应
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    if not assistant_messages:
        return new_state
    
    latest_response = assistant_messages[-1].content
    
    # 基础合规检查
    compliance_flags = []
    
    # 1. 风险免责声明检查
    if "风险" in latest_response and "免责声明" not in latest_response:
        compliance_flags.append("missing_risk_disclaimer")
    
    # 2. 投资建议合规检查
    if "投资" in latest_response:
        if "投资有风险" not in latest_response:
            compliance_flags.append("missing_investment_warning")
        if new_state.risk_level == "high" and "谨慎" not in latest_response:
            compliance_flags.append("insufficient_high_risk_warning")
    
    # 3. 监管合规检查
    if "保证收益" in latest_response or "保本" in latest_response:
        compliance_flags.append("prohibited_guarantee_statement")
    
    # 应用合规标记
    for flag in compliance_flags:
        new_state.add_compliance_flag(flag)
    
    # 如果存在合规问题，添加修正消息
    if compliance_flags:
        correction = generate_compliance_correction(compliance_flags)
        new_state.add_message(
            role=MessageRole.SYSTEM,
            content=correction,
            message_type=MessageType.SYSTEM_MESSAGE,
            metadata={"compliance_flags": compliance_flags, "type": "compliance_correction"}
        )
    
    return new_state


# 辅助函数
def create_memory_entry(content: str, context: str, message_type: MessageType, 
                       metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
    """创建记忆条目"""
    import hashlib
    from datetime import datetime
    
    timestamp = datetime.utcnow()
    memory_hash = hashlib.sha256(f"{content}|{context}|{timestamp.isoformat()}".encode()).hexdigest()[:16]
    memory_id = hashlib.md5(f"{content}|{context}|{timestamp.isoformat()}".encode()).hexdigest()
    
    return MemoryEntry(
        id=memory_id,
        content=content,
        context=context,
        timestamp=timestamp,
        metadata=metadata or {},
        hash=memory_hash,
        message_type=message_type
    )


def generate_risk_assessment_response(state: AgentState) -> str:
    """生成风险评估响应"""
    risk_level = state.get_fact("risk_level") or "中等"
    
    return f"""基于您的风险承受能力评估，您的风险等级为{risk_level}。

在进行任何投资决策前，请注意以下重要事项：
1. 投资有风险，过往业绩不代表未来表现
2. 请根据您的实际情况谨慎投资
3. 建议分散投资以降低风险
4. 如有疑问，请咨询专业投资顾问

免责声明：本建议仅供参考，不构成投资建议。投资有风险，决策需谨慎。"""


def generate_investment_advice_response(state: AgentState) -> str:
    """生成投资建议响应"""
    risk_level = state.get_fact("risk_level") or "中等"
    
    advice_map = {
        "low": "建议您考虑稳健型理财产品，如货币基金、国债等",
        "medium": "建议您考虑平衡型投资组合，如混合基金、债券基金等",
        "high": "建议您可考虑成长型投资，但请充分评估风险承受能力"
    }
    
    base_advice = advice_map.get(risk_level, advice_map["medium"])
    
    return f"""基于您的风险等级（{risk_level}），{base_advice}。

重要提醒：
- 投资有风险，请根据自身情况谨慎决策
- 建议进行充分的产品研究和风险评估
- 分散投资可以有效降低投资风险
- 定期评估和调整投资组合

本建议基于一般性投资原则，具体投资决策请结合个人实际情况。投资有风险，入市需谨慎。"""


def generate_contextual_response(state: AgentState) -> str:
    """生成基于上下文的响应"""
    # 获取相关记忆
    relevant_memories = []
    for memory in state.memories.values():
        if memory.context == state.context and memory.timestamp.date() == datetime.now().date():
            relevant_memories.append(memory)
    
    if relevant_memories:
        context_info = "根据我们之前的对话，我了解到："
        for memory in relevant_memories[-2:]:  # 取最近2条
            context_info += f"\n- {memory.content}"
        
        return f"""{context_info}

基于以上信息，我来回答您的当前问题：

我理解您持续关注相关话题。如果您有具体的问题或需要更详细的解释，请随时告诉我。

请注意：任何具体的投资建议都需要基于您的个人情况和风险承受能力进行评估。"""
    else:
        return generate_general_response(state)


def generate_general_response(state: AgentState) -> str:
    """生成一般性响应"""
    return """我理解您的问题。作为AI助手，我可以为您提供一般性的金融知识和信息。

需要提醒您的是：
1. 任何具体的投资决策都应该基于您的个人情况
2. 建议您咨询专业的金融顾问获取个性化建议
3. 投资有风险，请充分了解相关产品信息
4. 保持理性投资，不要盲目跟风

如果您需要了解特定的金融产品或投资知识，我很乐意为您提供相关信息。"""


def generate_compliance_correction(flags: List[str]) -> str:
    """生成合规修正建议"""
    corrections = []
    
    if "missing_risk_disclaimer" in flags:
        corrections.append("需要添加风险免责声明")
    
    if "missing_investment_warning" in flags:
        corrections.append("需要添加投资风险提示")
    
    if "insufficient_high_risk_warning" in flags:
        corrections.append("高风险投资需要更充分的警示")
    
    if "prohibited_guarantee_statement" in flags:
        corrections.append("移除了违规的收益保证表述")
    
    return f"合规检查提醒：{'; '.join(corrections)}。请确保所有建议都符合相关法规要求。"