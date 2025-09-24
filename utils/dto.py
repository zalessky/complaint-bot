from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class ComplaintDTO:
    userid: int = 0
    categorykey: str = ''
    subcategoryid: int = 0
    subcategoryname: str = ''
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    description: Optional[str] = None
    mediafileids: List[str] = field(default_factory=list)
    createdat: datetime = field(default_factory=datetime.now)
    routenumber: Optional[str] = None
    violationdatetime: Optional[datetime] = None
    fio: Optional[str] = None
    phone: Optional[str] = None
