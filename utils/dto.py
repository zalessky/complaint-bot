from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class ComplaintDTO:
    user_id: int = 0
    category_key: str = ""
    subcategory_id: int = 0
    subcategory_name: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    description: Optional[str] = None
    media_file_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    route_number: Optional[str] = None
    violation_datetime: Optional[datetime] = None
