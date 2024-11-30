import requests
from urllib.parse import quote
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.filters import create
from utils.misc import modules_help, prefix
from utils.db import db

# Google Translate function
def google_translate(query, source_lang="auto", target_lang="en"):
    url = "https://translate.google.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": query
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return "".join([item[0] for item in data[0]])
    else:
        raise Exception("Failed to fetch translation.")

# Custom filter for auto-translation
def auto_translate_filter(_, __, message: Message):
    """Filter to process messages only if translation is enabled for the chat."""
    lang_code = db.get("custom.gtranslate", str(message.chat.id), None)
    return bool(lang_code) and not message.text.startswith(prefix)

auto_translate_filter = create(auto_translate_filter)

# Command to set the language for translation
@Client.on_message(filters.command(["setglang"], prefix))
async def set_language(_, message: Message):
    """Set the preferred language for a chat."""
    if len(message.command) < 2:
        await message.edit(
            "Usage: `setglang <language_code>`\n"
            "Example:\n"
            "`setglang ru` to set Russian."
        )
        return

    lang_code = message.text.split(maxsplit=1)[1].lower()
    db.set("custom.gtranslate", str(message.chat.id), lang_code)
    await message.edit(f"Language for this chat has been set to `{lang_code}`.")

# Command to check or disable auto-translation
@Client.on_message(filters.command(["glang"], prefix))
async def language_status(_, message: Message):
    """Show the current language or turn off auto-translation."""
    chat_id = str(message.chat.id)
    command_text = message.text.strip().lower()

    if command_text == f"{prefix}glang":
        # Display the current language
        lang_code = db.get("custom.gtranslate", chat_id, None)
        if lang_code:
            await message.edit(f"The language for this chat is set to `{lang_code}`.")
        else:
            await message.edit("No language set for this chat. Use `setglang` to set one.")
    elif command_text == f"{prefix}glang off":
        # Turn off translation
        result = db.remove("custom.gtranslate", chat_id)
        if result:
            await message.edit("Auto-translation has been turned off for this chat.")
        else:
            await message.edit("Auto-translation is already disabled for this chat.")
    else:
        await message.edit("Invalid usage. Use `glang` to check the language or `glang off` to turn off auto-translation.")

# Auto-translation of messages
@Client.on_message(filters.text & auto_translate_filter)
async def auto_translate(_, message: Message):
    """Automatically translate and edit messages in chats with a set language."""
    lang_code = db.get("custom.gtranslate", str(message.chat.id), None)
    if not lang_code:
        return  # Skip if no language is set

    try:
        # Use Google Translate for translation
        translated_text = google_translate(message.text, target_lang=lang_code)
        if translated_text.strip() and translated_text != message.text:
            await message.edit(translated_text)
    except Exception as e:
        await message.reply(f"Translation failed: {e}")

# Add module details to help
modules_help["translate_auto"] = {
    "setglang <language_code>": "Set the preferred language for this chat.",
    "glang": "Show the chat's language or use `glang off` to turn off auto-translation.",
    "Auto-translation": "Automatically translates and edits your messages in the chat to the set language."
}
