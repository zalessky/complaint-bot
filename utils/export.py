import csv
import aiosqlite
import os
from typing import List, Dict, Any
from .constants import STATUS_LABEL_RU, CATEGORIES

DB_PATH = os.environ.get('DB_FILE', 'data/complaints.sqlite3')

async def get_all_complaints_for_export() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM complaints ORDER BY id DESC") as cursor:
            return [dict(row) for row in await cursor.fetchall()]

async def export_complaints_to_csv() -> str:
    complaints = await get_all_complaints_for_export()
    file_path = "export_complaints.csv"
    
    headers = [
        "ID", "Дата", "Статус", "Категория", "Подкатегория", 
        "Адрес", "Описание", "ФИО", "Телефон", "User ID"
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for c in complaints:
            writer.writerow([
                c.get('id'),
                c.get('created_at'),
                STATUS_LABEL_RU.get(c.get('status', ''), c.get('status', '')),
                CATEGORIES.get(c.get('category_key', ''), {}).get('name', c.get('category_key')),
                c.get('subcategory_name'),
                c.get('address'),
                c.get('description'),
                c.get('fio'),
                c.get('phone'),
                c.get('user_id')
            ])
    
    return file_path
