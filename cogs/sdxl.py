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
#                   MAIN FUNCTIONS
#------------------------------------------------------------------------

class Sdxl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('STABLEDIFFUSION_API_KEY')
        self.job_ids = {}  #to store user IDs and their prompts
        self.prompts = {}
        self.negative_prompts = {}  # Dictionary to store user IDs and their negative prompts
        self.image_urls = {}  # Dictionary to store user IDs and their image URLs
      

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

#-------------------------------------------------------------------------------
#                         SLASH COMMANDS          
#-------------------------------------------------------------------------------
  
    @nextcord.slash_command(description="Use StableDiffusion API")
    async def sdxl(self, interaction: nextcord.Interaction, 
                  prompt: str = SlashOption(description="Enter a prompt for the image"),
                  resolution: str = SlashOption(
                      choices={ 
                          "1024x768 (landscape)": "1024x768", 
                          "1024x1024 (square)": "1024x1024",
                          "768x1024 (portrait)": "768x1024"},
                      description="Choose the resolution for the image"),
                  negative_prompt: str = SlashOption(description="Enter a negative prompt for the image", required=False)
                  ):
        try:
            await interaction.response.defer()
            logging.info(f'Received /sdxl command with prompt: {prompt}')
    
            width, height = resolution.split('x')
    
            response_json = await post_stablediffusion(self.api_key, prompt, negative_prompt, width, height)
            job_id = response_json['id'] if 'id' in response_json else None
            if job_id:
                user_id = interaction.user.id
                self.job_ids[user_id] = job_id
                self.prompts[user_id] = prompt
                self.negative_prompts[user_id] = negative_prompt
    
                logging.info(f'Successfully saved job ID: {job_id} for user ID: {user_id}')
                
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

def setup(bot):
    bot.add_cog(Sdxl(bot))
