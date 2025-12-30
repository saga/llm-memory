"""
简化版状态机实现 - 修复版本，无LangGraph依赖
"""
from typing import Dict, Any, Optional, List, Callable
from framework.state import AgentState
from framework.nodes import (
    planner_node, memory_recall_node, decision_node,
    response_generator_node, memory_storage_node
)
from framework.policy import routing_policy


class SimpleStateMachine:
    """简化版状态机 - 参考LangGraph思想但无依赖"""
    
    def __init__(self, state_class: type = AgentState):
        self.state_class = state_class
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Callable] = {}
        self.entry_point: str = ""
        self.end_point: str = "__end__"
        
    def add_node(self, name: str, func: Callable):
        """添加节点（纯函数）"""
        self.nodes[name] = func
        
    def add_edge(self, from_node: str, to_node: str):
        """添加固定边"""
        self.edges[from_node] = to_node
        
    def add_conditional_edges(self, from_node: str, condition_func: Callable, 
                               conditions: Dict[str, str]):
        """添加条件边"""
        self.conditional_edges[from_node] = (condition_func, conditions)
        
    def set_entry_point(self, node: str):
        """设置入口点"""
        self.entry_point = node
        
    def compile(self):
        """编译状态机"""
        return CompiledStateMachine(self)


class CompiledStateMachine:
    """编译后的状态机"""
    
    def __init__(self, builder: SimpleStateMachine):
        self.builder = builder
        
    def invoke(self, initial_state: AgentState, max_steps: int = 10) -> AgentState:
        """执行状态机"""
        current_state = initial_state
        current_node = self.builder.entry_point
        steps = 0
        
        while current_node != self.builder.end_point and steps < max_steps:
            # 执行当前节点
            if current_node in self.builder.nodes:
                node_func = self.builder.nodes[current_node]
                current_state = node_func(current_state)
            
            # 确定下一个节点
            if current_node in self.builder.conditional_edges:
                # 条件边
                condition_func, conditions = self.builder.conditional_edges[current_node]
                result = condition_func(current_state)
                next_node = conditions.get(result, self.builder.end_point)
            elif current_node in self.builder.edges:
                # 固定边
                next_node = self.builder.edges[current_node]
            else:
                # 默认结束
                next_node = self.builder.end_point
                
            current_node = next_node
            steps += 1
            
        return current_state


def create_simple_base_graph(state_class: type = AgentState) -> CompiledStateMachine:
    """创建简化版基础图"""
    
    # 创建状态机构建器
    builder = SimpleStateMachine(state_class)
    
    # 添加节点
    builder.add_node("planner", planner_node)
    builder.add_node("memory_recall", memory_recall_node)
    builder.add_node("decision", decision_node)
    builder.add_node("response_generator", response_generator_node)
    builder.add_node("memory_storage", memory_storage_node)
    
    # 设置入口点
    builder.set_entry_point("planner")
    
    # 添加边
    builder.add_edge("planner", "memory_recall")
    builder.add_edge("memory_recall", "decision")
    builder.add_edge("decision", "response_generator")
    builder.add_edge("response_generator", "memory_storage")
    
    # 添加条件边
    builder.add_conditional_edges(
        "memory_storage",
        routing_policy,
        {
            "continue": "planner",  # 继续下一轮
            "end": "__end__",       # 结束
            "error": "compliance_check"  # 错误处理
        }
    )
    
    return builder.compile()


def create_simple_financial_graph() -> CompiledStateMachine:
    """创建简化版金融专用图（应用层实现，框架保持通用）"""
    return create_simple_base_graph(AgentState)


def run_simple_agent_workflow(
    initial_state: AgentState,
    graph_type: str = "base",
    max_steps: int = 10
) -> AgentState:
    """运行简化版智能体工作流"""
    
    # 选择图类型
    if graph_type == "base":
        graph = create_simple_base_graph()
    elif graph_type == "financial":
        graph = create_simple_financial_graph()
    else:
        raise ValueError(f"未知的图类型: {graph_type}")
    
    # 运行工作流
    result = graph.invoke(initial_state, max_steps)
    
    return result
