from telethon import TelegramClient, errors

# 输入您的 API ID 和 API Hash
# 可以前往 telegram 官网注册获取，也可以使用下面的 nekogram 的
api_id = "1391584"
api_hash = "355c91550b0d658cfb7ff89dcf91a08c"

# 输入您的电话号码
phone_number = "+86xxxxxxxxxx"  # 替换为您的电话号码

# 创建客户端
client = TelegramClient(
    "tgapi.session", api_id, api_hash, proxy=("http", "127.0.0.1", 7890)
)


async def main():
    # 登录并启动客户端
    await client.start(phone=phone_number)

    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        code = input("请输入您收到的验证码：")
        try:
            await client.sign_in(phone_number, code)
        except errors.SessionPasswordNeededError:
            password = input("请输入两步验证密码：")
            await client.sign_in(password=password)


# 运行主函数
client.loop.run_until_complete(main())
