import asyncio
from utils.scripts import import_library
from utils.config import cohere_key
from utils.misc import modules_help, prefix
from pyrogram import Client, filters, enums
from pyrogram.types import Message

# Importing and initializing the Cohere client
cohere = import_library("cohere")
co = cohere.ClientV2(api_key=cohere_key)

@Client.on_message(filters.command(["cr", "crplus"], prefix) & filters.me)
async def generate_text(c: Client, message: Message):
    # Extracting prompt from command or reply message
    prompt = (message.text.split(maxsplit=1)[1].strip() 
              if len(message.command) > 1 else message.reply_to_message.text.strip()
              if message.reply_to_message else None)
    
    if not prompt:
        await message.edit_text(f"<b>Usage:</b> <code>{prefix}commandr [prompt/reply to message]</code>")
        return

    await message.edit_text("<code>Umm, lemme think...</code>")

    try:
        # Cohere API call to generate response
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "user", "content": prompt}],
        )
        output = response.message.content[0].text.strip() or "No response generated for the given prompt."

        # Display the final output to the user
        await message.edit_text(f"**Question:** `{prompt}`\n**Answer:** {output}", 
                                parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        await message.edit_text(f"An error occurred: {e}")

# Updating the help dictionary for the module
modules_help["command_r"] = {
    "cr [prompt/reply to message]": "Talk with Command-R Cohere AI model.",
    "crplus [prompt/reply to message]": "Talk with Command-R Cohere AI model."
}
