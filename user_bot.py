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

# Features
VERIFICATION_HOURS = 28
FREE_DAILY_LIMIT = 1
AUTO_DELETE_HOURS = 2
HELP_CHANNEL = "https://t.me/bfghffghfg"

print("=" * 50)
print("🤖 USER BOT STARTING (Full Features)...")
print(f"⏰ Verification: {VERIFICATION_HOURS}hrs")
print(f"🎁 Daily free: {FREE_DAILY_LIMIT}")
print(f"🗑️ Auto-delete: {AUTO_DELETE_HOURS}hrs")
print("=" * 50)

# Database
mongo = MongoClient(MONGO_URL)
db = mongo['fileshare_system']
files = db['files']
users = db['users']
daily_usage = db['daily_usage']
print("✅ Database connected")

# Bot
app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, bot_token=USER_BOT_TOKEN)

# ========== FUNCTIONS ==========

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

# ========== AUTO-DELETE FUNCTION ==========
async def auto_delete_message(chat_id, message_id, hours):
    """Delete message after specified hours"""
    try:
        # Wait for specified hours
        await asyncio.sleep(hours * 3600)
        
        # Delete the message
        await app.delete_messages(chat_id=chat_id, message_ids=message_id)
        
        print(f"🗑️ Auto-deleted message {message_id} from {chat_id}")
        
    except Exception as e:
        print(f"❌ Auto-delete error: {e}")

