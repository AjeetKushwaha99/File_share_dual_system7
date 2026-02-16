# -*- coding: utf-8 -*-
"""
USER BOT (DUAL SYSTEM)
Ye code DONO user bots ke liye use hoga (Primary + Backup)
Sirf token alag hoga, baaki sab same!
"""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import requests
from datetime import datetime
import os

import config
import database as db

# ========== BOT TOKEN DECIDE KARO ==========
# Environment variable se check karo kaun sa bot hai
BOT_MODE = os.environ.get("BOT_MODE", "primary")  # Default: primary

if BOT_MODE == "primary":
    BOT_TOKEN = config.USER_BOT_PRIMARY_TOKEN
    BOT_NAME = "PRIMARY"
    print("🤖 Running as: PRIMARY USER BOT")
elif BOT_MODE == "backup":
    BOT_TOKEN = config.USER_BOT_BACKUP_TOKEN
    BOT_NAME = "BACKUP"
    print("🤖 Running as: BACKUP USER BOT")
else:
    # Fallback to primary
    BOT_TOKEN = config.USER_BOT_PRIMARY_TOKEN
    BOT_NAME = "PRIMARY (Fallback)"
    print("⚠️ Invalid BOT_MODE, using PRIMARY")

print("=" * 60)
print(f"🤖 USER BOT STARTING ({BOT_NAME})...")
print(f"⏰ Verification: {config.VERIFICATION_HOURS} hours")
print(f"🎁 Daily free: {config.FREE_DAILY_LIMIT} videos")
print(f"🗑️ Auto-delete: {config.AUTO_DELETE_HOURS} hours")
print("=" * 60)

# ========== BOT INITIALIZE ==========
app = Client(
    f"UserBot_{BOT_NAME}",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=BOT_TOKEN
)

# ========== HELPER FUNCTIONS ==========

def shorten_url(url):
    """VPLinks se URL short karta hai"""
    try:
        api_url = f"{config.SHORTENER_URL}/api?api={config.SHORTENER_API}&url={url}"
        response = requests.get(api_url, timeout=10).json()
        
        if response.get("status") == "success":
            return response.get("shortenedUrl", url)
        return url
    except Exception as e:
        print(f"Shortener error: {e}")
        return url

async def auto_delete_message(chat_id, message_id, hours):
    """Message ko specified hours ke baad delete karta hai"""
    try:
        # Wait karo specified hours ke liye
        await asyncio.sleep(hours * 3600)
        
        # Message delete karo
        await app.delete_messages(chat_id=chat_id, message_ids=message_id)
        
        print(f"🗑️ Auto-deleted message {message_id} from chat {chat_id}")
        
    except Exception as e:
        print(f"❌ Auto-delete error: {e}")

