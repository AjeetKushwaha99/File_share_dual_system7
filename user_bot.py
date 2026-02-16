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

# ========== NEW FEATURES CONFIG ==========
VERIFICATION_HOURS = 28  # Changed from 48 to 28 hours
FREE_DAILY_LIMIT = 1  # 1 free file per day
AUTO_DELETE_HOURS = 2  # Auto delete after 2 hours
HELP_CHANNEL = "https://t.me/bfghffghfg"  # Your guide channel

print("=" * 50)
print("🤖 USER BOT STARTING (Enhanced Version)...")
print(f"⏰ Verification: {VERIFICATION_HOURS} hours")
print(f"🎁 Daily free files: {FREE_DAILY_LIMIT}")
print(f"🗑️ Auto-delete: {AUTO_DELETE_HOURS} hours")
print("=" * 50)

try:
    mongo = MongoClient(MONGO_URL)
    db = mongo['fileshare_system']
    files = db['files']
    users = db['users']
    daily_usage = db['daily_usage']
    print("✅ Database connected!")
except Exception as e:
    print(f"❌ Database error: {e}")

app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, bot_token=USER_BOT_TOKEN)

# ========== HELPER FUNCTIONS ==========

def is_verified(user_id):
    """Check if user verified within 28 hours"""
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("verified_at"):
        return False
    
    verification_seconds = VERIFICATION_HOURS * 3600  # Convert to seconds
    time_diff = (datetime.datetime.now() - user["verified_at"]).total_seconds()
    return time_diff < verification_seconds

def get_daily_usage(user_id):
    """Get today's usage count for user"""
    today = datetime.datetime.now().date()
    usage = daily_usage.find_one({
        "user_id": user_id,
        "date": today
    })
    return usage.get("count", 0) if usage else 0

def increment_daily_usage(user_id):
    """Increment today's usage count"""
    today = datetime.datetime.now().date()
    daily_usage.update_one(
        {"user_id": user_id, "date": today},
        {"$inc": {"count": 1}},
        upsert=True
    )

def can_use_free_daily(user_id):
    """Check if user can use free daily file"""
    return get_daily_usage(user_id) < FREE_DAILY_LIMIT

def shorten_url(url):
    """Shorten URL using VPLinks"""
    try:
        api_url = f"{SHORTENER_URL}/api?api={SHORTENER_API}&url={url}"
        response = requests.get(api_url, timeout=10).json()
        if response.get("status") == "success":
            return response.get("shortenedUrl", url)
        return url
    except Exception as e:
        print(f"Shortener error: {e}")
        return url

async def delete_message_after_delay(chat_id, message_id, hours):
    """Delete message after specified hours"""
    try:
        await asyncio.sleep(hours * 3600)  # Convert hours to seconds
        await app.delete_messages(chat_id, message_id)
        print(f"🗑️ Auto-deleted message {message_id} from chat {chat_id}")
    except Exception as e:
        print(f"❌ Delete error: {e}")

