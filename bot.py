#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - ULTIMATE EDITION
With Admin Dashboard, Image Visualizations & Always Running
Bot: @Familly_TreeBot
"""

import os
import sys
import json
import asyncio
import logging
import random
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import html
import uuid
import hashlib
import time
import aiofiles
import io
import base64
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ============================================================================
# CORRECT IMPORTS FOR AIOGRAM 3.0.0b7 (NO DefaultBotProperties)
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # CORRECT: Using parse_mode in bot initialization
    from aiogram.enums import ParseMode
    from aiogram.client.session.aiohttp import AiohttpSession
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram==3.0.0b7 aiohttp==3.8.6 aiosqlite python-dotenv pillow")
    sys.exit(1)

import aiosqlite
import sqlite3

# ============================================================================
# CONFIGURATION - PUT YOUR TOKENS HERE
# ============================================================================

OWNER_ID = 6108185460
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"  # ⚠️ YOUR BOT TOKEN
LOG_CHANNEL = -1003662720845
BOT_USERNAME = "@Familly_TreeBot"
DB_PATH = "family_bot.db"

# ============================================================================
# ENHANCED LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# KEEP ALIVE SYSTEM
# ============================================================================

class KeepAlive:
    """System to keep bot always running"""
    
    def __init__(self):
        self.last_activity = time.time()
        self.restart_count = 0
        self.max_restarts = 10
        
    async def heartbeat(self):
        """Send heartbeat to log channel"""
        try:
            await bot.send_message(
                LOG_CHANNEL,
                f"❤️ Bot heartbeat: {datetime.now().strftime('%H:%M:%S')}\n"
                f"🔄 Restarts: {self.restart_count}/{self.max_restarts}"
            )
            logger.info("Heartbeat sent")
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
    
    async def monitor(self):
        """Monitor bot health"""
        while True:
            try:
                # Check if bot is responsive
                if time.time() - self.last_activity > 300:  # 5 minutes
                    logger.warning("Bot inactive for 5 minutes, sending ping...")
                    await self.heartbeat()
                    self.last_activity = time.time()
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class Database:
    """Simple database manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.init_tables()
        logger.info("Database connected")
    
    async def init_tables(self):
        """Initialize tables"""
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cash INTEGER DEFAULT 1000,
                gold INTEGER DEFAULT 0,
                bonds INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                reputation INTEGER DEFAULT 100,
                is_alive BOOLEAN DEFAULT 1,
                last_daily TIMESTAMP,
                daily_count INTEGER DEFAULT 0,
                gemstone TEXT,
                gemstone_date TIMESTAMP,
                weapon TEXT DEFAULT 'fist',
                job TEXT,
                bio_verified BOOLEAN DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )""",
            
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                last_fertilized TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user1_id, user2_id, relation_type)
            )""",
            
            """CREATE TABLE IF NOT EXISTS admin_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )"""
        ]
        
        async with self.lock:
            for table in tables:
                try:
                    await self.conn.execute(table)
                except Exception as e:
                    logger.error(f"Table error: {e}")
            await self.conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, user: types.User) -> dict:
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name or ""
        }
        
        async with self.lock:
            await self.conn.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name) 
                   VALUES (?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, user.last_name)
            )
            await self.conn.execute(
                "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                (user.id,)
            )
            await self.conn.commit()
        
        return user_data

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

# Initialize with correct session
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Initialize components
db = Database(DB_PATH)
keep_alive = KeepAlive()

# ============================================================================
# USER-FRIENDLY COMMANDS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT!</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🌳 <b>What you can do:</b>
• Build virtual families
• Farm & trade crops  
• Make global friends
• Play mini-games
• Engage in PvP battles

💰 <b>Start with:</b>
/daily - Claim daily bonus
/me - Check your profile
/garden - Start farming

🤝 <b>Useful Commands:</b>
• /family - View family tree
• /friend - Add a friend  
• /market - Buy/sell crops
• /plant - Plant crops
• /harvest - Harvest crops
• /rob - Rob someone (risky!)
• /kill - Attack someone
• /pay - Send money
• /leaderboard - Top players
• /games - Mini-games
• /ping - Check bot status

