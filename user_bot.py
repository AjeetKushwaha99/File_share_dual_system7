from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import datetime
import requests

# FIXED CONFIG - All hardcoded
API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"
USER_BOT_TOKEN = "8537476620:AAHf1XxjpjFGJICxNAQ4i9A06gN0Z0ephDk"
CHANNEL_ID = -1003777551559
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"
SHORTENER_API = "5cbb1b2088d2ed06d7e9feae35dc17cc033169d6"
SHORTENER_URL = "https://vplink.in"

print("=" * 50)
print("🤖 USER BOT STARTING...")
print(f"Bot Token: {USER_BOT_TOKEN[:20]}...")
print("=" * 50)

try:
    mongo = MongoClient(MONGO_URL)
    db = mongo['fileshare_system']
    files = db['files']
    users = db['users']
    print("✅ Database connected!")
except Exception as e:
    print(f"❌ Database error: {e}")

app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, bot_token=USER_BOT_TOKEN)

def is_verified(user_id):
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("verified_at"):
        return False
    time_diff = (datetime.datetime.now() - user["verified_at"]).total_seconds()
    return time_diff < 93600

def shorten_url(url):
    try:
        api_url = f"{SHORTENER_URL}/api?api={SHORTENER_API}&url={url}"
        response = requests.get(api_url, timeout=10).json()
        if response.get("status") == "success":
            return response.get("shortenedUrl", url)
        return url
    except Exception as e:
        print(f"Shortener error: {e}")
        return url

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start_user(c, m):
    user_id = m.from_user.id
    
    print(f"📥 /start from user: {user_id}")
    
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "username": m.from_user.username,
            "first_name": m.from_user.first_name,
            "verified_at": None,
            "joined_at": datetime.datetime.now()
        })
        print(f"✅ New user added: {user_id}")
    
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        print(f"📁 File request: {code}")
        
        if code.startswith("verify_"):
            users.update_one(
                {"user_id": user_id},
                {"$set": {"verified_at": datetime.datetime.now()}}
            )
            await m.reply(
                "🎉 **Verification Successful!**\n\n"
                "✅ You now have **26 hours** of unlimited access!\n\n"
                "📁 Download files without restrictions!"
            )
            print(f"✅ User verified: {user_id}")
            return
        
        if not is_verified(user_id):
            bot_username = (await c.get_me()).username
            verify_url = f"https://t.me/{bot_username}?start=verify_{user_id}"
            short_link = shorten_url(verify_url)
            
            print(f"🔐 Verification required for {user_id}")
            print(f"🔗 Verify link: {short_link}")
            
            await m.reply(
                "🔐 **Verification Required**\n\n"
                "Complete quick verification for 26hr access!\n\n"
                " ✅️🤖 How to verify - @fillings4you "
                "👇 Click below:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Verify Now", url=short_link)
                ]])
            )
            return
        
        file_data = files.find_one({"file_id": code})
        
        if not file_data:
            print(f"❌ File not found: {code}")
            await m.reply("❌ **File Not Found**\n\nThis link may be expired or invalid.")
            return
        
        try:
            print(f"📤 Sending file {code} to user {user_id}")
            await c.copy_message(
                chat_id=m.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=file_data['message_id']
            )
            files.update_one({"file_id": code}, {"$inc": {"downloads": 1}})
            print(f"✅ File sent successfully!")
        except Exception as e:
            print(f"❌ Error sending file: {e}")
            await m.reply(f"❌ **Error:** {str(e)}")
    
    else:
        await m.reply(
            f"👋 **Welcome {m.from_user.first_name}!**\n\n"
            "🤖 **Premium File Sharing Bot**\n\n"
            "📌 **Features:**\n"
            "• Fast downloads\n"
            "• 26hr unlimited access\n"
            " ✅️🤖 How to verify - @fillings4you "
            "• Secure & encrypted\n\n"
            "❓ /help for guide"
        )

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_user(c, m):
    await m.reply(
        "📖 **Help Guide**\n\n"
        "**Download Files:**\n"
        "1️⃣ Click file link\n"
        "2️⃣ Verify (one-time)\n"
        "3️⃣ Get 26hr access\n"
        "4️⃣ Download freely!\n\n"
        " ✅️🤖 How to verify - @fillings4you "
        "**Verification expired?**\n"
        "Simply verify again!"
    )

@app.on_message(filters.command("about") & filters.private & ~filters.bot)
async def about_user(c, m):
    await m.reply(
        "ℹ️ **About**\n\n"
        "🤖 Premium File Sharing Bot\n"
        "📥 Fast & Secure Downloads\n"
        "🔐 Private & Encrypted\n\n"
        "✅️🤖 How to verify - @fillings4you"
        "Thank you for using! ❤️"
    )

print("🚀 Starting User Bot...")
try:
    app.run()
    print("✅ User Bot is running!")
except Exception as e:
    print(f"❌ Bot failed to start: {e}")
