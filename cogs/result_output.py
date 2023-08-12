import nextcord
from nextcord import Embed
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
            print("Checking database...")  
            unretrieved_entries = await retrieve_data()
            unretrieved_entries_dicts = [dict(zip(COLUMN_NAMES, entry)) for entry in unretrieved_entries]
            safe_unretrieved_entries = [entry for entry in unretrieved_entries_dicts if entry["safetychecker"] != 'no']
            print(f"Found {len(safe_unretrieved_entries)} safe unretrieved entries to post.")
            channel = self.bot.get_channel(RESULTS_CHAN_ID)
            if not channel:
                print(f"Unable to find channel with ID: {RESULTS_CHAN_ID}")
                return

            for entry in safe_unretrieved_entries:
                embed = Embed(title="Made at SShift DAO", color=0x3498db)
                embed.description = "Created by a talented owner of a Move Bot NFT living on the APTOS blockchain."
            
                # Adding the two URLs as fields
                embed.add_field(name="Wapal NFT marketplace", value="https://wapal.io/collection/Move%20Bots", inline=False)
                embed.add_field(name="Topaz NFT marketplace", value="https://www.topaz.so/collection/Move-Bots-50cbfbedad", inline=False)
            
                embed.set_image(url=entry["output"])  # Set the image of the embed to the URL after adding fields
            
                message = await channel.send(embed=embed)
                if message:
                    await message.publish()
                    print(f"Successfully sent and published message {message.id} to channel {channel.name}.")
                else:
                    print(f"Failed to send message for entry with track_id: {entry['track_id']} and id: {entry['id']}.")
                await update_retrieved_status(entry["track_id"], entry["id"])
                print(f"Updated 'retrieved' status for entry with track_id: {entry['track_id']} and id: {entry['id']}.")

        except Exception as e:
            print(f"An error occurred during the check_db loop: {e}")
        finally:
            print("check_db loop iteration completed.")

    @check_db.before_loop
    async def before_checking(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Results(bot))