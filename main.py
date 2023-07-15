import os
import logging
import asyncio
import nextcord
from nextcord.ext import commands
from server import keep_alive

os.environ['PYTHONASYNCIODEBUG'] = '1'

with open('discord.log', 'w'):
    pass

logging.basicConfig(filename='discord.log', level=logging.INFO)

intents = nextcord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

discord_token = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    logging.info('Bot has connected to Discord!')
    print('Bot has connected to Discord!')

def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            try:
                logging.info(f"Loading cog: {cog_name}")
                bot.load_extension(f'cogs.{cog_name}')
            except Exception as e:
                logging.error(f"Failed to load cog: {cog_name}. Error: {e}")

async def main():
    try:
        load()
        keep_alive()  # Start the server to keep your bot awake
        await bot.start(discord_token)
    except Exception as e:
        logging.error(f"Failed to start the bot. Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
