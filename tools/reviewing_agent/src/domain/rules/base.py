from dataclasses import dataclass
from typing import Optional

@dataclass
class Finding:
    rule_id: str
    severity: str          # ERROR | WARNING
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None
