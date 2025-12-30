from langgraph.graph import StateGraph, END
from state import AgentState, FinancialAgentState
from nodes import (
    planner_node, memory_recall_node, decision_node, 
    response_generator_node, memory_storage_node, compliance_check_node
)
from policy import next_step_policy, routing_policy
from typing import Type


def create_base_graph(state_class: Type[AgentState] = AgentState) -> StateGraph:
    """创建基础图"""
    
    # 创建图构建器
    builder = StateGraph(state_class)
    
    # 添加节点
    builder.add_node("planner", planner_node)
    builder.add_node("memory_recall", memory_recall_node)
    builder.add_node("decision", decision_node)
    builder.add_node("response_generator", response_generator_node)
    builder.add_node("memory_storage", memory_storage_node)
    builder.add_node("compliance_check", compliance_check_node)
    
    # 设置入口点
    builder.set_entry_point("planner")
    
    # 添加边
    builder.add_edge("planner", "memory_recall")
    builder.add_edge("memory_recall", "decision")
    builder.add_edge("decision", "response_generator")
    builder.add_edge("response_generator", "compliance_check")
    builder.add_edge("compliance_check", "memory_storage")
    
    # 添加条件边
    builder.add_conditional_edges(
        "memory_storage",
        routing_policy,
        {
            "continue": "planner",  # 继续下一轮
            "end": END,             # 结束
            "error": "compliance_check"  # 错误处理
        }
    )
    
    return builder


def create_financial_graph() -> StateGraph:
    """创建金融专用图"""
    
    # 创建基础图
    builder = create_base_graph(FinancialAgentState)
    
    # 添加金融专用节点（可以扩展）
    # builder.add_node("risk_validator", risk_validator_node)
    # builder.add_node("compliance_officer", compliance_officer_node)
    
    # 添加金融专用边
    # builder.add_edge("decision", "risk_validator", condition=is_financial_decision)
    # builder.add_edge("risk_validator", "compliance_officer")
    # builder.add_edge("compliance_officer", "response_generator")
    
    return builder


def create_chat_graph() -> StateGraph:
    """创建聊天专用图（简化版）"""
    
    builder = StateGraph(AgentState)
    
    # 简化节点
    builder.add_node("process_input", planner_node)
    builder.add_node("recall_memory", memory_recall_node)
    builder.add_node("generate_response", response_generator_node)
    builder.add_node("store_memory", memory_storage_node)
    
    # 设置入口点
    builder.set_entry_point("process_input")
    
    # 添加边
    builder.add_edge("process_input", "recall_memory")
    builder.add_edge("recall_memory", "generate_response")
    builder.add_edge("generate_response", "store_memory")
    builder.add_edge("store_memory", END)
    
    return builder


def compile_graph(builder: StateGraph, checkpointer=None) -> StateGraph:
    """编译图"""
    return builder.compile(checkpointer=checkpointer)


# 预编译的图实例
base_graph = compile_graph(create_base_graph())
financial_graph = compile_graph(create_financial_graph())
chat_graph = compile_graph(create_chat_graph())


def get_graph(graph_type: str = "base") -> StateGraph:
    """获取指定类型的图"""
    graphs = {
        "base": base_graph,
        "financial": financial_graph,
        "chat": chat_graph
    }
    
    return graphs.get(graph_type, base_graph)


def run_agent_workflow(
    initial_state: AgentState,
    graph_type: str = "base",
    max_steps: int = 10
) -> AgentState:
    """运行代理工作流"""
    
    graph = get_graph(graph_type)
    current_state = initial_state
    
    for step in range(max_steps):
        # 运行一步
        result = graph.invoke(current_state)
        
        # 确保返回的是AgentState对象
        if isinstance(result, dict):
            # 如果是字典，转换为AgentState
            current_state = AgentState(**result)
        elif isinstance(result, AgentState):
            current_state = result
        else:
            # 如果返回类型不匹配，使用当前状态
            pass
        
        # 检查是否结束
        if current_state.status in ["complete", "error"]:
            break
        
        # 检查步骤限制
        if current_state.step >= max_steps:
            current_state.set_status("complete")
            break
    
    return current_state