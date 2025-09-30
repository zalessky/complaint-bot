import asyncio
import aiosqlite
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    db_path = Path("data/complaints.sqlite3")
    db_path.parent.mkdir(exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        logger.info("📦 Начало миграции...")
        
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            position TEXT,
            department TEXT,
            role TEXT NOT NULL DEFAULT 'operator',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            type TEXT DEFAULT 'complaint',
            description TEXT NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            photos TEXT,
            status TEXT DEFAULT 'new',
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            sla_deadline TIMESTAMP,
            is_overdue INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_by INTEGER,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            author_type TEXT NOT NULL,
            text TEXT NOT NULL,
            attachments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            is_internal INTEGER DEFAULT 0,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        )''')
        
        await db.commit()
        logger.info("✅ Миграция завершена успешно!")

if __name__ == "__main__":
    asyncio.run(migrate_database())