# ========== COMMANDS ==========

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start_user(c, m):
    user_id = m.from_user.id
    
    print(f"📥 /start from user: {user_id}")
    
    # Add user to database
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "username": m.from_user.username,
            "first_name": m.from_user.first_name,
            "verified_at": None,
            "joined_at": datetime.datetime.now(),
            "total_downloads": 0
        })
        print(f"✅ New user added: {user_id}")
    
    # Check if file request
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        print(f"📁 File request: {code}")
        
        # Verification callback
        if code.startswith("verify_"):
            users.update_one(
                {"user_id": user_id},
                {"$set": {"verified_at": datetime.datetime.now()}}
            )
            await m.reply(
                f"🎉 **Verification Successful!**\n\n"
                f"✅ You now have **{VERIFICATION_HOURS} hours** of unlimited access!\n\n"
                f"📁 Download files without any restrictions.\n"
                f"⏰ Access expires after {VERIFICATION_HOURS} hours.\n\n"
                f"Thank you for verifying! 😊"
            )
            print(f"✅ User verified: {user_id}")
            return
        
        # Check verification status
        is_user_verified = is_verified(user_id)
        can_use_free = can_use_free_daily(user_id)
        
        # Allow if verified OR can use free daily
        if not is_user_verified and not can_use_free:
            bot_username = (await c.get_me()).username
            verify_url = f"https://t.me/{bot_username}?start=verify_{user_id}"
            short_link = shorten_url(verify_url)
            
            print(f"🔐 Verification required for {user_id}")
            print(f"🔗 Verify link: {short_link}")
            
            # NEW: Added "How to Verify" button
            await m.reply(
                f"🔐 **Verification Required**\n\n"
                f"⚠️ You've used your free daily file!\n\n"
                f"Complete quick verification for **{VERIFICATION_HOURS} hours** unlimited access!\n\n"
                f"✅ **Benefits:**\n"
                f"• {VERIFICATION_HOURS}hr unlimited downloads\n"
                f"• No daily limits\n"
                f"• Fast & secure\n\n"
                f"👇 Click button below:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Verify Now", url=short_link)],
                    [InlineKeyboardButton("❓ How to Verify?", url=HELP_CHANNEL)]
                ])
            )
            return
        
        # Get file data
        file_data = files.find_one({"file_id": code})
        
        if not file_data:
            print(f"❌ File not found: {code}")
            await m.reply("❌ **File Not Found**\n\nThis link may be expired or invalid.")
            return
        
        # Send file
        try:
            print(f"📤 Sending file {code} to user {user_id}")
            
            # Determine if using free daily
            using_free = not is_user_verified and can_use_free
            
            if using_free:
                increment_daily_usage(user_id)
                print(f"🎁 Using free daily file for user {user_id}")
            
            # Send file with PROTECTED content (prevent save/forward)
            sent_message = await c.copy_message(
                chat_id=m.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=file_data['message_id'],
                protect_content=True  # 🔐 Prevent save/forward!
            )
            
            # Update download count
            files.update_one({"file_id": code}, {"$inc": {"downloads": 1}})
            users.update_one({"user_id": user_id}, {"$inc": {"total_downloads": 1}})
            
            # Send auto-delete warning
            warning_msg = await m.reply(
                f"⚠️ **Important Notice**\n\n"
                f"📁 This file will be **automatically deleted after {AUTO_DELETE_HOURS} hours**.\n\n"
                f"⏰ Please watch/download before deletion!\n\n"
                f"🔒 File is protected - save/forward disabled for security."
            )
            
            # Schedule auto-delete
            asyncio.create_task(delete_message_after_delay(m.chat.id, sent_message.id, AUTO_DELETE_HOURS))
            asyncio.create_task(delete_message_after_delay(m.chat.id, warning_msg.id, AUTO_DELETE_HOURS))
            
            print(f"✅ File sent! Auto-delete scheduled for {AUTO_DELETE_HOURS} hours")
            
            # Show usage info if using free
            if using_free:
                await m.reply(
                    f"🎁 **Free Daily File Used**\n\n"
                    f"You've used your free file for today!\n\n"
                    f"Want unlimited access?\n"
                    f"Verify once for {VERIFICATION_HOURS} hours unlimited downloads!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Verify Now", url=shorten_url(f"https://t.me/{(await c.get_me()).username}?start=verify_{user_id}"))
                    ]])
                )
            
        except Exception as e:
            print(f"❌ Error sending file: {e}")
            await m.reply(f"❌ **Error:** {str(e)}\n\nPlease contact admin.")
    
    else:
        # Welcome message
        daily_left = FREE_DAILY_LIMIT - get_daily_usage(user_id)
        
        await m.reply(
            f"👋 **Welcome {m.from_user.first_name}!**\n\n"
            f"🤖 **Premium File Sharing Bot**\n\n"
            f"🎁 **Daily Free:** {daily_left}/{FREE_DAILY_LIMIT} files left today\n\n"
            f"📌 **Features:**\n"
            f"• 🎁 {FREE_DAILY_LIMIT} free file daily\n"
            f"• ⏰ {VERIFICATION_HOURS}hr access after verify\n"
            f"• 🔒 Protected & secure files\n"
            f"• 🗑️ Auto-delete after {AUTO_DELETE_HOURS}hrs\n"
            f"• 🚫 Save/Forward disabled\n\n"
            f"📥 **How to use:**\n"
            f"1. Get file link from admin\n"
            f"2. Use {FREE_DAILY_LIMIT} free file OR verify\n"
            f"3. Download instantly!\n\n"
            f"❓ /help for guide",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❓ How to Verify?", url=HELP_CHANNEL)
            ]])
        )

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_user(c, m):
    await m.reply(
        f"📖 **Complete Guide**\n\n"
        f"**🎁 Free Daily Files:**\n"
        f"• Get {FREE_DAILY_LIMIT} free file every day\n"
        f"• No verification needed for daily file\n"
        f"• Resets every 24 hours\n\n"
        f"**✅ Verification Benefits:**\n"
        f"• {VERIFICATION_HOURS} hours unlimited access\n"
        f"• No daily limits\n"
        f"• Download as many files as you want\n\n"
        f"**🔒 File Protection:**\n"
        f"• Files are protected (save/forward disabled)\n"
        f"• Auto-delete after {AUTO_DELETE_HOURS} hours\n"
        f"• Watch/download before deletion!\n\n"
        f"**❓ How to Verify:**\n"
        f"• Click verification link\n"
        f"• Complete simple steps\n"
        f"• Get {VERIFICATION_HOURS}hr unlimited access!\n\n"
        f"**Need Help?**\n"
        f"Join guide channel: {HELP_CHANNEL}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❓ Verification Guide", url=HELP_CHANNEL)
        ]])
    )

