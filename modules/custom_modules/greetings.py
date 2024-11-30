from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import ChatForwardsRestricted

from utils.misc import modules_help, prefix

# Default time zone offset in hours (e.g., +5 for Asia/Karachi)
DEFAULT_TIME_ZONE_OFFSET = 5

# Predefined greetings
GREETINGS = {
    "morning": [
        "Good morning! 🌞",
        "Good Morning, love ❤️",
        "Morning, and love you",
        "Morning 🌄",
        "Have a good day, love",
    ],
    "night": [
        "Good night! 🌙",
        "Sweet dreams! 💤",
        "Rest well, love",
        "Good night and love you",
        "Take rest, GN love ❤️",
    ],
}


def local_to_utc(local_time: datetime) -> datetime:
    """Converts local time to UTC based on the default time zone offset."""
    return local_time - timedelta(hours=DEFAULT_TIME_ZONE_OFFSET)


def parse_time_and_days(args: list) -> tuple:
    """
    Parses the days and time from the command arguments.
    :param args: List of command arguments.
    :return: Number of days (int) and scheduled time (datetime object).
    """
    days = int(args[1])
    local_time = datetime.strptime(args[2], "%I:%M %p")  # 12-hour format with AM/PM
    now = datetime.now()
    scheduled_time = now.replace(
        hour=local_time.hour, minute=local_time.minute, second=0, microsecond=0
    )
    return days, scheduled_time


async def schedule_greetings(
    client: Client, chat_id: int, messages: list, start_time: datetime, days: int
):
    """
    Schedules greetings in the chat.
    :param client: The Pyrogram client.
    :param chat_id: Target chat ID.
    :param messages: List of predefined messages.
    :param start_time: Time to start scheduling messages (in UTC).
    :param days: Number of days to schedule.
    """
    for day in range(days):
        schedule_date = start_time + timedelta(days=day)
        message_text = messages[day % len(messages)]
        try:
            await client.send_message(
                chat_id=chat_id, text=message_text, schedule_date=schedule_date
            )
        except ChatForwardsRestricted:
            await client.send_message(
                chat_id,
                "<code>Current chat has restricted message copy/forwards. Scheduling failed.</code>",
            )
            return


async def handle_schedule_command(client: Client, message: Message, greeting_type: str):
    """
    Handles scheduling commands for greetings.
    :param client: The Pyrogram client.
    :param message: Incoming command message.
    :param greeting_type: Type of greeting ('morning' or 'night').
    """
    try:
        # Extract command arguments
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            raise ValueError

        # Parse days and time
        days, scheduled_time = parse_time_and_days(args)

        # Convert to UTC and adjust for past times
        start_time_utc = local_to_utc(scheduled_time)
        if start_time_utc < datetime.utcnow():
            start_time_utc += timedelta(days=1)

        # Schedule greetings
        await schedule_greetings(
            client, message.chat.id, GREETINGS[greeting_type], start_time_utc, days
        )

        # Format and send confirmation message
        formatted_time = scheduled_time.strftime("%I:%M %p")
        await message.edit(
            f"<code>Scheduled {greeting_type} greetings for {days} days starting at {formatted_time} (UTC+{DEFAULT_TIME_ZONE_OFFSET}).</code>"
        )
    except ValueError:
        await message.edit(
            f"<code>Invalid format! Use:</code>\n<code>/{greeting_type} <days> <HH:MM AM/PM></code>"
        )


@Client.on_message(filters.command("morning", prefix) & filters.me)
async def schedule_morning(client: Client, message: Message):
    """Schedules morning greetings."""
    await handle_schedule_command(client, message, "morning")


@Client.on_message(filters.command("night", prefix) & filters.me)
async def schedule_night(client: Client, message: Message):
    """Schedules night greetings."""
    await handle_schedule_command(client, message, "night")


# Help information
modules_help["greetings"] = {
    "morning <days> <HH:MM AM/PM>": "Schedules morning greetings for the specified number of days starting today at the given time.",
    "night <days> <HH:MM AM/PM>": "Schedules night greetings for the specified number of days starting today at the given time.",
    "\n<b>Default time zone offset:</b>": f"UTC+{DEFAULT_TIME_ZONE_OFFSET}",
}
