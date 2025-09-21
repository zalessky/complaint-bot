import os
from typing import Callable, Dict, Any, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


def get_admin_ids() -> list[int]:
    """Parses ADMINS env var and returns a list of integer IDs."""
    admins_str = os.getenv("ADMINS", "")
    if not admins_str:
        return []
    
    admin_ids = []
    for admin_id in admins_str.split(','):
        if admin_id.strip().isdigit():
            admin_ids.append(int(admin_id.strip()))
    return admin_ids


class AccessControlMiddleware(BaseMiddleware):
    """Middleware to add an 'is_admin' flag to the event data."""
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        admin_ids = get_admin_ids()
        data["is_admin"] = event.from_user.id in admin_ids
        return await handler(event, data)


class IsAdmin:
    """A simple filter to check if the user is an admin."""
    def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        admin_ids = get_admin_ids()
        return event.from_user.id in admin_ids