# ========== START COMMAND ==========

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start_handler(client, message):
    """
    Start command handler
    - Adult warning dikha
    - User add karo database mein
    - Video request handle karo
    - Verification handle karo
    """
    user_id = message.from_user.id
    print(f"📥 /start from user: {user_id}")
    
    # User ko database mein add karo (agar naya hai)
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    # Check karo agar video request hai (link ke saath aaya)
    if len(message.text.split()) > 1:
        code = message.text.split()[1]
        print(f"📹 Video request: {code}")
        
        # ========== VERIFICATION CALLBACK HANDLE ==========
        if code.startswith("verify_"):
            db.verify_user(user_id)
            
            await message.reply(
                f"🎉 **Verification Successful!**\n\n"
                f"✅ Aapko **{config.VERIFICATION_HOURS} hours** ka unlimited access mil gaya!\n\n"
                f"📹 Ab aap unlimited videos download kar sakte ho.\n"
                f"⏰ Access {config.VERIFICATION_HOURS} hours baad expire hoga.\n\n"
                f"Thank you for verifying! 😊"
            )
            print(f"✅ User {user_id} verified successfully")
            return
        
        # ========== VIDEO REQUEST HANDLE ==========
        
        # Check user ka access status
        is_verified = db.is_user_verified(user_id)
        can_free = db.can_use_free_daily(user_id)
        
        print(f"User {user_id} status: verified={is_verified}, can_free={can_free}")
        
        # Agar verified nahi aur free bhi use kar chuka
        if not is_verified and not can_free:
            bot_username = (await client.get_me()).username
            verify_url = f"https://t.me/{bot_username}?start=verify_{user_id}"
            short_link = shorten_url(verify_url)
            
            print(f"🔐 Verification required for user {user_id}")
            
            await message.reply(
                f"🔐 **Verification Required**\n\n"
                f"⚠️ Aapne aaj ka free video use kar liya!\n\n"
                f"✅ **{config.VERIFICATION_HOURS} hours** unlimited access ke liye verify karein:\n\n"
                f"👇 Neeche diye buttons use karein:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Verify Now", url=short_link)],
                    [InlineKeyboardButton("❓ How to Verify?", url=config.HELP_CHANNEL)]
                ])
            )
            return
        
        # Video data nikalo database se
        video_data = db.get_video(code)
        
        if not video_data:
            print(f"❌ Video {code} not found in database")
            await message.reply(
                "❌ **Video Not Found!**\n\n"
                "Ye link invalid hai ya expire ho gaya hai.\n\n"
                "Please check the link and try again."
            )
            return
        
        # ========== VIDEO SEND KARO ==========
        try:
            print(f"📤 Sending video {code} to user {user_id}")
            
            # Agar free use kar raha hai to count badhao
            if not is_verified and can_free:
                db.increment_daily_usage(user_id)
                print(f"🎁 Free daily video used by user {user_id}")
            
            # Video send karo with PROTECTION
            sent_message = await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=config.CHANNEL_ID,
                message_id=video_data['message_id'],
                protect_content=True,  # 🔒 Save/Forward DISABLED!
                caption=(
                    f"⚠️ **AUTO-DELETE WARNING**\n\n"
                    f"📹 Ye video **{config.AUTO_DELETE_HOURS} hours** mein automatically delete ho jayega!\n\n"
                    f"⏰ Please pehle dekh lein.\n\n"
                    f"🔒 **Protection Active:**\n"
                    f"• Save disabled ❌\n"
                    f"• Forward disabled ❌\n"
                    f"• Download kar ke dekh sakte ho ✅"
                )
            )
            
            print(f"✅ Video sent! Message ID: {sent_message.id}")
            
            # Database stats update karo
            db.increment_download(code)
            db.increment_user_downloads(user_id)
            
            # AUTO-DELETE SCHEDULE KARO
            print(f"🗑️ Scheduling auto-delete for {config.AUTO_DELETE_HOURS} hours...")
            asyncio.create_task(
                auto_delete_message(message.chat.id, sent_message.id, config.AUTO_DELETE_HOURS)
            )
            
            print(f"✅ Auto-delete task scheduled successfully!")
            
            # Agar free video use kiya to reminder bhejo
            if not is_verified and can_free:
                await message.reply(
                    f"🎁 **Free Daily Video Used!**\n\n"
                    f"Aapne aaj ka free video use kar liya.\n\n"
                    f"💡 **Want unlimited access?**\n"
                    f"Verify karein aur {config.VERIFICATION_HOURS} hours unlimited videos paayen!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "✅ Verify Now",
                            url=shorten_url(f"https://t.me/{(await client.get_me()).username}?start=verify_{user_id}")
                        )
                    ]])
                )
            
        except Exception as e:
            print(f"❌ Error sending video: {e}")
            await message.reply(
                f"❌ **Error Occurred!**\n\n"
                f"Video send karne mein error aaya.\n\n"
                f"Error: `{str(e)}`\n\n"
                f"Please contact admin."
            )
    
    else:
        # ========== NORMAL START (NO VIDEO REQUEST) ==========
        
        # User ka daily usage check karo
        daily_left = config.FREE_DAILY_LIMIT - db.get_daily_usage(user_id)
        
        # Adult warning + Welcome message
        await message.reply(config.ADULT_WARNING)
        
        await asyncio.sleep(1)  # Thoda gap
        
        welcome_text = config.WELCOME_MESSAGE.format(
            name=message.from_user.first_name,
            left=daily_left,
            total=config.FREE_DAILY_LIMIT
        )
        
        await message.reply(
            welcome_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❓ How to Verify?", url=config.HELP_CHANNEL)
            ]])
        )

