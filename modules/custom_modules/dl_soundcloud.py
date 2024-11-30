import aiohttp
import os
import re
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress

BASE_URL = "https://api.agatz.xyz/api"

@Client.on_message(filters.command(["soundcloud", "sc"], prefix) & filters.me)
async def soundcloud_music(client: Client, message: Message):
    chat_id = message.chat.id

    # Extract query from message or reply
    query = (
        message.text.split(maxsplit=1)[1].strip()
        if len(message.command) > 1 else
        message.reply_to_message.text.strip()
        if message.reply_to_message else None
    )
    
    if not query:
        await message.edit(f"<b>Usage:</b> <code>{prefix}soundcloud [song name]</code>")
        return

    status_message = await message.edit_text(f"<code>Searching for '{query}' on SoundCloud...</code>")

    async with aiohttp.ClientSession() as session:
        # SoundCloud Search API
        search_response = await session.get(f"{BASE_URL}/soundcloud?message={query}")
        if search_response.status != 200:
            await status_message.edit("<code>Failed to fetch search results. Please try again later.</code>")
            return
        search_result = await search_response.json()

        if not (search_result.get("status") == 200 and search_result.get("data")):
            await status_message.edit(f"<code>No results found for '{query}'</code>")
            return

        # Select the first song
        song_data = search_result["data"][0]
        song_title = song_data["judul"]
        song_link = song_data["link"]

        await status_message.edit(f"<code>Found: {song_title}</code>\n<code>Fetching download link...</code>")

        # SoundCloud Download API
        download_response = await session.get(f"{BASE_URL}/soundclouddl?url={song_link}")
        if download_response.status != 200:
            await status_message.edit("<code>Failed to fetch download link. Please try again later.</code>")
            return
        download_result = await download_response.json()

        if not (download_result.get("status") == 200 and download_result.get("data")):
            await status_message.edit("<code>Failed to fetch download link for the song.</code>")
            return

        # Extract song details
        song_download_link = download_result["data"]["download"]
        song_title = download_result["data"]["title"]
        song_thumbnail = download_result["data"]["thumbnail"]

        # Sanitize file names
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", song_title)
        thumbnail_path = f"{sanitized_title}.jpg"
        song_path = f"{sanitized_title}.mp3"

        await status_message.edit(f"<code>Downloading {song_title}...</code>")

        # Download thumbnail and song
        async with session.get(song_thumbnail) as thumb_response:
            with open(thumbnail_path, "wb") as thumb_file:
                thumb_file.write(await thumb_response.read())

        async with session.get(song_download_link) as song_response:
            with open(song_path, "wb") as song_file:
                song_file.write(await song_response.read())

    await status_message.edit(f"<code>Uploading {song_title}...</code>")
    c_time = time.time()

    # Upload to Telegram
    await client.send_audio(
        chat_id,
        song_path,
        caption=f"<b>Song Name:</b> {song_title}",
        progress=progress,
        progress_args=(status_message, c_time, f"<code>Uploading {song_title}...</code>"),
        thumb=thumbnail_path
    )

    # Cleanup
    await status_message.delete()
    os.remove(thumbnail_path)
    os.remove(song_path)

modules_help["soundcloud"] = {
    "soundcloud [song name]": "Search, download, and upload songs from SoundCloud"
}
