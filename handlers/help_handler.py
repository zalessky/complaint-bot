from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_help_menu_inline
from utils.db import get_admin_details

router = Router()

@router.message(Command('help'))
async def show_help(message: Message):
    admin_info = await get_admin_details(message.from_user.id)
    is_admin = bool(admin_info)
    await message.answer(
        "Выберите действие:",
        reply_markup=get_help_menu_inline(is_admin)
    )

@router.callback_query(F.data == "menu:start")
async def do_start(cb: CallbackQuery):
    await cb.message.answer("/start")
    await cb.answer()

@router.callback_query(F.data == "menu:complaint")
async def do_complaint(cb: CallbackQuery):
    await cb.message.answer("/complaint")
    await cb.answer()

@router.callback_query(F.data == "menu:panel")
async def do_panel(cb: CallbackQuery):
    admin_info = await get_admin_details(cb.from_user.id)
    if not admin_info:
        await cb.message.answer("Панель администратора доступна только сотрудникам МУП/администрации!")
    else:
        await cb.message.answer("Панель администратора доступна!\nИспользуйте кнопки в админ-меню для работы с жалобами.")
    await cb.answer()

@router.callback_query(F.data == "menu:help")
async def do_help(cb: CallbackQuery):
    admin_info = await get_admin_details(cb.from_user.id)
    is_admin = bool(admin_info)
    text = (
        "<b>Возможности бота:</b>\n"
        "• Подать жалобу — выберите категорию, заполните детали и отправьте.\n"
        "• Направить благодарность — поблагодарите службу или работника.\n"
    )
    if is_admin:
        text += "• Панель администратора — реагируйте на обращения, меняйте статусы (доступно только администраторам).\n"
    text += (
        "\n<b>Команды:</b>\n"
        "<code>/start</code> — начать работу\n"
        "<code>/complaint</code> — подать жалобу\n"
    )
    if is_admin:
        text += "<code>/panel</code> — админ-панель\n"
    text += "<code>/help</code> — справка"
    await cb.message.answer(text, parse_mode="HTML")
    await cb.answer()

@router.callback_query(F.data == "menu:gratitude")
async def gratitude(cb: CallbackQuery):
    await cb.message.answer("Функционал 'благодарности' будет добавлен позже!")
    await cb.answer()
