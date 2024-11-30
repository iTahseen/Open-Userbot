import requests
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

GOOGLE_TTS_URL = "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang}&q={text}"

async def download_audio(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        return output_file
    except requests.RequestException:
        return None

@Client.on_message(filters.command(["gtts"], prefix))
async def text_to_speech(_, message: Message):
    if len(message.command) < 2:
        await message.edit("Usage: `tts <text>`")
        return

    text = " ".join(message.command[1:]).strip()
    lang = "en"
    if not text:
        await message.edit("Error: No text provided.")
        return

    tts_url = GOOGLE_TTS_URL.format(lang=lang, text=text.replace(" ", "+"))
    await message.edit("<code>Generating speech...</code>")
    mp3_file = "tts_output.mp3"
    audio_file = await download_audio(tts_url, mp3_file)

    if not audio_file:
        await message.edit("Error: Failed to generate speech.")
        return

    try:
        await message.reply_voice(mp3_file)
        await message.delete()
    finally:
        if os.path.exists(mp3_file):
            os.remove(mp3_file)

modules_help["gtts"] = {"gtts [text]*": "Generate text-to-speech voice using Google's TTS service"}
