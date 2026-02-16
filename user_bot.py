from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import datetime
import requests
import asyncio
import time

# FIXED CONFIG
API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"
USER_BOT_TOKEN = "8537476620:AAHf1XxjpjFGJICxNAQ4i9A06gN0Z0ephDk"
CHANNEL_ID = -1003777551559
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"
SHORTENER_API = "5cbb1b2088d2ed06d7e9feae35dc17cc033169d6"
SHORTENER_URL = "https://vplink.in"

# Channel and contact info
VERIFICATION_CHANNEL = "https://t.me/bfghffghfg"
DEVELOPER = "SMARTHELPE1_BOT"
SUPPORT = "SMARTHELPE1_BOT"
CONTACT = "SMARTHELPE1_BOT"
WELCOME_PHOTO = "https://i.ibb.co/W4hgwj1p.jpg"

print("=" * 50)
print("🤖 USER BOT STARTING WITH NEW FEATURES...")
print(f"Bot Token: {USER_BOT_TOKEN[:20]}...")
print("=" * 50)

# Database connection with error handling
try:
    mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = mongo['fileshare_system']
    files = db['files']
    users = db['users']
    free_usage = db['free_usage']
    print("✅ Database connected!")
except Exception as e:
    print(f"❌ Database connection error: {e}")
    # Create in-memory storage if DB fails
    print("⚠️ Using in-memory storage as fallback")
    files = None
    users = None
    free_usage = None

app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, bot_token=USER_BOT_TOKEN)

def is_verified(user_id):
    """Check if user is verified within 28 hours"""
    if not users:
        return False
    
    try:
        user = users.find_one({"user_id": user_id})
        if not user or not user.get("verified_at"):
            return False
        time_diff = (datetime.datetime.now() - user["verified_at"]).total_seconds()
        return time_diff < 100800  # 28 hours in seconds
    except Exception as e:
        print(f"❌ Error checking verification: {e}")
        return False

def has_free_access_today(user_id):
    """Check if user has used free access today"""
    if not free_usage:
        return False
    
    try:
        today = datetime.date.today().isoformat()
        record = free_usage.find_one({
            "user_id": user_id,
            "date": today
        })
        return record is not None
    except Exception as e:
        print(f"❌ Error checking free access: {e}")
        return True  # Assume used to be safe

def mark_free_access_used(user_id):
    """Mark free access as used for today"""
    if not free_usage:
        return
    
    try:
        today = datetime.date.today().isoformat()
        free_usage.update_one(
            {"user_id": user_id, "date": today},
            {"$set": {"user_id": user_id, "date": today, "used_at": datetime.datetime.now()}},
            upsert=True
        )
    except Exception as e:
        print(f"❌ Error marking free access: {e}")

def shorten_url(url):
    """Shorten URL using service"""
    try:
        api_url = f"{SHORTENER_URL}/api?api={SHORTENER_API}&url={url}"
        response = requests.get(api_url, timeout=5).json()
        if response.get("status") == "success":
            return response.get("shortenedUrl", url)
        return url
    except Exception as e:
        print(f"⚠️ Shortener error: {e}")
        return url

async def delete_message_after_delay(chat_id, message_id, delay_hours=2):
    """Delete message after specified hours"""
    await asyncio.sleep(delay_hours * 3600)
    try:
        await app.delete_messages(chat_id, message_id)
        print(f"✅ Auto-deleted message {message_id} after {delay_hours} hours")
    except Exception as e:
        print(f"❌ Error auto-deleting message: {e}")

