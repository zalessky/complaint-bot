import aiosqlite, asyncio

async def check_admins(path="data/complaints.sqlite3"):
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row  # Вот это ключ
        async with db.execute("SELECT * FROM admins") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(dict(row))

asyncio.run(check_admins("data/complaints.sqlite3"))
