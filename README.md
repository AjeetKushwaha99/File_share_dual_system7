# 🤖 Dual Bot File Sharing System

**Hindi Setup Guide - Step by Step**

---

## 📋 Project Overview

Ye ek **Dual Bot System** hai jisme:
- **1 Admin Bot** - Video upload aur management ke liye
- **2 User Bots** - Primary aur Backup (agar ek ban ho to dusra use karo)

**Features:**
- ✅ Daily 1 free video (no verification)
- ✅ 26 hours unlimited access after verification
- ✅ Auto-delete videos after 2 hours
- ✅ Protected content (save/forward disabled)
- ✅ Broadcast messages to all users
- ✅ Switch between primary/backup bot

---

## 🛠️ Setup Process

### **Step 1: GitHub Repository**

1. GitHub pe account banao
2. New repository: `fileshare-dual-bot`
3. Saari files upload karo:
   - config.py
   - database.py
   - admin_bot.py
   - user_bot.py
   - requirements.txt
   - Procfile

### **Step 2: MongoDB Setup**

1. mongodb.com pe jaao
2. Free cluster banao
3. Database user create karo
4. Connection string copy karo
5. `config.py` mein `MONGO_URL` update karo

### **Step 3: Telegram Setup**

**Bot Tokens:**
1. @BotFather se 3 bots banao:
   - Admin bot
   - User bot primary
   - User bot backup

2. `config.py` mein tokens update karo

**API Credentials:**
1. my.telegram.org pe jaao
2. API ID aur API Hash nikalo
3. `config.py` mein update karo

**Storage Channel:**
1. Private channel banao
2. Teeno bots ko admin banao
3. Channel ID nikalo (@JsonDumpBot use karo)
4. `config.py` mein update karo

### **Step 4: Railway Deployment**

**Admin Bot:**
1. Railway → New Project → GitHub
2. Select: fileshare-dual-bot
3. Service name: admin-bot
4. Start command: `python admin_bot.py`

**Primary User Bot:**
1. Same project → New Service
2. Service name: user-bot-primary
3. Environment Variable add:
   - `BOT_MODE = primary`
4. Start command: `python user_bot.py`

**Backup User Bot:**
1. Same project → New Service
2. Service name: user-bot-backup
3. Environment Variable add:
   - `BOT_MODE = backup`
4. Start command: `python user_bot.py`

---

## 📊 Usage Guide

### **Admin Bot Commands:**
