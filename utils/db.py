import os
import aiosqlite
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from aiogram.types import User
from .dto import ComplaintDTO
from .constants import ComplaintStatus

logger = logging.getLogger(__name__)
COMPLAINTS_DB_PATH = os.environ.get('DB_FILE', 'data/complaints.sqlite3')
USERS_DB_PATH = os.environ.get('USERS_DB_FILE', 'data/users.sqlite3')

async def init_db():
    db_dir = os.path.dirname(COMPLAINTS_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                created_at TEXT,
                category_key TEXT,
                subcategory_id INTEGER,
                subcategory_name TEXT,
                address TEXT,
                route_number TEXT,
                description TEXT,
                fio TEXT,
                phone TEXT,
                status TEXT DEFAULT 'new'
            );
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER,
                file_id TEXT,
                FOREIGN KEY (complaint_id) REFERENCES complaints(id)
            );
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                role TEXT,
                added_at TEXT
            );
        """)
        await db.commit()

async def init_users_db():
    db_dir = os.path.dirname(USERS_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    async with aiosqlite.connect(USERS_DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TEXT,
                last_seen TEXT
            )
        """)
        await db.commit()

async def log_user_activity(user: User):
    now_iso = datetime.now().isoformat()
    async with aiosqlite.connect(USERS_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            last_seen = excluded.last_seen,
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name
            """,
            (user.id, user.username, user.first_name, user.last_name, now_iso, now_iso)
        )
        await db.commit()

async def get_total_users_count() -> int:
    async with aiosqlite.connect(USERS_DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_complaint_count_for_user(user_id: int) -> int:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM complaints WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_all_users_with_stats() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as c_db:
        async with aiosqlite.connect(USERS_DB_PATH) as u_db:
            
            c_db.row_factory = aiosqlite.Row
            u_db.row_factory = aiosqlite.Row
            
            complaint_counts = {}
            async with c_db.execute("SELECT user_id, COUNT(*) as count FROM complaints GROUP BY user_id") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    complaint_counts[row['user_id']] = row['count']

            users_with_stats = []
            async with u_db.execute("SELECT * FROM users ORDER BY last_seen DESC") as cursor:
                user_rows = await cursor.fetchall()
                for user_row in user_rows:
                    user_data = dict(user_row)
                    user_data['complaint_count'] = complaint_counts.get(user_data['user_id'], 0)
                    users_with_stats.append(user_data)

    return users_with_stats

async def sync_superadmins():
    superadmin_ids_str = os.getenv("SUPERADMINS", "")
    if not superadmin_ids_str:
        logger.warning("SUPERADMINS environment variable is not set.")
        return

    superadmin_ids = [int(sid.strip()) for sid in superadmin_ids_str.split(',') if sid.strip().isdigit()]
    
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        for user_id in superadmin_ids:
            await db.execute(
                "INSERT OR IGNORE INTO admins (user_id, role, added_at) VALUES (?, 'superadmin', ?)",
                (user_id, datetime.now().isoformat())
            )
        await db.commit()
        logger.info(f"Synced {len(superadmin_ids)} superadmins into the database.")

async def get_admin_details(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id, role FROM admins WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def save_complaint(dto: ComplaintDTO) -> None:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO complaints (
                user_id, username, created_at, category_key, subcategory_id, subcategory_name, 
                address, route_number, description, fio, phone, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dto.user_id,
            dto.username,
            dto.created_at.isoformat(),
            dto.categorykey,
            dto.subcategoryid,
            dto.subcategoryname,
            dto.address,
            dto.routenumber,
            dto.description,
            dto.fio,
            dto.phone,
            'new'
        ))
        complaint_id = cursor.lastrowid
        if dto.mediafileids:
            for file_id in dto.mediafileids:
                await db.execute("INSERT INTO media (complaint_id, file_id) VALUES (?, ?)", (complaint_id, file_id))
        await db.commit()

async def get_admin_stats() -> Dict[str, int]:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT status, COUNT(*) as count FROM complaints GROUP BY status') as cursor:
            rows = await cursor.fetchall()
            stats = {row['status']: row['count'] for row in rows}
            
            completed_statuses = [ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value, ComplaintStatus.CLOSED.value]
            in_work_statuses = [ComplaintStatus.IN_WORK.value, ComplaintStatus.CLARIFICATION_NEEDED.value]
            
            return {
                'new': stats.get(ComplaintStatus.NEW.value, 0),
                'in_work': sum(stats.get(s, 0) for s in in_work_statuses),
                'completed': sum(stats.get(s, 0) for s in completed_statuses),
                'all': sum(stats.values())
            }

async def get_complaints_by_status(statuses: List[str]) -> List[Dict[str, Any]]:
    q = "SELECT * FROM complaints WHERE status IN ({}) ORDER BY created_at DESC".format(','.join(['?'] * len(statuses)))
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(q, statuses) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_complaints() -> List[Dict[str, Any]]:
    q = "SELECT * FROM complaints ORDER BY created_at DESC"
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(q) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_complaint_by_id(complaint_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_media_by_complaint_id(complaint_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT file_id FROM media WHERE complaint_id = ?", (complaint_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def update_complaint_status(complaint_id: int, new_status: str) -> None:
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        await db.execute("UPDATE complaints SET status = ? WHERE id = ?", (new_status, complaint_id))
        await db.commit()
