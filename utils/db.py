import aiosqlite, logging, os
from datetime import datetime
from typing import List, Dict, Any, Optional
from .dto import ComplaintDTO
from .constants import ComplaintStatus

DB_FILE_PATH = f"data/{os.getenv('DB_FILE', 'city_bot_final.sqlite3')}"
logger = logging.getLogger(__name__)

async def execute(query, params=(), fetch=None):
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        if fetch == 'one':
            data = await cursor.fetchone()
        elif fetch == 'all':
            data = await cursor.fetchall()
        else:
            data = None
        await db.commit()
        if cursor.lastrowid and fetch is None:
            return cursor.lastrowid
        if isinstance(data, list):
            return [dict(row) for row in data]
        return dict(data) if data else None

async def init_db():
    await execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TEXT NOT NULL,
            category_key TEXT NOT NULL,
            subcategory_id INTEGER NOT NULL,
            subcategory_name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            address TEXT,
            description TEXT,
            assigned_admin_id INTEGER,
            route_number TEXT,
            violation_datetime TEXT
        )
    """)
    await execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            complaint_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
        )
    """)
    await execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT NOT NULL,
            added_at TEXT NOT NULL
        )
    """)
    await execute("""
        CREATE TABLE IF NOT EXISTS admin_permissions (
            admin_user_id INTEGER NOT NULL,
            category_key TEXT NOT NULL,
            PRIMARY KEY (admin_user_id, category_key),
            FOREIGN KEY (admin_user_id) REFERENCES admins (user_id) ON DELETE CASCADE
        )
    """)
    await execute("""
        CREATE TABLE IF NOT EXISTS complaint_history (
            id INTEGER PRIMARY KEY,
            complaint_id INTEGER NOT NULL,
            admin_user_id INTEGER,
            action_type TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
        )
    """)
    logger.info("Database tables are ready.")
    await bootstrap_superadmins()

async def bootstrap_superadmins():
    s_ids_str = os.getenv('SUPERADMINS', '')
    if not s_ids_str:
        return
    s_ids = [int(uid.strip()) for uid in s_ids_str.split(',') if uid.strip().isdigit()]
    for uid in s_ids:
        await execute(
            """
            INSERT INTO admins (user_id, role, added_at)
            VALUES (?, 'superadmin', ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (uid, datetime.now().isoformat()),
        )
    if s_ids:
        logger.info(f"Bootstrapped {len(s_ids)} superadmins.")

async def add_complaint(dto: ComplaintDTO) -> int:
    c_id = await execute(
        """
        INSERT INTO complaints (
            user_id, created_at, category_key, subcategory_id, subcategory_name,
            latitude, longitude, address, description,
            route_number, violation_datetime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dto.user_id,
            dto.created_at.isoformat(),
            dto.category_key,
            dto.subcategory_id,
            dto.subcategory_name,
            dto.latitude,
            dto.longitude,
            dto.address,
            dto.description,
            dto.route_number,
            dto.violation_datetime.isoformat() if dto.violation_datetime else None,
        ),
    )
    if dto.media_file_ids:
        for fid in dto.media_file_ids:
            await execute(
                "INSERT INTO media (complaint_id, file_id) VALUES (?, ?)",
                (c_id, fid),
            )
    return c_id

async def get_admin_details(user_id: int) -> Optional[Dict[str, Any]]:
    admin = await execute(
        "SELECT user_id, username, role FROM admins WHERE user_id = ?",
        (user_id,),
        fetch='one',
    )
    if not admin:
        return None
    if admin['role'] == 'superadmin':
        admin['permissions'] = ['all']
    else:
        perms = await execute(
            "SELECT category_key FROM admin_permissions WHERE admin_user_id = ?",
            (user_id,),
            fetch='all',
        )
        admin['permissions'] = [p['category_key'] for p in perms] if perms else []
    return admin

async def get_admin_stats(cats: List[str]) -> Dict[str, int]:
    q = 'SELECT status, COUNT(*) as count FROM complaints'
    params: tuple[Any, ...] = ()
    if 'all' not in cats:
        placeholders = ', '.join('?' for _ in cats)
        q += f' WHERE category_key IN ({placeholders})'
        params = tuple(cats)
    q += ' GROUP BY status'
    rows = await execute(q, params, fetch='all') or []
    stats = {r['status']: r['count'] for r in rows}
    return {
        'new': stats.get('new', 0),
        'in_work': stats.get('in_work', 0) + stats.get('clarification_needed', 0),
    }

async def get_complaints_by_status(statuses: List[str], cats: List[str]) -> List[Dict[str, Any]]:
    s_ph = ', '.join('?' for _ in statuses)
    q = (
        f"SELECT *, strftime('%Y-%m-%d %H:%M', created_at) as created_at "
        f"FROM complaints WHERE status IN ({s_ph})"
    )
    params: list[Any] = list(statuses)
    if 'all' not in cats:
        c_ph = ', '.join('?' for _ in cats)
        q += f" AND category_key IN ({c_ph})"
        params.extend(cats)
    q += ' ORDER BY id ASC LIMIT 10'
    return await execute(q, tuple(params), fetch='all')

async def get_complaint_by_id(cid: int) -> Optional[Dict[str, Any]]:
    return await execute(
        'SELECT * FROM complaints WHERE id = ?',
        (cid,),
        fetch='one',
    )

async def get_media_file_ids(cid: int) -> list[str]:
    rows = await execute("SELECT file_id FROM media WHERE complaint_id = ?", (cid,), fetch="all")
    return [r["file_id"] for r in rows] if rows else []

async def assign_complaint_to_admin(cid: int, aid: int):
    await update_complaint_status(cid, ComplaintStatus.IN_WORK)
    await execute('UPDATE complaints SET assigned_admin_id = ? WHERE id = ?', (aid, cid))

async def update_complaint_status(cid: int, status: ComplaintStatus):
    await execute('UPDATE complaints SET status = ? WHERE id = ?', (status.value, cid))

async def add_history_record(cid: int, aid: int, action: str, details: str):
    await execute(
        'INSERT INTO complaint_history (complaint_id, admin_user_id, action_type, details, timestamp) VALUES (?, ?, ?, ?, ?)',
        (cid, aid, action, details, datetime.now().isoformat()),
    )

async def get_complaint_history(cid: int) -> List[Dict[str, Any]]:
    return await execute(
        "SELECT *, strftime('%Y-%m-%d %H:%M', timestamp) as timestamp FROM complaint_history WHERE complaint_id = ? ORDER BY id ASC",
        (cid,),
        fetch='all',
    )
