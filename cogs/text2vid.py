import logging
import aiohttp
import os
import json
import nextcord
from nextcord.ext import commands
from config import STABLE_GUILD_ID

# Set up logging
logging.basicConfig(level=logging.INFO)

class Text2Vid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('STABLEDIFFUSION_API_KEY')

    async def post_stablediffusion(self, prompt, negative_prompt, seconds):
        url = "https://stablediffusionapi.com/api/v5/text2video"
        payload = json.dumps({
            "key": self.api_key,
            "prompt": prompt,
            "negative_prompt": negative_prompt if negative_prompt != "" else None,
            "scheduler": "UniPCMultistepScheduler",
            "seconds": seconds
        })
        headers = {
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                response_content = await response.text()
        return json.loads(response_content)

    @nextcord.slash_command(description="Use StableDiffusion API to generate a video", guild_ids=[STABLE_GUILD_ID])
    async def text2vid(self, interaction: nextcord.Interaction, 
                       prompt: str = nextcord.SlashOption(description="Enter a prompt for the video"),
                       seconds: int = nextcord.SlashOption(description="Duration of the video in seconds"),
                       negative_prompt: str = nextcord.SlashOption(description="Enter a negative prompt for the video", required=False)):
        try:
            logging.info('Received command')
            await interaction.response.defer()
            response_json = await self.post_stablediffusion(prompt, negative_prompt, seconds)
            print(response_json)
            if response_json.get('status') == 'success':
                video_url = response_json['output'][0]
                await interaction.followup.send(f"Here's your generated video: {video_url}")
        except nextcord.NotFound:
            logging.error('Nextcord.NotFound exception caught')
            return
        except Exception as e:
            logging.error(f'Unexpected error: {e}')

def setup(bot):
    bot.add_cog(Text2Vid(bot))

