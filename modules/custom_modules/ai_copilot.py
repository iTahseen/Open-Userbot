import requests
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# API URL
COPILOT_API_URL = "https://deliriussapi-oficial.vercel.app/ia/bingia?query="

async def fetch_copilot_response(query: str, message: Message, reply=False):
    """Fetch response from the Copilot API and send it back to the user."""
    response_msg = await message.reply("Thinking...") if reply else await message.edit("Thinking...")
    try:
        # Make a GET request to the API
        response = requests.get(f"{COPILOT_API_URL}{query}")
        response.raise_for_status()
        data = response.json()

        # Extract the result
        result_text = data.get("data", "No response found.")
        response_content = f"**Prompt:**\n{query}\n**Response:**\n{result_text}"

        # Edit the appropriate message with the result
        if reply:
            await response_msg.edit_text(response_content, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.edit(response_content, parse_mode=enums.ParseMode.MARKDOWN)
    except requests.exceptions.RequestException:
        # Handle API errors gracefully
        error_msg = "An error occurred while connecting to the API. Please try again later."
        if reply:
            await response_msg.edit_text(error_msg)
        else:
            await message.edit(error_msg)

@Client.on_message(filters.command(["copilot"], prefix))
async def copilot_v2(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: `copilot <query>`")
        return
    query = " ".join(message.command[1:]).strip()
    await fetch_copilot_response(query, message, reply=not message.from_user.is_self)

# Add the command to modules_help
modules_help["copilot"] = {
    "copilot [query]*": "Ask anything to Copilot AI (v2)."
}
