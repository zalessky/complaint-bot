import re
from datetime import datetime
from typing import Optional

def parse_user_datetime(text: str) -> Optional[datetime]:
    text = text.replace('.', '-').replace(':', ' ')
    patterns = [
        r'(\d{2})-(\d{2})\s(\d{2}) (\d{2})', # DD-MM HH MM
    ]
    for pattern in patterns:
        match = re.match(pattern, text.strip())
        if match:
            day, month, hour, minute = map(int, match.groups())
            try: return datetime(datetime.now().year, month, day, hour, minute)
            except ValueError: continue
    return None
