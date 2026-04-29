import asyncio

from telegram import Bot

async def test():

    bot = Bot(token='8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA')

    await bot.send_message(

        chat_id=-1003859247655,

        message_thread_id=1304,

        text='MoodRoom is online! '

    )

    print('Telegram works!')

asyncio.run(test())
