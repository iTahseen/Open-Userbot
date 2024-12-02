import os
import httpx
from asyncio import sleep
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.db import db

# Default ElevenLabs configuration
DEFAULT_PARAMS = {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default voice ID
    "stability": 0.5,  # Voice stability
    "similarity_boost": 0.7,  # Voice similarity
}

# Generate audio using ElevenLabs API
async def generate_elevenlabs_audio(text: str):
    api_key = db.get("custom.elevenlabs", "api_key")
    if not api_key:
        raise ValueError(f"ElevenLabs `api_key` is not configured. Use `{prefix}set_elevenlabs` to set it.")

    params = {key: db.get("custom.elevenlabs", key, default) for key, default in DEFAULT_PARAMS.items()}

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": params["stability"],
            "similarity_boost": params["similarity_boost"],
        },
    }

    voice_id = params["voice_id"]
    audio_path = "elevenlabs_voice.mp3"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=data,
        )

        if response.status_code == 200:
            with open(audio_path, "wb") as f:
                f.write(response.content)
        else:
            raise ValueError(f"Error from ElevenLabs API: {response.text}")

    return audio_path

# Command: ElevenLabs voice generation
@Client.on_message(filters.command(["elevenlabs", "el"], prefix))
async def elevenlabs_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit_text(
            "**Usage:**\n"
            f"`{prefix}elevenlabs <text>`\n\n"
            "**Example:**\n"
            f"`{prefix}elevenlabs Hello, how are you?`",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        return

    text = " ".join(message.command[1:]).strip()
    await message.delete()

    try:
        audio_path = await generate_elevenlabs_audio(text)
        if audio_path:
            await client.send_voice(chat_id=message.chat.id, voice=audio_path)
            os.remove(audio_path)
    except Exception as e:
        await client.send_message(message.chat.id, f"Error: {e}", parse_mode=enums.ParseMode.MARKDOWN)

# Command: Set or view ElevenLabs configuration
@Client.on_message(filters.command(["set_elevenlabs", "set_el"], prefix) & filters.me)
async def set_elevenlabs_config(_, message: Message):
    args = message.command
    if len(args) == 1:
        current_values = {key: db.get("custom.elevenlabs", key, default) for key, default in DEFAULT_PARAMS.items()}
        api_key = db.get("custom.elevenlabs", "api_key", "Not Set")
        response = (
            "**ElevenLabs Configuration:**\n"
            f"- **api_key**: `{api_key}`\n"
            + "\n".join([f"- **{key}**: `{value}`" for key, value in current_values.items()])
            + "\n\n**Usage:**\n"
            f"`{prefix}set_elevenlabs <key> <value>`\n"
            "**Keys:** `api_key`, `voice_id`, `stability`, `similarity_boost`"
        )
        await message.edit_text(response, parse_mode=enums.ParseMode.MARKDOWN)
        return

    if len(args) < 3:
        await message.edit_text(
            "**Invalid Usage:**\n"
            f"`{prefix}set_elevenlabs <key> <value>`\n"
            f"Use `{prefix}set_elevenlabs` to see the current configuration.",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        return

    key = args[1].lower()
    value = " ".join(args[2:])
    if key not in ["api_key", *DEFAULT_PARAMS.keys()]:
        await message.edit_text(
            "**Invalid Key:**\n"
            "Allowed keys are: `api_key`, `voice_id`, `stability`, `similarity_boost`.",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        return

    # Convert to appropriate types
    if key in ["stability", "similarity_boost"]:
        try:
            value = float(value)
        except ValueError:
            await message.edit_text(f"`{key}` must be a numeric value (float).", parse_mode=enums.ParseMode.MARKDOWN)
            return

    db.set("custom.elevenlabs", key, value)
    await message.edit_text(
        f"**ElevenLabs {key} updated successfully!**\nNew value: `{value}`",
        parse_mode=enums.ParseMode.MARKDOWN,
    )

# Module help
modules_help["elevenlabs"] = {
    "el [text]*": "Generate a voice message using ElevenLabs API.",
    "set_el": "View or update ElevenLabs configuration parameters.",
    "set_el <key> <value>": "Set a specific ElevenLabs parameter.",
                                    }
