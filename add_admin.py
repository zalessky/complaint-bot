import aiosqlite, asyncio
async def add_admin():
    async with aiosqlite.connect("data/complaints.sqlite3") as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id, username, role, added_at) VALUES (?, ?, ?, datetime('now'))", (258031537, '@sterxx', 'superadmin'))
        await db.commit()
asyncio.run(add_admin())
