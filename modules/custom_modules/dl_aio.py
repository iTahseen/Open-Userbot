import json
import requests
import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress

API_URL = "https://bk9.fun/download/alldownload?url="

@Client.on_message(filters.command(["aio", "aiol"], prefix))
async def aio_downloader(client: Client, message: Message):
    chat_id = message.chat.id
    command = message.command[0]
    quality = "high" if command == "aio" else "low"
    
    if len(message.command) > 1:
        video_url = message.text.split(maxsplit=1)[1].strip()
    elif message.reply_to_message:
        video_url = message.reply_to_message.text.strip()
    else:
        usage_msg = f"<b>Usage:</b> <code>{prefix}{command} [video link]</code>"
        if message.from_user.id == (await client.get_me()).id:
            await message.edit(usage_msg)
        else:
            await message.reply(usage_msg)
        return
        
    ms = await (message.edit_text if message.from_user.id == (await client.get_me()).id else message.reply_text)(
        f"<code>Fetching video details...</code>"
    )
    
    api_response = requests.get(f"{API_URL}{video_url}")
    if api_response.status_code != 200:
        await ms.edit_text(f"<code>Failed to fetch video details. API Error.</code>")
        return
    
    try:
        video_data = api_response.json()
        if not video_data.get("status"):
            await ms.edit_text(f"<code>No video found for the provided link.</code>")
            return
        
        video_title = video_data["BK9"]["title"]
        download_url = video_data["BK9"][quality]

        await ms.edit_text(f"<code>Downloading {quality}-quality video...</code>")
        
        video_response = requests.get(download_url, stream=True)
        if video_response.status_code != 200:
            await ms.edit_text(f"<code>Failed to download video. Error occurred.</code>")
            return

        video_file = f"{video_title[:50].strip()}.mp4"
        with open(video_file, "wb") as f:
            for chunk in video_response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        c_time = time.time()
        await ms.edit_text(f"<code>Uploading {quality}-quality video...</code>")
        await client.send_video(
            chat_id,
            video=video_file,
            caption=f"<b>Title:</b> {video_title}\n<b>Quality:</b> {quality.capitalize()}",
            progress=progress,
            progress_args=(ms, c_time, f"<code>Uploading {quality}-quality video...</code>")
        )

        await ms.delete()

        if os.path.exists(video_file):
            os.remove(video_file)

    except json.JSONDecodeError:
        await ms.edit_text(f"<code>Invalid response from the API.</code>")
    except Exception as e:
        await ms.edit_text(f"<code>Error:</code> {str(e)}")


modules_help["aio_downloader"] = {
    "aio [video link]": "Download high-quality video from the provided link",
    "aiol [video link]": "Download low-quality video from the provided link",
}
