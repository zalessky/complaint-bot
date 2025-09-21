import aiosqlite
import logging
import os
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from .dto import ComplaintDTO

DB_FILE_PATH = f"data/{os.getenv('DB_FILE', 'complaints.sqlite3')}"
logger = logging.getLogger(__name__)

class ComplaintStatus(Enum):
    NEW = "new"
    IN_WORK = "in_work"
    OK = "ok"
    REJECT = "reject"

async def init_db() -> None:
    """Initializes the database and creates tables if they don't exist."""
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL,
            violation_datetime TEXT NOT NULL,
            complaint_type_id INTEGER NOT NULL,
            complaint_type_name TEXT NOT NULL,
            other_description TEXT,
            route_number TEXT NOT NULL,
            direction TEXT NOT NULL
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints (id)
        )
        """)
        await db.commit()
    logger.info("Database tables are ready.")

async def add_complaint(dto: ComplaintDTO) -> int:
    """Adds a new complaint to the database and returns its ID."""
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        cursor = await db.cursor()
        await cursor.execute("""
        INSERT INTO complaints (user_id, created_at, violation_datetime, complaint_type_id, 
                                complaint_type_name, other_description, route_number, direction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (dto.user_id, datetime.now().isoformat(), dto.violation_datetime.isoformat(),
              dto.complaint_type_id, dto.complaint_type_name, dto.other_description,
              dto.route_number, dto.direction))
        
        complaint_id = cursor.lastrowid
        
        if dto.media_file_ids:
            for file_id in dto.media_file_ids:
                await cursor.execute("INSERT INTO media (complaint_id, file_id) VALUES (?, ?)", (complaint_id, file_id))
        
        await db.commit()
        return complaint_id

async def get_stats() -> Dict[str, Any]:
    """Retrieves complaint statistics from the database."""
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as count FROM complaints WHERE date(created_at) = date('now')") as cursor:
            today = await cursor.fetchone()
        async with db.execute("SELECT COUNT(*) as count FROM complaints") as cursor:
            total = await cursor.fetchone()
        async with db.execute("SELECT complaint_type_name, COUNT(*) as count FROM complaints GROUP BY complaint_type_name ORDER BY count DESC") as cursor:
            by_type = await cursor.fetchall()
        return {
            "total_today": today['count'] if today else 0,
            "total_all_time": total['count'] if total else 0,
            "by_type": [dict(row) for row in by_type]
        }

async def get_last_complaints(limit: int) -> List[Dict[str, Any]]:
    """Retrieves the last N complaints, including media file IDs."""
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
        SELECT c.id, c.status, strftime('%Y-%m-%d %H:%M', c.created_at) as created_at, 
               c.complaint_type_name, c.route_number, GROUP_CONCAT(m.file_id) as media_file_ids
        FROM complaints c
        LEFT JOIN media m ON c.id = m.complaint_id
        GROUP BY c.id
        ORDER BY c.id DESC 
        LIMIT ?
        """
        async with db.execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_complaints_for_export() -> List[Dict[str, Any]]:
    """Retrieves all complaints with their media for CSV export."""
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
        SELECT c.id, c.user_id, c.status, c.created_at, c.violation_datetime, 
               c.complaint_type_name, c.other_description, c.route_number, c.direction, 
               GROUP_CONCAT(m.file_id) as media_file_ids
        FROM complaints c
        LEFT JOIN media m ON c.id = m.complaint_id
        GROUP BY c.id
        ORDER BY c.id ASC
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def update_complaint_status(complaint_id: int, status: ComplaintStatus) -> bool:
    """Updates the status of a specific complaint."""
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        cursor = await db.execute("UPDATE complaints SET status = ? WHERE id = ?", (status.value, complaint_id))
        await db.commit()
        return cursor.rowcount > 0
