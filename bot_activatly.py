import asyncio
from pathlib import Path
import threading
import config
from telethon import TelegramClient, events


bot = TelegramClient(
    Path("tgapi.bot.session"),
    config.api_id,
    config.api_hash,
    proxy=("http", "127.0.0.1", 7890),
)


async def bot_handler(bot: TelegramClient):
    await bot.send_message(config.demo191, "bot")


async def bot_main():
    await bot.start(bot_token=config.bot_token)
    async with bot:
        await bot_handler(bot)


if __name__ == "__main__":
    t = threading.Thread(target=lambda: asyncio.run(bot_main()))
    t.start()
    t.join()
