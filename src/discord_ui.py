import nextcord
import aiohttp
import json
import os
from urllib.parse import quote
import logging

#-------------------------------------------------------------
#                      UI CLASSES
#-------------------------------------------------------------


# Custom button class for 2K upscaling
class UpscaleButton(nextcord.ui.Button):
    def __init__(self, image_url):
        super().__init__(label="2K Upscale", style=nextcord.ButtonStyle.primary, row=0)  
        self.image_url = image_url

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
    
        # Temporary ephemeral message
        await interaction.followup.send(content="Working on it....💫", ephemeral=True)
    
        url = "https://stablediffusionapi.com/api/v3/super_resolution"
        payload = json.dumps({
            "key": os.getenv('STABLEDIFFUSION_API_KEY'),
            "url": self.image_url,
            "scale": 4,
            "webhook": None,
            "face_enhance": False,
        })
        headers = {'Content-Type': 'application/json'}
        
        logging.info(f'Sending request to upscale API with URL: {self.image_url}')
    
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                response_content = await response.text()
    
        logging.info(f'Status code: {response.status}')
        logging.info(f'Response content: {response_content}')
    
        result_url = json.loads(response_content).get('output', 'Error while processing the image.')
    
        logging.info(f'result_url: {result_url}')
    
        # Check the URL validity before setting it in the embed
        if result_url.startswith('http://') or result_url.startswith('https://'):
            embed = nextcord.Embed(title="Upscaled to 2K")  
            embed.set_image(url=result_url)  
    
            view = UpscaleView(result_url)
            await interaction.followup.send(embed=embed, view=view)
        else:
            logging.error(f'Invalid URL received: {result_url}')
            await interaction.followup.send('Error occurred while processing the image. Please try again later.', ephemeral=True)


# Custom button class for fetching results
class FetchResultsButton(nextcord.ui.Button):
    def __init__(self, sdxl_instance, user_id, interaction):
        super().__init__(label="Fetch Results", style=nextcord.ButtonStyle.secondary)
        self.sdxl_instance = sdxl_instance
        self.user_id = user_id
        self.interaction = interaction

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()  # Defer the interaction response
        
        await self.sdxl_instance.process_fetch_response(self.interaction, self.user_id)

# Custom view class for fetching results
class FetchResultsView(nextcord.ui.View):
    def __init__(self, sdxl_instance, user_id, interaction):
        super().__init__()
        self.add_item(FetchResultsButton(sdxl_instance, user_id, interaction))

# Custom view class for image options
class ImageView(nextcord.ui.View):
    def __init__(self, image_url):
        super().__init__()
        self.add_item(UpscaleButton(image_url=image_url))
        self.add_item(TweetButton(image_url=image_url))

# Custom view class for additional upscaling options
class UpscaleView(nextcord.ui.View):
    def __init__(self, image_url):
        super().__init__()
        self.add_item(TweetButton(image_url=image_url))

# Custom button class for tweeting the image
class TweetButton(nextcord.ui.Button):
    def __init__(self, image_url):
        tweet_text = f"I made this with with #SDXL stable diffusion at #SShiftDAO @SShift_NFT, own one #MoveBot #NFT to access our #AiArt #StableDiffusion art machine! {image_url}"
        tweet_text_encoded = quote(tweet_text)
        tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text_encoded}"
        super().__init__(label="Tweet", style=nextcord.ButtonStyle.secondary, url=tweet_url)