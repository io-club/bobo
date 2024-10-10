import asyncio
import json
from pathlib import Path
import random
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ForwardMessagesRequest
import config

from openai import OpenAI

client = TelegramClient(
    Path("tgapi.session"),
    config.api_id,
    config.api_hash,
    proxy=("http", "127.0.0.1", 7890),
)


class AI:
    client = None

    class DialogManager:
        def __init__(self) -> None:
            self.dialog = {}
            self.dialog_local = {}

        def update_prompt(self, channel_id, prompt):
            channel_id = str(channel_id)
            msg = {"user_id": 0, "role": "system", "content": prompt}
            if channel_id not in self.dialog:
                self.dialog[channel_id] = [msg]
            elif len(self.dialog[channel_id]) == 0:
                self.dialog[channel_id].append(msg)
            else:
                self.dialog[channel_id][0]["content"] = prompt

        def append_and_get(self, channel_id, user_id, text, prompt=None, res=False):
            channel_id = str(channel_id)
            if channel_id not in self.dialog:
                self.dialog[channel_id] = []
                if prompt is not None:
                    self.dialog[channel_id].append(
                        {
                            "user_id": 0,
                            "role": "system",
                            "content": prompt,
                        }
                    )

            if len(self.dialog[channel_id]) >= 10:
                del self.dialog[channel_id][0 if prompt is None else 1]

            self.dialog[channel_id].append(
                {
                    "user_id": str(user_id) if not res else 0,
                    "role": "user" if not res else "system",
                    "content": text,
                }
            )
            return self.dialog[channel_id]

        def append_and_get_by_user(
            self, channel_id, user_id, text, prompt=None, res=False
        ):
            channel_id = str(channel_id)
            user_id = str(user_id)
            if channel_id not in self.dialog_local:
                self.dialog_local[channel_id] = {}
            if user_id not in self.dialog_local[channel_id]:
                self.dialog_local[channel_id][user_id] = []
                if prompt is not None:
                    self.dialog_local[channel_id][user_id].append(
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    )

            if len(self.dialog_local[channel_id][user_id]) >= 10:
                del self.dialog_local[channel_id][user_id][0 if prompt is None else 1]

            self.dialog_local[channel_id][user_id].append(
                {
                    "role": "user",
                    "content": text,
                }
            )
            return self.dialog_local[channel_id][user_id]

        def clear(self, channel_id):
            del self.dialog[channel_id]

        def clear_by_user(self, channel_id, usre_id):
            del self.dialog_local[channel_id][usre_id]

    def __init__(self) -> None:
        self.dialog = self.DialogManager()

    def get_client(self):
        if not self.client:
            self.client = OpenAI(
                api_key=config.openai_api_key,
                base_url=config.openai_base_url,
            )
        return self.client

    def _ask(self, messages):
        client = self.get_client()
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )
            res = response.choices[0].message.content
            print("res: " + res)
            return res
        except Exception as e:
            print(e)
            self.client = None
            return "失败"

    def ask(self, text):
        print("req", text)
        return self._ask(
            [
                {
                    "role": "user",
                    "content": f"""{text}""",
                }
            ]
        )

    def if_fruit(self, text: str):
        try:
            response = self.ask(
                f"""下面一段话包含了购物推荐信息，判断是否是现摘水果 或者 特别便宜的小零食
- 不要以水果为原料制作的产品
- 不要果汁
返回值使用标准 json 格式，不要带有 markdown 格式，需要能被 python json.loads 成功解析，例如：
{{
    "is_fruit": true,
    "reason": "这里解释原因，简洁一点"
}}
---
{text}"""
            )
            return {"ai": True, **json.loads(response)}
        except Exception as e:
            print(e)
            self.client = None
            keywords = [
                # 水果
                "橘",
                "橙",
                "芒",
                "柿子",
                "苹果",
                "香蕉",
                "葡萄",
                "桃",
                "梨",
                "菠萝"
                # 小零食
                "趣多多",
            ]
            for keyword in keywords:
                if keyword in text:
                    return {"ai": False, "is_fruit": True}
            return {"ai": False, "is_fruit": False}


ai = AI()


