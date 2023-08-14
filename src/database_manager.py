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
            safety_checker_type TEXT,
            seed INTEGER,
            output TEXT,
            retrieved TEXT DEFAULT 'no',
            timestamp INTEGER
        )
        """)

        # Create the composite index
        await cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp_track_id_id_retrieved ON webhook_data(timestamp, track_id, id, retrieved);
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
        safety_checker_type = data["meta"].get("safety_checker_type", "")  # Default to empty string if not available
        seed = data["meta"].get("seed")
        output = data.get("output")[0] if data.get("output") else None  # Taking the first output, if available
        timestamp = data.get("timestamp")  # Get the timestamp from the data

        # Insert data into the table
        await cursor.execute('''
        INSERT INTO webhook_data (track_id, id, status, model, prompt, negative_prompt, safetychecker, safety_checker_type, seed, output, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (track_id, id, status, model, prompt, negative_prompt, safetychecker, safety_checker_type, seed, output, timestamp))

        await conn.commit()

async def retrieve_data():
    """
    Retrieve data from the database where 'retrieved' is set to "no".
    """
    async with aiosqlite.connect(db_file) as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM webhook_data WHERE retrieved='no'")
        entries = await cursor.fetchall()
        print(f"Retrieved {len(entries)} entries from the database.")
        return entries

async def update_retrieved_status(track_id, id):
    """
    Update the 'retrieved' status of an entry in the database to 'yes'.
    """
    async with aiosqlite.connect(db_file) as conn:
        cursor = await conn.cursor()
        await cursor.execute("UPDATE webhook_data SET retrieved = 'yes' WHERE track_id=? AND id=?", (track_id, id))
        print(f"Updated retrieved status for track_id: {track_id}, id: {id}")
        await conn.commit()


