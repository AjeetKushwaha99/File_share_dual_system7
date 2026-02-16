# -*- coding: utf-8 -*-
"""
ADMIN BOT
Video upload, link generation, broadcast functionality
"""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import hashlib
from datetime import datetime
import asyncio

import config
import database as db

print("=" * 60)
print("🤖 ADMIN BOT STARTING...")
print(f"👑 Owner ID: {config.OWNER_ID}")
print(f"📁 Channel ID: {config.CHANNEL_ID}")
print(f"🎯 Active User Bot: {config.ACTIVE_USER_BOT}")
print("=" * 60)

# ========== BOT INITIALIZE ==========
app = Client(
    "AdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.ADMIN_BOT_TOKEN
)

# ========== HELPER FUNCTIONS ==========

def generate_video_id():
    """Unique 8-character video ID generate karta hai"""
    timestamp = str(datetime.now().timestamp())
    return hashlib.md5(timestamp.encode()).hexdigest()[:8]

def get_bot_username_for_link():
    """Active bot ka username link ke liye"""
    active_bot = db.get_active_bot()
    if active_bot == "primary":
        return config.PRIMARY_BOT_USERNAME
    else:
        return config.BACKUP_BOT_USERNAME

# ========== COMMANDS ==========

@app.on_message(filters.command("start") & filters.private)
async def admin_start(client, message):
    """Start command - admin panel dikhata hai"""
    if message.from_user.id != config.OWNER_ID:
        await message.reply("🔐 **Private Admin Bot**\n\nOnly owner can access.")
        return
    
    await message.reply(
        "👑 **Admin Control Panel**\n\n"
        "📤 **Upload Video:**\n"
        "Simply send video file to get share link\n\n"
        "📊 **Commands:**\n"
        "/stats - Bot statistics\n"
        "/switch - Switch user bot (primary/backup)\n"
        "/broadcast - Send message to all users\n"
        "/info - System information\n"
        "/help - Admin help guide"
    )

@app.on_message(filters.command("stats") & filters.private)
async def admin_stats(client, message):
    """Bot statistics dikhata hai"""
    if message.from_user.id != config.OWNER_ID:
        return
    
    total_users = db.get_total_users()
    verified_users = db.get_verified_users()
    total_videos = db.get_total_videos()
    active_bot = db.get_active_bot()
    
    await message.reply(
        f"📊 **Bot Statistics**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"✅ **Verified Users:** `{verified_users}`\n"
        f"📹 **Total Videos:** `{total_videos}`\n\n"
        f"🤖 **Active User Bot:** `{active_bot}`\n"
        f"💾 **Database:** Connected ✅\n"
        f"📡 **Status:** Active 🟢"
    )

@app.on_message(filters.command("switch") & filters.private)
async def switch_bot(client, message):
    """User bot switch karta hai (primary/backup)"""
    if message.from_user.id != config.OWNER_ID:
        return
    
    args = message.text.split()
    
    if len(args) < 2:
        current = db.get_active_bot()
        await message.reply(
            f"🔄 **Switch User Bot**\n\n"
            f"Current active: `{current}`\n\n"
            f"**Usage:**\n"
            f"`/switch primary` - Primary bot activate\n"
            f"`/switch backup` - Backup bot activate\n\n"
            f"**Bot Names:**\n"
            f"• primary = @{config.PRIMARY_BOT_USERNAME}\n"
            f"• backup = @{config.BACKUP_BOT_USERNAME}"
        )
        return
    
    new_bot = args[1].lower()
    
    if new_bot not in ["primary", "backup"]:
        await message.reply("❌ Invalid option! Use: primary or backup")
        return
    
    db.set_active_bot(new_bot)
    
    bot_username = config.PRIMARY_BOT_USERNAME if new_bot == "primary" else config.BACKUP_BOT_USERNAME
    
    await message.reply(
        f"✅ **Bot Switched Successfully!**\n\n"
        f"🆕 Active Bot: `{new_bot}`\n"
        f"🤖 Username: @{bot_username}\n\n"
        f"All new video links will use this bot!"
    )

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast(client, message):
    """Sabhi users ko message bhejta hai"""
    if message.from_user.id != config.OWNER_ID:
        return
    
    # Check agar message ka reply hai
    if not message.reply_to_message:
        await message.reply(
            "📢 **Broadcast Message**\n\n"
            "**Usage:**\n"
            "Jis message ko broadcast karna hai, usko reply karo aur type karo:\n"
            "`/broadcast`\n\n"
            "Bot automatically us message ko sabko bhej dega!"
        )
        return
    
    broadcast_message = message.reply_to_message
    
    status_msg = await message.reply("📤 **Broadcasting...**\n\n⏳ Please wait...")
    
    user_ids = db.get_all_user_ids()
    success = 0
    failed = 0
    blocked = 0
    
    for user_id in user_ids:
        try:
            await broadcast_message.copy(user_id)
            success += 1
            
            # Flood avoid ke liye thoda delay
            await asyncio.sleep(0.05)
            
        except Exception as e:
            error_text = str(e).lower()
            
            if "blocked" in error_text or "user is deactivated" in error_text:
                blocked += 1
            else:
                failed += 1
            
            print(f"Broadcast failed for {user_id}: {e}")
    
    await status_msg.edit(
        f"📢 **Broadcast Complete!**\n\n"
        f"✅ Success: `{success}`\n"
        f"🚫 Blocked: `{blocked}`\n"
        f"❌ Failed: `{failed}`\n"
        f"📊 Total: `{len(user_ids)}`"
    )

