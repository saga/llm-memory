"""
简化版策略函数 - 修复版本
"""
from typing import Dict, Any, Optional, List, Literal
from simple_state import AgentState, FinancialAgentState


def next_step_policy(state: AgentState) -> str:
    """下一步决策策略"""
    # 基于当前状态决定下一步
    if state.status == "error":
        return "error"
    elif state.status == "complete":
        return "end"
    elif len(state.messages) > 10:  # 限制对话长度
        return "end"
    else:
        return "continue"


def routing_policy(state: AgentState) -> str:
    """路由策略 - 决定下一个节点"""
    # 基于状态决定路由
    if state.status == "error":
        return "error"
    elif state.status == "complete":
        return "end"
    elif len(state.messages) > 10:
        return "end"
    else:
        return "continue"


def compliance_policy(state: AgentState) -> Dict[str, Any]:
    """合规策略"""
    result = {
        "approved": True,
        "flags": [],
        "modifications": [],
        "disclosures": []
    }
    
    # 检查是否为金融状态
    if isinstance(state, FinancialAgentState):
        # 检查投资建议
        if state.decision == "investment_advice":
            result["flags"].append("investment_advice")
            
            # 检查风险等级
            if state.risk_level == "high" and not state.risk_profile.get("factors"):
                result["approved"] = False
                result["flags"].append("high_risk_without_factors")
            
            # 检查是否需要风险披露
            if not state.risk_disclosures:
                result["disclosures"].append("investment_risk")
    
    # 检查消息内容
    assistant_messages = [msg for msg in state.messages if msg.role == "assistant"]
    if assistant_messages:
        latest_response = assistant_messages[-1].content
        
        # 检查保证性语言
        if any(word in latest_response for word in ["保证", "确保", "一定", "100%"]):
            result["flags"].append("guarantee_language")
            result["modifications"].append("remove_guarantees")
        
        # 检查投资建议
        if any(word in latest_response for word in ["投资", "理财", "股票", "基金"]):
            if "investment_risk" not in result["disclosures"]:
                result["disclosures"].append("investment_risk")
    
    return result


def memory_retention_policy(state: AgentState, memory_content: str) -> Dict[str, Any]:
    """记忆保留策略"""
    result = {
        "retain": True,
        "retention_period": "long",  # short, medium, long
        "encryption_required": False,
        "access_control": "standard"
    }
    
    # 基于内容类型决定保留策略
    if any(word in memory_content for word in ["投资", "理财", "股票", "基金", "风险"]):
        result["retention_period"] = "long"
        result["encryption_required"] = True
        result["access_control"] = "financial"
    elif any(word in memory_content for word in ["个人", "隐私", "敏感"]):
        result["retention_period"] = "medium"
        result["encryption_required"] = True
        result["access_control"] = "restricted"
    else:
        result["retention_period"] = "short"
        result["encryption_required"] = False
        result["access_control"] = "standard"
    
    # 检查是否为金融状态
    if isinstance(state, FinancialAgentState):
        if state.risk_level == "high":
            result["retention_period"] = "long"
            result["encryption_required"] = True
        
        # 检查合规级别
        if state.compliance_level in ["professional", "institutional"]:
            result["access_control"] = "financial"
    
    return result


def risk_assessment_policy(state: FinancialAgentState, user_input: str) -> Dict[str, Any]:
    """风险评估策略"""
    risk_score = 0
    risk_factors = []
    
    # 基于用户输入评估风险
    if any(word in user_input for word in ["比特币", "加密货币", "杠杆", "期货", "期权"]):
        risk_score += 3
        risk_factors.append("high_risk_investment")
    
    if any(word in user_input for word in ["保证", "确保", "稳赚", "无风险"]):
        risk_score += 2
        risk_factors.append("unrealistic_expectations")
    
    if any(word in user_input for word in ["借钱", "贷款", "融资"]):
        risk_score += 2
        risk_factors.append("leverage_usage")
    
    # 基于用户档案评估
    if state.risk_profile:
        user_risk_level = state.risk_profile.get("level", "medium")
        if user_risk_level == "low" and risk_score >= 2:
            risk_factors.append("risk_mismatch")
        elif user_risk_level == "high":
            risk_score -= 1  # 高风险用户容忍度更高
    
    # 确定风险等级
    if risk_score >= 4:
        risk_level = "high"
    elif risk_score >= 2:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "requires_review": risk_level == "high",
        "recommended_action": "proceed_with_caution" if risk_level in ["medium", "high"] else "proceed"
    }


def content_filter_policy(content: str, context: str = "general") -> Dict[str, Any]:
    """内容过滤策略"""
    result = {
        "approved": True,
        "flags": [],
        "modifications": [],
        "blocked": False,
        "reason": ""
    }
    
    # 敏感词检查
    sensitive_words = ["暴力", "色情", "赌博", "毒品", "诈骗"]
    for word in sensitive_words:
        if word in content:
            result["approved"] = False
            result["flags"].append("sensitive_content")
            result["blocked"] = True
            result["reason"] = f"包含敏感词: {word}"
            return result
    
    # 金融专用检查
    if context == "financial":
        # 检查投资建议
        if any(word in content for word in ["推荐", "建议", "购买", "卖出"]):
            result["flags"].append("investment_recommendation")
            result["modifications"].append("add_disclaimer")
        
        # 检查保证性语言
        if any(word in content for word in ["保证", "确保", "稳赚", "无风险"]):
            result["approved"] = False
            result["flags"].append("guarantee_language")
            result["modifications"].append("remove_guarantees")
            result["reason"] = "包含保证性语言"
    
    return result
