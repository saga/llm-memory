from typing import Dict, Any, Callable
from framework.state import AgentState
from framework.nodes import (
    planner_node, memory_recall_node, decision_node,
    response_generator_node, memory_storage_node
)
from framework.policy import routing_policy


class SimpleStateMachine:
    def __init__(self, state_class: type = AgentState):
        self.state_class = state_class
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Callable] = {}
        self.entry_point: str = ""
        self.end_point: str = "__end__"

    def add_node(self, name: str, func: Callable):
        self.nodes[name] = func

    def add_edge(self, from_node: str, to_node: str):
        self.edges[from_node] = to_node

    def add_conditional_edges(self, from_node: str, condition_func: Callable,
                              conditions: Dict[str, str]):
        self.conditional_edges[from_node] = (condition_func, conditions)

    def set_entry_point(self, node: str):
        self.entry_point = node

    def compile(self):
        return CompiledStateMachine(self)


class CompiledStateMachine:
    def __init__(self, builder: SimpleStateMachine):
        self.builder = builder

    def invoke(self, initial_state: AgentState, max_steps: int = 10) -> AgentState:
        current_state = initial_state
        current_node = self.builder.entry_point
        steps = 0

        while current_node != self.builder.end_point and steps < max_steps:
            if current_node in self.builder.nodes:
                node_func = self.builder.nodes[current_node]
                current_state = node_func(current_state)

            if current_node in self.builder.conditional_edges:
                condition_func, conditions = self.builder.conditional_edges[current_node]
                result = condition_func(current_state)
                next_node = conditions.get(result, self.builder.end_point)
            elif current_node in self.builder.edges:
                next_node = self.builder.edges[current_node]
            else:
                next_node = self.builder.end_point

            current_node = next_node
            steps += 1

        return current_state


def create_simple_base_graph(state_class: type = AgentState) -> CompiledStateMachine:
    builder = SimpleStateMachine(state_class)
    builder.add_node("planner", planner_node)
    builder.add_node("memory_recall", memory_recall_node)
    builder.add_node("decision", decision_node)
    builder.add_node("response_generator", response_generator_node)
    builder.add_node("memory_storage", memory_storage_node)
    builder.set_entry_point("planner")
    builder.add_edge("planner", "memory_recall")
    builder.add_edge("memory_recall", "decision")
    builder.add_edge("decision", "response_generator")
    builder.add_edge("response_generator", "memory_storage")
    builder.add_conditional_edges(
        "memory_storage",
        routing_policy,
        {
            "continue": "planner",
            "end": "__end__",
            "error": "planner"
        }
    )
    return builder.compile()


def create_simple_financial_graph() -> CompiledStateMachine:
    return create_simple_base_graph(AgentState)


def run_simple_agent_workflow(
    initial_state: AgentState,
    graph_type: str = "base",
    max_steps: int = 10
) -> AgentState:
    if graph_type == "base":
        graph = create_simple_base_graph()
    elif graph_type == "financial":
        graph = create_simple_financial_graph()
    else:
        raise ValueError(f"未知的图类型: {graph_type}")
    return graph.invoke(initial_state, max_steps)
