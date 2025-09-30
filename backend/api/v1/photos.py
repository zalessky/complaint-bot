from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from backend.core.config import settings
import httpx
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{file_id}")
async def get_photo(file_id: str):
    """
    Получает фото из Telegram по file_id
    """
    try:
        # Получаем информацию о файле
        async with httpx.AsyncClient() as client:
            file_response = await client.get(
                f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getFile",
                params={"file_id": file_id}
            )
            file_data = file_response.json()
            
            if not file_data.get("ok"):
                logger.error(f"Ошибка получения файла: {file_data}")
                raise HTTPException(status_code=404, detail="Photo not found")
            
            file_path = file_data["result"]["file_path"]
            
            # Скачиваем файл
            photo_url = f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
            photo_response = await client.get(photo_url)
            
            if photo_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Photo not found")
            
            # Возвращаем как поток
            return StreamingResponse(
                io.BytesIO(photo_response.content),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"}
            )
    except Exception as e:
        logger.error(f"Ошибка получения фото {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch photo")
