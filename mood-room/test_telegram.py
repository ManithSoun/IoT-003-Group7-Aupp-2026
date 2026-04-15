import asyncio
from telegram import Bot

BOT_TOKEN = "telegram_token"
CHAT_ID = chat_id
THREAD_ID = thread_id

async def send_test():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        message_thread_id=THREAD_ID,
        text="MoodRoom Bot is online and working!"
    )
    print("Message sent successfully!")

asyncio.run(send_test())