@client.on(events.NewMessage(incoming=True, chats=[config.线报]))
async def my_event_handler(event):
    print("Message:", event.text)

    res = ai.if_fruit(event.text)
    if res["is_fruit"]:
        # 转发消息到指定的群组和主题
        # await client.forward_messages(
        #     address.IO群, event.message.id, from_peer=event.chat_id, slice=True
        # )
        # 使用下面的 api 是因为上面的方法不支持指定 topic
        await client(
            ForwardMessagesRequest(
                from_peer=event.chat_id,
                id=[event.message.id],
                to_peer=config.IO群,
                silent=True,
                top_msg_id=config.TOPIC_DICT["便宜水果"],  # 指定 topic
            )
        )

        use_ai = res["ai"]
        if not use_ai:
            await client.send_message(config.IO群, f"useAI: {use_ai}")
        else:
            reason = res["reason"]
            await client.send_message(
                config.IO群,
                f"原因: {reason}",
                reply_to=event.message.id,
                link_preview=False,
            )

    await client.send_read_acknowledge(
        event.chat_id, [event.message.id], max_id=event.message.id
    )


@client.on(events.NewMessage(incoming=True, chats=[config.自己], pattern="/?rand"))
@client.on(events.NewMessage(outgoing=True, pattern="/?rand"))
async def rand_from_other_send(event):
    print("--- rand_from_other_send")
    rdm = random.randint(1, 10)
    m = await event.respond(str(rdm) + " (5秒后自动删除)")
    await asyncio.sleep(5)
    await client.delete_messages(event.chat_id, [event.message.id, m.id])


@client.on(
    events.NewMessage(
        incoming=True,
        pattern="/?ask.*",
        chats=[config.IO群, config.demo191, config.trdthg177],
    )
)
async def ask_from_other_send(event):
    print("--- ask_from_other_send")
    if event.text == "clear":
        ai.dialog.clear(event.chat_id)
    messages = ai.dialog.append_and_get(event.peer_id, event.text)
    res = ai._ask(messages)
    ai.dialog.append_and_get(event.chat_id, res, res=True)
    await event.respond(res)


@client.on(
    events.NewMessage(
        incoming=True, chats=[config.IO群, config.demo191, config.trdthg177]
    )
)
async def cat_from_stuff_send(event):
    if event.text.startswith("prompt"):
        ai.dialog.update_prompt(event.peer_id, event.text[6:])
        return

    print("--- cat_from_stuff_send")
    messages = ai.dialog.append_and_get(
        event.peer_id,
        event.from_id,
        event.text,
        prompt=config.cat_prompt,
        res=True,
    )

    message = "\n".join(
        [
            "id:"
            + str(id)
            + ", user_id:"
            + str(msg["user_id"])
            + ":"
            + msg["content"]
            + "\n"
            for (id, msg) in enumerate(messages)
        ]
    )
    print(message)
    res = ai._ask(
        [
            {
                "role": "system",
                "content": """以下是一段对话，里面包含多个角色
- id 表示对话编号
- user_id 表示用户，其中 user_id 为 0 的表示你，其他为普通用户

请仔细分辨这段对话中的最后一句话，是对你的提问，还是对其他用户的提问
- @xxx 的一般是和其他用户的交流，你不用回复，但是要按情况
- 如果提问没有主语，请结合上下文分析，没有上下文你可以回复
- 心情好你也可以随意接话，可以适当积极一些
如果是对你的提问 请回复 1， 如果不是请回复 0，只回复这个数字即可，不要带任何其他内容:\n"""
                + message,
            }
        ]
    )
    if res == "0":
        print("不是问题")
        return

    print(messages)
    res = ai._ask(messages)
    ai.dialog.append_and_get(event.peer_id, event.from_id, res, True)

    m = await client.send_message(
        event.chat_id,
        res + " (10秒后自动删除)",
        reply_to=event.message.id,
        silent=True,
    )

    # 等待用户是否保留
    await asyncio.sleep(10)

    # 检查是否有 reaction，因为只有 bot api 支持发送按钮
    m = await client.get_messages(event.chat_id, ids=m.id)
    if m is not None and m.reactions is not None and len(m.reactions.results) > 0:
        # 有了就不删除，并把结尾的 (10s 后自动删除去掉)
        await client.edit_message(event.chat_id, m, res)
    else:
        # 没有就删除
        await client.delete_messages(event.chat_id, [m.id])


if __name__ == "__main__":
    client.start()
    print("启动了")
    client.run_until_disconnected()
