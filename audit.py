import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from state import AgentState, FinancialAgentState


class AuditLog:
    """审计日志，append-only存储"""
    
    def __init__(self, path: str = "audit.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self._init_tables()
    
    def _init_tables(self):
        """初始化审计表"""
        # 状态变更日志表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS state_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            step INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            state_json TEXT NOT NULL,
            state_hash TEXT NOT NULL,
            transition_type TEXT NOT NULL,
            metadata TEXT
        )
        """)
        
        # 消息日志表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS message_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT
        )
        """)
        
        # 合规检查表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS compliance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            check_type TEXT NOT NULL,
            result TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL
        )
        """)
        
        # 创建索引
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_state_session ON state_log(session_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_state_step ON state_log(session_id, step)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_message_session ON message_log(session_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_compliance_session ON compliance_log(session_id)")
        
        self.conn.commit()
    
    def append_state(self, state: AgentState, transition_type: str = "node_transition") -> None:
        """追加状态变更"""
        state_json = state.model_dump_json()
        state_hash = self._compute_hash(state_json)
        
        self.conn.execute(
            """INSERT INTO state_log 
               (session_id, step, timestamp, state_json, state_hash, transition_type, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                state.session_id,
                state.step,
                datetime.utcnow().isoformat(),
                state_json,
                state_hash,
                transition_type,
                json.dumps(state.get_audit_info())
            )
        )
        self.conn.commit()
    
    def append_message(self, session_id: str, message) -> None:
        """追加消息"""
        self.conn.execute(
            """INSERT INTO message_log 
               (session_id, message_id, role, content, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                f"{session_id}_{message.timestamp.isoformat()}",
                message.role,
                message.content,
                message.timestamp.isoformat(),
                json.dumps(message.metadata)
            )
        )
        self.conn.commit()
    
    def append_compliance_check(self, session_id: str, check_type: str, 
                               result: str, details: Optional[Dict[str, Any]] = None) -> None:
        """追加合规检查"""
        self.conn.execute(
            """INSERT INTO compliance_log 
               (session_id, check_type, result, details, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_id,
                check_type,
                result,
                json.dumps(details) if details else None,
                datetime.utcnow().isoformat()
            )
        )
        self.conn.commit()
    
    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_session_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取会话历史"""
        cursor = self.conn.execute(
            "SELECT * FROM state_log WHERE session_id = ? ORDER BY step DESC LIMIT ?",
            (session_id, limit)
        )
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "step": row[2],
                "timestamp": row[3],
                "state_json": json.loads(row[4]),
                "transition_type": row[6],
                "metadata": json.loads(row[7]) if row[7] else {}
            })
        
        return history
    
    def get_compliance_report(self, session_id: str) -> Dict[str, Any]:
        """获取合规报告"""
        cursor = self.conn.execute(
            "SELECT check_type, result, details, timestamp FROM compliance_log WHERE session_id = ?",
            (session_id,)
        )
        
        checks = []
        for row in cursor.fetchall():
            checks.append({
                "check_type": row[0],
                "result": row[1],
                "details": json.loads(row[2]) if row[2] else {},
                "timestamp": row[3]
            })
        
        return {
            "session_id": session_id,
            "total_checks": len(checks),
            "passed_checks": len([c for c in checks if c["result"] == "PASS"]),
            "failed_checks": len([c for c in checks if c["result"] == "FAIL"]),
            "checks": checks
        }
    
    def verify_state_integrity(self, session_id: str) -> bool:
        """验证状态完整性"""
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
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


class FinancialAuditLog(AuditLog):
    """金融专用审计日志"""
    
    def __init__(self, path: str = "financial_audit.db"):
        super().__init__(path)
        self._init_financial_tables()
    
    def _init_financial_tables(self):
        """初始化金融专用审计表"""
        # 风险评估审计表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS risk_assessment_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            risk_factors TEXT,
            recommendation_type TEXT,
            timestamp TEXT NOT NULL
        )
        """)
        
        # 投资建议审计表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_recommendation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            product_type TEXT NOT NULL,
            recommendation TEXT,
            risk_disclaimer TEXT,
            compliance_check TEXT,
            timestamp TEXT NOT NULL
        )
        """)
        
        self.conn.commit()
    
    def log_risk_assessment(self, session_id: str, risk_level: str, 
                           risk_factors: Dict[str, Any], recommendation_type: str) -> None:
        """记录风险评估"""
        self.conn.execute(
            """INSERT INTO risk_assessment_log 
               (session_id, risk_level, risk_factors, recommendation_type, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_id,
                risk_level,
                json.dumps(risk_factors),
                recommendation_type,
                datetime.utcnow().isoformat()
            )
        )
        self.conn.commit()
    
    def log_investment_recommendation(self, session_id: str, product_type: str,
                                    recommendation: str, risk_disclaimer: str,
                                    compliance_check: Dict[str, Any]) -> None:
        """记录投资建议"""
        self.conn.execute(
            """INSERT INTO investment_recommendation_log 
               (session_id, product_type, recommendation, risk_disclaimer, compliance_check, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                product_type,
                recommendation,
                risk_disclaimer,
                json.dumps(compliance_check),
                datetime.utcnow().isoformat()
            )
        )
        self.conn.commit()
    
    def get_risk_assessment_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取风险评估历史"""
        cursor = self.conn.execute(
            "SELECT * FROM risk_assessment_log WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "risk_level": row[2],
                "risk_factors": json.loads(row[3]) if row[3] else {},
                "recommendation_type": row[4],
                "timestamp": row[5]
            })
        
        return history