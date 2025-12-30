from framework.state import AgentState, MessageRole, MessageType


def compliance_check_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    if not assistant_messages:
        return new_state
    latest_response = assistant_messages[-1]
    if any(word in latest_response.content for word in ["保证", "确保", "一定", "100%"]):
        latest_response.content = latest_response.content.replace("保证", "").replace("确保", "")
    new_state.increment_step()
    return new_state

