import nextcord
from nextcord.ext import commands
import random
from config import guild_ids, channel_ids, emojis


class React(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_ready(self):
    print("Reactor Online")

  @commands.Cog.listener()
  async def on_message(self, message):
    if message.guild.id in guild_ids and message.channel.id in channel_ids and not message.author.bot:
      for emoji in random.sample(
          emojis, 20):  # This will pick 20 random emojis from the list
        await message.add_reaction(emoji)


def setup(bot):
  bot.add_cog(React(bot))
