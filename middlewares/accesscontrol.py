from typing import Union
from aiogram.types import Message, CallbackQuery
from utils.db import get_admin_details

class IsAdminFilter:
    def __init__(self, is_superadmin: bool = False):
        self.is_superadmin = is_superadmin

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        admin_info = await get_admin_details(event.from_user.id)
        if not admin_info:
            return False
        if self.is_superadmin:
            return admin_info.get('role') == 'superadmin'
        return admin_info.get('role') in ('admin', 'superadmin')
