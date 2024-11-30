import os
import requests
from urllib.parse import quote
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

GEMINIIMG_URL = "https://bk9.fun/ai/geminiimg"

@Client.on_message(filters.command(["describe"], prefix))
async def describe_image(client, message: Message):
    if not (message.reply_to_message and message.reply_to_message.photo):
        response_text = "Reply to an image and provide a prompt. Usage: `describe <prompt>`"
        await message.edit(response_text) if message.from_user.is_self else await message.reply(response_text)
        return

    prompt = " ".join(message.command[1:]).strip() or "Get details of given image, be as accurate as possible."
    download_message = await (message.edit("<code>Downloading image...</code>") if message.from_user.is_self else message.reply("Downloading image..."))
    
    photo_path = await client.download_media(message.reply_to_message.photo.file_id)

    try:
        upload_response = requests.post("https://x0.at", files={"file": open(photo_path, "rb")})
        upload_response.raise_for_status()
        image_url = upload_response.text.strip()

        url = f"{GEMINIIMG_URL}?url={quote(image_url)}&q={quote(prompt)}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        description = data.get("BK9", "No description found.")
        response_content = f"**Prompt:** {prompt}\n**Description:** {description}"

        await download_message.edit(response_content, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        await download_message.edit(f"An error occurred: {str(e)}")
    finally:
        os.remove(photo_path)

modules_help["ask"] = {
    "describe [image_url] [query]*": "Describe an image with a query."
}
