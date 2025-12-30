"""
简化版策略函数 - 修复版本
"""
from typing import Dict, Any
from framework.state import AgentState


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


# 合规策略迁移至应用层


def memory_retention_policy(state: AgentState, memory_content: str) -> Dict[str, Any]:
    """记忆保留策略"""
    result = {
        "retain": True,
        "retention_period": "short",
        "encryption_required": False,
        "access_control": "standard"
    }
    
    if len(memory_content) > 1000:
        result["retention_period"] = "medium"
    
    return result


# 风险评估策略迁移至应用层


def content_filter_policy(content: str, context: str = "general") -> Dict[str, Any]:
    return {"approved": True, "flags": [], "modifications": [], "blocked": False, "reason": ""}