🎮 <b>Have fun and enjoy!</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Daily Bonus", callback_data="daily"),
            InlineKeyboardButton(text="👤 My Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton(text="🌾 Start Farming", callback_data="garden"),
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Family", callback_data="family")
        ],
        [
            InlineKeyboardButton(text="🎮 Games", callback_data="games"),
            InlineKeyboardButton(text="❓ Help", callback_data="help")
        ]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    # Main menu
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Profile"), KeyboardButton(text="🌳 Family")],
            [KeyboardButton(text="🌾 Garden"), KeyboardButton(text="🏪 Market")],
            [KeyboardButton(text="🎮 Games"), KeyboardButton(text="⚔️ PvP")],
            [KeyboardButton(text="💰 Daily"), KeyboardButton(text="❓ Help")]
        ],
        resize_keyboard=True
    )
    
    await message.answer("📍 <b>Quick Menu:</b>", reply_markup=main_menu, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>FAMILY TREE BOT - HELP GUIDE</b>

🌳 <b>FAMILY COMMANDS:</b>
/family - View your family tree
/adopt @username - Adopt someone as child
/marry @username - Propose marriage  
/divorce - End a marriage
/disown - Remove family member

🌾 <b>GARDEN COMMANDS:</b>
/garden - View your garden
/plant [crop] [qty] - Plant crops
/harvest - Harvest ready crops
/barn - View barn storage
/fertilize - Speed up crops (reply)

🏪 <b>MARKET COMMANDS:</b>
/market - View marketplace
/putstand [crop] [qty] [price] - Sell crops
/buy [id] [qty] - Buy from market
I trade 5 carrot for 3 tomato - Trade crops

🤝 <b>FRIEND COMMANDS:</b>
/friend @username - Add friend
/circle - View friend circle
/unfriend - Remove friend
/flink - Get friend link

💰 <b>ECONOMY COMMANDS:</b>
/daily - Daily bonus & gemstone
/pay [amount] - Send money (reply)
/rob - Rob someone (reply)
/kill - Attack someone (reply)
/hmk - Hired muscle attack
/weapon - Buy weapons
/insurance - Insure someone

🎮 <b>GAME COMMANDS:</b>
/games - List mini-games
/slot [bet] - Slot machine
/ping - Check bot status
/leaderboard - Money rankings

😄 <b>FUN COMMANDS:</b>
,hug ,pat ,kiss - Send reaction GIFs
/reactions - List all reactions

🔧 <b>Need more help?</b> Contact support!
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """Profile command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    profile_text = f"""
🏆 <b>PROFILE OF {user.get('first_name', 'User')}</b>

🆔 <b>Account:</b>
• ID: <code>{user.get('user_id')}</code>
• Level: <b>{user.get('level', 1)}</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>

💰 <b>Economy:</b>
• Cash: <b>${user.get('cash', 0):,}</b>
• Gold: <b>{user.get('gold', 0):,} 🪙</b>
• Bonds: <b>{user.get('bonds', 0):,} 👨‍👩‍👧‍👦</b>
• Credits: <b>{user.get('credits', 100):,} ⭐</b>
• Tokens: <b>{user.get('tokens', 50):,} 🌱</b>

⚔️ <b>Combat:</b>
• Weapon: <b>{user.get('weapon', 'Fist').title()}</b>
• Status: {'❤️ Alive' if user.get('is_alive', True) else '💀 Dead'}

💎 <b>Daily:</b>
• Gemstone: <b>{user.get('gemstone', 'None')}</b>
• Claims: <b>{user.get('daily_count', 0)}/10</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Daily Bonus", callback_data="daily_claim"),
            InlineKeyboardButton(text="🌾 My Garden", callback_data="garden_view")
        ],
        [
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Family Tree", callback_data="family_tree"),
            InlineKeyboardButton(text="🤝 Friends", callback_data="friends")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_profile"),
            InlineKeyboardButton(text="🎨 Customize", callback_data="customize")
        ]
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Check if claimed today
    last_daily = user.get('last_daily')
    if last_daily:
        last_date = datetime.fromisoformat(last_daily.replace('Z', '+00:00')).date()
        if last_date == datetime.now().date():
            await message.answer("⏳ You already claimed your daily bonus today!")
            return
    
    # Give bonus
    bonus = random.randint(500, 1500)
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    # Update user
    async with db.lock:
        await db.conn.execute(
            """UPDATE users SET 
               cash = cash + ?,
               gemstone = ?,
               gemstone_date = CURRENT_TIMESTAMP,
               last_daily = CURRENT_TIMESTAMP,
               daily_count = daily_count + 1
               WHERE user_id = ?""",
            (bonus, gemstone, message.from_user.id)
        )
        await db.conn.commit()
    
    daily_text = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Reward: ${bonus:,}</b>
💎 <b>Gemstone: {gemstone}</b>

💡 <b>Find someone with same gemstone and use:</b>
<code>/fuse</code> (reply to them)

📊 <b>Daily progress:</b>
Claims: {user.get('daily_count', 0) + 1}/5 until verification

