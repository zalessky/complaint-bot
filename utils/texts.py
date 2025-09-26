from keyboards.admin_panel import status_emoji_map

def format_complaint_brief(c):
    return f"[ID {c['id'][-5:]}] {status_emoji_map.get(c['status'], c['status'])}: {c.get('category','')[:20]}…"

def format_complaint_full(c):
    lines = [
        f"ID: {c['id']}",
        f"Дата: {c.get('created','')}",
        f"Статус: {status_emoji_map.get(c['status'], c['status'])}",
        f"Категория: {c.get('category','')}",
        f"Автор: {c.get('user_id','')}",
        f"Описание: {c.get('description','')[:500]}"
    ]
    if c.get("photos"):
        lines.append(f"Фото: {len(c['photos'])} вложений (file_id)")
    return "\n".join(lines)
