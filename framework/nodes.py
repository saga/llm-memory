from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from framework.state import AgentState, MessageRole, MessageType, MemoryEntry


def planner_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    latest_message = new_state.get_latest_message()
    if not latest_message or latest_message.role != MessageRole.USER:
        return new_state
    new_state.decision = "general"
    new_state.add_message(
        role=MessageRole.SYSTEM,
        content=f"路由决策: {new_state.decision}",
        message_type=MessageType.SYSTEM_MESSAGE
    )
    new_state.increment_step()
    return new_state


def memory_recall_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    latest_message = new_state.get_latest_message()
    if not latest_message:
        return new_state
    recalled_count = 0
    if new_state.memories:
        recalled_count = min(3, len(new_state.memories))
    if recalled_count:
        new_state.add_message(
            role=MessageRole.SYSTEM,
            content=f"召回 {recalled_count} 条记忆",
            message_type=MessageType.MEMORY_RECALL,
            metadata={"recalled_count": recalled_count}
        )
    new_state.increment_step()
    return new_state


def decision_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    new_state.set_status("processing")
    new_state.increment_step()
    return new_state


def response_generator_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    if not user_messages:
        return new_state
    latest_user_message = user_messages[-1]
    response_content = generate_general_response(new_state, latest_user_message.content)
    new_state.add_message(
        role=MessageRole.ASSISTANT,
        content=response_content,
        message_type=MessageType.ASSISTANT_RESPONSE
    )
    new_state.increment_step()
    return new_state


def memory_storage_node(state: AgentState) -> AgentState:
    new_state = state.model_copy(deep=True)
    user_messages = new_state.get_messages_by_role(MessageRole.USER)
    assistant_messages = new_state.get_messages_by_role(MessageRole.ASSISTANT)
    if user_messages and assistant_messages:
        memory_content = f"用户: {user_messages[-1].content}\n助手: {assistant_messages[-1].content}"
        memory_entry = create_memory_entry(
            content=memory_content,
            context=new_state.context,
            message_type=MessageType.USER_INPUT,
            metadata={"decision": new_state.decision}
        )
        new_state.add_memory(memory_entry)
    new_state.increment_step()
    return new_state


def create_memory_entry(content: str, context: str, message_type: MessageType,
                       metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
    memory_id = hashlib.md5(f"{content}_{context}".encode()).hexdigest()[:16]
    memory_hash = hashlib.sha256(f"{content}_{context}".encode()).hexdigest()
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


def generate_general_response(state: AgentState, user_input: str) -> str:
    return "我理解您的问题。作为AI助手，我会尽力为您提供准确和有用的信息。"