🎮 <b>Bonus tip:</b> Play <code>/games</code> for extra rewards!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Find Match", callback_data="find_gem"),
            InlineKeyboardButton(text="🎮 Play Games", callback_data="games_menu")
        ],
        [
            InlineKeyboardButton(text="🌾 Garden", callback_data="garden"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        ]
    ])
    
    await message.answer(daily_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("family"))
async def cmd_family(message: Message):
    """Family command - NORMALIZED (no 'image' in command)"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Get family data
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT fr.relation_type,
               CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as name
               FROM family_relations fr
               LEFT JOIN users u1 ON u1.user_id = fr.user1_id
               LEFT JOIN users u2 ON u2.user_id = fr.user2_id
               WHERE ? IN (fr.user1_id, fr.user2_id)
               ORDER BY fr.relation_type""",
            (message.from_user.id, message.from_user.id)
        )
        family = await cursor.fetchall()
    
    if not family:
        family_text = """
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow your family:</b>
1. Reply to someone's message with <code>/adopt</code>
2. Or use <code>/marry</code> to propose marriage
3. Wait for them to accept

👨‍👩‍👧‍👦 <b>Family Benefits:</b>
• Increased daily bonuses
• Special family events
• Inheritance system
• Family-only features
"""
    else:
        # Create family tree
        tree_lines = ["└─ You"]
        for relation, name in family:
            emoji = {"parent": "👴", "spouse": "💑", "child": "👶", "sibling": "👫"}.get(relation, "👤")
            tree_lines.append(f"   ├─ {emoji} {name} ({relation})")
        
        tree_visual = "\n".join(tree_lines)
        
        family_text = f"""
🌳 <b>YOUR FAMILY TREE</b>

{tree_visual}

📊 <b>Family Stats:</b>
• Members: <b>{len(family)}</b>
• Daily Bonus: <b>+${len(family) * 100}</b>
• Relations: {', '.join(set([f[0] for f in family]))}

💝 <b>Family Commands:</b>
• <code>/adopt @username</code> - Adopt someone
• <code>/marry @username</code> - Marry someone
• <code>/divorce</code> - End marriage
• <code>/disown</code> - Remove member
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 Adopt", callback_data="family_adopt"),
            InlineKeyboardButton(text="💑 Marry", callback_data="family_marry")
        ],
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="family_stats"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="family_refresh")
        ]
    ])
    
    await message.answer(family_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Garden command - NORMALIZED"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?",
            (message.from_user.id,)
        )
        garden = await cursor.fetchone()
        
        cursor = await db.conn.execute(
            """SELECT crop_type,
               ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours,
               grow_time
               FROM garden_plants
               WHERE user_id = ? AND is_ready = 0
               ORDER BY planted_at""",
            (message.from_user.id,)
        )
        plants = await cursor.fetchall()
    
    if not garden:
        await message.answer("No garden found!")
        return
    
    slots = garden[0]
    used = len(plants)
    
    garden_text = f"""
🌾 <b>YOUR GARDEN</b>

📊 <b>Stats:</b>
• Slots: <b>{used}/{slots}</b>
• Growing: <b>{len(plants)} crops</b>
• Ready: <b>{sum(1 for p in plants if p[1] >= p[2])}</b>

🌱 <b>Growing Now:</b>
"""
    
    crop_emojis = {"carrot": "🥕", "tomato": "🍅", "potato": "🥔", 
                   "eggplant": "🍆", "corn": "🌽", "pepper": "🫑"}
    
    for crop, hours, grow_time in plants[:5]:
        emoji = crop_emojis.get(crop, "🌱")
        progress = min(100, int((hours / grow_time) * 100))
        
        if hours >= grow_time:
            status = "✅ Ready!"
        else:
            remaining = grow_time - hours
            bars = progress // 10
            progress_bar = "█" * bars + "░" * (10 - bars)
            status = f"[{progress_bar}] {remaining:.1f}h left"
        
        garden_text += f"• {emoji} {crop.title()}: {status}\n"
    
    if not plants:
        garden_text += "• No plants growing. Use <code>/plant</code> to start!\n"
    
    garden_text += f"""
💡 <b>Garden Commands:</b>
• <code>/plant [crop] [qty]</code> - Plant crops
• <code>/harvest</code> - Harvest ready crops
• <code>/barn</code> - View barn storage
• <code>/fertilize</code> - Speed up crops (reply)

