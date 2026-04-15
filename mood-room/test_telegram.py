import asyncio
from telegram import Bot

BOT_TOKEN = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
CHAT_ID = -1003859247655
THREAD_ID = 1304

async def send_test():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        message_thread_id=THREAD_ID,
        text="MoodRoom Bot is online and working!"
    )
    print("Message sent successfully!")

asyncio.run(send_test())