import asyncio
import aiosqlite
import os
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения, чтобы найти правильные пути к БД
load_dotenv()

# Настройка логирования для вывода информации в консоль
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

COMPLAINTS_DB_PATH = os.environ.get('DB_FILE', 'data/complaints.sqlite3')
USERS_DB_PATH = os.environ.get('USERS_DB_FILE', 'data/users.sqlite3')

async def update_complaints_schema():
    """
    Проверяет и добавляет недостающие столбцы в таблицу complaints.
    """
    db_dir = os.path.dirname(COMPLAINTS_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    if not os.path.exists(COMPLAINTS_DB_PATH):
        logging.warning(f"Файл '{COMPLAINTS_DB_PATH}' не найден. Патч не требуется, база будет создана при запуске бота.")
        return

    logging.info(f"Проверка схемы базы данных: {COMPLAINTS_DB_PATH}")
    
    async with aiosqlite.connect(COMPLAINTS_DB_PATH) as db:
        try:
            cursor = await db.execute("PRAGMA table_info(complaints)")
            columns_info = await cursor.fetchall()
            existing_columns = {col[1] for col in columns_info}
            
            changes_made = False
            columns_to_add = {
                "username": "TEXT",
                "route_number": "TEXT"
            }

            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    logging.info(f"Добавляется столбец '{col_name}' в таблицу 'complaints'...")
                    await db.execute(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}")
                    changes_made = True
                else:
                    logging.info(f"Столбец '{col_name}' уже существует.")
            
            if changes_made:
                await db.commit()
                logging.info("Схема таблицы 'complaints' успешно обновлена!")
            else:
                logging.info("Обновление схемы 'complaints' не требуется.")

        except aiosqlite.Error as e:
            logging.error(f"Произошла ошибка при обновлении 'complaints': {e}")

async def create_users_db_if_not_exists():
    """
    Создает базу данных users.sqlite3 и таблицу users, если их еще нет.
    """
    db_dir = os.path.dirname(USERS_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    logging.info(f"Проверка базы данных пользователей: {USERS_DB_PATH}")
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
        logging.info("База данных пользователей готова к работе.")


async def main():
    await update_complaints_schema()
    await create_users_db_if_not_exists()

if __name__ == "__main__":
    asyncio.run(main())