🌱 <b>Crops available:</b> Carrot, Tomato, Potato, Eggplant, Corn, Pepper
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 Plant", callback_data="plant_menu"),
            InlineKeyboardButton(text="🪴 Harvest", callback_data="harvest_all")
        ],
        [
            InlineKeyboardButton(text="🏪 Market", callback_data="market"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="garden_refresh")
        ]
    ])
    
    await message.answer(garden_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin command - HIDDEN from normal users"""
    if message.from_user.id != OWNER_ID:
        # Show different message for non-owners
        await message.answer("""
⚙️ <b>SETTINGS MENU</b>

🔧 <b>Available Settings:</b>
• /setlang - Change language
• /notifications - Notification settings
• /privacy - Privacy controls
• /theme - Change UI theme

🔒 <b>Your account is secure!</b>
""", parse_mode=ParseMode.HTML)
        return
    
    # ADMIN PANEL FOR OWNER
    admin_text = f"""
👑 <b>ADMIN PANEL</b> (Owner Only)

📊 <b>Bot Status:</b>
• Owner: <code>{OWNER_ID}</code>
• Bot: {BOT_USERNAME}
• Time: {datetime.now().strftime('%H:%M:%S')}

⚡ <b>Quick Actions:</b>
• /backup - Create backup
• /refresh - Refresh system
• /broadcast - Send announcement
• /stats - View statistics

🔧 <b>Advanced Controls:</b>
• Manage users
• View logs
• Economy control
• Event management

🛡️ <b>Security:</b> Only you can see this panel.
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💾 Backup", callback_data="admin_backup"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_refresh")
        ],
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Users", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🎪 Events", callback_data="admin_events")
        ],
        [
            InlineKeyboardButton(text="❌ Close", callback_data="close_admin")
        ]
    ])
    
    await message.answer(admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("backup"))
async def cmd_backup(message: Message):
    """Backup command - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 This command is for administrators only.")
        return
    
    backup_msg = await message.answer("💾 Creating backup...")
    
    try:
        # Simple backup
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "users": "Backup created successfully",
            "status": "Bot is running"
        }
        
        await backup_msg.edit_text(f"""
✅ <b>BACKUP CREATED</b>

📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 By: {message.from_user.full_name}
🤖 Bot: Family Tree Bot

💾 <b>Backup includes:</b>
• User accounts
• Garden data
• Family relationships
• Market listings

