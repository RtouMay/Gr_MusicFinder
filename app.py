import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, filters

app = Flask(__name__)

# گرفتن توکن و کلید API از محیط اجرا
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHAZAM_API_KEY = os.getenv("SHAZAM_API_KEY")
CHANNEL_ID = "@gamerenterchannel"

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# چک عضویت در کانال
def check_membership(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    resp = requests.get(url).json()
    status = resp.get("result", {}).get("status", "")
    return status in ["member", "administrator", "creator"]

# پیام خوش‌آمد بعد از /start
def handle_start(update: Update, context):
    user_id = update.effective_user.id
    if not check_membership(user_id):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url="https://t.me/gamerenterchannel")]])
        update.message.reply_text(
            "🎧 به ربات GR Music Finder خوش اومدید!\n\nلطفاً برای ادامه کار با این ربات عضو چنل زیر بشید 👇",
            reply_markup=btn
        )
        return

    update.message.reply_text("✅ حالا لطفاً لینک، ویدیو یا ویس مربوط به آهنگ رو بفرستید تا اسم آهنگ و لینک پخش واستون ارسال بشه 🎶")

# تشخیص آهنگ با Shazam
def identify_song(audio_url):
    headers = {
        "X-RapidAPI-Key": SHAZAM_API_KEY,
        "X-RapidAPI-Host": "shazam.p.rapidapi.com"
    }
    params = {"url": audio_url}
    resp = requests.get("https://shazam.p.rapidapi.com/songs/detect", headers=headers, params=params)
    data = resp.json()
    track = data.get("track", {})
    return {
        "title": track.get("title"),
        "artist": track.get("subtitle"),
        "youtube": track.get("hub", {}).get("actions", [{}])[0].get("uri"),
        "spotify": track.get("hub", {}).get("providers", [{}])[0].get("actions", [{}])[0].get("uri"),
        "image": track.get("images", {}).get("coverart")
    }

# پاسخ به ویس
def handle_voice(update: Update, context):
    user_id = update.effective_user.id
    if not check_membership(user_id):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url="https://t.me/gamerenterchannel")]])
        update.message.reply_text("برای استفاده از ربات لطفاً ابتدا عضو کانال شوید 👇", reply_markup=btn)
        return

    file = bot.get_file(update.message.voice.file_id)
    audio_url = file.file_path
    song = identify_song(audio_url)

    if song["title"]:
        msg = f"""🎶 آهنگ پیدا شد!

📌 عنوان: {song['title']}
🎤 خواننده: {song['artist']}
📺 YouTube: {song['youtube']}
🎧 Spotify: {song['spotify']}

📢 برای خرید اشتراک YouTube و Spotify  
به سایت Gamerenter.ir سر بزنید 👇  
🌐 https://gamerenter.ir
"""
        update.message.reply_photo(photo=song["image"], caption=msg)
    else:
        update.message.reply_text("متأسفانه نتونستم آهنگ رو تشخیص بدم 😔 لطفاً دوباره امتحان کن.")

# هندلرها
dispatcher.add_handler(CommandHandler("start", handle_start))
dispatcher.add_handler(MessageHandler(filters.VOICE, handle_voice))

# وب‌هوک
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"
