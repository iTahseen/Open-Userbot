import requests
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# API URL
GPT_API_URL = "https://deliriussapi-oficial.vercel.app/ia/gptweb?text="

async def fetch_gpt_response(query: str, message: Message, is_self: bool):
    """Fetch a response from the GPT API and send it to the user."""
    # Display a loading message
    response_msg = await (message.edit("Thinking...") if is_self else message.reply("Thinking..."))
    
    try:
        # Send the API request
        response = requests.get(f"{GPT_API_URL}{query.strip()}")
        response.raise_for_status()
        data = response.json()

        # Extract and format the response
        if data.get("status", False):
            gpt_response = data.get("data", "No response found.")
            formatted_response = f"**Prompt:**\n{query}\n**Response:**\n{gpt_response}"
        else:
            formatted_response = "Failed to fetch a response. Please try again."

        # Send the formatted response
        await response_msg.edit_text(formatted_response, parse_mode=enums.ParseMode.MARKDOWN)
    except requests.exceptions.RequestException:
        await response_msg.edit_text("An error occurred while connecting to the API. Please try again later.")
    except Exception:
        await response_msg.edit_text("An unexpected error occurred. Please try again.")

@Client.on_message(filters.command("gpt", prefix))
async def gpt_command(client: Client, message: Message):
    """Handle the GPT command."""
    if len(message.command) < 2:
        await message.reply("Usage: `gpt <query>`")
        return

    # Extract the query from the command
    query = " ".join(message.command[1:])

    # Fetch and send the GPT response
    await fetch_gpt_response(query, message, message.from_user.is_self)

# Update module help
modules_help["gpt"] = {
    "gpt [query]*": "Ask anything to GPT (via custom API)",
}
