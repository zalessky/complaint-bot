from typing import Any, Awaitable, Callable, Dict, Union
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter
from utils.db import get_admin_details

class IsAdminFilter(Filter):
    """
    Фильтр для проверки, является ли пользователь администратором.
    """
    def __init__(self, is_superadmin: bool = False):
        self.is_superadmin = is_superadmin

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        admin_info = await get_admin_details(event.from_user.id)
        if not admin_info:
            return False
        if self.is_superadmin:
            return admin_info.get("role") == "superadmin"
        return admin_info.get("role") in ["admin", "superadmin"]