# ========== HELP COMMAND ==========

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_handler(client, message):
    """Help guide dikhata hai"""
    await message.reply(config.HELP_TEXT)

# ========== MYSTATS COMMAND ==========

@app.on_message(filters.command("mystats") & filters.private & ~filters.bot)
async def stats_handler(client, message):
    """User ka personal stats dikhata hai"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.reply("❌ Data nahi mila!")
        return
    
    total_downloads = user.get("total_downloads", 0)
    joined_date = user.get("joined_at", datetime.now())
    daily_used = db.get_daily_usage(user_id)
    is_verified = db.is_user_verified(user_id)
    
    # Status text banao
    if is_verified:
        verify_time = user.get("verified_at")
        time_passed = (datetime.now() - verify_time).total_seconds() / 3600
        remaining = config.VERIFICATION_HOURS - time_passed
        
        status_text = (
            f"✅ **Verified**\n"
            f"⏰ Remaining: {remaining:.1f} hours\n"
            f"🎁 Unlimited access active!"
        )
    else:
        left = config.FREE_DAILY_LIMIT - daily_used
        status_text = (
            f"🎁 **Free Mode**\n"
            f"📹 Videos left today: {left}/{config.FREE_DAILY_LIMIT}\n"
            f"⚠️ Verification pending"
        )
    
    await message.reply(
        f"📊 **Your Statistics**\n\n"
        f"👤 **User:** {message.from_user.first_name}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"**Status:**\n{status_text}\n\n"
        f"📥 **Total Downloads:** {total_downloads}\n"
        f"📆 **Today's Usage:** {daily_used}/{config.FREE_DAILY_LIMIT}\n"
        f"🗓️ **Member Since:** {joined_date.strftime('%d %b %Y')}\n\n"
        f"💡 Want unlimited access?\n"
        f"Verify for {config.VERIFICATION_HOURS} hours!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "✅ Verify Now",
                url=shorten_url(f"https://t.me/{(await client.get_me()).username}?start=verify_{user_id}")
            )
        ]])
    )

# ========== ABOUT COMMAND ==========

@app.on_message(filters.command("about") & filters.private & ~filters.bot)
async def about_handler(client, message):
    """Bot ke baare mein info"""
    bot_info = await client.get_me()
    
    await message.reply(
        f"ℹ️ **About This Bot**\n\n"
        f"🤖 **Bot:** @{bot_info.username}\n"
        f"📦 **Type:** Premium Video Sharing\n"
        f"🔐 **Security:** Protected Content\n"
        f"⚡ **Speed:** Fast Delivery\n"
        f"💯 **Reliability:** 24/7 Uptime\n\n"
        f"**Features:**\n"
        f"• {config.FREE_DAILY_LIMIT} free video daily\n"
        f"• {config.VERIFICATION_HOURS}hr verification access\n"
        f"• Auto-delete after {config.AUTO_DELETE_HOURS}hrs\n"
        f"• Save/Forward protected\n"
        f"• Secure storage\n\n"
        f"**Our Mission:**\n"
        f"Provide fast, secure, and free video sharing service!\n\n"
        f"Thank you for using! ❤️"
    )

# ========== RUN BOT ==========
print(f"🚀 Starting {BOT_NAME} User Bot...")
print("⏳ Connecting to Telegram...")

try:
    app.run()
    print(f"✅ {BOT_NAME} User Bot is running!")
except KeyboardInterrupt:
    print(f"⏹️ {BOT_NAME} User Bot stopped by user")
except Exception as e:
    print(f"❌ {BOT_NAME} User Bot error: {e}")
    import traceback
    traceback.print_exc()
