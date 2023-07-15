import json
import aiohttp

async def fetch_stablediffusion(api_key, job_id):
    url = "https://stablediffusionapi.com/api/v4/dreambooth/fetch"
    payload = json.dumps({
        "key": api_key,
        "request_id": job_id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            response_content = await response.text()
    return json.loads(response_content)

async def post_stablediffusion(api_key, prompt, negative_prompt, width, height):
    url = "https://stablediffusionapi.com/api/v4/dreambooth"
    payload = json.dumps({
        "key": api_key,
        "model_id": "sdxl",
        "prompt": prompt,
        "negative_prompt": negative_prompt if negative_prompt != "" else None,
        "width": width,
        "height": height,
        "samples": "1",
        "num_inference_steps": "21",
        "safety_checker": "yes",
        "enhance_prompt": "yes",
        "seed": None,
        "guidance_scale": 7.5,
        "multi_lingual": "no",
        "panorama": "no",
        "self_attention": "no",
        "scheduler": "DDPMScheduler",
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
