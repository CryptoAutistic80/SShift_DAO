import nextcord
from nextcord import Embed
from nextcord.ext import commands, tasks
from src.database_manager import retrieve_data, update_retrieved_status
from config import RESULTS_CHAN_ID
import random  
import time
import asyncio

# Define the column names based on your database schema
COLUMN_NAMES = [
    "track_id", "id", "status", "model", "prompt", "negative_prompt",
    "safetychecker", "safety_checker_type", "seed", "output", "retrieved", "timestamp"
]

class Results(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.entries_list = []  # Initialize the list
        self.check_db.start()  # Start the background task
        self.send_message_loop.start()  # Start the message sending loop

    @commands.Cog.listener()
    async def on_ready(self):
        print("Result Output Online")

    @tasks.loop(minutes=2)
    async def check_db(self):
        try:
            print("Checking database...")  
            unretrieved_entries = await retrieve_data()
            print("Unretrieved entries:", unretrieved_entries)  # Debugging statement
            unretrieved_entries_dicts = [dict(zip(COLUMN_NAMES, entry)) for entry in unretrieved_entries]

            # Filter entries where safety_checker_type is 'none' or NULL
            safe_unretrieved_entries = [entry for entry in unretrieved_entries_dicts if not entry["safety_checker_type"] or entry["safety_checker_type"].lower() == 'none']
            print("Safe unretrieved entries:", safe_unretrieved_entries)  # Debugging statement

            print(f"Found {len(safe_unretrieved_entries)} safe unretrieved entries to post.")
            for entry in safe_unretrieved_entries:
                self.entries_list.append(entry)  # Add the safe entries to the list

        except Exception as e:
            print(f"An error occurred during the check_db loop: {e}")
        finally:
            print("check_db loop iteration completed.")

    @tasks.loop(seconds=90)  # New loop to send messages every 120 seconds
    async def send_message_loop(self):
        if not self.entries_list:
            return

        entry = random.choice(self.entries_list)  # Select a random entry
        self.entries_list.remove(entry)  # Remove the selected entry from the list
        channel = self.bot.get_channel(RESULTS_CHAN_ID)
        if not channel:
            print(f"Unable to find channel with ID: {RESULTS_CHAN_ID}")
            return

        try:
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

                # Check rate limit headers
                remaining = int(message._http.response.headers.get('X-RateLimit-Remaining', 1))
                reset_time = int(message._http.response.headers.get('X-RateLimit-Reset', time.time()))

                # If we're at the limit, wait until the reset time
                if remaining == 0:
                    current_time = time.time()
                    sleep_duration = reset_time - current_time
                    if sleep_duration > 0:
                        await asyncio.sleep(sleep_duration)

            else:
                print(f"Failed to send message for entry with track_id: {entry['track_id']} and id: {entry['id']}.")

            await update_retrieved_status(entry["track_id"], entry["id"])
            print(f"Updated 'retrieved' status for entry with track_id: {entry['track_id']} and id: {entry['id']}.")

        except nextcord.HTTPException as http_exception:
            if http_exception.status == 429:
                # We've been rate limited, wait for the specified duration
                await asyncio.sleep(http_exception.retry_after)
            else:
                print(f"Exception while sending message for entry with track_id: {entry['track_id']} and id: {entry['id']}. Exception: {http_exception}")

    @check_db.before_loop
    async def before_checking(self):
        await self.bot.wait_until_ready()

    @send_message_loop.before_loop  # Ensure the bot is ready before starting the send_message_loop
    async def before_sending(self):
        await self.bot.wait_until_ready()

#def setup(bot):
   bot.add_cog(Results(bot))
   print("Results cog loaded")