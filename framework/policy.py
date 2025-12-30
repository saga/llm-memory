from framework.state import AgentState


def routing_policy(state: AgentState) -> str:
    if state.status == "error":
        return "error"
    elif state.status == "complete":
        return "end"
    elif len(state.messages) > 10:
        return "end"
    else:
        return "continue"


def memory_retention_policy(state: AgentState, memory_content: str) -> dict:
    result = {
        "retain": True,
        "retention_period": "short",
        "encryption_required": False,
        "access_control": "standard"
    }
    if len(memory_content) > 1000:
        result["retention_period"] = "medium"
    return result
