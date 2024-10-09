from pathlib import Path
from telethon import TelegramClient

import logging

import config

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.WARNING
)

# 创建客户端，指定 session_name
client = TelegramClient(
    Path("tgapi.session"),
    config.api_id,
    config.api_hash,
    proxy=("http", "127.0.0.1", 7890),
)


# 获取所有 channel
async def get_all_channel():
    d = {}
    async for dialog in client.iter_dialogs():
        d[dialog.name] = dialog.id
    print(d)


async def main():
    # 如果 session 文件存在，client.start() 会自动使用它
    await client.start()
    await get_all_channel()


# 运行主函数
client.loop.run_until_complete(main())
