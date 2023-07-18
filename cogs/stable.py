#------------------------------------------------------------
#                  IMPORT STATEMENTS
#------------------------------------------------------------

import os
import nextcord
from nextcord import SlashOption
from nextcord.ext import commands
import asyncio
import logging

from src.api_calls import fetch_stablediffusion, post_stablediffusion
from src.discord_ui import ( 
    UpscaleButton,  
    FetchResultsButton,
    FetchResultsView,
    ImageView,
    UpscaleView,
    TweetButton
)

#------------------------------------------------------------------------
#                   Queue Management
#------------------------------------------------------------------------

# TaskQueue class
class TaskQueue:
    def __init__(self, workers):
        self.queue = asyncio.Queue()
        self.workers = workers
        for _ in range(self.workers):
            asyncio.create_task(self._worker())

    async def put(self, task):
        await self.queue.put(task)

    async def _worker(self):
        while True:
            task = await self.queue.get()
            await task
            self.queue.task_done()

#------------------------------------------------------------------------
#                   MAIN FUNCTIONS
#------------------------------------------------------------------------

class Stable(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('STABLEDIFFUSION_API_KEY')
        self.job_ids = {}  #to store user IDs and their prompts
        self.prompts = {}
        self.negative_prompts = {}  # Dictionary to store user IDs and their negative prompts
        self.image_urls = {}  # Dictionary to store user IDs and their image URLs
        self.task_queue = TaskQueue(5)  # 5 workers for 5 tasks per second

    # Function to process the fetch response and send the results to the user
    async def process_fetch_response(self, interaction, user_id):
        job_id = self.job_ids[user_id]
        while True:
            response_json = await fetch_stablediffusion(self.api_key, job_id)
            if response_json['status'] == 'success':
                image_url = response_json['output'][0]  # We expect only one image now
                view = ImageView(image_url)  # Create an ImageView with the image URL

                embed = nextcord.Embed(  # Create an embed
                    title="Generated using:",
                    description=f"Prompt: {self.prompts[user_id]}, Negative prompt: {self.negative_prompts[user_id]}",
                    color=nextcord.Color.blurple()
                )
                embed.set_image(url=image_url)  # Set the image URL in the embed

                await interaction.followup.send(embed=embed, view=view)  # Send the embed along with the view
                break
            else:
                await asyncio.sleep(3)

    async def process_task(self, interaction, model, prompt, negative_prompt, width, height, enhance_prompt, track_id):
        try:
            ##print(f"Track ID: {track_id}")
            # Make the API call
            response_json = await post_stablediffusion(self.api_key, model, prompt, negative_prompt, width, height, enhance_prompt, track_id)
        
            # Process the response
            if 'id' in response_json:
                job_id = response_json['id']
                user_id = str(interaction.user.id)
                self.job_ids[user_id] = job_id
                self.prompts[user_id] = prompt
                self.negative_prompts[user_id] = negative_prompt
                generation_time = response_json.get('generationTime', 0)
                estimated_time = f"{generation_time:.2f}"  # Convert generation_time to a formatted string with 2 decimal places
                view = FetchResultsView(self, user_id, interaction)
                await interaction.followup.send(f'Your request has been processed. Your job ID is {job_id}. Estimated generation time: {estimated_time} seconds. You may manually fetch your results by clicking the "Fetch Results" button.', view=view)
            else:
                logging.error('Failed to retrieve job ID')
                logging.error(f'API response: {response_json}')
                await interaction.followup.send('Something went wrong, try again later.')
        except nextcord.NotFound:
            logging.error('NotFound exception encountered')
            return

    @nextcord.slash_command(description="Use StableDiffusion API")
    async def stable(self, interaction: nextcord.Interaction, 
                  model: str = SlashOption(
                      choices={ 
                          "Stable 1.5": "sd-1.5",
                          "SDXL 0.9": "sdxl",
                          "Disney Pixar": "disney-pixar-cartoon",
                          "Horror": "dreadless-v3",
                          "Anime": "anything-v5",
                          "Dream Shaper": "dreamshaper-v6",
                          "Game Character": "zovya",
                          "Portait Plus (use 'portait+ style')": "portraitplus-diffusion",
                          "GTA-V": "gta5-artwork-diffusi",
                          "Realistic Vision": "realistic-vision-v13"},
                      description="Choose the model for the image generation"),
                  prompt: str = SlashOption(description="Enter a prompt for the image"),
                  resolution: str = SlashOption(
                      choices={ 
                          "1024x768 (landscape)": "1024x768", 
                          "1024x1024 (square)": "1024x1024",
                          "768x1024 (portrait)": "768x1024"},
                      description="Choose the resolution for the image"),
                  enhance_prompt: bool = SlashOption(description="Choose whether to enhance the prompt or not"),
                  negative_prompt: str = SlashOption(description="Enter a negative prompt for the image", required=False)
                  ):
        await interaction.response.defer()
        logging.info(f'Received /stable command with prompt: {prompt}')
        width, height = resolution.split('x')
        user_id = str(interaction.user.id)
        print(f"User ID: {user_id}")  # Add this line
        task = self.process_task(interaction, model, prompt, negative_prompt, width, height, enhance_prompt, user_id)
        await self.task_queue.put(task)

def setup(bot):
    bot.add_cog(Stable(bot))