@app.on_message(filters.command("start") & filters.private)
async def start_user(c, m):
    user_id = m.from_user.id
    first_name = m.from_user.first_name or "User"
    
    print(f"📥 /start from user: {user_id} - {first_name}")
    
    # Initialize user in database
    if users:
        try:
            if not users.find_one({"user_id": user_id}):
                users.insert_one({
                    "user_id": user_id,
                    "username": m.from_user.username,
                    "first_name": first_name,
                    "verified_at": None,
                    "joined_at": datetime.datetime.now(),
                    "total_downloads": 0
                })
                print(f"✅ New user added: {user_id}")
        except Exception as e:
            print(f"❌ Error adding user: {e}")
    
    # Handle verification or file requests
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        print(f"📁 File/Verify request: {code}")
        
        # Handle verification
        if code.startswith("verify_"):
            if users:
                try:
                    users.update_one(
                        {"user_id": user_id},
                        {"$set": {
                            "verified_at": datetime.datetime.now(),
                            "verification_count": 1
                        }}
                    )
                except Exception as e:
                    print(f"❌ Error updating verification: {e}")
            
            await m.reply(
                "🎉 **Verification Successful!** 🔥\n\n"
                "✅ You now have **28 hours** of unlimited access! ⏳\n\n"
                "🚀 Enjoy unlimited downloads without restrictions!\n"
                "🎬 All videos available for you!\n\n"
                "📥 Start downloading now!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📂 Start Downloading", url=f"https://t.me/{(await c.get_me()).username}")
                ]])
            )
            print(f"✅ User verified: {user_id} - 28 hours access granted")
            return
        
        # Check verification status
        is_user_verified = is_verified(user_id)
        has_free_today = has_free_access_today(user_id)
        
        # If not verified and hasn't used free access today, allow one video
        if not is_user_verified and not has_free_today:
            print(f"🎁 Giving free access to user {user_id} for first video today")
        elif not is_user_verified:
            # Ask for verification
            bot_username = (await c.get_me()).username
            verify_url = f"https://t.me/{bot_username}?start=verify_{user_id}"
            short_link = shorten_url(verify_url)
            
            print(f"🔐 Verification required for {user_id}")
            
            await m.reply(
                "🔐 **Verification Required** ⚡️\n\n"
                "⚠️ **Free Access Used for Today!**\n\n"
                "🎁 You already used your **1 FREE video** today!\n"
                "👉 **Verify now** to get **28 HOURS** of unlimited access!\n\n"
                "✅ **Benefits after verification:**\n"
                "• 📥 Unlimited Downloads\n"
                "• 🎬 All Videos Accessible\n"
                "• ⚡️ Priority Speed\n"
                "• 🔒 Secure Connection\n\n"
                "👇 Click below to verify:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ VERIFY NOW (28 HOURS ACCESS)", url=short_link)],
                    [InlineKeyboardButton("📖 How to Verify", url=VERIFICATION_CHANNEL)]
                ])
            )
            return
        
        # Get file data
        file_data = None
        if files:
            try:
                file_data = files.find_one({"file_id": code})
            except Exception as e:
                print(f"❌ Error finding file: {e}")
        
        if not file_data:
            print(f"❌ File not found: {code}")
            await m.reply("❌ **File Not Found**\n\nThis link may be expired or invalid.")
            return
        
        try:
            print(f"📤 Sending file {code} to user {user_id}")
            
            # Send the file
            sent_message = await c.copy_message(
                chat_id=m.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=file_data['message_id'],
                protect_content=True  # Disable save/forward
            )
            
            # Send warning message
            warning_msg = await m.reply(
                f"⚠️ **IMPORTANT:** This video will be **automatically deleted** after **2 hours** ⏳\n\n"
                f"⏰ Please watch/download it before it's removed!\n"
                f"📥 Save it to your device if needed.\n\n"
                f"🔒 **Note:** Forwarding and saving in Telegram is disabled for security."
            )
            
            # Schedule auto-delete
            asyncio.create_task(delete_message_after_delay(m.chat.id, sent_message.id, 2))
            asyncio.create_task(delete_message_after_delay(m.chat.id, warning_msg.id, 2))
            
            # Update stats if database available
            if files:
                try:
                    files.update_one({"file_id": code}, {"$inc": {"downloads": 1}})
                except Exception as e:
                    print(f"❌ Error updating file stats: {e}")
            
            if users:
                try:
                    users.update_one({"user_id": user_id}, {"$inc": {"total_downloads": 1}})
                except Exception as e:
                    print(f"❌ Error updating user stats: {e}")
            
            # Mark free access as used
            if not is_user_verified and not has_free_today:
                mark_free_access_used(user_id)
                await m.reply(
                    "🎁 **FREE VIDEO ACCESSED!**\n\n"
                    "✅ You've used your **1 free video** for today!\n"
                    "🔓 Want more? Verify now for **28 HOURS** unlimited access!\n\n"
                    "⚡️ No limits, no restrictions!"
                )
            
            print(f"✅ File sent successfully! Auto-delete scheduled for 2 hours")
            
        except Exception as e:
            print(f"❌ Error sending file: {e}")
            await m.reply("❌ **Error:** Failed to send file. Please try again later.")
    
    else:
        # Welcome message
        welcome_text = f"""
🎬 **WELCOME TO PREMIUM 18+ CONTENT BOT** 🔥

👋 **Hey {first_name}!** Ready for some exclusive content? 😉

⚡️ **BOT FEATURES:**
✅ **Daily 1 FREE Video** - No verification needed!
✅ **28 HOURS Unlimited Access** after verification
✅ **Auto-Delete Videos** after 2 hours
✅ **Secure & Private** - No forwarding/saving allowed
✅ **High Quality Content**
✅ **24/7 Available** - Download anytime!

🎁 **TODAY'S SPECIAL:**
👉 Get **1 VIDEO FREE** right now!
👉 Verify for **28 HOURS** unlimited access!

🔞 **Age Restriction:**
This bot contains adult content. You must be 18+ to use.

👇 **GET STARTED:** Send me any file link or use /help
        """
        
        try:
            await m.reply_photo(
                photo=WELCOME_PHOTO,
                caption=welcome_text,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🚀 GET STARTED", callback_data="get_started"),
                        InlineKeyboardButton("🎬 FREE VIDEO", callback_data="free_video")
                    ],
                    [
                        InlineKeyboardButton("✅ HOW TO VERIFY", url=VERIFICATION_CHANNEL),
                        InlineKeyboardButton("📊 STATUS", callback_data="status")
                    ],
                    [
                        InlineKeyboardButton("📞 CONTACT", url=f"https://t.me/{CONTACT}"),
                        InlineKeyboardButton("🤖 ABOUT", callback_data="about")
                    ]
                ])
            )
        except Exception as e:
            # Fallback to text if photo fails
            print(f"❌ Error sending photo: {e}")
            await m.reply(
                welcome_text,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🚀 GET STARTED", callback_data="get_started"),
                        InlineKeyboardButton("🎬 FREE VIDEO", callback_data="free_video")
                    ],
                    [
                        InlineKeyboardButton("✅ HOW TO VERIFY", url=VERIFICATION_CHANNEL),
                        InlineKeyboardButton("📊 STATUS", callback_data="status")
                    ],
                    [
                        InlineKeyboardButton("📞 CONTACT", url=f"https://t.me/{CONTACT}"),
                        InlineKeyboardButton("🤖 ABOUT", callback_data="about")
                    ]
                ])
            )

