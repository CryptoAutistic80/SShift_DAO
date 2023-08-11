import aiosqlite

# Define the database file name
db_file = "database/webhook_data.db"

async def setup_db():
    """
    Set up the SQLite database and create the table if it doesn't exist.
    """
    async with aiosqlite.connect(db_file) as conn:
        cursor = await conn.cursor()

        # Create the table
        await cursor.execute("""
        CREATE TABLE IF NOT EXISTS webhook_data (
            track_id TEXT,
            id INTEGER,
            status TEXT,
            model TEXT,
            prompt TEXT,
            negative_prompt TEXT,
            safetychecker TEXT,
            seed INTEGER,
            output TEXT,
            retrieved TEXT DEFAULT 'no'
        )
        """)

        await conn.commit()

async def insert_data(data):
    """
    Insert the webhook data into the database.
    """
    async with aiosqlite.connect(db_file) as conn:
        cursor = await conn.cursor()

        # Extract the necessary fields from the data
        track_id = data.get("track_id")
        id = data.get("id")
        status = data.get("status")
        model = data["meta"].get("model")
        prompt = data["meta"].get("prompt")
        negative_prompt = data["meta"].get("negative_prompt")
        safetychecker = data["meta"].get("safetychecker")
        seed = data["meta"].get("seed")
        output = data.get("output")[0] if data.get("output") else None  # Taking the first output, if available

        # Insert data into the table
        await cursor.execute("""
        INSERT INTO webhook_data (track_id, id, status, model, prompt, negative_prompt, safetychecker, seed, output)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (track_id, id, status, model, prompt, negative_prompt, safetychecker, seed, output))

        await conn.commit()

async def retrieve_data(track_id=None, id=None):
    """
    Retrieve data from the database based on track_id and/or id.
    """
    async with aiosqlite.connect(db_file) as conn:
        cursor = await conn.cursor()

        if track_id and id:
            await cursor.execute("SELECT * FROM webhook_data WHERE track_id=? AND id=?", (track_id, id))
        elif track_id:
            await cursor.execute("SELECT * FROM webhook_data WHERE track_id=?", (track_id,))
        elif id:
            await cursor.execute("SELECT * FROM webhook_data WHERE id=?", (id,))
        else:
            return []

        return await cursor.fetchall()


