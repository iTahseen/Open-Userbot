import os
import io
import time
import aiohttp
import asyncio
import logging
from PIL import Image
from pyrogram import filters, Client, enums
from pyrogram.types import Message
from concurrent.futures import ThreadPoolExecutor
from utils.misc import modules_help, prefix
from utils.scripts import format_exc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
HUGGINGFACE_API_TOKEN = "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"

async def query_huggingface(payload):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    timeout = aiohttp.ClientTimeout(total=60)
    start_time = time.time()
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(HUGGINGFACE_API_URL, headers=headers, json=payload) as response:
                fetch_time = int((time.time() - start_time) * 1000)
                if response.status != 200:
                    logger.error(f"API Error {response.status}: {await response.text()}")
                    return None, fetch_time
                return await response.read(), fetch_time
    except aiohttp.ClientError as e:
        logger.error(f"Network Error: {e}")
        return None, int((time.time() - start_time) * 1000)

async def save_image(image_bytes, path):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, lambda: Image.open(io.BytesIO(image_bytes)).save(path))

@Client.on_message(filters.command(["flux", "fl"], prefix))
async def imgflux_(client: Client, message: Message):
    prompt = message.text.split(" ", 1)[1] if len(message.command) > 1 else None
    if not prompt:
        usage_message = f"<b>Usage:</b> <code>{prefix}{message.command[0]} [custom prompt]</code>"
        return await (message.edit_text if message.from_user.is_self else message.reply_text)(usage_message)

    processing_message = await (message.edit_text if message.from_user.is_self else message.reply_text)("Processing...")

    try:
        image_bytes, fetch_time = await query_huggingface({"inputs": prompt})
        if not image_bytes:
            return await processing_message.edit_text("Failed to generate an image.")

        image_path = "hf_flux_gen.jpg"
        await save_image(image_bytes, image_path)

        caption = f"**Prompt used:**\n> {prompt}\n\n**Fetching:** {fetch_time} ms"
        await message.reply_photo(image_path, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)

        os.remove(image_path)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        await processing_message.edit_text(format_exc(e))
    finally:
        await processing_message.delete()

modules_help["flux"] = {
    "flux [custom prompt]*": "Generate an AI image using FLUX",
    "fl [custom prompt]*": "Generate an AI image using FLUX"
}
