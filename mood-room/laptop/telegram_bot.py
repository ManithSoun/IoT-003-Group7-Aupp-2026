import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import paho.mqtt.client as mqtt_lib
import requests

BOT_TOKEN     = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
CHAT_ID       = -1003859247655
THREAD_ID     = 1304
MQTT_BROKER   = "broker.hivemq.com"
TOPIC_EMOTION = "moodroom/emotion"
TOPIC_PIR     = "moodroom/pir"
TOPIC_STATUS  = "moodroom/status"
FLASK_URL     = "http://127.0.0.1:5001"


LED_COLORS = {
    'happy':    '🟡 Yellow',
    'sad':      '🔵 Blue',
    'angry':    '🔴 Red',
    'fear':     '🟣 Purple',
    'surprise': '⚪ White',
    'neutral':  '⚪ Soft White',
    'off':      '⚫ Off',
    '...':      '⚫ Off',
}

MUSIC_MAP = {
    'happy':    'Upbeat',
    'sad':      'Lo-fi',
    'angry':    'Calm',
    'fear':     'Soothing',
    'surprise': 'Upbeat',
    'neutral':  'Chill',
    'off':      'Stopped',
    '...':      'Stopped',
}

EMOJI_MAP = {
    'happy':    '😊',
    'sad':      '😢',
    'angry':    '😠',
    'fear':     '😨',
    'surprise': '😮',
    'neutral':  '😐',
    'off':      '⚫',
    '...':      '⚫',
}

# Global state
current_emotion = "neutral"
person_in_room  = False
is_auto_mode    = True

# MQTT
bot_mqtt = mqtt_lib.Client(
    mqtt_lib.CallbackAPIVersion.VERSION2,
    client_id="moodroom_telegram_bot_v2"
)

def on_mqtt_message(client, userdata, message):
    global current_emotion, person_in_room
    topic = message.topic
    msg   = message.payload.decode().strip()

    if topic == TOPIC_STATUS:
        current_emotion = msg
        person_in_room  = msg not in ["off", "..."]
        print(f"Status updated: {current_emotion}")

    elif topic == TOPIC_PIR:
        if msg == "detected":
            person_in_room = True
        elif msg == "left":
            person_in_room  = False
            current_emotion = "..."

def setup_mqtt():
    bot_mqtt.on_message = on_mqtt_message
    bot_mqtt.connect(MQTT_BROKER, 1883)
    bot_mqtt.subscribe(TOPIC_STATUS)
    bot_mqtt.subscribe(TOPIC_PIR)
    bot_mqtt.loop_start()
    print("Bot MQTT connected!")

# ===== COMMANDS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎭 MoodRoom Bot is alive!\n\n"
        "📋 Commands:\n"
        "/capture — force emotion scan\n"
        "/status — current room state\n"
        "/play happy|sad|angry|fear|surprise|neutral\n"
        "/room off — turn everything off\n"
        "/auto — switch to auto mode\n"
        "/help — show all commands"
    )

async def capture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Forcing face scan...")
    bot_mqtt.publish(TOPIC_PIR, "detected")
    await update.message.reply_text("✅ Scan triggered! Check the room.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        requests.get(f"{FLASK_URL}/test", timeout=2)
        server_status = "🟢 Online"
    except:
        server_status = "🔴 Offline"

    emoji = EMOJI_MAP.get(current_emotion, '❓')
    led   = LED_COLORS.get(current_emotion, '⚪ White')
    music = MUSIC_MAP.get(current_emotion, 'Unknown')
    room  = "👤 Someone is here" if person_in_room else "🚪 Empty"
    mode  = "🤖 Auto" if is_auto_mode else "🎮 Manual"

    await update.message.reply_text(
        f"📊 MoodRoom Status\n"
        f"{'─' * 20}\n"
        f"🖥️ Server: {server_status}\n"
        f"🚪 Room: {room}\n"
        f"🎭 Mood: {emoji} {current_emotion.upper()}\n"
        f"💡 LED: {led}\n"
        f"🎵 Music: {music} playlist\n"
        f"⚙️ Mode: {mode}"
    )

async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_auto_mode
    is_auto_mode = True
    bot_mqtt.publish("moodroom/mode", "auto")
    await update.message.reply_text(
        "🤖 Auto mode ON!\n"
        "Room will now react automatically to emotions."
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_auto_mode
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /play [emotion]\n"
            "Options: happy, sad, angry, fear, surprise, neutral"
        )
        return

    emotion = context.args[0].lower()
    valid = ["happy", "sad", "angry", "fear", "surprise", "neutral"]
    if emotion not in valid:
        await update.message.reply_text(f"❌ Invalid! Choose: {', '.join(valid)}")
        return

    is_auto_mode = False
    bot_mqtt.publish("moodroom/mode", "manual")
    bot_mqtt.publish(TOPIC_EMOTION, emotion)
    bot_mqtt.publish(TOPIC_STATUS, emotion)

    emoji = EMOJI_MAP.get(emotion, '🎭')
    led   = LED_COLORS.get(emotion, 'White')
    music = MUSIC_MAP.get(emotion, 'Chill')

    await update.message.reply_text(
        f"🎮 Manual mode ON!\n"
        f"✅ Switched to {emotion}!\n"
        f"{emoji} Mood: {emotion.upper()}\n"
        f"💡 LED: {led}\n"
        f"🎵 Music: {music} playlist\n\n"
        f"Music keeps playing until /room off\n"
        f"Use /auto to return to auto mode"
    )

async def room_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_emotion, person_in_room, is_auto_mode
    if context.args and context.args[0].lower() == "off":
        is_auto_mode    = True
        current_emotion = "off"
        person_in_room  = False
        bot_mqtt.publish(TOPIC_EMOTION, "off")
        bot_mqtt.publish(TOPIC_PIR, "left")
        bot_mqtt.publish(TOPIC_STATUS, "off")
        bot_mqtt.publish("moodroom/mode", "auto")
        await update.message.reply_text(
            "🔴 Room turned off!\n"
            "💡 LED: Off\n"
            "🎵 Music: Stopped\n"
            "💨 Fan: Off\n\n"
            "🤖 Auto mode restored!"
        )
    else:
        await update.message.reply_text("Usage: /room off")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 MoodRoom Commands\n"
        "──────────────────\n"
        "🤖 Auto Mode:\n"
        "/auto — turn on auto mode\n"
        "/capture — force face scan\n"
        "/status — current room state\n\n"
        "🎮 Manual Mode:\n"
        "/play happy — switch to happy\n"
        "/play sad — switch to sad\n"
        "/play angry — switch to angry\n"
        "/play fear — switch to fear\n"
        "/play surprise — switch to surprise\n"
        "/play neutral — switch to neutral\n\n"
        "🔴 Control:\n"
        "/room off — turn everything off\n"
        "/help — show this message"
    )

# ===== MAIN =====
def main():
    setup_mqtt()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("capture", capture))
    app.add_handler(CommandHandler("status",  status))
    app.add_handler(CommandHandler("play",    play))
    app.add_handler(CommandHandler("room",    room_off))
    app.add_handler(CommandHandler("auto",    auto))
    app.add_handler(CommandHandler("help",    help_cmd))

    print("MoodRoom Telegram bot running...")
    app.run_polling()

if __name__ == '__main__':
    main()
