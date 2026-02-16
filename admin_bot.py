# -*- coding: utf-8 -*-
"""
ADMIN BOT - COMPLETE STANDALONE VERSION
Sab kuch ek hi file mein - Railway friendly!
"""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import hashlib
from datetime import datetime
import asyncio

# ========== CONFIG ==========
API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"
ADMIN_BOT_TOKEN = "8596951434:AAF98nta7kfLKqeR9ImT5pUCTZoZ1rLFOwI"
CHANNEL_ID = -1003777551559
OWNER_ID = 6549083920
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"

# Bot settings
PRIMARY_BOT_USERNAME = "Filling4You_bot"
BACKUP_BOT_USERNAME = "FiLing4YoU_bot"

print("=" * 60)
print("🤖 ADMIN BOT STARTING...")
print(f"👑 Owner: {OWNER_ID}")
print(f"📁 Channel: {CHANNEL_ID}")
print("=" * 60)

# ========== DATABASE ==========
try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client['fileshare_dual']
    videos_db = db['videos']
    users_db = db['users']
    settings_db = db['settings']
    print("✅ Database connected!")
except Exception as e:
    print(f"❌ Database error: {e}")
    # Continue without database for now
    videos_db = None
    users_db = None
    settings_db = None

# ========== BOT ==========
app = Client("AdminBot", api_id=API_ID, api_hash=API_HASH, bot_token=ADMIN_BOT_TOKEN)

# ========== FUNCTIONS ==========

def generate_id():
    return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]

def get_active_bot():
    try:
        s = settings_db.find_one({"key": "active_bot"})
        return s['value'] if s else "primary"
    except:
        return "primary"

def set_active_bot(bot):
    try:
        settings_db.update_one({"key": "active_bot"}, {"$set": {"value": bot}}, upsert=True)
        return True
    except:
        return False

def get_bot_username():
    active = get_active_bot()
    return PRIMARY_BOT_USERNAME if active == "primary" else BACKUP_BOT_USERNAME

# ========== COMMANDS ==========

@app.on_message(filters.command("start") & filters.private)
async def start(c, m):
    if m.from_user.id != OWNER_ID:
        await m.reply("🔐 Admin only")
        return
    
    await m.reply(
        "👑 **Admin Panel**\n\n"
        "📤 Send video to upload\n\n"
        "**Commands:**\n"
        "/stats - Statistics\n"
        "/switch - Switch bot\n"
        "/broadcast - Broadcast message\n"
        "/info - System info"
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    try:
        total_videos = videos_db.count_documents({})
        total_users = users_db.count_documents({})
    except:
        total_videos = 0
        total_users = 0
    
    await m.reply(
        f"📊 **Stats**\n\n"
        f"📹 Videos: {total_videos}\n"
        f"👥 Users: {total_users}\n"
        f"🤖 Active: @{get_bot_username()}"
    )

@app.on_message(filters.command("switch") & filters.private)
async def switch(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    args = m.text.split()
    if len(args) < 2:
        await m.reply(
            f"🔄 **Switch Bot**\n\n"
            f"Current: @{get_bot_username()}\n\n"
            f"Usage:\n"
            f"`/switch primary`\n"
            f"`/switch backup`"
        )
        return
    
    new_bot = args[1].lower()
    if new_bot not in ["primary", "backup"]:
        await m.reply("❌ Use: primary or backup")
        return
    
    set_active_bot(new_bot)
    bot_name = PRIMARY_BOT_USERNAME if new_bot == "primary" else BACKUP_BOT_USERNAME
    
    await m.reply(f"✅ Switched to @{bot_name}")

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    if not m.reply_to_message:
        await m.reply(
            "📢 **Broadcast**\n\n"
            "Reply to a message with `/broadcast`"
        )
        return
    
    status = await m.reply("📤 Broadcasting...")
    
    try:
        user_ids = [u["user_id"] for u in users_db.find({}, {"user_id": 1})]
    except:
        await status.edit("❌ Database error!")
        return
    
    success = 0
    failed = 0
    
    for uid in user_ids:
        try:
            await m.reply_to_message.copy(uid)
            success += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status.edit(
        f"📢 **Complete!**\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )

@app.on_message(filters.command("info") & filters.private)
async def info(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    await m.reply(
        f"ℹ️ **System Info**\n\n"
        f"🤖 Admin: @{(await c.get_me()).username}\n"
        f"📦 Primary: @{PRIMARY_BOT_USERNAME}\n"
        f"🔄 Backup: @{BACKUP_BOT_USERNAME}\n\n"
        f"🎯 Active: @{get_bot_username()}"
    )

@app.on_message(filters.video & filters.private)
async def upload(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    status = await m.reply("⏳ Uploading...")
    
    try:
        fwd = await m.forward(CHANNEL_ID)
        vid_id = generate_id()
        
        fname = m.video.file_name or "video.mp4"
        fsize = m.video.file_size
        
        try:
            videos_db.insert_one({
                "video_id": vid_id,
                "message_id": fwd.id,
                "file_name": fname,
                "file_size": fsize,
                "uploaded_at": datetime.now(),
                "downloads": 0
            })
        except:
            pass
        
        bot_un = get_bot_username()
        link = f"https://t.me/{bot_un}?start={vid_id}"
        
        if fsize > 1024*1024:
            size = f"{fsize/(1024*1024):.2f} MB"
        else:
            size = f"{fsize/1024:.2f} KB"
        
        await status.edit(
            f"✅ **Uploaded!**\n\n"
            f"📁 {fname}\n"
            f"📊 {size}\n\n"
            f"🔗 `{link}`\n\n"
            f"🤖 @{bot_un}"
        )
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

print("🚀 Starting...")
app.run()
