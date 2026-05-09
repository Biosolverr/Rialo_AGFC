from pydantic import BaseModel
from typing import Optional


class ConsensusResult(BaseModel):
    decision: str
    confidence: float
    margin: float
    quorum_met: bool
    appeal_required: bool
    details: Optional[dict] = None
