import os
import json
import aiohttp
import nextcord
from nextcord import SlashOption
from nextcord.ext import commands
import asyncio
import logging
from PIL import Image
from io import BytesIO
from typing import List

async def download_image(image_url: str) -> Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            response_content = await response.read()
    img = Image.open(BytesIO(response_content))
    return img

async def save_image(image: Image, path: str) -> None:
    image.save(path)

async def create_and_save_collage(images: List[Image.Image], path: str) -> None:
    max_width = max(img.size[0] for img in images)
    max_height = max(img.size[1] for img in images)
    collage = Image.new('RGB', (max_width * 2, max_height * 2))  # create a new 2x2 collage
    for i, img in enumerate(images):
        collage.paste(img, (max_width * (i % 2), max_height * (i // 2)))
    collage.save(path)

class ImageButton(nextcord.ui.Button):
    def __init__(self, label, image_path):
        super().__init__(label=label, style=nextcord.ButtonStyle.primary, row=0)
        self.image_path = image_path

    async def callback(self, interaction: nextcord.Interaction):
        with open(self.image_path, 'rb') as f:
            picture = nextcord.File(f)
            await interaction.response.send_message(file=picture, ephemeral=True)

class UpscaleButton(nextcord.ui.Button):
    def __init__(self, label, image_url):
        super().__init__(label=label, style=nextcord.ButtonStyle.primary, row=1)
        self.image_url = image_url

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        url = "https://stablediffusionapi.com/api/v3/super_resolution"
        payload = json.dumps({
            "key": os.getenv('STABLEDIFFUSION_API_KEY'),
            "url": self.image_url,
            "scale": 4,
            "webhook": None,
            "face_enhance": True,
        })
        headers = {'Content-Type': 'application/json'}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                response_content = await response.text()

        logging.info(f'Status code: {response.status}')
        logging.info(f'Response content: {response_content}')

        result_url = json.loads(response_content).get('output', 'Error while processing the image.')

        logging.info(f'result_url: {result_url}')

        view = AnotherUpscaleView(result_url)
        await interaction.followup.send(result_url, view=view)


class AnotherUpscaleButton(nextcord.ui.Button):
    def __init__(self, image_url):
        super().__init__(label="Go to 4K resolution", style=nextcord.ButtonStyle.primary)
        self.image_url = image_url

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        url = "https://stablediffusionapi.com/api/v3/super_resolution"
        payload = json.dumps({
            "key": os.getenv('STABLEDIFFUSION_API_KEY'),
            "url": self.image_url,
            "scale": 4,
            "webhook": None,
            "face_enhance": True,
        })
        headers = {'Content-Type': 'application/json'}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                response_content = await response.text()

        logging.info(f'Status code: {response.status}')
        logging.info(f'Response content: {response_content}')

        result_url = json.loads(response_content).get('output', 'Error while processing the image.')

        logging.info(f'result_url: {result_url}')

        await interaction.followup.send(result_url)


class ImageView(nextcord.ui.View):
    def __init__(self, image_paths, image_urls):
        super().__init__()
        for i, (path, url) in enumerate(zip(image_paths, image_urls)):
            self.add_item(ImageButton(label=f'I{i+1}', image_path=path))
            self.add_item(UpscaleButton(label=f'S{i+1}', image_url=url))


class AnotherUpscaleView(nextcord.ui.View):
    def __init__(self, image_url):
        super().__init__()
        self.add_item(AnotherUpscaleButton(image_url))

class Leo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('STABLEDIFFUSION_API_KEY')
        self.job_ids = {}
        self.prompts = {}
        self.negative_prompts = {}
        self.image_urls = {}

    async def post_stablediffusion(self, prompt, negative_prompt, width, height, panorama):
        url = "https://stablediffusionapi.com/api/v3/text2img"
        payload = json.dumps({
            "key": self.api_key,
            "prompt": prompt,
            "negative_prompt": negative_prompt if negative_prompt != "" else None,
            "width": width,
            "height": height,
            "samples": "4",
            "num_inference_steps": "21",
            "seed": None,
            "guidance_scale": 7.5,
            "safety_checker": "yes",
            "multi_lingual": "yes",
            "panorama": panorama,
            "self_attention": "yes",
            "upscale": "no",  # Set upscale to "no" by default
            "embeddings_model": None,
            "webhook": None,
            "track_id": None
        })
        headers = {
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                response_content = await response.text()
        return json.loads(response_content)

    async def fetch_stablediffusion(self, job_id):
        url = f"https://stablediffusionapi.com/api/v3/fetch/{job_id}"
        payload = json.dumps({
            "key": self.api_key
        })
        headers = {
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                response_content = await response.text()
        return json.loads(response_content)

    async def process_fetch_response(self, interaction, user_id):
        job_id = self.job_ids[user_id]
    
        while True:
            response_json = await self.fetch_stablediffusion(job_id)
    
            if response_json['status'] == 'success':
                images = []
                paths = []
                urls = []
                for i, image_url in enumerate(response_json['output']):
                    img = await download_image(image_url)
                    path = f'generations/{user_id}_{job_id}_{i}.png'
                    await save_image(img, path)
                    images.append(img)
                    paths.append(path)
                    urls.append(image_url)
    
                self.image_urls[user_id] = urls  # store URLs
    
                collage_path = f'generations/collage_{user_id}_{job_id}.png'
                await create_and_save_collage(images, collage_path)
    
                view = ImageView(paths, urls)
    
                file = nextcord.File(collage_path)
    
                embed = nextcord.Embed(
                    title="Generated using:",
                    description=f"Prompt: {self.prompts[user_id]}, Negative prompt: {self.negative_prompts[user_id]}",
                    color=nextcord.Color.blurple()
                )
    
                await interaction.followup.send(file=file, view=view, embed=embed)
                break
            else:
                await asyncio.sleep(3)

    @nextcord.slash_command(description="Use StableDiffusion API")
    async def leo(self, interaction: nextcord.Interaction, prompt: str = SlashOption(description="Enter a prompt for the image"),
                  resolution: str = SlashOption(
                      choices={
                          "256x256": "256x256", 
                          "512x512": "512x512", 
                          "640x480": "640x480", 
                          "800x600": "800x600", 
                          "1024x576": "1024x576", 
                          "1024x768": "1024x768", 
                          "1024x1024": "1024x1024",
                          "768x1024 (portrait)": "768x1024",
                          "576x1024 (portrait)": "576x1024",
                          "480x640 (portrait)": "480x640",
                          "600x800 (portrait)": "600x800"},
                  description="Choose the resolution for the image"),
                  panorama: str = SlashOption(
                      choices={"yes": "yes", "no": "no"},
                      description="Choose whether to enable panorama mode",
                  ),
                  negative_prompt: str = SlashOption(description="Enter a negative prompt for the image", required=False)
                  ):
        try:
            await interaction.response.defer()
            logging.info(f'Received /leo command with prompt: {prompt}')

            width, height = resolution.split('x')

            response_json = await self.post_stablediffusion(prompt, negative_prompt, width, height, panorama)
            job_id = response_json['id'] if 'id' in response_json else None
            if job_id:
                user_id = interaction.user.id
                self.job_ids[user_id] = job_id
                self.prompts[user_id] = prompt
                self.negative_prompts[user_id] = negative_prompt

                logging.info(f'Successfully saved job ID: {job_id} for user ID: {user_id}')
                await interaction.followup.send(f'Your request has been processed. Your job ID is {job_id}. Please wait 15 seconds and I will start to look for your results.')

                await asyncio.sleep(15)
                await self.process_fetch_response(interaction, user_id)
            else:
                logging.error('Failed to retrieve job ID')
                logging.error(f'API response: {response_json}')
                await interaction.followup.send('Something went wrong, try again later.')
        except nextcord.NotFound:
            logging.error('NotFound exception encountered')
            return

def setup(bot):
    bot.add_cog(Leo(bot))