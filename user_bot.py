# -*- coding: utf-8 -*-
"""
USER BOT - COMPLETE STANDALONE VERSION
Works for both Primary & Backup (BOT_MODE env variable se decide hoga)
"""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import asyncio
import requests
from datetime import datetime
import os

# ========== CONFIG ==========
API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"

# Bot mode decide karo (Railway environment variable se)
BOT_MODE = os.environ.get("BOT_MODE", "primary")

if BOT_MODE == "backup":
    BOT_TOKEN = "7788869673:AAHheU98TueCNHmfOf6GERSHWEp9QwETyho"
    print("🤖 MODE: BACKUP BOT")
else:
    BOT_TOKEN = "8537476620:AAHf1XxjpjFGJICxNAQ4i9A06gN0Z0ephDk"
    print("🤖 MODE: PRIMARY BOT")

CHANNEL_ID = -1003777551559
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"
SHORTENER_API = "5cbb1b2088d2ed06d7e9feae35dc17cc033169d6"
SHORTENER_URL = "https://vplink.in"

# Settings
VERIFICATION_HOURS = 26
FREE_DAILY_LIMIT = 1
AUTO_DELETE_HOURS = 2
HELP_CHANNEL = "https://t.me/fillings4you"

print("=" * 60)
print(f"🤖 USER BOT STARTING ({BOT_MODE.upper()})...")
print(f"⏰ Verification: {VERIFICATION_HOURS}hrs")
print(f"🎁 Free daily: {FREE_DAILY_LIMIT}")
print("=" * 60)

# ========== DATABASE ==========
try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client['fileshare_dual']
    videos_db = db['videos']
    users_db = db['users']
    daily_usage_db = db['daily_usage']
    print("✅ Database connected!")
except Exception as e:
    print(f"❌ Database error: {e}")
    videos_db = None
    users_db = None
    daily_usage_db = None

