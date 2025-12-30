from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import Field
from framework.state import AgentState


class FinancialAgentState(AgentState):
    risk_profile: Dict[str, Any] = Field(default_factory=dict)
    portfolio_info: Dict[str, Any] = Field(default_factory=dict)
    regulatory_context: str = Field(default="")
    compliance_level: Literal["retail", "professional", "institutional"] = "retail"
    investment_limit: Optional[float] = Field(default=None, ge=0)
    approved_products: List[str] = Field(default_factory=list)
    restricted_products: List[str] = Field(default_factory=list)
    risk_disclosures: List[str] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_flags: List[str] = Field(default_factory=list)

    def set_risk_profile(self, risk_level: str, factors: Dict[str, Any]) -> None:
        self.risk_profile = {
            "level": risk_level,
            "factors": factors,
            "assessed_at": datetime.utcnow().isoformat()
        }
        self.add_fact("risk_level", risk_level)

    def add_compliance_flag(self, flag: str) -> None:
        if flag not in self.compliance_flags:
            self.compliance_flags.append(flag)
