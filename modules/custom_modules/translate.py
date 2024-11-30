import requests
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# API endpoint
TRANSLATE_API = "https://deliriussapi-oficial.vercel.app/tools/translate?text={query}&language=en"

@Client.on_message(filters.command(["tr"], prefix))
async def translate_text(client, message: Message):
    # Extract query from the command or replied message
    query = " ".join(message.command[1:]).strip()
    if not query and message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()
    
    if not query:
        # Send usage instructions if no query is provided
        usage_message = "Usage: `tr <text>`\nOr reply to a message with `tr` to translate it."
        await message.edit(usage_message) if message.from_user.is_self else await message.reply(usage_message)
        return

    # Indicate that the bot is processing the request
    processing_message = await (message.edit("Translating...") if message.from_user.is_self else message.reply("Translating..."))
    
    try:
        # Call the translation API
        response = requests.get(TRANSLATE_API.format(query=query))
        response.raise_for_status()
        data = response.json()

        # Extract translated text
        translated_text = data.get("data", "No translation found.")

        # Send the translation result
        await processing_message.edit(f"{translated_text}", parse_mode=enums.ParseMode.MARKDOWN)
    except requests.exceptions.RequestException:
        await processing_message.edit("Failed to translate the text. Please try again later.")
    except ValueError:
        await processing_message.edit("Invalid response received from the translation API.")

# Add the command to the modules help
modules_help["translate"] = {
    "tr <text>": "Translate the provided text to English."
}