# ========== BOT ==========
app = Client(f"UserBot_{BOT_MODE}", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ========== FUNCTIONS ==========

def shorten(url):
    try:
        r = requests.get(f"{SHORTENER_URL}/api?api={SHORTENER_API}&url={url}", timeout=10).json()
        return r.get("shortenedUrl", url)
    except:
        return url

async def auto_delete(chat_id, msg_id, hours):
    try:
        await asyncio.sleep(hours * 3600)
        await app.delete_messages(chat_id, msg_id)
        print(f"🗑️ Deleted message {msg_id}")
    except Exception as e:
        print(f"Delete error: {e}")

def add_user(uid, username, fname):
    try:
        if not users_db.find_one({"user_id": uid}):
            users_db.insert_one({
                "user_id": uid,
                "username": username,
                "first_name": fname,
                "verified_at": None,
                "joined_at": datetime.now()
            })
    except:
        pass

def is_verified(uid):
    try:
        u = users_db.find_one({"user_id": uid})
        if not u or not u.get("verified_at"):
            return False
        diff = (datetime.now() - u["verified_at"]).total_seconds()
        return diff < (VERIFICATION_HOURS * 3600)
    except:
        return False

def verify_user(uid):
    try:
        users_db.update_one({"user_id": uid}, {"$set": {"verified_at": datetime.now()}})
    except:
        pass

def get_daily_usage(uid):
    try:
        today = datetime.now().date()
        u = daily_usage_db.find_one({"user_id": uid, "date": today})
        return u.get("count", 0) if u else 0
    except:
        return 0

def increment_daily(uid):
    try:
        today = datetime.now().date()
        daily_usage_db.update_one(
            {"user_id": uid, "date": today},
            {"$inc": {"count": 1}},
            upsert=True
        )
    except:
        pass

def can_use_free(uid):
    return get_daily_usage(uid) < FREE_DAILY_LIMIT

def get_video(vid_id):
    try:
        return videos_db.find_one({"video_id": vid_id})
    except:
        return None

def increment_downloads(vid_id):
    try:
        videos_db.update_one({"video_id": vid_id}, {"$inc": {"downloads": 1}})
    except:
        pass

# ========== COMMANDS ==========

@app.on_message(filters.command("start") & filters.private & ~filters.bot)
async def start(c, m):
    uid = m.from_user.id
    print(f"📥 /start from {uid}")
    
    add_user(uid, m.from_user.username, m.from_user.first_name)
    
    if len(m.text.split()) > 1:
        code = m.text.split()[1]
        
        # Verify callback
        if code.startswith("verify_"):
            verify_user(uid)
            await m.reply(
                f"🎉 **Verified!**\n\n"
                f"✅ {VERIFICATION_HOURS} hours unlimited access!"
            )
            return
        
        # Video request
        verified = is_verified(uid)
        free = can_use_free(uid)
        
        if not verified and not free:
            bot_un = (await c.get_me()).username
            link = shorten(f"https://t.me/{bot_un}?start=verify_{uid}")
            
            await m.reply(
                f"🔐 **Verification Required**\n\n"
                f"⚠️ Daily limit used!\n\n"
                f"Verify for {VERIFICATION_HOURS}hrs access:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Verify", url=link)],
                    [InlineKeyboardButton("❓ How to Verify?", url=HELP_CHANNEL)]
                ])
            )
            return
        
        vid = get_video(code)
        if not vid:
            await m.reply("❌ Video not found!")
            return
        
        try:
            if not verified and free:
                increment_daily(uid)
            
            sent = await c.copy_message(
                m.chat.id,
                CHANNEL_ID,
                vid['message_id'],
                protect_content=True,
                caption=(
                    f"⚠️ **AUTO-DELETE in {AUTO_DELETE_HOURS}hrs!**\n\n"
                    f"🔒 Save/Forward disabled"
                )
            )
            
            increment_downloads(code)
            asyncio.create_task(auto_delete(m.chat.id, sent.id, AUTO_DELETE_HOURS))
            
        except Exception as e:
            await m.reply(f"❌ Error: {e}")
    
    else:
        # Adult warning
        await m.reply(
            "⚠️ **18+ ADULT WARNING** ⚠️\n\n"
            "18 saal se kam umr wale please leave karein.\n\n"
            "Continue?"
        )
        
        await asyncio.sleep(1)
        
        left = FREE_DAILY_LIMIT - get_daily_usage(uid)
        await m.reply(
            f"👋 Welcome {m.from_user.first_name}!\n\n"
            f"🎁 Daily free: {left}/{FREE_DAILY_LIMIT}\n\n"
            f"📌 Features:\n"
            f"• {FREE_DAILY_LIMIT} free video daily\n"
            f"• {VERIFICATION_HOURS}hr access\n"
            f"• Auto-delete {AUTO_DELETE_HOURS}hr\n\n"
            f"❓ /help",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❓ How to Verify?", url=HELP_CHANNEL)
            ]])
        )

@app.on_message(filters.command("help") & filters.private & ~filters.bot)
async def help_cmd(c, m):
    await m.reply(
        f"📖 **Guide**\n\n"
        f"🎁 {FREE_DAILY_LIMIT} free daily\n"
        f"✅ Verify for {VERIFICATION_HOURS}hr access\n"
        f"🗑️ Auto-delete: {AUTO_DELETE_HOURS}hr\n"
        f"🔒 Protected content\n\n"
        f"Guide: {HELP_CHANNEL}"
    )

@app.on_message(filters.command("mystats") & filters.private & ~filters.bot)
async def stats(c, m):
    uid = m.from_user.id
    verified = is_verified(uid)
    used = get_daily_usage(uid)
    
    status = f"✅ Verified" if verified else f"🎁 Free ({FREE_DAILY_LIMIT - used} left)"
    
    await m.reply(
        f"📊 **Your Stats**\n\n"
        f"Status: {status}\n"
        f"Today: {used}/{FREE_DAILY_LIMIT}"
    )

print("🚀 Starting...")
app.run()
