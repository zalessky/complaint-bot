from aiogram.utils.keyboard import InlineKeyboardBuilder

status_emoji_map = {
    "NEW": "🆕 Новая",
    "IN_WORK": "⏳ В работе",
    "CLARIFICATION_NEEDED": "❓ Нужны уточнения",
    "RESOLVED": "✅ Решена",
    "REJECTED": "❌ Отклонена",
    "CLOSED": "📁 Закрыта",
}

def admin_main_kb(cnt_new, cnt_work, cnt_finished, cnt_all):
    kb = InlineKeyboardBuilder()
    kb.button(text=f"🆕 Новые ({cnt_new})", callback_data="admin-list-new")
    kb.button(text=f"📝 В работе ({cnt_work})", callback_data="admin-list-inwork")
    kb.button(text=f"🔚 Завершённые ({cnt_finished})", callback_data="admin-list-finished")
    kb.button(text=f"📄 Все ({cnt_all})", callback_data="admin-list-all")
    kb.button(text="⬇️ Экспорт CSV", callback_data="admin-csv")
    return kb.adjust(2, 2, 1).as_markup()

def complaints_list_kb(complaints):
    kb = InlineKeyboardBuilder()
    for c in complaints:
        txt = f"[{c['id'][-5:]}] {status_emoji_map.get(c['status'], c['status'])} — {c.get('category','')[:15]}..."
        kb.button(text=txt, callback_data=f"admin-view-{c['id']}")
    return kb.adjust(1).as_markup()

def complaint_manage_kb(complaint):
    kb = InlineKeyboardBuilder()
    curr = complaint["status"]
    allowed = []
    if curr == "NEW":
        allowed = ["IN_WORK", "CLARIFICATION_NEEDED", "REJECTED", "CLOSED"]
    elif curr == "IN_WORK":
        allowed = ["RESOLVED", "CLARIFICATION_NEEDED", "REJECTED", "CLOSED"]
    elif curr == "CLARIFICATION_NEEDED":
        allowed = ["IN_WORK", "RESOLVED", "REJECTED", "CLOSED"]
    for st in allowed:
        kb.button(text=status_emoji_map[st], callback_data=f"admin-status-{complaint['id']}-{st}")
    return kb.adjust(2).as_markup()
