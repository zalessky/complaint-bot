import asyncio
import aiosqlite
import sys
import os
from datetime import datetime
import pytz

DB_PATH = os.environ.get('DB_FILE', 'complaints.sqlite3')
SARATOV_TZ = pytz.timezone('Europe/Saratov')

async def add_superadmin(user_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO admins (user_id, role, added_at) VALUES (?, 'superadmin', ?)",
                (user_id, datetime.now(SARATOV_TZ).isoformat())
            )
            await db.commit()
        print(f"[+] Successfully added/updated user {user_id} as a superadmin.")
    except Exception as e:
        print(f"[-] An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Usage: poetry run python3 add_superadmin.py <USER_ID>")
        print("Example: poetry run python3 add_superadmin.py 123456789")
        sys.exit(1)
    
    user_id_to_add = int(sys.argv[1])
    asyncio.run(add_superadmin(user_id_to_add))
