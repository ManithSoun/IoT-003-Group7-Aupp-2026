import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import requests

BOT_TOKEN = "tele_token"
CHAT_ID = chat_id
THREAD_ID = thread_id


FLASK_URL = "http://localhost:5001"
ESP32_URL = "http://192.168.0.107/command"

current_emotion = "neutral"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "MoodRoom Bot is alive!\n"
        "Commands:\n"
        "/capture - force emotion detection\n"
        "/status - check current room state\n"
        "/play happy|sad|angry|fear|surprise\n"
        "/room off - turn everything off\n"
        "/help - show commands"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Current emotion: {current_emotion}\n"
        f"Room state: {get_room_state(current_emotion)}"
    )

async def capture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Forcing capture... Please wait!")
    try:
        response = requests.get(f"{FLASK_URL}/capture", timeout=5)
        emotion = response.text
        await update.message.reply_text(f"Detected: {emotion}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /play happy | sad | angry | fear | surprise"
        )
        return
    emotion = context.args[0].lower()
    valid = ["happy", "sad", "angry", "fear", "surprise", "neutral"]
    if emotion not in valid:
        await update.message.reply_text(f"Invalid emotion! Choose from: {valid}")
        return
    try:
        requests.get(
            f"{ESP32_URL}",
            params={"emotion": emotion},
            timeout=2
        )
        await update.message.reply_text(f"Switched to {emotion} mode!")
    except Exception as e:
        await update.message.reply_text(f"ESP32 not reachable: {e}")

async def room_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        requests.get(
            f"{ESP32_URL}",
            params={"emotion": "off"},
            timeout=2
        )
        await update.message.reply_text("Room turned off!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/capture - force photo + detection\n"
        "/status - current emotion + room state\n"
        "/play [emotion] - switch mood manually\n"
        "/room off - turn everything off\n"
        "/help - show this message"
    )

def get_room_state(emotion):
    states = {
        "happy":    "Yellow LED | Fan slow | Upbeat playlist",
        "sad":      "Blue LED | Fan slow | Lo-fi playlist",
        "angry":    "Red LED | Fan fast | Calm playlist",
        "fear":     "Purple LED | Fan fast | Soothing playlist",
        "surprise": "White flash | Fan medium | Upbeat playlist",
        "neutral":  "Soft white | Fan slow | Chill playlist",
        "off":      "Everything OFF",
    }
    return states.get(emotion, "Unknown state")

async def send_notification(emotion):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        message_thread_id=THREAD_ID,
        text=f"Emotion changed to: {emotion}\n{get_room_state(emotion)}"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("capture", capture))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("room", room_off))
    app.add_handler(CommandHandler("help", help_cmd))
    print("MoodRoom Telegram bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
