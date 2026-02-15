from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import datetime
import requests
import os

API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"
USER_BOT_TOKEN = os.environ.get("USER_BOT_TOKEN", "")
CHANNEL_ID = -1003777551559
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"
SHORTENER_API = "5cbb1b2088d2ed06d7e9feae35dc17cc033169d6"
SHORTENER_URL = "https://vplink.in"

print("🤖 User Bot Starting...")

mongo = MongoClient(MONGO_URL)
db = mongo['fileshare_system']
files = db['files']
users = db['users']
print("✅ Database connected!")

app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, bot_token=USER_BOT_TOKEN)

def is_verified(user_id):
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("verified_at"):
        return False
    return (datetime.datetime.now() - user["verified_at"]).total_seconds() < 172800

def shorten_url(url):
    try:
        r = requests.get(f"{SHORTENER_URL}/api?api={SHORTENER_API}&url={url}", timeout=10).json()
        return r.get("shortenedUrl", url)
    except:
        return url

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start_user(c, m):
    user_id = m.from_user.id
    
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "username": m.from_user.username,
            "first_name": m.from_user.first_name,
            "verified_at": None,
            "joined_at": datetime.datetime.now()
        })
    
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        
        if code.startswith("verify_"):
            users.update_one(
                {"user_id": user_id},
                {"$set": {"verified_at": datetime.datetime.now()}}
            )
            await m.reply(
                "🎉 **Verification Successful!**\n\n"
                "✅ 48 hours unlimited access activated!\n\n"
                "📁 Now download files freely!"
            )
            return
        
        if not is_verified(user_id):
            bot_username = (await c.get_me()).username
            verify_url = f"https://t.me/{bot_username}?start=verify_{user_id}"
            short_link = shorten_url(verify_url)
            
            await m.reply(
                "🔐 **Verification Required**\n\n"
                "✅ One-time verify for 48hr access!\n\n"
                "👇 Click below:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Verify Now", url=short_link)
                ]])
            )
            return
        
        file_data = files.find_one({"file_id": code})
        
        if not file_data:
            await m.reply("❌ File not found or expired.")
            return
        
        try:
            await c.copy_message(
                chat_id=m.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=file_data['message_id']
            )
            files.update_one({"file_id": code}, {"$inc": {"downloads": 1}})
        except Exception as e:
            await m.reply(f"❌ Error: {e}")
    
    else:
        await m.reply(
            f"👋 **Welcome {m.from_user.first_name}!**\n\n"
            "🤖 **File Sharing Bot**\n\n"
            "📌 Features:\n"
            "• Fast downloads\n"
            "• 48hr access\n"
            "• Secure links\n\n"
            "❓ /help"
        )

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_user(c, m):
    await m.reply(
        "📖 **Help**\n\n"
        "1️⃣ Click file link\n"
        "2️⃣ Verify (one-time)\n"
        "3️⃣ Get 48hr access\n"
        "4️⃣ Download freely!"
    )

@app.on_message(filters.command("about") & filters.private & ~filters.bot)
async def about_user(c, m):
    await m.reply(
        "ℹ️ **About**\n\n"
        "🤖 Premium File Sharing Bot\n"
        "📥 Fast & Secure Downloads\n"
        "🔐 Private & Encrypted\n\n"
        "Thank you! ❤️"
    )

print("🚀 Starting User Bot...")
app.run()