@app.on_message(filters.command("info") & filters.private)
async def system_info(client, message):
    """System information dikhata hai"""
    if message.from_user.id != config.OWNER_ID:
        return
    
    active_bot = db.get_active_bot()
    active_username = get_bot_username_for_link()
    
    await message.reply(
        f"ℹ️ **System Information**\n\n"
        f"**Bots:**\n"
        f"🤖 Admin: @{(await client.get_me()).username}\n"
        f"📦 Primary: @{config.PRIMARY_BOT_USERNAME}\n"
        f"🔄 Backup: @{config.BACKUP_BOT_USERNAME}\n\n"
        f"**Active:**\n"
        f"🎯 Mode: `{active_bot}`\n"
        f"🤖 Bot: @{active_username}\n\n"
        f"**Settings:**\n"
        f"⏰ Verification: {config.VERIFICATION_HOURS} hours\n"
        f"🎁 Daily free: {config.FREE_DAILY_LIMIT} videos\n"
        f"🗑️ Auto-delete: {config.AUTO_DELETE_HOURS} hours\n\n"
        f"📁 **Channel:** `{config.CHANNEL_ID}`\n"
        f"💾 **Database:** MongoDB Atlas\n"
        f"🔗 **Shortener:** VPLinks"
    )

@app.on_message(filters.command("help") & filters.private)
async def admin_help(client, message):
    """Admin help guide"""
    if message.from_user.id != config.OWNER_ID:
        return
    
    await message.reply(
        "📖 **Admin Help Guide**\n\n"
        "**📤 Video Upload:**\n"
        "• Simply send video file\n"
        "• Bot automatically processes\n"
        "• Share link generate hoga\n\n"
        "**🔄 Bot Switching:**\n"
        "Agar primary bot ban ho gaya:\n"
        "1. `/switch backup` command use karo\n"
        "2. New videos backup bot se share honge\n"
        "3. Old data safe rahega!\n\n"
        "**📢 Broadcast:**\n"
        "1. Message type karo\n"
        "2. Us message ko reply karo\n"
        "3. `/broadcast` command type karo\n"
        "4. Sabko send ho jayega!\n\n"
        "**📊 Stats:**\n"
        "`/stats` - Real-time statistics dekho"
    )

@app.on_message(filters.video & filters.private)
async def upload_video(client, message):
    """Video upload aur link generate karta hai"""
    if message.from_user.id != config.OWNER_ID:
        await message.reply("❌ Only admin can upload videos!")
        return
    
    status = await message.reply("⏳ **Processing video...**")
    
    try:
        # Video ko channel mein forward karo
        forwarded = await message.forward(config.CHANNEL_ID)
        
        # Unique video ID generate karo
        video_id = generate_video_id()
        
        # Video details
        file_name = message.video.file_name or "video.mp4"
        file_size = message.video.file_size
        
        # Database mein save karo
        db.save_video(video_id, forwarded.id, file_name, file_size)
        
        # Active bot ka username nikalo
        bot_username = get_bot_username_for_link()
        
        # Share link generate karo
        share_link = f"https://t.me/{bot_username}?start={video_id}"
        
        # File size format karo
        if file_size > 1024*1024*1024:  # GB
            size_str = f"{file_size/(1024*1024*1024):.2f} GB"
        elif file_size > 1024*1024:  # MB
            size_str = f"{file_size/(1024*1024):.2f} MB"
        else:
            size_str = f"{file_size/1024:.2f} KB"
        
        await status.edit(
            f"✅ **Video Uploaded Successfully!**\n\n"
            f"📁 **File:** `{file_name}`\n"
            f"📊 **Size:** `{size_str}`\n"
            f"🆔 **Video ID:** `{video_id}`\n\n"
            f"🔗 **Share Link:**\n`{share_link}`\n\n"
            f"🤖 **Using Bot:** @{bot_username}\n"
            f"📤 Share this link with users!"
        )
        
        print(f"✅ Video uploaded: {video_id} - {file_name}")
        
    except Exception as e:
        await status.edit(
            f"❌ **Upload Failed!**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"Please check:\n"
            f"• Bot is admin in channel\n"
            f"• Channel ID is correct"
        )
        print(f"❌ Upload error: {e}")

# ========== RUN BOT ==========
print("🚀 Starting Admin Bot...")
try:
    app.run()
    print("✅ Admin Bot is running!")
except Exception as e:
    print(f"❌ Admin Bot error: {e}")
