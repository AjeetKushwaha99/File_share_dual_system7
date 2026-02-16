from pyrogram import Client, filters
from pymongo import MongoClient
import datetime
import hashlib
import os

API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"
ADMIN_BOT_TOKEN = "8596951434:AAF98nta7kfLKqeR9ImT5pUCTZoZ1rLFOwI"
CHANNEL_ID = -1003777551559
OWNER_ID = 6549083920
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"
ACTIVE_USER_BOT = "Filling4You_bot"

print("🤖 Admin Bot Starting...")

mongo = MongoClient(MONGO_URL)
db = mongo['fileshare_system']
files = db['files']
users = db['users']
settings = db['settings']
print("✅ Database connected!")

app = Client("AdminBot", api_id=API_ID, api_hash=API_HASH, bot_token=ADMIN_BOT_TOKEN)

def generate_file_id():
    return hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:8]

def get_active_bot():
    setting = settings.find_one({"key": "active_user_bot"})
    if setting:
        return setting['value']
    return ACTIVE_USER_BOT

def set_active_bot(bot_username):
    settings.update_one({"key": "active_user_bot"}, {"$set": {"value": bot_username}}, upsert=True)

@app.on_message(filters.command("start") & filters.private)
async def start_admin(c, m):
    if m.from_user.id != OWNER_ID:
        await m.reply("🔐 Private admin bot.")
        return
    await m.reply(
        "👑 **Admin Control Panel**\n\n"
        "📤 Send file to upload\n\n"
        "**Commands:**\n"
        "/stats - Statistics\n"
        "/switch - Switch user bot\n"
        "/info - System info"
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats_admin(c, m):
    if m.from_user.id != OWNER_ID:
        return
    total_files = files.count_documents({})
    total_users = users.count_documents({})
    await m.reply(
        f"📊 **Statistics**\n\n"
        f"📁 Files: `{total_files}`\n"
        f"👥 Users: `{total_users}`\n"
        f"🤖 Active Bot: @{get_active_bot()}"
    )

@app.on_message(filters.command("switch") & filters.private)
async def switch_bot(c, m):
    if m.from_user.id != OWNER_ID:
        return
    if len(m.text.split()) < 2:
        await m.reply(
            f"🔄 **Switch Bot**\n\n"
            f"Usage: /switch bot_username\n\n"
            f"Example:\n"
            f"`/switch FiLing4YoU_bot`\n\n"
            f"Current: @{get_active_bot()}"
        )
        return
    new_bot = m.text.split()[1].replace("@", "")
    set_active_bot(new_bot)
    await m.reply(f"✅ Switched to @{new_bot}")

@app.on_message(filters.command("info") & filters.private)
async def info_admin(c, m):
    if m.from_user.id != OWNER_ID:
        return
    await m.reply(
        f"ℹ️ **System Info**\n\n"
        f"🤖 Admin: @FileshareADMINpanel_bot\n"
        f"📦 Primary: @Filling4You_bot\n"
        f"🔄 Backup: @FiLing4YoU_bot\n\n"
        f"🎯 Active: @{get_active_bot()}"
    )

@app.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private)
async def upload_file(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    status = await m.reply("⏳ Uploading...")
    
    try:
        forwarded = await m.forward(CHANNEL_ID)
        file_id = generate_file_id()
        
        file_name = "file"
        file_size = 0
        
        if m.document:
            file_name = m.document.file_name
            file_size = m.document.file_size
        elif m.video:
            file_name = "video.mp4"
            file_size = m.video.file_size
        elif m.audio:
            file_name = m.audio.file_name or "audio.mp3"
            file_size = m.audio.file_size
        elif m.photo:
            file_name = "photo.jpg"
        
        files.insert_one({
            "file_id": file_id,
            "message_id": forwarded.id,
            "file_name": file_name,
            "file_size": file_size,
            "uploaded_at": datetime.datetime.now(),
            "downloads": 0
        })
        
        active_bot = get_active_bot()
        link = f"https://t.me/{active_bot}?start={file_id}"
        
        if file_size > 1024*1024:
            size = f"{file_size/(1024*1024):.2f} MB"
        elif file_size > 1024:
            size = f"{file_size/1024:.2f} KB"
        else:
            size = f"{file_size} B"
        
        await status.edit(
            f"✅ **Uploaded!**\n\n"
            f"📁 {file_name}\n"
            f"📊 {size}\n\n"
            f"🔗 `{link}`\n\n"
            f"🤖 @{active_bot}"
        )
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

print("🚀 Starting Admin Bot...")
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(c, m):
    if m.from_user.id != OWNER_ID:
        return
    
    if len(m.text.split(None, 1)) < 2:
        await m.reply(
            "📢 **Broadcast Message**\n\n"
            "**Usage:**\n"
            "`/broadcast Your message here`\n\n"
            "**Example:**\n"
            "`/broadcast 🎉 New movies uploaded! Check now!`\n\n"
            "This will send message to ALL users!"
        )
        return
    
    broadcast_text = m.text.split(None, 1)[1]
    
    status = await m.reply("📤 **Broadcasting...**\n\n⏳ Please wait...")
    
    all_users = users.find()
    success = 0
    failed = 0
    
    for user in all_users:
        try:
            await c.send_message(user["user_id"], broadcast_text)
            success += 1
            await asyncio.sleep(0.05)  # Avoid flood
        except Exception as e:
            failed += 1
            print(f"Failed to send to {user['user_id']}: {e}")
    
    await status.edit(
        f"📢 **Broadcast Complete!**\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {success + failed}"
    )
app.run()
