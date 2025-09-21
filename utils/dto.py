from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class ComplaintDTO:
    """Data Transfer Object for complaint data."""
    user_id: int = 0
    complaint_type_id: int = 0
    complaint_type_name: str = ""
    route_number: str = ""
    direction: str = ""
    violation_datetime: datetime = field(default_factory=datetime.now)
    other_description: Optional[str] = None
    media_file_ids: List[str] = field(default_factory=list)
