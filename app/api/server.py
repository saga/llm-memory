from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.service.chat import SimpleLLMChatWithMemory, SimpleFinancialLLMChat


class CreateSessionRequest(BaseModel):
    mode: Optional[str] = "base"
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class MessageRequest(BaseModel):
    content: str
    mode: Optional[str] = "base"


class RiskProfileRequest(BaseModel):
    risk_level: str
    factors: Optional[Dict[str, Any]] = None


app = FastAPI()

chats: Dict[str, SimpleLLMChatWithMemory] = {
    "base": SimpleLLMChatWithMemory(audit_log_path="api_audit_base.db"),
    "financial": SimpleFinancialLLMChat(audit_log_path="api_audit_financial.db"),
}


@app.post("/sessions")
def create_session(req: CreateSessionRequest):
    mode = req.mode or "base"
    chat = chats.get(mode)
    if not chat:
        raise HTTPException(status_code=400, detail="unsupported mode")
    session_id = req.session_id or chat.create_session()
    if req.user_id:
        state = chat.get_session(session_id)
        if state:
            state.user_id = req.user_id
    return {"session_id": session_id, "mode": mode}


@app.post("/sessions/{session_id}/messages")
def post_message(session_id: str, req: MessageRequest):
    mode = req.mode or "base"
    chat = chats.get(mode)
    if not chat:
        raise HTTPException(status_code=400, detail="unsupported mode")
    if not chat.get_session(session_id):
        raise HTTPException(status_code=404, detail="session not found")
    try:
        reply = chat.get_chat_completion(session_id, req.content)
        return {"session_id": session_id, "mode": mode, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
def get_session(session_id: str, mode: str = "base"):
    chat = chats.get(mode)
    if not chat:
        raise HTTPException(status_code=400, detail="unsupported mode")
    state = chat.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="session not found")
    history = chat.get_session_history(session_id)
    audit = chat.audit_log.get_session_history(session_id)
    integrity = chat.audit_log.verify_state_integrity(session_id)
    return {
        "session_id": session_id,
        "mode": mode,
        "history": history,
        "audit_records": len(audit),
        "integrity": integrity,
    }


@app.post("/sessions/{session_id}/risk_profile")
def set_risk_profile(session_id: str, req: RiskProfileRequest):
    chat = chats.get("financial")
    if not chat:
        raise HTTPException(status_code=500, detail="financial mode unavailable")
    if not chat.get_session(session_id):
        raise HTTPException(status_code=404, detail="session not found")
    ok = chat.set_risk_profile(session_id, req.risk_level, req.factors or {})
    if not ok:
        raise HTTPException(status_code=400, detail="set risk profile failed")
    return {"session_id": session_id, "ok": True}


@app.get("/audit/{session_id}")
def get_audit(session_id: str, mode: str = "base"):
    chat = chats.get(mode)
    if not chat:
        raise HTTPException(status_code=400, detail="unsupported mode")
    history = chat.audit_log.get_session_history(session_id)
    integrity = chat.audit_log.verify_state_integrity(session_id)
    return {"session_id": session_id, "records": history, "integrity": integrity}
