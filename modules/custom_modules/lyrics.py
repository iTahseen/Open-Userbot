import requests
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

def format_lyrics_result(data):
    return f"🎵 **{data['fullTitle']}** by {data['artist']}\n\n{data['lyrics']}"

async def search_lyrics(api_url, format_function, message, query):
    await message.edit("Searching...")
    url = f"{api_url}{query}"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            
            if isinstance(data, list):
                result = format_function(data)
            elif isinstance(data, dict) and "data" in data:
                result = format_function(data["data"])
            else:
                result = "No data found or unexpected format."

            await message.edit(result, parse_mode=enums.ParseMode.MARKDOWN)
        except (ValueError, KeyError, TypeError) as e:
            await message.edit(f"An error occurred while processing the data: {str(e)}")
    else:
        await message.edit("An error occurred, please try again later.")

@Client.on_message(filters.command(["lyrics"], prefix) & filters.me)
async def lyrics_search(client, message: Message):
    query = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else message.reply_to_message.text
    if not query:
        await message.edit("Usage: lyrics <song name>")
        return
    await search_lyrics("https://deliriussapi-oficial.vercel.app/search/letra?query=", format_lyrics_result, message, query)

modules_help["lyrics"] = {
  "lyrics [song name]*": "Get the lyrics of a song"
}
