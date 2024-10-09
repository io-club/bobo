import asyncio
from pathlib import Path
from telethon import TelegramClient, sync
from telethon.tl.functions.channels import GetForumTopicsRequest

import config

group_id = -1001714492898

client = TelegramClient(
    Path("tgapi.session"),
    config.api_id,
    config.api_hash,
    proxy=("http", "127.0.0.1", 7890),
)


async def get_topics():
    try:
        topics = []
        date, offset, offset_topic, total = 0, 0, 0, 0
        while True:
            r = await client(
                GetForumTopicsRequest(
                    channel=group_id,
                    offset_date=date,
                    offset_id=offset,
                    offset_topic=offset_topic,
                    limit=100,
                )
            )
            if not total:
                total = r.count
            topic_list = r.topics
            if not topic_list or len(topics) >= total:
                break

            topics.extend(topic_list)
            last = topic_list[-1]

            offset_topic, offset = last.id, last.top_message
            date = {m.id: m.date for m in r.messages}.get(offset, 0)

        return total, topics
    except Exception as e:
        print(f"Errore: {type(e).__name__}: {e}")
        return None, None


async def main():
    await client.start()
    total, topics = await get_topics()
    if topics:
        print("Lista dei topic presenti nel supergruppo:")
        print("Total topics:", total)
        for i, topic in enumerate(topics, start=1):
            print(f"{i} - ID: {topic.id} — {topic.title}")
    else:
        print("The supergroup contains no topic information.")


if __name__ == "__main__":
    asyncio.run(main())
