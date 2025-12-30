"""
简化版审计日志 - 修复版本
"""
import sqlite3
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from simple_state import AgentState, FinancialAgentState
import uuid


class SimpleAuditLog:
    """简化版审计日志 - 不依赖复杂依赖"""
    
    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")  # 启用WAL模式，提高并发性能
        self._init_tables()
    
    def _init_tables(self):
        """初始化表结构"""
        # 状态日志表
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
        
        # 审计事件表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details_json TEXT NOT NULL,
                risk_level TEXT,
                compliance_flags TEXT
            )
        """)
        
        # 创建索引
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
        """记录状态变化"""
        try:
            # 验证状态哈希
            computed_hash = self._compute_hash(state_json)
            if state_hash != computed_hash:
                raise ValueError(f"状态哈希不匹配: 期望 {state_hash}, 计算 {computed_hash}")
            
            # 检查父哈希是否匹配
            if parent_hash:
                cursor = self.conn.execute(
                    "SELECT state_hash FROM state_log WHERE session_id = ? AND step = ?",
                    (session_id, step - 1)
                )
                result = cursor.fetchone()
                if result and result[0] != parent_hash:
                    raise ValueError("父状态哈希不匹配，可能存在状态篡改")
            
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
    
    def log_event(self, 
                   session_id: str,
                   event_type: str,
                   details: Dict[str, Any],
                   risk_level: Optional[str] = None,
                   compliance_flags: Optional[List[str]] = None) -> bool:
        """记录审计事件"""
        try:
            self.conn.execute("""
                INSERT INTO audit_events 
                (session_id, event_type, timestamp, details_json, risk_level, compliance_flags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                event_type,
                datetime.now().isoformat(),
                json.dumps(details),
                risk_level,
                json.dumps(compliance_flags) if compliance_flags else None
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"审计事件记录失败: {e}")
            self.conn.rollback()
            return False
    
    def get_session_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取会话历史"""
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
    
    def get_audit_trail(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取审计追踪"""
        cursor = self.conn.execute("""
            SELECT event_type, timestamp, details_json, risk_level, compliance_flags
            FROM audit_events 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (session_id, limit))
        
        trail = []
        for row in cursor.fetchall():
            trail.append({
                "event_type": row[0],
                "timestamp": row[1],
                "details": json.loads(row[2]),
                "risk_level": row[3],
                "compliance_flags": json.loads(row[4]) if row[4] else None
            })
        
        return trail
    
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
    
    def get_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取审计统计"""
        # 状态变化统计
        cursor = self.conn.execute(
            "SELECT COUNT(*), MAX(step) FROM state_log WHERE session_id = ?",
            (session_id,)
        )
        state_count, max_step = cursor.fetchone()
        
        # 事件统计
        cursor = self.conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT event_type) FROM audit_events WHERE session_id = ?",
            (session_id,)
        )
        event_count, unique_events = cursor.fetchone()
        
        # 合规统计
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM audit_events WHERE session_id = ? AND compliance_flags IS NOT NULL",
            (session_id,)
        )
        compliance_events = cursor.fetchone()[0]
        
        return {
            "state_changes": state_count or 0,
            "max_step": max_step or 0,
            "audit_events": event_count or 0,
            "unique_event_types": unique_events or 0,
            "compliance_events": compliance_events or 0,
            "integrity_verified": self.verify_state_integrity(session_id)
        }
    
    def _compute_hash(self, data: str) -> str:
        """计算哈希值（与AgentState.compute_hash对齐）"""
        try:
            payload = json.loads(data)
        except Exception:
            payload = data
        
        if isinstance(payload, dict):
            payload.pop("last_updated", None)
            normalized = json.dumps(payload, sort_keys=True, default=str)
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        
        return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


class SimpleFinancialAuditLog(SimpleAuditLog):
    """金融专用审计日志"""
    
    def __init__(self, db_path: str = "financial_audit.db"):
        super().__init__(db_path)
        self._init_financial_tables()
    
    def _init_financial_tables(self):
        """初始化金融专用表"""
        # 风险事件表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                risk_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details_json TEXT NOT NULL,
                mitigation_actions TEXT,
                regulatory_reference TEXT
            )
        """)
        
        # 合规检查表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                check_type TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details_json TEXT NOT NULL,
                regulatory_rule TEXT,
                disclosure_required BOOLEAN DEFAULT FALSE
            )
        """)
        
        self.conn.commit()
    
    def log_risk_event(self, session_id: str, risk_type: str, risk_level: str,
                      details: Dict[str, Any], mitigation_actions: Optional[List[str]] = None,
                      regulatory_reference: Optional[str] = None) -> bool:
        """记录风险事件"""
        try:
            self.conn.execute("""
                INSERT INTO risk_events 
                (session_id, risk_type, risk_level, timestamp, details_json, mitigation_actions, regulatory_reference)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                risk_type,
                risk_level,
                datetime.now().isoformat(),
                json.dumps(details),
                json.dumps(mitigation_actions) if mitigation_actions else None,
                regulatory_reference
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"风险事件记录失败: {e}")
            self.conn.rollback()
            return False
    
    def log_compliance_check(self, session_id: str, check_type: str, result: str,
                            details: Dict[str, Any], regulatory_rule: Optional[str] = None,
                            disclosure_required: bool = False) -> bool:
        """记录合规检查"""
        try:
            self.conn.execute("""
                INSERT INTO compliance_checks 
                (session_id, check_type, result, timestamp, details_json, regulatory_rule, disclosure_required)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                check_type,
                result,
                datetime.now().isoformat(),
                json.dumps(details),
                regulatory_rule,
                disclosure_required
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"合规检查记录失败: {e}")
            self.conn.rollback()
            return False
    
    def get_compliance_summary(self, session_id: str) -> Dict[str, Any]:
        """获取合规摘要"""
        # 合规检查统计
        cursor = self.conn.execute("""
            SELECT check_type, result, COUNT(*)
            FROM compliance_checks 
            WHERE session_id = ?
            GROUP BY check_type, result
        """, (session_id,))
        
        compliance_stats = {}
        for row in cursor.fetchall():
            check_type, result, count = row
            if check_type not in compliance_stats:
                compliance_stats[check_type] = {}
            compliance_stats[check_type][result] = count
        
        # 风险事件统计
        cursor = self.conn.execute("""
            SELECT risk_type, risk_level, COUNT(*)
            FROM risk_events 
            WHERE session_id = ?
            GROUP BY risk_type, risk_level
        """, (session_id,))
        
        risk_stats = {}
        for row in cursor.fetchall():
            risk_type, risk_level, count = row
            if risk_type not in risk_stats:
                risk_stats[risk_type] = {}
            risk_stats[risk_type][risk_level] = count
        
        return {
            "compliance_checks": compliance_stats,
            "risk_events": risk_stats,
            "integrity_status": self.verify_state_integrity(session_id)
        }
