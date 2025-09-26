from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.reply import main_menu_keyboard
from utils.db import get_admin_details, log_user_activity
from middlewares.access_control import IsAdminFilter
from .help_handler import HELP_TEXT
from .admin_panel import show_admin_panel_from_main_menu
from .superadmin_panel import superadmin_panel_entry
from .complaint_wizard import start_complaint
from .feedback_wizard import start_feedback

router = Router()

async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await log_user_activity(message.from_user)
    admin_info = await get_admin_details(message.from_user.id)
    role = admin_info.get('role') if admin_info else None
    await message.answer('Главное меню:', reply_markup=main_menu_keyboard(role))

@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    await show_main_menu(message, state)

@router.message(Command("menu"))
async def command_menu(message: Message, state: FSMContext):
    await show_main_menu(message, state)

# --- Main Menu Button Handlers ---

@router.message(F.text == "📝 Подать жалобу")
async def handle_complaint_button(message: Message, state: FSMContext):
    await start_complaint(message, state)

@router.message(F.text == "📢 Обратная связь")
async def handle_feedback_button(message: Message, state: FSMContext):
    await start_feedback(message, state)

@router.message(F.text == "🆘 Справка/О сервисе")
async def handle_help_button(message: Message):
    await message.answer(HELP_TEXT)

@router.message(F.text == "🛠️ Панель администратора", IsAdminFilter())
async def handle_admin_panel_button(message: Message, state: FSMContext):
    await show_admin_panel_from_main_menu(message, state)

@router.message(F.text == "👑 Панель Суперадминистратора", IsAdminFilter(is_superadmin=True))
async def handle_superadmin_panel_button(message: Message, state: FSMContext):
    await superadmin_panel_entry(message, state)

@router.message(F.text == "⬅️ Назад в Главное меню", IsAdminFilter())
async def handle_back_to_main_menu(message: Message, state: FSMContext):
    await show_main_menu(message, state)

@router.message(Command('id'))
async def cmd_id(message: Message):
    await message.answer(f'Ваш user_id: {message.from_user.id}')
