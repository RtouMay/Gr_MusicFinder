import os
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHAZAM_API_KEY = os.getenv("SHAZAM_API_KEY")
CHANNEL_ID = "@gamerenterchannel"

application = Application.builder().token(BOT_TOKEN).build()

# چک عضویت در کانال
async def check_membership(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    try:
        resp = requests.get(url).json()
        status = resp.get("result", {}).get("status", "")
        return status in ["member", "administrator", "creator"]
    except:
        return False

# هندلر /start
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url="https://t.me/gamerenterchannel")]])
        await update.message.reply_text(
            "🎧 به ربات GR Music Finder خوش اومدید!\n\nلطفاً برای ادامه کار با این ربات عضو چنل زیر بشید 👇",
            reply_markup=btn
        )
        return
    await update.message.reply_text("✅ حالا لطفاً لینک، ویدیو یا ویس مربوط به آهنگ رو بفرستید تا اسم آهنگ و لینک پخش واستون ارسال بشه 🎶")

# تشخیص آهنگ با Shazam
def identify_song(audio_url):
    headers = {
        "X-RapidAPI-Key": SHAZAM_API_KEY,
        "X-RapidAPI-Host": "shazam.p.rapidapi.com"
    }
    params = {"url": audio_url}
    try:
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
    except:
        return {}

# هندلر ویس
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال", url="https://t.me/gamerenterchannel")]])
        await update.message.reply_text("برای استفاده از ربات لطفاً ابتدا عضو کانال شوید 👇", reply_markup=btn)
        return
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        audio_url = file.file_path
        song = identify_song(audio_url)
        if song.get("title"):
            msg = f"""🎶 آهنگ پیدا شد!

📌 عنوان: {song['title']}
🎤 خواننده: {song['artist']}
📺 YouTube: {song['youtube']}
🎧 Spotify: {song['spotify']}

📢 برای خرید اشتراک YouTube و Spotify  
به سایت Gamerenter.ir سر بزنید 👇  
🌐 https://gamerenter.ir
"""
            await update.message.reply_photo(photo=song["image"], caption=msg)
        else:
            await update.message.reply_text("متأسفانه نتونستم آهنگ رو تشخیص بدم 😔 لطفاً دوباره امتحان کن.")
    except:
        await update.message.reply_text("یه مشکلی پیش اومد موقع دریافت ویس. لطفاً دوباره امتحان کن.")

# ثبت هندلرها
application.add_handler(CommandHandler("start", handle_start))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))

# آماده‌سازی اپلیکیشن برای دریافت آپدیت
application.initialize()

# مسیر وب‌هوک
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "ok"
