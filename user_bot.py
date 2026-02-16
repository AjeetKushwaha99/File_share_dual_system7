from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import datetime
import requests
import asyncio

# ========== CONFIG ==========
API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"
USER_BOT_TOKEN = "8537476620:AAHf1XxjpjFGJICxNAQ4i9A06gN0Z0ephDk"
CHANNEL_ID = -1003777551559
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"
SHORTENER_API = "5cbb1b2088d2ed06d7e9feae35dc17cc033169d6"
SHORTENER_URL = "https://vplink.in"
VERIFICATION_HOURS = 28
FREE_DAILY_LIMIT = 1
AUTO_DELETE_HOURS = 2
HELP_CHANNEL = "https://t.me/bfghffghfg"

print("🤖 User Bot Starting...")

mongo = MongoClient(MONGO_URL)
db = mongo['fileshare_system']
files = db['files']
users = db['users']
daily_usage = db['daily_usage']

app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, bot_token=USER_BOT_TOKEN)

def is_verified(user_id):
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("verified_at"):
        return False
    time_diff = (datetime.datetime.now() - user["verified_at"]).total_seconds()
    return time_diff < (VERIFICATION_HOURS * 3600)

def get_daily_usage(user_id):
    today = datetime.datetime.now().date()
    usage = daily_usage.find_one({"user_id": user_id, "date": today})
    return usage.get("count", 0) if usage else 0

def increment_daily_usage(user_id):
    today = datetime.datetime.now().date()
    daily_usage.update_one(
        {"user_id": user_id, "date": today},
        {"$inc": {"count": 1}},
        upsert=True
    )

def can_use_free_daily(user_id):
    return get_daily_usage(user_id) < FREE_DAILY_LIMIT

def shorten_url(url):
    try:
        r = requests.get(f"{SHORTENER_URL}/api?api={SHORTENER_API}&url={url}", timeout=10).json()
        return r.get("shortenedUrl", url)
    except:
        return url

async def delete_after(chat_id, msg_id, hours):
    await asyncio.sleep(hours * 3600)
    try:
        await app.delete_messages(chat_id, msg_id)
    except:
        pass

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start(c, m):
    uid = m.from_user.id
    
    if not users.find_one({"user_id": uid}):
        users.insert_one({
            "user_id": uid,
            "username": m.from_user.username,
            "first_name": m.from_user.first_name,
            "verified_at": None,
            "joined_at": datetime.datetime.now(),
            "total_downloads": 0
        })
    
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        
        if code.startswith("verify_"):
            users.update_one({"user_id": uid}, {"$set": {"verified_at": datetime.datetime.now()}})
            await m.reply(
                f"🎉 **Verified!**\n\n✅ {VERIFICATION_HOURS}hr unlimited access activated!"
            )
            return
        
        verified = is_verified(uid)
        free = can_use_free_daily(uid)
        
        if not verified and not free:
            bot_un = (await c.get_me()).username
            link = shorten_url(f"https://t.me/{bot_un}?start=verify_{uid}")
            await m.reply(
                f"🔐 **Verification Required**\n\n⚠️ Daily limit used!\n\nVerify for {VERIFICATION_HOURS}hr access:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Verify", url=link)],
                    [InlineKeyboardButton("❓ How to Verify", url=HELP_CHANNEL)]
                ])
            )
            return
        
        f = files.find_one({"file_id": code})
        if not f:
            await m.reply("❌ File not found!")
            return
        
        try:
            if not verified and free:
                increment_daily_usage(uid)
            
            sent = await c.copy_message(m.chat.id, CHANNEL_ID, f['message_id'], protect_content=True)
            files.update_one({"file_id": code}, {"$inc": {"downloads": 1}})
            users.update_one({"user_id": uid}, {"$inc": {"total_downloads": 1}})
            
            warn = await m.reply(
                f"⚠️ **Auto-Delete Warning**\n\n"
                f"📁 File deletes in {AUTO_DELETE_HOURS} hours!\n"
                f"🔒 Save/Forward disabled."
            )
            
            asyncio.create_task(delete_after(m.chat.id, sent.id, AUTO_DELETE_HOURS))
            asyncio.create_task(delete_after(m.chat.id, warn.id, AUTO_DELETE_HOURS))
            
        except Exception as e:
            await m.reply(f"❌ Error: {e}")
    
    else:
        left = FREE_DAILY_LIMIT - get_daily_usage(uid)
        await m.reply(
            f"👋 Welcome {m.from_user.first_name}!\n\n"
            f"🎁 Daily free: {left}/{FREE_DAILY_LIMIT}\n\n"
            f"📌 Features:\n"
            f"• {FREE_DAILY_LIMIT} free file daily\n"
            f"• {VERIFICATION_HOURS}hr access after verify\n"
            f"• Auto-delete in {AUTO_DELETE_HOURS}hr\n\n"
            f"❓ /help",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❓ How to Verify", url=HELP_CHANNEL)
            ]])
        )

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_cmd(c, m):
    await m.reply(
        f"📖 **Help**\n\n"
        f"🎁 {FREE_DAILY_LIMIT} free file daily\n"
        f"✅ Verify for {VERIFICATION_HOURS}hr access\n"
        f"🗑️ Files auto-delete in {AUTO_DELETE_HOURS}hr\n\n"
        f"Guide: {HELP_CHANNEL}"
    )

@app.on_message(filters.command("mystats") & filters.private & ~filters.bot)
async def stats(c, m):
    u = users.find_one({"user_id": m.from_user.id})
    if not u:
        await m.reply("❌ No data!")
        return
    
    downloads = u.get("total_downloads", 0)
    used = get_daily_usage(m.from_user.id)
    verified = is_verified(m.from_user.id)
    
    status = f"✅ Verified" if verified else f"🎁 Free ({FREE_DAILY_LIMIT - used} left)"
    
    await m.reply(
        f"📊 **Your Stats**\n\n"
        f"Status: {status}\n"
        f"Downloads: {downloads}\n"
        f"Today: {used}/{FREE_DAILY_LIMIT}"
    )

print("🚀 Starting...")
app.run()
