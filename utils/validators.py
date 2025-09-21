import re
from datetime import datetime

def validate_datetime(dt_str: str) -> bool:
    """Validates a datetime string in 'YYYY-MM-DD HH:MM' format."""
    try:
        datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False

def is_valid_route_or_plate(text: str) -> bool:
    """Checks if the text is a valid route number or a license plate."""
    if not text or len(text) > 20:
        return False
    # Simple check, can be improved with regex for license plates
    return True

def is_valid_direction_text(text: str) -> bool:
    """Checks if the direction text is valid."""
    if not text or len(text) > 100:
        return False
    return True