@app.on_message(filters.command("help") & filters.private)
async def help_user(c, m):
    help_text = """
📖 **USER GUIDE & HELP** ⚡️

**🔰 HOW TO USE:**
1️⃣ Send me any file link
2️⃣ Get **1 FREE video daily** without verification
3️⃣ Verify for **28 HOURS** unlimited access
4️⃣ Enjoy exclusive content!

**🎯 FEATURES:**
• **Daily Free Video** - 1 video per day
• **Auto-Delete** - Videos delete in 2 hours
• **No Save/Forward** - Content protected
• **High Speed** - Fast downloads

**⚠️ IMPORTANT NOTES:**
• Videos auto-delete after 2 hours ⏳
• Download videos to your device
• Verification gives 28 hours access
• Age 18+ only

**📌 COMMANDS:**
/start - Start bot & check status
/help - This help message
/about - About this bot
/status - Check your remaining access

**🆘 NEED HELP?**
Contact: @SMARTHELPE1_BOT
    """
    
    await m.reply(
        help_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📖 VERIFICATION GUIDE", url=VERIFICATION_CHANNEL),
            InlineKeyboardButton("🚀 GET STARTED", url=f"https://t.me/{(await c.get_me()).username}")
        ]])
    )

@app.on_message(filters.command("status") & filters.private)
async def user_status(c, m):
    user_id = m.from_user.id
    
    is_user_verified = is_verified(user_id)
    has_free_today = has_free_access_today(user_id)
    
    if is_user_verified:
        try:
            user_data = users.find_one({"user_id": user_id}) if users else {}
            verified_at = user_data.get("verified_at", datetime.datetime.now() - datetime.timedelta(hours=1))
            time_remaining = 100800 - (datetime.datetime.now() - verified_at).total_seconds()
            hours = int(time_remaining // 3600)
            minutes = int((time_remaining % 3600) // 60)
            
            status_text = f"""
✅ **VERIFIED USER STATUS**

⏳ **Access Remaining:** {max(hours, 0)}h {max(minutes, 0)}m
📥 **Total Downloads:** {user_data.get('total_downloads', 0)}
👤 **Member Since:** {user_data.get('joined_at', datetime.datetime.now()).strftime('%Y-%m-%d') if user_data.get('joined_at') else 'Today'}

🎉 **You have unlimited access!**
⚡️ Download as much as you want!
            """
        except Exception as e:
            print(f"❌ Error in status check: {e}")
            status_text = "✅ **VERIFIED USER**\n\nYou have unlimited access for 28 hours!"
    else:
        free_status = "✅ AVAILABLE" if not has_free_today else "❌ USED TODAY"
        status_text = f"""
🔓 **UNVERIFIED USER STATUS**

🎁 **Free Video Today:** {free_status}
📥 **Total Downloads:** 0

⚠️ **Verify now for 28 HOURS access!**
👉 Get unlimited downloads!
        """
    
    await m.reply(
        status_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ VERIFY NOW", url=f"https://t.me/{(await c.get_me()).username}?start=verify_{user_id}")
        ]]) if not is_user_verified else None
    )