@app.on_message(filters.command("about") & filters.private & ~filters.bot)
async def about_user(c, m):
    user = users.find_one({"user_id": m.from_user.id})
    total_downloads = user.get("total_downloads", 0) if user else 0
    daily_used = get_daily_usage(m.from_user.id)
    daily_left = FREE_DAILY_LIMIT - daily_used
    
    verified = is_verified(m.from_user.id)
    status = f"✅ Verified ({VERIFICATION_HOURS}hr access)" if verified else f"🎁 Free Mode ({daily_left} files left today)"
    
    await m.reply(
        f"ℹ️ **Your Account Info**\n\n"
        f"👤 **User:** {m.from_user.first_name}\n"
        f"🆔 **ID:** `{m.from_user.id}`\n"
        f"📊 **Status:** {status}\n"
        f"📥 **Total Downloads:** {total_downloads}\n"
        f"🎁 **Today's Usage:** {daily_used}/{FREE_DAILY_LIMIT}\n\n"
        f"**Bot Features:**\n"
        f"🤖 Premium File Sharing\n"
        f"🔐 Protected Content\n"
        f"🗑️ Auto-delete: {AUTO_DELETE_HOURS}hrs\n"
        f"⏰ Verification: {VERIFICATION_HOURS}hrs access\n\n"
        f"Thank you for using! ❤️"
    )

@app.on_message(filters.command("mystats") & filters.private & ~filters.bot)
async def mystats_user(c, m):
    user = users.find_one({"user_id": m.from_user.id})
    if not user:
        await m.reply("❌ No data found!")
        return
    
    total_downloads = user.get("total_downloads", 0)
    joined = user.get("joined_at", datetime.datetime.now())
    daily_used = get_daily_usage(m.from_user.id)
    verified = is_verified(m.from_user.id)
    
    if verified:
        verify_time = user.get("verified_at")
        remaining = VERIFICATION_HOURS - ((datetime.datetime.now() - verify_time).total_seconds() / 3600)
        status_text = f"✅ Verified\n⏰ {remaining:.1f} hours remaining"
    else:
        status_text = f"🎁 Free Mode\n📁 {FREE_DAILY_LIMIT - daily_used} files left today"
    
    await m.reply(
        f"📊 **Your Statistics**\n\n"
        f"**Status:**\n{status_text}\n\n"
        f"📥 **Total Downloads:** {total_downloads}\n"
        f"🗓️ **Member Since:** {joined.strftime('%d %b %Y')}\n"
        f"📆 **Today's Usage:** {daily_used}/{FREE_DAILY_LIMIT}\n\n"
        f"Want unlimited access?\n"
        f"Verify for {VERIFICATION_HOURS} hours!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Verify Now", url=shorten_url(f"https://t.me/{(await c.get_me()).username}?start=verify_{m.from_user.id}"))
        ]])
    )

print("🚀 Starting Enhanced User Bot...")
try:
    app.run()
    print("✅ User Bot is running!")
except Exception as e:
    print(f"❌ Bot failed: {e}")