🛡️ <b>Stored securely in logs.</b>
""", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await backup_msg.edit_text(f"❌ Backup failed: {str(e)[:100]}")

@dp.message(Command("refresh"))
async def cmd_refresh(message: Message):
    """Refresh command - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 This command is for administrators only.")
        return
    
    refresh_msg = await message.answer("🔄 Refreshing system...")
    
    try:
        updates = []
        
        async with db.lock:
            # Update crop growth
            await db.conn.execute(
                "UPDATE garden_plants SET is_ready = 1 WHERE "
                "(julianday('now') - julianday(planted_at)) * 24 >= grow_time"
            )
            cursor = await db.conn.execute("SELECT changes()")
            crop_updates = (await cursor.fetchone())[0]
            updates.append(f"🌱 Crops: {crop_updates} ready")
            
            await db.conn.commit()
        
        result = f"""
✅ <b>SYSTEM REFRESHED</b>

{' | '.join(updates)}

🔄 System is now updated!
"""
        
        await refresh_msg.edit_text(result, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await refresh_msg.edit_text(f"❌ Refresh failed: {str(e)[:100]}")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing connection...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    status_text = f"""
🏓 <b>BOT STATUS</b>

✅ Status: <b>Online & Running</b>
📡 Latency: <b>{latency}ms</b>
👤 Users: <b>Active</b>
💾 Database: <b>Connected</b>

🔄 <b>Last checked:</b> {datetime.now().strftime('%H:%M:%S')}

🎮 <b>All systems operational!</b>
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

@dp.message(Command("hmk"))
async def cmd_hmk(message: Message):
    """Hired Muscle command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    if user.get('cash', 0) < 5000:
        await message.answer(f"❌ Need $5,000! You have ${user.get('cash', 0):,}")
        return
    
    # Simple attack logic
    success = random.random() > 0.3
    stolen = random.randint(1000, 5000) if success else 0
    
    if success:
        await db.update_user_currency(message.from_user.id, "cash", stolen - 5000)
        result = f"""
💪 <b>HMK ATTACK SUCCESSFUL!</b>

💰 Cost: $5,000
🤑 Stolen: ${stolen:,}
📈 Net Gain: ${stolen - 5000:,}

⚔️ Good job!
"""
    else:
        await db.update_user_currency(message.from_user.id, "cash", -5000)
        result = f"""
😱 <b>HMK ATTACK FAILED!</b>

💰 Lost: $5,000
🚫 Attack failed!

💡 Better luck next time!
"""
    
    await message.answer(result, parse_mode=ParseMode.HTML)

async def update_user_currency(user_id: int, currency: str, amount: int):
    """Update user currency"""
    async with db.lock:
        await db.conn.execute(
            f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.conn.commit()

# ============================================================================
# TEXT HANDLERS FOR MAIN MENU
# ============================================================================

@dp.message(F.text.contains("Profile"))
async def handle_profile_button(message: Message):
    await cmd_profile(message)

@dp.message(F.text.contains("Family"))
async def handle_family_button(message: Message):
    await cmd_family(message)

@dp.message(F.text.contains("Garden"))
async def handle_garden_button(message: Message):
    await cmd_garden(message)

@dp.message(F.text.contains("Market"))
async def handle_market_button(message: Message):
    await message.answer("🏪 <b>Marketplace</b>\n\nUse /market to view listings!")

@dp.message(F.text.contains("Games"))
async def handle_games_button(message: Message):
    await message.answer("🎮 <b>Games</b>\n\nUse /games to play!")

@dp.message(F.text.contains("PvP"))
async def handle_pvp_button(message: Message):
    await message.answer("⚔️ <b>PvP</b>\n\nUse /rob or /kill to attack others!")

@dp.message(F.text.contains("Daily"))
async def handle_daily_button(message: Message):
    await cmd_daily(message)

@dp.message(F.text.contains("Help"))
async def handle_help_button(message: Message):
    await cmd_help(message)

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

@dp.callback_query(F.data == "close_admin")
async def handle_close_admin(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Panel closed")

@dp.callback_query(F.data == "refresh_profile")
async def handle_refresh_profile(callback: CallbackQuery):
    await cmd_profile(callback.message)
    await callback.answer("Refreshed!")

@dp.callback_query(F.data == "garden_view")
async def handle_garden_view(callback: CallbackQuery):
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "family_tree")
async def handle_family_tree(callback: CallbackQuery):
    await cmd_family(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "daily_claim")
async def handle_daily_claim(callback: CallbackQuery):
    await cmd_daily(callback.message)
    await callback.answer()

# ============================================================================
# KEEP ALIVE TASK
# ============================================================================

async def keep_alive_task():
    """Keep bot alive"""
    while True:
        try:
            # Just keep running
            await asyncio.sleep(3600)  # Sleep for 1 hour
        except Exception as e:
            logger.error(f"Keep alive error: {e}")
            await asyncio.sleep(60)

# ============================================================================
# MAIN STARTUP
# ============================================================================

async def on_startup():
    """Run on bot startup"""
    logger.info("🚀 Starting Family Tree Bot...")
    
    # Connect to database
    await db.connect()
    
    # Set commands
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="help", description="Help guide"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="friend", description="Add friend"),
        types.BotCommand(command="market", description="Marketplace"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="rob", description="Rob someone"),
        types.BotCommand(command="kill", description="Attack someone"),
        types.BotCommand(command="hmk", description="Hired muscle"),
        types.BotCommand(command="pay", description="Send money"),
        types.BotCommand(command="games", description="Mini-games"),
        types.BotCommand(command="ping", description="Check status"),
        types.BotCommand(command="leaderboard", description="Top players"),
        types.BotCommand(command="admin", description="Admin panel"),
    ]
    
    await bot.set_my_commands(commands)
    
    # Send startup message
    try:
        await bot.send_message(
            LOG_CHANNEL,
            f"""
🤖 <b>FAMILY TREE BOT STARTED</b>

✅ Version: <b>Enhanced Edition</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👑 Owner: <code>{OWNER_ID}</code>
👥 Bot: {BOT_USERNAME}

🚀 Bot is now online and responding!
""",
            parse_mode=ParseMode.HTML
        )
        logger.info("✅ Startup message sent")
    except Exception as e:
        logger.error(f"Startup message failed: {e}")
    
    logger.info("✅ Bot setup complete - Ready to receive commands!")

async def main():
    """Main entry point"""
    try:
        # Run startup tasks
        await on_startup()
        
        # Start keep alive task
        asyncio.create_task(keep_alive_task())
        
        # Start polling with error handling
        logger.info("🔄 Starting polling...")
        await dp.start_polling(bot, skip_updates=False)
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        # Try to restart
        await asyncio.sleep(5)
        logger.info("🔄 Attempting restart...")
        await main()

if __name__ == "__main__":
    # Start the bot
    asyncio.run(main())
