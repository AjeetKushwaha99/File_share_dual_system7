# -*- coding: utf-8 -*-
"""
CONFIG FILE
Yaha sab settings hain - easy edit ke liye
"""

# ========== TELEGRAM API CREDENTIALS ==========
API_ID = 37067823
API_HASH = "ed9e62ed4538d2d2b835fb54529c358f"

# ========== BOT TOKENS ==========
ADMIN_BOT_TOKEN = "8596951434:AAF98nta7kfLKqeR9ImT5pUCTZoZ1rLFOwI"
USER_BOT_PRIMARY_TOKEN = "8537476620:AAHf1XxjpjFGJICxNAQ4i9A06gN0Z0ephDk"
USER_BOT_BACKUP_TOKEN = "7788869673:AAHheU98TueCNHmfOf6GERSHWEp9QwETyho"

# ========== CHANNEL & OWNER ==========
CHANNEL_ID = -1003777551559  # File storage channel
OWNER_ID = 6549083920  # Tumhara user ID

# ========== DATABASE ==========
MONGO_URL = "mongodb+srv://Ajeet:XgGFRFWVT2NwWipw@cluster0.3lxz0p7.mongodb.net/?appName=Cluster0"

# ========== SHORTENER ==========
SHORTENER_API = "5cbb1b2088d2ed06d7e9feae35dc17cc033169d6"
SHORTENER_URL = "https://vplink.in"

# ========== FEATURE SETTINGS ==========
VERIFICATION_HOURS = 26  # 26 hours verification
FREE_DAILY_LIMIT = 1  # 1 free video daily
AUTO_DELETE_HOURS = 2  # Auto-delete after 2 hours
HELP_CHANNEL = "https://t.me/fillings4you"  # How to verify guide

# ========== ACTIVE BOT SETTING ==========
# Ye setting decide karti hai kaun sa user bot active hai
# Options: "primary" ya "backup"
ACTIVE_USER_BOT = "primary"  # Default primary bot use hoga

# ========== BOT USERNAMES (for link generation) ==========
PRIMARY_BOT_USERNAME = "Filling4You_bot"
BACKUP_BOT_USERNAME = "FiLing4YoU_bot"

def get_active_bot_token():
    """Active bot ka token return karta hai"""
    if ACTIVE_USER_BOT == "primary":
        return USER_BOT_PRIMARY_TOKEN
    else:
        return USER_BOT_BACKUP_TOKEN

def get_active_bot_username():
    """Active bot ka username return karta hai"""
    if ACTIVE_USER_BOT == "primary":
        return PRIMARY_BOT_USERNAME
    else:
        return BACKUP_BOT_USERNAME

# ========== MESSAGES ==========
ADULT_WARNING = """
⚠️ **18+ ADULT WARNING** ⚠️

Ye bot adult content share karta hai.

🔞 18 saal se kam umr ke log please leave karein.

✅ Agar 18+ ho to continue karo.
"""

WELCOME_MESSAGE = """
👋 **Welcome {name}!**

🤖 **Premium Video Sharing Bot**

🎁 **Daily Free:** {left}/{total} videos

📌 **Features:**
• 🎁 {total} free video daily (no verification)
• ⏰ 26 hours access after verification
• 🔒 Protected videos (save/forward blocked)
• 🗑️ Auto-delete after 2 hours

❓ **Commands:**
/help - Complete guide
/mystats - Your usage stats

👇 **How to verify:**
"""

HELP_TEXT = """
📖 **Complete Guide**

**🎁 Daily Free Videos:**
• Har din 1 video bilkul FREE
• Koi verification nahi chahiye
• Midnight ko reset hota hai

**✅ Verification Benefits:**
• 26 hours unlimited access
• Jitne chahe videos download karo
• Koi daily limit nahi

**🔒 Video Protection:**
• Save disabled ❌
• Forward disabled ❌
• Auto-delete in 2 hours 🗑️

**❓ How to Verify:**
Visit guide channel for help!
"""
