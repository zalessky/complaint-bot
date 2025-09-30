def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса"""
    return {
        "new": "🟡",
        "in_progress": "🔵",
        "resolved": "🟢",
        "rejected": "🔴"
    }.get(status, "⚪")

def get_status_text(status: str) -> str:
    """Возвращает текст статуса на русском"""
    return {
        "new": "Новое",
        "in_progress": "В работе",
        "resolved": "Решено",
        "rejected": "Отклонено"
    }.get(status, status)
