from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.constants import CATEGORIES, ComplaintStatus

class AdminPanelCallback(CallbackData, prefix='admin_panel'):
    action: str

class ComplaintActionCallback(CallbackData, prefix='complaint_action'):
    action: str
    complaint_id: int

class ComplaintStatusCallback(CallbackData, prefix='complaint_status'):
    action: str = 'set_status'
    status: str
    complaint_id: int

def get_categories_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=d['name'], callback_data=f'category_{k}')]
        for k, d in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_subcategories_keyboard(cat_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=sd['name'], callback_data=f'subcategory_{sid}')]
        for sid, sd in CATEGORIES[cat_key]['subcategories'].items()
    ]
    buttons.append([
        InlineKeyboardButton(text='⬅️ Назад к категориям', callback_data='back_to_categories')
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📍 Отправить геолокацию', callback_data='send_geolocation')],
            [InlineKeyboardButton(text='⌨️ Ввести адрес вручную', callback_data='enter_address_manually')],
            [InlineKeyboardButton(text='⬅️ Назад к подкатегориям', callback_data='back_to_subcategories')],
        ]
    )

def confirm_complaint_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Все верно, отправить', callback_data='submit_complaint')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_complaint')],
        ]
    )

def get_datetime_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Сейчас', callback_data='datetime_now')],
            [InlineKeyboardButton(text='⌨️ Ввести вручную', callback_data='datetime_manual')],
        ]
    )

def get_admin_panel_keyboard(stats: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'📬 Новые ({stats.get("new", 0)})',
                    callback_data=AdminPanelCallback(action='show_new').pack(),
                ),
                InlineKeyboardButton(
                    text=f'⏳ В работе ({stats.get("in_work", 0)})',
                    callback_data=AdminPanelCallback(action='show_in_work').pack(),
                ),
            ]
        ]
    )

def get_complaint_actions_keyboard(cid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✅ Принять в работу',
                    callback_data=ComplaintActionCallback(action='accept', complaint_id=cid).pack(),
                ),
                InlineKeyboardButton(
                    text='✍️ Ответить/Статус',
                    callback_data=ComplaintActionCallback(action='manage', complaint_id=cid).pack(),
                ),
            ],
            [InlineKeyboardButton(text='📜 История действий', callback_data=ComplaintActionCallback(action='history', complaint_id=cid).pack())],
        ]
    )

def get_status_selection_keyboard(cid: int) -> InlineKeyboardMarkup:
    statuses = [s for s in ComplaintStatus if s != ComplaintStatus.NEW]
    buttons = [
        [
            InlineKeyboardButton(
                text=f'Статус: {s.value}',
                callback_data=ComplaintStatusCallback(status=s.value, complaint_id=cid).pack(),
            )
        ]
        for s in statuses
    ]
    buttons.append([
        InlineKeyboardButton(
            text='⬅️ Назад',
            callback_data=ComplaintActionCallback(action='back_to_actions', complaint_id=cid).pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_help_menu_inline(is_admin=False):
    buttons = [
        [InlineKeyboardButton(text="🚀 Запустить бота", callback_data="menu:start")],
        [InlineKeyboardButton(text="📝 Подать обращение", callback_data="menu:complaint")],
        [InlineKeyboardButton(text="🌟 Направить благодарность", callback_data="menu:gratitude")],
        [InlineKeyboardButton(text="🆘 Справка", callback_data="menu:help")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="🛠 Панель администратора", callback_data="menu:panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
