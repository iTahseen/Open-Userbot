import json
import requests
import time
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress


@Client.on_message(filters.command(["sdl", "spotify"], prefix) & filters.me)
async def spotify_download(client: Client, message: Message):
    chat_id = message.chat.id
    # Extract query from message
    if len(message.command) > 1:
        query = message.text.split(maxsplit=1)[1]
    elif message.reply_to_message:
        query = message.reply_to_message.text.strip()
    else:
        await message.edit(
            f"<b>Usage:</b> <code>{prefix}spt [song name]</code>"
        )
        return

    # Notify the user that the search is starting
    ms = await message.edit_text(f"<code>Searching for {query} on Spotify...</code>")

    # Perform Spotify search
    search_url = f"https://deliriussapi-oficial.vercel.app/search/spotify?q={query}&limit=2"
    search_response = requests.get(search_url)
    search_result = search_response.json()

    # Check if the search was successful
    if search_result['status'] and search_result['data']:
        song_details = search_result['data'][0]
        song_name = song_details['title']
        song_artist = song_details['artist']
        song_thumb = song_details['image']
        song_url = song_details['url']

        # Notify the user that the song was found
        await ms.edit_text(f"<code>Found: {song_name} by {song_artist}</code>\n<code>Fetching download link...</code>")

        # Get the download link
        download_url = f"https://deliriussapi-oficial.vercel.app/download/spotifydlv3?url={song_url}"
        download_response = requests.get(download_url)
        download_result = download_response.json()

        if download_result['status']:
            song_download_link = download_result['data']['url']
            song_name = download_result['data']['title']
            song_artist = download_result['data']['author']
            song_thumb = download_result['data']['image']

            # Notify the user that the song is being downloaded
            await ms.edit_text(f"<code>Downloading {song_name}...</code>")

            # Download thumbnail if available
            thumb_path = None
            if song_thumb:
                thumb_response = requests.get(song_thumb)
                thumb_path = f"{song_name}.jpg"
                with open(thumb_path, "wb") as f:
                    f.write(thumb_response.content)

            # Download the song
            song_path = f"{song_name}.mp3"
            song_response = requests.get(song_download_link)
            with open(song_path, "wb") as f:
                f.write(song_response.content)

            # Notify the user that the song is being uploaded
            await ms.edit_text(f"<code>Uploading {song_name}...</code>")
            c_time = time.time()

            # Upload the song to Telegram
            await client.send_audio(
                chat_id,
                song_path,
                caption=f"<b>Song Name:</b> {song_name}\n<b>Artist:</b> {song_artist}",
                progress=progress,
                progress_args=(ms, c_time, f"<code>Uploading {song_name}...</code>"),
                thumb=thumb_path,
            )

            # Clean up
            await ms.delete()
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            if os.path.exists(song_path):
                os.remove(song_path)
        else:
            await ms.edit_text(f"<code>Failed to fetch download link for {song_name}</code>")
    else:
        await ms.edit_text(f"<code>No results found for {query}</code>")


modules_help["spotify"] = {
    "spotify [song name]": "Search, download, and upload songs from Spotify"
}
