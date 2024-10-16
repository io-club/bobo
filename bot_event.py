import asyncio
import multiprocessing
from pathlib import Path
import threading
import config
from telethon import TelegramClient, events


bot = TelegramClient(
    Path("tgapi.bot.session"),
    config.api_id,
    config.api_hash,
    proxy=("http", "127.0.0.1", 7890),
).start(bot_token=config.bot_token)


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Send a message when the command /start is issued."""
    await event.respond("Hi!")
    raise events.StopPropagation


@bot.on(events.NewMessage)
async def echo(event):
    """Echo the user message."""
    await event.respond(event.text)


if __name__ == "__main__":
    t = multiprocessing.Process(target=lambda: bot.run_until_disconnected())
    t.start()
    t.join()
