from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class ComplaintDTO:
    user_id: int
    username: Optional[str]
    categorykey: str
    subcategoryid: int
    subcategoryname: str
    address: Optional[str]
    routenumber: Optional[str]
    description: str
    fio: str
    phone: str
    mediafileids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
