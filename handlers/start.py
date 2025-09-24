from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.reply import main_menu_keyboard
from utils.db import get_admin_details

router = Router()

@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(message.from_user.id)
    is_admin = admin_info and admin_info.get('role','') in ('admin','superadmin')
    await message.answer('Главное меню:', reply_markup=main_menu_keyboard(is_admin))

@router.message(Command("menu"))
async def command_menu(message: Message, state: FSMContext):
    await state.clear()
    admin_info = await get_admin_details(message.from_user.id)
    is_admin = admin_info and admin_info.get('role','') in ('admin','superadmin')
    await message.answer('Главное меню:', reply_markup=main_menu_keyboard(is_admin))

@router.message(Command("panel"))
async def command_panel(message: Message, state: FSMContext):
    from keyboards.inline import get_admin_panel_keyboard
    from utils.db import get_admin_stats
    admin_info = await get_admin_details(message.from_user.id)
    await message.answer(f"DEBUG: user_id={message.from_user.id}, admin_info={admin_info}")
    if not admin_info or admin_info.get('role','') not in ('admin','superadmin'):
        await message.answer("Панель администратора доступна только администраторам.", reply_markup=main_menu_keyboard())
        return
    stats = await get_admin_stats(admin_info.get('permissions',[]))
    await message.answer(f"Панель администратора (role={admin_info.get('role')}, perms={admin_info.get('permissions')})", reply_markup=get_admin_panel_keyboard(stats))

@router.message(lambda m: m.text and m.text.lower() == "панель администратора")
async def handle_panel_admin(message: Message, state: FSMContext):
    from keyboards.inline import get_admin_panel_keyboard
    from utils.db import get_admin_stats
    admin_info = await get_admin_details(message.from_user.id)
    await message.answer(f"DEBUG: user_id={message.from_user.id}, admin_info={admin_info}")
    if not admin_info or admin_info.get('role','') not in ('admin','superadmin'):
        await message.answer("Панель администратора доступна только администраторам.", reply_markup=main_menu_keyboard())
        return
    stats = await get_admin_stats(admin_info.get('permissions',[]))
    await message.answer(f"Панель администратора (role={admin_info.get('role')}, perms={admin_info.get('permissions')})", reply_markup=get_admin_panel_keyboard(stats))

@router.message(lambda m: m.text and m.text.lower() == "направить благодарность")
async def handle_gratitude(message: Message, state: FSMContext):
    admin_info = await get_admin_details(message.from_user.id)
    is_admin = admin_info and admin_info.get('role','') in ('admin','superadmin')
    await message.answer("Функционал 'благодарности' будет добавлен позже!", reply_markup=main_menu_keyboard(is_admin))

@router.message(lambda m: m.text and m.text.lower() == "справка/о сервисе")
async def handle_help(message: Message, state: FSMContext):
    admin_info = await get_admin_details(message.from_user.id)
    is_admin = admin_info and admin_info.get('role','') in ('admin','superadmin')
    text = (
        "🤖 <b>Что умеет бот</b>:\n\n"
        "• Подать жалобу — фото, адрес, ФИО, телефон (обязательны).\n"
        "• Направить благодарность — поддержите сотрудников или сервис.\n"
        "• Краткая инфо о работе и контактах сервиса.\n"
    )
    if is_admin:
        text += "• Панель администратора — управление жалобами и статусами (только для админов).\n"
    await message.answer(text, parse_mode='HTML', reply_markup=main_menu_keyboard(is_admin))

@router.message(Command('id'))
async def cmd_id(message: Message, state: FSMContext):
    await message.answer(f'Ваш user_id: {message.from_user.id}')