# ========== COMMANDS ==========

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start(c, m):
    uid = m.from_user.id
    print(f"📥 /start from {uid}")
    
    # Add user
    if not users.find_one({"user_id": uid}):
        users.insert_one({
            "user_id": uid,
            "username": m.from_user.username,
            "first_name": m.from_user.first_name,
            "verified_at": None,
            "joined_at": datetime.datetime.now()
        })
        print(f"✅ New user: {uid}")
    
    # File request
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        print(f"📁 File code: {code}")
        
        # Verify callback
        if code.startswith("verify_"):
            users.update_one(
                {"user_id": uid},
                {"$set": {"verified_at": datetime.datetime.now()}}
            )
            await m.reply(
                f"🎉 **Verification Successful!**\n\n"
                f"✅ You have **{VERIFICATION_HOURS} hours** unlimited access!\n\n"
                f"📁 Download files freely now!"
            )
            print(f"✅ User {uid} verified")
            return
        
        # Check access
        verified = is_verified(uid)
        can_free = can_use_free_daily(uid)
        
        print(f"User {uid}: verified={verified}, can_free={can_free}")
        
        if not verified and not can_free:
            bot_un = (await c.get_me()).username
            link = shorten_url(f"https://t.me/{bot_un}?start=verify_{uid}")
            
            print(f"🔐 Sending verification request to {uid}")
            
            await m.reply(
                f"🔐 **Verification Required**\n\n"
                f"⚠️ You used your daily free file!\n\n"
                f"Verify for **{VERIFICATION_HOURS} hours** unlimited access:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Verify Now", url=link)],
                    [InlineKeyboardButton("❓ How to Verify?", url=HELP_CHANNEL)]
                ])
            )
            return
        
        # Get file
        f = files.find_one({"file_id": code})
        if not f:
            print(f"❌ File {code} not found")
            await m.reply("❌ **File Not Found**\n\nLink expired or invalid.")
            return
        
        # Send file
        try:
            print(f"📤 Sending file {code} to {uid}")
            
            # Increment usage if using free
            if not verified and can_free:
                increment_daily_usage(uid)
                print(f"🎁 Used free file for {uid}")
            
            # Send file with PROTECTION
            sent_msg = await c.copy_message(
                chat_id=m.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=f['message_id'],
                protect_content=True  # 🔒 PROTECT - Save/Forward disabled!
            )
            
            print(f"✅ File sent successfully! Message ID: {sent_msg.id}")
            
            # Update stats
            files.update_one({"file_id": code}, {"$inc": {"downloads": 1}})
            
            # Send warning about auto-delete
            warning_msg = await m.reply(
                f"⚠️ **IMPORTANT NOTICE**\n\n"
                f"📁 This file will **AUTO-DELETE** in **{AUTO_DELETE_HOURS} hours**!\n\n"
                f"⏰ Please watch/save before deletion.\n\n"
                f"🔒 **Protection Active:**\n"
                f"• Save disabled ❌\n"
                f"• Forward disabled ❌\n"
                f"• Screenshot allowed ✅"
            )
            
            print(f"⚠️ Warning sent. Message ID: {warning_msg.id}")
            
            # Schedule AUTO-DELETE for both messages
            print(f"🗑️ Scheduling auto-delete for {AUTO_DELETE_HOURS} hours...")
            
            # Delete file message
            asyncio.create_task(auto_delete_message(m.chat.id, sent_msg.id, AUTO_DELETE_HOURS))
            
            # Delete warning message
            asyncio.create_task(auto_delete_message(m.chat.id, warning_msg.id, AUTO_DELETE_HOURS))
            
            print(f"✅ Auto-delete scheduled!")
            
        except Exception as e:
            print(f"❌ Send error: {e}")
            await m.reply(f"❌ **Error:** {e}")
    
    else:
        # Welcome
        left = FREE_DAILY_LIMIT - get_daily_usage(uid)
        await m.reply(
            f"👋 **Welcome {m.from_user.first_name}!**\n\n"
            f"🤖 **Premium File Sharing Bot**\n\n"
            f"🎁 **Today's Free:** {left}/{FREE_DAILY_LIMIT} files\n\n"
            f"📌 **Features:**\n"
            f"• {FREE_DAILY_LIMIT} free file daily (no verify)\n"
            f"• {VERIFICATION_HOURS}hr access after verify\n"
            f"• Auto-delete in {AUTO_DELETE_HOURS}hrs\n"
            f"• Protected content (save/forward blocked)\n\n"
            f"❓ /help for guide",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❓ How to Verify?", url=HELP_CHANNEL)
            ]])
        )

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_cmd(c, m):
    await m.reply(
        f"📖 **Complete Guide**\n\n"
        f"**🎁 Free Daily Files:**\n"
        f"• Get {FREE_DAILY_LIMIT} free file every day\n"
        f"• No verification needed\n"
        f"• Resets at midnight\n\n"
        f"**✅ Verification Benefits:**\n"
        f"• {VERIFICATION_HOURS} hours unlimited access\n"
        f"• No daily limits\n"
        f"• Download unlimited files\n\n"
        f"**🔒 File Protection:**\n"
        f"• Save/Forward disabled\n"
        f"• Auto-delete in {AUTO_DELETE_HOURS}hrs\n"
        f"• Download before deletion!\n\n"
        f"**❓ How to Verify:**\n"
        f"Visit: {HELP_CHANNEL}"
    )

@app.on_message(filters.command("mystats") & filters.private & ~filters.bot)
async def stats(c, m):
    uid = m.from_user.id
    u = users.find_one({"user_id": uid})
    
    if not u:
        await m.reply("❌ No data!")
        return
    
    used = get_daily_usage(uid)
    verified = is_verified(uid)
    
    if verified:
        v_time = u.get("verified_at")
        remaining = VERIFICATION_HOURS - ((datetime.datetime.now() - v_time).total_seconds() / 3600)
        status = f"✅ Verified\n⏰ {remaining:.1f} hours left"
    else:
        status = f"🎁 Free Mode\n📁 {FREE_DAILY_LIMIT - used} files left today"
    
    await m.reply(
        f"📊 **Your Stats**\n\n"
        f"**Status:**\n{status}\n\n"
        f"📆 **Today's Usage:** {used}/{FREE_DAILY_LIMIT}\n"
        f"🗓️ **Member Since:** {u.get('joined_at').strftime('%d %b %Y')}"
    )

print("🚀 Starting bot with ALL features...")
print("⏳ Connecting to Telegram...")

try:
    app.run()
    print("✅ Bot is running!")
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
