from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.constants import CATEGORIES, ComplaintStatus, STATUS_LABEL_RU

class AdminPanelCallback(CallbackData, prefix='admin_panel'):
    action: str

class ComplaintActionCallback(CallbackData, prefix='complaint_action'):
    action: str
    complaint_id: int

class ComplaintStatusCallback(CallbackData, prefix='complaint_status'):
    action: str = 'set_status'
    status: str
    complaint_id: int

class FeedbackCallback(CallbackData, prefix='feedback'):
    type: str

def get_feedback_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💬 Предложение по улучшению", callback_data=FeedbackCallback(type='suggestion').pack())],
        [InlineKeyboardButton(text="🗣️ Сообщить об ошибке", callback_data=FeedbackCallback(type='bug_report').pack())],
        [InlineKeyboardButton(text="🙏 Направить благодарность", callback_data=FeedbackCallback(type='gratitude').pack())],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_complaint")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_categories_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=d['name'], callback_data=f'category_{k}')]
        for k, d in CATEGORIES.items() if k not in ['gratitude', 'feedback']]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_complaint")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_subcategories_keyboard(cat_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=sd['name'], callback_data=f'subcategory_{sid}')]
        for sid, sd in CATEGORIES[cat_key]['subcategories'].items()
    ]
    buttons.append([InlineKeyboardButton(text='⬅️ Назад к категориям', callback_data='back_to_categories')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_complaint_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Все верно, отправить', callback_data='submit_complaint')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_complaint')],
        ]
    )

def get_admin_panel_keyboard(stats: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'🆕 Новые ({stats.get("new", 0)})',
                    callback_data=AdminPanelCallback(action='show_new').pack(),
                ),
                InlineKeyboardButton(
                    text=f'⏳ В работе ({stats.get("in_work", 0)})',
                    callback_data=AdminPanelCallback(action='show_in_work').pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f'✅ Завершенные ({stats.get("completed", 0)})',
                    callback_data=AdminPanelCallback(action='show_completed').pack(),
                ),
                InlineKeyboardButton(
                    text=f'📂 Все ({stats.get("all", 0)})',
                    callback_data=AdminPanelCallback(action='show_all').pack(),
                ),
            ]
        ]
    )

def get_complaint_list_keyboard(complaints: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in complaints:
        status_icon = STATUS_LABEL_RU.get(c['status'], '❓').split(' ')[0]
        category_name = CATEGORIES.get(c['category_key'], {}).get('name', c['category_key'])
        author = f"@{c['username']}" if c.get('username') else f"ID: {c['user_id']}"
        text = f"{status_icon} #{c['id']} | {category_name[:15]} | {author}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=ComplaintActionCallback(action='view', complaint_id=c['id']).pack()
        )])
    buttons.append([InlineKeyboardButton(text='⬅️ Назад в панель', callback_data=AdminPanelCallback(action='back_to_panel').pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_complaint_actions_keyboard(cid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✍️ Изменить статус',
                    callback_data=ComplaintActionCallback(action='change_status', complaint_id=cid).pack(),
                ),
            ],
            [InlineKeyboardButton(text='⬅️ Назад в панель', callback_data=AdminPanelCallback(action='back_to_panel').pack())]
        ]
    )

def get_status_selection_keyboard(cid: int) -> InlineKeyboardMarkup:
    buttons = []
    for s in ComplaintStatus:
        buttons.append([
            InlineKeyboardButton(
                text=STATUS_LABEL_RU.get(s.value, s.value),
                callback_data=ComplaintStatusCallback(status=s.value, complaint_id=cid).pack(),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
