# -*- coding: utf-8 -*-
"""
DATABASE HELPER FUNCTIONS
MongoDB operations ke liye helper functions
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import config

# ========== DATABASE CONNECTION ==========
try:
    client = MongoClient(config.MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client['fileshare_dual_system']
    
    # Collections
    videos = db['videos']
    users = db['users']
    daily_usage = db['daily_usage']
    settings = db['settings']
    
    print("✅ Database connected successfully!")
    
except Exception as e:
    print(f"❌ Database connection error: {e}")
    raise

# ========== VIDEO FUNCTIONS ==========

def save_video(video_id, message_id, file_name, file_size):
    """Video ko database mein save karta hai"""
    try:
        videos.insert_one({
            "video_id": video_id,
            "message_id": message_id,
            "file_name": file_name,
            "file_size": file_size,
            "uploaded_at": datetime.now(),
            "downloads": 0,
            "active_bot": config.ACTIVE_USER_BOT
        })
        return True
    except Exception as e:
        print(f"❌ Save video error: {e}")
        return False

def get_video(video_id):
    """Video ID se video data return karta hai"""
    return videos.find_one({"video_id": video_id})

def increment_download(video_id):
    """Download count badhata hai"""
    videos.update_one(
        {"video_id": video_id},
        {"$inc": {"downloads": 1}}
    )

# ========== USER FUNCTIONS ==========

def add_user(user_id, username, first_name):
    """Naya user database mein add karta hai"""
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "verified_at": None,
            "joined_at": datetime.now(),
            "total_downloads": 0
        })
        print(f"✅ New user added: {user_id}")
        return True
    return False

def get_user(user_id):
    """User ka data return karta hai"""
    return users.find_one({"user_id": user_id})

def verify_user(user_id):
    """User ko verify karta hai - 26 hours access deta hai"""
    users.update_one(
        {"user_id": user_id},
        {"$set": {"verified_at": datetime.now()}}
    )
    print(f"✅ User verified: {user_id}")

def is_user_verified(user_id):
    """Check karta hai user verified hai ya nahi (26 hours)"""
    user = get_user(user_id)
    if not user or not user.get("verified_at"):
        return False
    
    # 26 hours = 26 * 3600 seconds
    time_diff = (datetime.now() - user["verified_at"]).total_seconds()
    return time_diff < (config.VERIFICATION_HOURS * 3600)

def increment_user_downloads(user_id):
    """User ka download count badhata hai"""
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"total_downloads": 1}}
    )

# ========== DAILY USAGE FUNCTIONS ==========

def get_daily_usage(user_id):
    """Aaj kitne videos download kiye"""
    today = datetime.now().date()
    usage = daily_usage.find_one({
        "user_id": user_id,
        "date": today
    })
    return usage.get("count", 0) if usage else 0

def increment_daily_usage(user_id):
    """Daily usage count badhata hai"""
    today = datetime.now().date()
    daily_usage.update_one(
        {"user_id": user_id, "date": today},
        {"$inc": {"count": 1}},
        upsert=True
    )

def can_use_free_daily(user_id):
    """Check karta hai daily free video use kar sakte hain"""
    return get_daily_usage(user_id) < config.FREE_DAILY_LIMIT

# ========== SETTINGS FUNCTIONS ==========

def get_active_bot():
    """Active user bot ka naam return karta hai"""
    setting = settings.find_one({"key": "active_user_bot"})
    if setting:
        return setting['value']
    return config.ACTIVE_USER_BOT

def set_active_bot(bot_name):
    """Active bot set karta hai (primary/backup)"""
    settings.update_one(
        {"key": "active_user_bot"},
        {"$set": {"value": bot_name}},
        upsert=True
    )
    print(f"✅ Active bot set: {bot_name}")

# ========== STATS FUNCTIONS ==========

def get_total_users():
    """Total users count"""
    return users.count_documents({})

def get_verified_users():
    """Verified users count"""
    return users.count_documents({"verified_at": {"$ne": None}})

def get_total_videos():
    """Total videos count"""
    return videos.count_documents({})

def get_all_user_ids():
    """Broadcast ke liye sab user IDs"""
    return [user["user_id"] for user in users.find({}, {"user_id": 1})]
