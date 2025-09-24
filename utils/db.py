import os
import aiosqlite
from datetime import datetime

DB_PATH = os.environ.get('DB_FILE', 'complaints.sqlite3')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                created_at TEXT,
                category_key TEXT,
                subcategory_id INTEGER,
                subcategory_name TEXT,
                latitude REAL,
                longitude REAL,
                address TEXT,
                description TEXT,
                route_number TEXT,
                violation_datetime TEXT,
                fio TEXT,
                phone TEXT,
                status TEXT DEFAULT 'new'
            );
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER,
                file_id TEXT
            );
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER,
                username TEXT,
                role TEXT,
                added_at TEXT,
                PRIMARY KEY (user_id,username)
            );
            CREATE TABLE IF NOT EXISTS admin_permissions (
                admin_user_id INTEGER,
                category_key TEXT,
                PRIMARY KEY(admin_user_id,category_key)
            );
        """)
        await db.commit()

async def get_admin_details(userid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id, username, role FROM admins WHERE user_id = ?", (userid,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            info = dict(row)
            if info.get('role', '') == 'superadmin':
                info['permissions'] = ['all']
            else:
                perms = []
                async with db.execute("SELECT category_key FROM admin_permissions WHERE admin_user_id = ?", (userid,)) as c2:
                    rows = await c2.fetchall()
                    perms = [r["category_key"] for r in rows]
                info['permissions'] = perms
            return info

async def save_complaint(dto):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO complaints (
                user_id, created_at, category_key, subcategory_id, subcategory_name, latitude, longitude, address, description,
                route_number, violation_datetime, fio, phone, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            getattr(dto, 'user_id', 0),
            getattr(dto, 'created_at', datetime.now().isoformat()),
            getattr(dto, 'categorykey', ''),
            getattr(dto, 'subcategoryid', 0),
            getattr(dto, 'subcategoryname', ''),
            getattr(dto, 'latitude', None),
            getattr(dto, 'longitude', None),
            getattr(dto, 'address', ''),
            getattr(dto, 'description', ''),
            getattr(dto, 'routenumber', ''),
            getattr(dto, 'violationdatetime', ''),
            getattr(dto, 'fio', ''),
            getattr(dto, 'phone', ''),
            'new'
        ))
        await db.commit()

async def get_admin_stats(categories):
    q = 'SELECT status,COUNT(*) as count FROM complaints'
    params = ()
    if categories and categories != ['all']:
        placeholders = ', '.join('?'*len(categories))
        q += f' WHERE category_key IN ({placeholders})'
        params = tuple(categories)
    q += ' GROUP BY status'
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(q, params) as cursor:
            rows = await cursor.fetchall()
            stats = {row['status']: row['count'] for row in rows}
            return {
                'new': stats.get('new', 0),
                'in_work': stats.get('in_work', 0)+stats.get('clarification_needed', 0)
            }

async def get_complaints_by_status(statuses, allowed_categories):
    q = "SELECT * FROM complaints WHERE status IN ({})".format(','.join(['?']*len(statuses)))
    params = list(statuses)
    if allowed_categories and allowed_categories != ['all']:
        q += " AND category_key IN ({})".format(','.join(['?']*len(allowed_categories)))
        params.extend(allowed_categories)
    q += " ORDER BY created_at DESC"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(q, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
