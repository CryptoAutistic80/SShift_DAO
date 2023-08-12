import nextcord
from nextcord.ext import commands, tasks
from src.database_manager import retrieve_data, update_retrieved_status
from config import RESULTS_CHAN_ID

# Define the column names based on your database schema
COLUMN_NAMES = [
    "track_id", "id", "status", "model", "prompt", "negative_prompt",
    "safetychecker", "seed", "output", "retrieved", "timestamp"
]

class Results(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_db.start()  # Start the background task

    @commands.Cog.listener()
    async def on_ready(self):
        print("Result Output Online")

    @tasks.loop(seconds=60)
    async def check_db(self):
        try:
            print("Checking database...")  # Log to ensure the loop runs
    
            # Fetch entries from the database with "retrieved" set to "no"
            unretrieved_entries = await retrieve_data()
    
            # Convert tuple entries to dictionaries
            unretrieved_entries_dicts = [dict(zip(COLUMN_NAMES, entry)) for entry in unretrieved_entries]
            
            # Filter out entries with safetychecker set to 'no'
            safe_unretrieved_entries = [entry for entry in unretrieved_entries_dicts if entry["safetychecker"] != 'no']

            # Log the number of unretrieved entries found
            print(f"Found {len(safe_unretrieved_entries)} safe unretrieved entries to post.")
    
            # Ensure the bot can get the specified channel
            channel = self.bot.get_channel(RESULTS_CHAN_ID)
            if not channel:
                print(f"Unable to find channel with ID: {RESULTS_CHAN_ID}")
                return
    
            for entry in safe_unretrieved_entries:
                # Send the output to the Discord channel
                message = await channel.send(entry["output"])
                if message:
                    await message.publish()  # This line publishes the message to followers
                    print(f"Successfully sent and published message {message.id} to channel {channel.name}.")
                else:
                    print(f"Failed to send message for entry with track_id: {entry['track_id']} and id: {entry['id']}.")
    
                # Update the "retrieved" field to "yes" for the entry
                await update_retrieved_status(entry["track_id"], entry["id"])
                print(f"Updated 'retrieved' status for entry with track_id: {entry['track_id']} and id: {entry['id']}.")
                
        except Exception as e:
            print(f"An error occurred during the check_db loop: {e}")
    
        finally:
            print("check_db loop iteration completed.")

    @check_db.before_loop
    async def before_checking(self):
        await self.bot.wait_until_ready()  # Wait until the bot logs in

def setup(bot):
    bot.add_cog(Results(bot))



