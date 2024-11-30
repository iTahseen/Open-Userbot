import requests
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.db import db

NEW_GEMINI_URL = (
    "http://api-samirxz.onrender.com/Gemini-apu?text={query}&cookies={cookie}"
)

async def fetch_response(url: str, query: str, message: Message):
    response_msg = await (
        message.edit("<code>Thinking...</code>")
        if message.from_user.is_self
        else message.reply("Thinking...")
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        response_text = data.get("text", "No answer found.")
        images = data.get("images", [])
        response_content = f"**Question:**\n{query}\n**Answer:**\n{response_text}"
        await response_msg.edit_text(
            response_content, parse_mode=enums.ParseMode.MARKDOWN
        )
        if images:
            await message.reply_photo(images[0], caption=f"Prompt: {query}")
    except (requests.exceptions.RequestException, ValueError):
        await response_msg.edit_text(
            "Error: Unable to retrieve data or invalid response format."
        )

@Client.on_message(filters.command(["set_askcookie"], prefix))
async def set_askcookie(_, message: Message):
    if len(message.command) < 2:
        usage_message = "Usage: `set_askcookie <cookie>`"
        if message.from_user.is_self:
            await message.edit(usage_message)
        else:
            await message.reply(usage_message)
        return
    cookie = message.text.split(maxsplit=1)[1]
    db.set("custom.askck", "cookie", cookie)
    await message.edit("Cookie set successfully.")

@Client.on_message(filters.command(["ai"], prefix))
async def gemini_image(_, message: Message):
    if len(message.command) < 2:
        usage_message = "Usage: `ai <query>`"
        if message.from_user.is_self:
            await message.edit(usage_message)
        else:
            await message.reply(usage_message)
        return
    query = " ".join(message.command[1:])
    cookie = db.get("custom.askck", "cookie", None)
    if cookie:
        url = NEW_GEMINI_URL.format(query=query, cookie=cookie)
    else:
        return await message.edit("No cookie set. Use `set_askcookie` to set one.")
    await fetch_response(url, query, message)


modules_help["ask"] = {
    "ai [query]*": "Ask anything to Gemini web",
}
