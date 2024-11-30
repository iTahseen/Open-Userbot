import json
import requests
import time
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress

@Client.on_message(filters.command(["amusic", "applemusic"], prefix) & filters.me)
async def apple_music(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        query = message.text.split(maxsplit=1)[1]
    elif message.reply_to_message:
        query = message.reply_to_message.text
    else:
        await message.edit(
            f"<b>Usage:</b> <code>{prefix}amusic [song name]</code>"
        )
        return
    
    ms = await message.edit_text(f"<code>Searching for {query} on Apple Music...</code>")
    
    search_url = f"https://deliriussapi-oficial.vercel.app/search/applemusicv2?query={query}"
    search_response = requests.get(search_url)
    search_result = search_response.json()

    if search_result['status'] and search_result['data']:
        song_details = search_result['data'][0]
        song_name = song_details['title']
        song_artist = song_details['artist']
        song_thumb = song_details['image']
        song_url = song_details['url']

        await ms.edit_text(f"<code>Found: {song_name} by {song_artist}</code>\n<code>Fetching download link...</code>")

        download_url = f"https://deliriussapi-oficial.vercel.app/download/applemusicdl?url={song_url}"
        download_response = requests.get(download_url)
        download_result = download_response.json()

        if download_result['status']:
            song_download_link = download_result['data']['download']
            song_name = download_result['data']['name']
            song_thumb = download_result['data']['image']

            await ms.edit_text(f"<code>Downloading {song_name}...</code>")

            thumb_response = requests.get(song_thumb)
            with open(f"{song_name}.jpg", "wb") as f:
                f.write(thumb_response.content)

            song_response = requests.get(song_download_link)
            with open(f"{song_name}.mp3", "wb") as f:
                f.write(song_response.content)

            await ms.edit_text(f"<code>Uploading {song_name}...</code>")
            c_time = time.time()
            
            await client.send_audio(
                chat_id,
                f"{song_name}.mp3",
                caption=f"<b>Song Name:</b> {song_name}\n<b>Artist:</b> {song_artist}",
                progress=progress,
                progress_args=(ms, c_time, f"<code>Uploading {song_name}...</code>"),
                thumb=f"{song_name}.jpg"
            )
            
            await ms.delete()
            if os.path.exists(f"{song_name}.jpg"):
                os.remove(f"{song_name}.jpg")
            if os.path.exists(f"{song_name}.mp3"):
                os.remove(f"{song_name}.mp3")
        else:
            await ms.edit_text(f"<code>Failed to fetch download link for {song_name}</code>")
    else:
        await ms.edit_text(f"<code>No results found for {query}</code>")

modules_help["applemusic"] = {
    "amusic": "search, download and upload songs from Apple Music"
}
