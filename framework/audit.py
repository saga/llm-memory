import sqlite3
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime


class SimpleAuditLog:
    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS state_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                step INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                state_json TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                metadata_json TEXT,
                parent_hash TEXT,
                UNIQUE(session_id, step)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details_json TEXT NOT NULL
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON state_log(session_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON state_log(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_event_session ON audit_events(session_id)")
        self.conn.commit()

    def log_state_change(self,
                        session_id: str,
                        step: int,
                        action: str,
                        state_json: str,
                        state_hash: str,
                        metadata: Optional[Dict[str, Any]] = None,
                        parent_hash: Optional[str] = None) -> bool:
        try:
            computed_hash = self._compute_hash(state_json)
            if state_hash != computed_hash:
                raise ValueError("状态哈希不匹配")
            self.conn.execute("""
                INSERT OR REPLACE INTO state_log 
                (session_id, step, timestamp, action, state_json, state_hash, metadata_json, parent_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                step,
                datetime.now().isoformat(),
                action,
                state_json,
                state_hash,
                json.dumps(metadata) if metadata else None,
                parent_hash
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"状态日志记录失败: {e}")
            self.conn.rollback()
            return False

    def get_session_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("""
            SELECT session_id, step, timestamp, action, state_json, state_hash, metadata_json
            FROM state_log 
            WHERE session_id = ? 
            ORDER BY step DESC 
            LIMIT ?
        """, (session_id, limit))
        history = []
        for row in cursor.fetchall():
            history.append({
                "session_id": row[0],
                "step": row[1],
                "timestamp": row[2],
                "action": row[3],
                "state_json": row[4],
                "state_hash": row[5],
                "metadata": json.loads(row[6]) if row[6] else None
            })
        return history

    def verify_state_integrity(self, session_id: str) -> bool:
        cursor = self.conn.execute(
            "SELECT state_json, state_hash FROM state_log WHERE session_id = ? ORDER BY step",
            (session_id,)
        )
        for row in cursor.fetchall():
            state_json = row[0]
            stored_hash = row[1]
            computed_hash = self._compute_hash(state_json)
            if stored_hash != computed_hash:
                return False
        return True

    def _compute_hash(self, data: str) -> str:
        try:
            payload = json.loads(data)
        except Exception:
            payload = data
        if isinstance(payload, dict):
            payload.pop("last_updated", None)
            normalized = json.dumps(payload, sort_keys=True, default=str)
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
