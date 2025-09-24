import aiosqlite, asyncio

async def add_myself():
    async with aiosqlite.connect("complaints.sqlite3") as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id, username, role, added_at) VALUES (?, ?, ?, datetime('now'))", (258031537, '@sterxx', 'superadmin'))
        await db.commit()
        print('[+] Inserted admin!')

asyncio.run(add_myself())
