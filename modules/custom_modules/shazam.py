import os
import requests
from urllib.parse import quote
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix

MUSIC_API_URL = "https://api.betabotz.eu.org/api/tools/whatmusic"
API_KEY = "sRAVUT6X"

@Client.on_message(filters.command(["shazam"], prefix))
async def shazam_music(client, message: Message):
    if not (message.reply_to_message and (message.reply_to_message.audio or message.reply_to_message.voice)):
        await message.edit("Reply to an audio or voice message to identify the music.")
        return

    media = message.reply_to_message.audio or message.reply_to_message.voice
    await message.edit("Downloading audio file...")
    audio_path = await client.download_media(media.file_id)

    try:
        await message.edit("Uploading audio file...")
        with open(audio_path, "rb") as audio_file:
            upload_response = requests.post("https://x0.at", files={"file": audio_file})
            upload_response.raise_for_status()
            audio_url = upload_response.text.strip()
        
        await message.edit("Analyzing audio file...")
        url = f"{MUSIC_API_URL}?url={quote(audio_url)}&apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("status"):
            result = data.get("result", "No details found.")
            lines = result.split("\n")
            formatted_result = "\n".join([f"**{line.split(':')[0].strip()}:** {line.split(':', 1)[1].strip()}" for line in lines if ':' in line])
            await message.edit(f"**Music Information:**\n\n{formatted_result}", parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.edit(f"Failed to fetch music information. Error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        await message.edit(f"An error occurred: {str(e)}")
    finally:
        os.remove(audio_path)

modules_help["shazam"] = {
    "shazam": "Reply to an audio or voice file to identify the music.",
}
