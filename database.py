import aiosqlite

DB_NAME = "medicines.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            medicine TEXT,
            time TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        await db.commit()

async def save_record(user_id: int, medicine: str, time: str, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
        INSERT INTO records (user_id, medicine, time, status)
        VALUES (?, ?, ?, ?)
        ''', (user_id, medicine, time, status))
        await db.commit()

async def get_history(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
        SELECT medicine, time, status, timestamp
        FROM records
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
        ''', (user_id,))
        return await cursor.fetchall()