@app.on_message(filters.command("about") & filters.private)
async def about_user(c, m):
    bot_info = await c.get_me()
    
    about_text = f"""
🤖 **PREMIUM 18+ CONTENT BOT**

**Version:** 2.0 🚀
**Bot:** @{bot_info.username}
**Features:**
• Daily Free Access
• 28 Hours Unlimited
• Auto-Delete Videos
• Secure & Protected

**📜 Terms:**
• Age 18+ Only
• No Illegal Sharing
• Respect Privacy
• Follow Rules

**👨‍💻 Developer:** @SMARTHELPE1_BOT
**📞 Support:** @SMARTHELPE1_BOT

⚡️ **Enjoy exclusive content responsibly!**
        """
    
    await m.reply(about_text)

@app.on_callback_query()
async def handle_callback(c, query):
    user_id = query.from_user.id
    data = query.data
    
    if data == "get_started":
        await query.message.edit_text(
            "🚀 **GET STARTED GUIDE**\n\n"
            "1️⃣ Find any file link from our channels\n"
            "2️⃣ Send it to me\n"
            "3️⃣ Get your content instantly!\n\n"
            "🎁 **BONUS:** First video FREE every day!\n\n"
            "👇 Start by sending me a file link!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="back_to_start")
            ]])
        )
    
    elif data == "free_video":
        await query.answer("🎁 Check your free video status with /status", show_alert=True)
    
    elif data == "status":
        await query.answer()
        await user_status(c, query.message)
    
    elif data == "about":
        await query.answer()
        await about_user(c, query.message)
    
    elif data == "back_to_start":
        await query.message.delete()
        await start_user(c, query.message)
    
    await query.answer()

async def cleanup_old_records():
    """Cleanup old records"""
    while True:
        try:
            if free_usage:
                one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
                result = free_usage.delete_many({"used_at": {"$lt": one_day_ago}})
                if result.deleted_count > 0:
                    print(f"🧹 Cleaned {result.deleted_count} old free usage records")
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"❌ Error in cleanup: {e}")
            await asyncio.sleep(300)

async def main():
    """Main function to run the bot"""
    print("🚀 Starting User Bot...")
    
    # Start the cleanup task
    asyncio.create_task(cleanup_old_records())
    
    # Start the bot
    await app.start()
    print("✅ User Bot is running!")
    
    # Keep the bot running
    await idle()
    
    # Stop the bot
    await app.stop()
    print("🛑 Bot stopped")

if __name__ == "__main__":
    try:
        # Run the bot
        app.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
