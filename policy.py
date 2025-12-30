from state import AgentState, FinancialAgentState
from typing import Literal


def next_step_policy(state: AgentState) -> str:
    """下一步决策策略"""
    if state.status == "error":
        return "error_handler"
    
    if state.step == 0:
        return "planner"
    
    # 基于决策结果选择下一步
    if state.decision == "PERFORM_RISK_ASSESSMENT":
        return "risk_assessment"
    elif state.decision == "PROVIDE_INVESTMENT_ADVICE":
        return "investment_advisor"
    elif state.decision == "USE_CONTEXTUAL_RESPONSE":
        return "contextual_response"
    elif state.decision == "GENERAL_RESPONSE":
        return "response_generator"
    
    # 默认流程
    if state.step < 3:  # 限制最大步骤数
        return "memory_recall"
    else:
        return "response_generator"


def routing_policy(state: AgentState) -> Literal["continue", "end", "error"]:
    """路由策略"""
    if state.status == "error":
        return "error"
    
    if state.status == "complete":
        return "end"
    
    # 检查是否需要用户输入
    if state.status == "waiting_input":
        return "end"
    
    return "continue"


def compliance_policy(state: AgentState) -> bool:
    """合规检查策略"""
    # 基础合规检查
    if not state.is_compliant():
        return False
    
    # 金融特定合规检查
    if isinstance(state, FinancialAgentState):
        # 检查投资限额
        if state.investment_limit is not None and state.investment_limit <= 0:
            return False
        
        # 检查风险等级
        if state.risk_level not in ["low", "medium", "high"]:
            return False
    
    return True


def memory_retention_policy(state: AgentState, memory_content: str) -> bool:
    """记忆保留策略"""
    # 敏感信息过滤
    sensitive_keywords = [
        "密码", "password", "身份证号", "银行卡号", 
        "phone", "email", "地址", "address"
    ]
    
    for keyword in sensitive_keywords:
        if keyword.lower() in memory_content.lower():
            return False
    
    # 合规内容检查
    if "违法" in memory_content or "illegal" in memory_content.lower():
        return False
    
    return True


def risk_assessment_policy(state: FinancialAgentState) -> Dict[str, Any]:
    """风险评估策略"""
    risk_factors = {}
    
    # 基于用户画像评估风险
    if state.risk_profile:
        risk_level = state.risk_profile.get("level", "medium")
        risk_factors["user_profile"] = risk_level
    
    # 基于合规级别评估
    compliance_risk_map = {
        "retail": "high",      # 零售客户需要更高保护
        "professional": "medium",  # 专业客户中等风险
        "institutional": "low"     # 机构客户低风险
    }
    
    risk_factors["compliance_level"] = compliance_risk_map.get(
        state.compliance_level, "medium"
    )
    
    # 综合风险等级
    overall_risk = max(risk_factors.values(), key=lambda x: ["low", "medium", "high"].index(x))
    
    return {
        "risk_level": overall_risk,
        "risk_factors": risk_factors,
        "recommendations": generate_risk_recommendations(overall_risk)
    }


def generate_risk_recommendations(risk_level: str) -> List[str]:
    """生成风险建议"""
    recommendations = {
        "low": [
            "可以提供标准投资建议",
            "适合推荐多样化产品",
            "可以进行详细的产品说明"
        ],
        "medium": [
            "需要充分的风险提示",
            "建议提供多种选择方案",
            "需要客户确认理解风险"
        ],
        "high": [
            "必须提供详细风险披露",
            "建议寻求专业意见",
            "需要额外的合规确认"
        ]
    }
    
    return recommendations.get(risk_level, recommendations["medium"])


def investment_restriction_policy(state: FinancialAgentState, product_type: str) -> Dict[str, Any]:
    """投资限制策略"""
    restrictions = {
        "allowed": True,
        "reasons": [],
        "conditions": []
    }
    
    # 检查是否在限制列表中
    if product_type in state.restricted_products:
        restrictions["allowed"] = False
        restrictions["reasons"].append(f"产品类型 {product_type} 在限制列表中")
        return restrictions
    
    # 检查是否在批准列表中（如果有的话）
    if state.approved_products and product_type not in state.approved_products:
        restrictions["allowed"] = False
        restrictions["reasons"].append(f"产品类型 {product_type} 不在批准列表中")
        return restrictions
    
    # 基于风险等级检查
    risk_product_map = {
        "low": ["savings", "bonds", "money_market"],
        "medium": ["balanced_funds", "etf", "blue_chips"],
        "high": ["stocks", "derivatives", "crypto"]
    }
    
    allowed_products = risk_product_map.get(state.risk_level, risk_product_map["medium"])
    if product_type not in allowed_products:
        restrictions["allowed"] = False
        restrictions["reasons"].append(f"产品风险等级与用户风险承受能力不匹配")
    
    # 基于投资限额检查
    if state.investment_limit is not None and state.investment_limit <= 0:
        restrictions["allowed"] = False
        restrictions["reasons"].append("投资限额已用完")
    
    return restrictions


def conversation_flow_policy(state: AgentState) -> Dict[str, Any]:
    """对话流控制策略"""
    flow_control = {
        "continue": True,
        "next_action": None,
        "reason": ""
    }
    
    # 步骤限制
    if state.step > 10:
        flow_control["continue"] = False
        flow_control["reason"] = "达到最大对话步骤限制"
        return flow_control
    
    # 基于状态决定下一步
    if state.status == "waiting_input":
        flow_control["continue"] = False
        flow_control["reason"] = "等待用户输入"
    elif state.decision:
        flow_control["next_action"] = state.decision.lower().replace("_", "_node")
    
    return flow_control