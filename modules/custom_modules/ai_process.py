import os
import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message
import google.generativeai as genai
from PIL import Image
from utils.config import gemini_key
from utils.misc import prefix
from utils.scripts import modules_help

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel("gemini-1.5-flash")

def split_message(text, max_length=4000):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

async def upload_and_process_file(file_path, prompt, file_type):
    uploaded_file = genai.upload_file(file_path)
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(10)
        uploaded_file = genai.get_file(uploaded_file.name)
    if uploaded_file.state.name == "FAILED":
        raise ValueError(f"{file_type.capitalize()} failed to process")
    return [prompt, uploaded_file]

async def process_file(message, prompt, status_msg):
    await message.edit_text(f"<code>{status_msg}</code>")
    reply = message.reply_to_message
    if not reply:
        return await message.edit_text(f"<b>Usage:</b> <code>{prefix}{message.command[0]} [prompt]</code> [Reply to a file]")
    file_path = await reply.download()
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return await message.edit_text("<code>Failed to process the file. Try again.</code>")
    try:
        input_data = None
        if reply.photo:
            with Image.open(file_path) as img:
                img.verify()
                input_data = [prompt, img]
        elif reply.document and file_path.endswith(".pdf"):
            input_data = await upload_and_process_file(file_path, prompt, "PDF")
        elif reply.video:
            input_data = await upload_and_process_file(file_path, prompt, "video")
        elif reply.audio or reply.voice:
            audio_file = genai.upload_file(file_path)
            input_data = [audio_file, prompt]
        elif reply.document:
            generic_file = genai.upload_file(file_path)
            input_data = [generic_file, prompt]
        else:
            return await message.edit_text("<code>Unsupported file type.</code>")
        response = model.generate_content(input_data)
        result_text = f"**Prompt:** {prompt}\n**Answer:** {response.text}" if response and response.text else f"**Prompt:** {prompt}\n<code>No content generated.</code>"
        if len(result_text) > 4000:
            chunks = split_message(result_text)
            for chunk in chunks:
                await message.reply_text(chunk, parse_mode=enums.ParseMode.MARKDOWN)
            await message.delete()
        else:
            await message.edit_text(result_text, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        await message.edit_text(f"Error: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@Client.on_message(filters.command("process", prefix) & filters.me)
async def process_generic_file(_, message):
    prompt = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else "Analyze this file."
    await process_file(message, prompt, "Processing file...")

modules_help["aimage"] = {
    "process [prompt] [reply to any file]*": "Process any file (image, audio, video, PDF, or document).",
  }
