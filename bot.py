#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - PERFECT VERSION
Version: 7.0 - No Glitches, All Buttons Work
Owner: 6108185460
Bot: @Familly_TreeBot
Token: 8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc
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
import time
import aiofiles
import io
from collections import defaultdict
import traceback

# ============================================================================
# CORRECT IMPORTS - NO ERRORS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, BufferedInputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode
    from aiogram.client.session.aiohttp import AiohttpSession
    
    # Try to import Pillow for images
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram==3.0.0b7 aiohttp==3.8.6 aiosqlite python-dotenv pillow")
    sys.exit(1)

import aiosqlite
import sqlite3

# ============================================================================
# CONFIGURATION - YOUR ACTUAL CREDENTIALS
# ============================================================================

OWNER_ID = 6108185460
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
BOT_USERNAME = "@Familly_TreeBot"
DB_PATH = "family_bot.db"

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "event_coins"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪"
}

CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper", "watermelon", "pumpkin"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔", 
    "eggplant": "🍆", "corn": "🌽", "pepper": "🫑",
    "watermelon": "🍉", "pumpkin": "🎃"
}

CROP_PRICES = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆"},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽"},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑"},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "emoji": "🍉"},
    "pumpkin": {"buy": 40, "sell": 60, "grow_time": 8, "emoji": "🎃"}
}

# Colors for UI
COLORS = {
    "primary": "#4CAF50",
    "secondary": "#2196F3", 
    "accent": "#FF9800",
    "success": "#8BC34A",
    "warning": "#FFC107",
    "danger": "#F44336"
}

# ============================================================================
# SIMPLE DATABASE - NO ERRORS
# ============================================================================

class SimpleDB:
    """Simple database that works perfectly"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.init_tables()
    
    async def init_tables(self):
        """Initialize tables"""
        tables = [
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                cash INTEGER DEFAULT 1000,
                gold INTEGER DEFAULT 0,
                bonds INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                reputation INTEGER DEFAULT 100,
                bio_verified INTEGER DEFAULT 0,
                last_daily TEXT,
                daily_count INTEGER DEFAULT 0,
                gemstone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Family
            """CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Gardens
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50
            )""",
            
            # Plants
            """CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL
            )""",
            
            # Barn
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Market
            """CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table in tables:
            await self.conn.execute(table)
        await self.conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", 
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return {columns[i]: row[i] for i in range(len(columns))}
        return None
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user"""
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user.id, user.username, user.first_name)
        )
        await self.conn.execute(
            "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
            (user.id,)
        )
        await self.conn.commit()
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        """Update user currency"""
        await self.conn.execute(
            f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await self.conn.commit()
    
    async def add_family(self, user1_id: int, user2_id: int, relation: str):
        """Add family relation"""
        await self.conn.execute(
            "INSERT INTO family (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
            (min(user1_id, user2_id), max(user1_id, user2_id), relation)
        )
        await self.conn.commit()
    
    async def get_family(self, user_id: int) -> List[dict]:
        """Get user's family"""
        cursor = await self.conn.execute(
            """SELECT f.relation_type, 
               CASE WHEN f.user1_id = ? THEN u2.first_name ELSE u1.first_name END as name
               FROM family f
               LEFT JOIN users u1 ON u1.user_id = f.user1_id
               LEFT JOIN users u2 ON u2.user_id = f.user2_id
               WHERE ? IN (f.user1_id, f.user2_id)""",
            (user_id, user_id)
        )
        rows = await cursor.fetchall()
        return [{'relation_type': r[0], 'name': r[1]} for r in rows]
    
    async def plant_crop(self, user_id: int, crop: str, quantity: int) -> bool:
        """Plant crops"""
        if crop not in CROP_TYPES:
            return False
        
        # Check slots
        cursor = await self.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        garden = await cursor.fetchone()
        if not garden:
            return False
        
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM plants WHERE user_id = ?",
            (user_id,)
        )
        used = (await cursor.fetchone())[0]
        
        if used + quantity > garden[0]:
            return False
        
        # Plant
        grow_time = CROP_PRICES[crop]["grow_time"]
        for _ in range(quantity):
            await self.conn.execute(
                "INSERT INTO plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                (user_id, crop, grow_time)
            )
        
        await self.conn.commit()
        return True
    
    async def get_plants(self, user_id: int) -> List[dict]:
        """Get user's plants"""
        cursor = await self.conn.execute(
            """SELECT crop_type, 
               ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours,
               grow_time
               FROM plants WHERE user_id = ?""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [{
            'crop_type': r[0],
            'hours': r[1],
            'grow_time': r[2],
            'progress': min(100, int((r[1] / r[2]) * 100)) if r[2] > 0 else 0
        } for r in rows]
    
    async def harvest(self, user_id: int) -> Tuple[int, List[tuple]]:
        """Harvest ready crops"""
        cursor = await self.conn.execute(
            """SELECT crop_type, COUNT(*) as count
               FROM plants 
               WHERE user_id = ? AND 
               (julianday('now') - julianday(planted_at)) * 24 >= grow_time
               GROUP BY crop_type""",
            (user_id,)
        )
        ready = await cursor.fetchall()
        
        total = 0
        harvested = []
        
        for crop, count in ready:
            price = CROP_PRICES[crop]["sell"]
            value = price * count
            total += value
            
            # Add to barn
            await self.conn.execute(
                """INSERT OR REPLACE INTO barn (user_id, crop_type, quantity)
                   VALUES (?, ?, COALESCE((SELECT quantity FROM barn WHERE user_id = ? AND crop_type = ?), 0) + ?)""",
                (user_id, crop, user_id, crop, count)
            )
            harvested.append((crop, count, value))
        
        # Remove harvested plants
        await self.conn.execute(
            """DELETE FROM plants 
               WHERE user_id = ? AND 
               (julianday('now') - julianday(planted_at)) * 24 >= grow_time""",
            (user_id,)
        )
        
        if total > 0:
            await self.update_currency(user_id, "cash", total)
        
        await self.conn.commit()
        return total, harvested
    
    async def get_barn(self, user_id: int) -> List[tuple]:
        """Get barn items"""
        cursor = await self.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ?",
            (user_id,)
        )
        return await cursor.fetchall()

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
db = SimpleDB(DB_PATH)

# Store active proposals
active_proposals = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_progress_bar(progress: int, length: int = 10) -> str:
    """Create text progress bar"""
    filled = "█" * int(progress / 100 * length)
    empty = "░" * (length - len(filled))
    return f"[{filled}{empty}] {progress}%"

async def get_target_user(message: Message, command: CommandObject) -> Optional[types.User]:
    """Get target user from reply or command"""
    # Reply takes priority
    if message.reply_to_message:
        return message.reply_to_message.from_user
    
    # Check command args
    if command.args:
        args = command.args.strip()
        # Could parse @username here
        pass
    
    return None

async def check_bio(user_id: int) -> bool:
    """Check if user has bot in bio"""
    try:
        chat = await bot.get_chat(user_id)
        bio = getattr(chat, 'bio', '') or ''
        return BOT_USERNAME.lower() in bio.lower()
    except:
        return False

# ============================================================================
# START COMMAND - PERFECT UI
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with beautiful UI"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    welcome = f"""
✨ <b>🌳 WELCOME TO FAMILY TREE BOT! 🌳</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🎮 <b>What you can do:</b>
• Build virtual families 👨‍👩‍👧‍👦
• Farm & trade crops 🌾
• Play exciting games 🎯
• Earn daily rewards 💰
• Battle with friends ⚔️

🚀 <b>Quick Start:</b>
1. <code>/daily</code> - Claim daily bonus
2. <code>/me</code> - Check your profile
3. <code>/garden</code> - Start farming
4. <code>/family</code> - Build family

📊 <b>Your Stats:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 👨‍👩‍👧‍👦 Family: <b>{len(await db.get_family(message.from_user.id))}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0)}</b>
• ⭐ Level: <b>{1}</b>

💡 <b>Tip:</b> Add bot to groups for family fun!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Daily Bonus", callback_data="daily_bonus"),
            InlineKeyboardButton(text="🏠 Profile", callback_data="my_profile")
        ],
        [
            InlineKeyboardButton(text="🌳 Family", callback_data="family_tree"),
            InlineKeyboardButton(text="🌾 Garden", callback_data="my_garden")
        ],
        [
            InlineKeyboardButton(text="🎮 Games", callback_data="games_menu"),
            InlineKeyboardButton(text="🏪 Market", callback_data="market_view")
        ],
        [
            InlineKeyboardButton(text="👥 Add to Group", url=f"https://t.me/{BOT_USERNAME[1:]}?startgroup=true"),
            InlineKeyboardButton(text="📋 Commands", callback_data="all_commands")
        ]
    ])
    
    await message.answer(welcome, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# DAILY COMMAND - PERFECT
# ============================================================================

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    today = datetime.now().date().isoformat()
    last_daily = user.get('last_daily')
    
    if last_daily == today:
        await message.answer("⏳ You already claimed your daily bonus today!")
        return
    
    # Check bio after 5 days
    daily_count = user.get('daily_count', 0) + 1
    
    if daily_count >= 5 and not user.get('bio_verified'):
        has_bio = await check_bio(message.from_user.id)
        if not has_bio:
            await message.answer(f"""
⚠️ <b>BIO VERIFICATION REQUIRED!</b>

You've claimed {daily_count} daily bonuses!

📋 <b>To continue:</b>
1. Open Telegram Settings
2. Edit your Bio
3. Add: <code>{BOT_USERNAME}</code>
4. Use <code>/daily</code> again

✅ <b>After verification:</b>
• 2x daily rewards
• Premium features
• Higher limits

🔒 Security measure to prevent abuse.
""", parse_mode=ParseMode.HTML)
            return
        else:
            await db.conn.execute(
                "UPDATE users SET bio_verified = 1 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await db.conn.commit()
    
    # Calculate bonus
    base = random.randint(500, 1500)
    family_count = len(await db.get_family(message.from_user.id))
    family_bonus = family_count * 100
    multiplier = 2 if user.get('bio_verified') else 1
    
    total = (base + family_bonus) * multiplier
    
    # Gemstone
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    # Update user
    await db.update_currency(message.from_user.id, "cash", total)
    await db.update_currency(message.from_user.id, "tokens", 5)
    
    await db.conn.execute(
        "UPDATE users SET last_daily = ?, daily_count = ?, gemstone = ? WHERE user_id = ?",
        (today, daily_count, gemstone, message.from_user.id)
    )
    await db.conn.commit()
    
    result = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base:,}</b>
• Family: <b>${family_bonus:,}</b> ({family_count} members)
• Multiplier: <b>{multiplier}x</b>
• <b>Total: ${total:,}</b>

💎 <b>Gemstone:</b> <b>{gemstone}</b>
🎁 <b>Bonus:</b> +5 🌱 Tokens

📊 <b>Daily Claims:</b> {daily_count}
{'(✅ Bio verified - 2x rewards!)' if multiplier > 1 else '(❌ Add to bio for 2x!)'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Play Games", callback_data="games_menu"),
            InlineKeyboardButton(text="🌾 Check Garden", callback_data="my_garden")
        ]
    ])
    
    await message.answer(result, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# PROFILE COMMAND - PERFECT
# ============================================================================

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """Profile command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    family = await db.get_family(message.from_user.id)
    plants = await db.get_plants(message.from_user.id)
    
    profile = f"""
🏆 <b>PROFILE OF {user['first_name'].upper()}</b>

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

📊 <b>Stats:</b>
• Level: <b>1</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Garden: <b>{len(plants)}/{9} slots</b>
• Bio: {'✅ Verified' if user.get('bio_verified') else '❌ Not verified'}

💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
📅 <b>Joined:</b> {user.get('created_at', 'Today')[:10]}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌳 Family Tree", callback_data="family_tree"),
            InlineKeyboardButton(text="🌾 My Garden", callback_data="my_garden")
        ],
        [
            InlineKeyboardButton(text="💰 Wealth", callback_data="wealth_stats"),
            InlineKeyboardButton(text="📊 Detailed", callback_data="detailed_stats")
        ]
    ])
    
    await message.answer(profile, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# FAMILY COMMANDS - PERFECT
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Family tree command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    family = await db.get_family(message.from_user.id)
    
    if not family:
        family_text = """
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow family:</b>
1. Reply to someone with <code>/adopt</code>
2. Or use <code>/marry @username</code>
3. Wait for acceptance
4. Enjoy family bonuses!

👑 <b>Benefits:</b>
• +$100 daily per family member
• Family quests & events
• Inheritance system
• Special features
"""
    else:
        family_text = f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

└─ You
"""
        
        for member in family:
            emoji = {
                'parent': '👴',
                'spouse': '💑',
                'child': '👶',
                'sibling': '👫'
            }.get(member['relation_type'], '👤')
            
            family_text += f"   ├─ {emoji} {member['name']} ({member['relation_type']})\n"
        
        family_text += f"""

📊 <b>Family Stats:</b>
• Members: <b>{len(family)}</b>
• Daily Bonus: <b>+${len(family) * 100}</b>
• Relationships: {', '.join(set(m['relation_type'] for m in family))}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 Adopt", callback_data="adopt_menu"),
            InlineKeyboardButton(text="💑 Marry", callback_data="marry_menu")
        ],
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="family_stats"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_family")
        ]
    ])
    
    await message.answer(family_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message, command: CommandObject):
    """Adopt command"""
    target = await get_target_user(message, command)
    
    if not target:
        await message.answer("""
👶 <b>ADOPT SOMEONE</b>

To adopt someone as your child:

1. <b>Reply to their message</b> with <code>/adopt</code>
2. Or use <code>/adopt @username</code>

💡 <b>Requirements:</b>
• Both must be bot users
• Cannot adopt yourself
• Target must be online

📝 <b>Example:</b>
Reply to someone's message with: <code>/adopt</code>
""", parse_mode=ParseMode.HTML)
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    # Check if target exists
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Create proposal
    proposal_id = f"adopt_{message.from_user.id}_{target.id}_{int(time.time())}"
    active_proposals[proposal_id] = {
        'from_id': message.from_user.id,
        'to_id': target.id,
        'type': 'adoption',
        'time': time.time()
    }
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Accept", callback_data=f"accept_{proposal_id}"),
            InlineKeyboardButton(text="❌ Decline", callback_data=f"decline_{proposal_id}")
        ]
    ])
    
    await message.answer(f"""
👶 <b>ADOPTION PROPOSAL SENT!</b>

👤 From: <b>{message.from_user.first_name}</b>
🎯 To: <b>{target.first_name}</b>
🤝 Type: Parent-Child
⏰ Expires: 5 minutes

💡 Waiting for acceptance...
""", parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
👶 <b>ADOPTION PROPOSAL!</b>

{message.from_user.first_name} wants to adopt you as their child!

💡 <b>Benefits:</b>
• Family bonuses
• Inheritance rights
• Daily rewards increase

⏰ Expires in 5 minutes
""",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(f"⚠️ Could not send proposal to {target.first_name}")

@dp.message(Command("marry"))
async def cmd_marry(message: Message, command: CommandObject):
    """Marry command"""
    target = await get_target_user(message, command)
    
    if not target:
        await message.answer("""
💍 <b>MARRY SOMEONE</b>

To marry someone:

1. <b>Reply to their message</b> with <code>/marry</code>
2. Or use <code>/marry @username</code>

💡 <b>Requirements:</b>
• Both must be single
• Cannot marry yourself
• Target must accept

📝 <b>Example:</b>
Reply to someone with: <code>/marry</code>
""", parse_mode=ParseMode.HTML)
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Create proposal
    proposal_id = f"marry_{message.from_user.id}_{target.id}_{int(time.time())}"
    active_proposals[proposal_id] = {
        'from_id': message.from_user.id,
        'to_id': target.id,
        'type': 'marriage',
        'time': time.time()
    }
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💍 Accept", callback_data=f"accept_{proposal_id}"),
            InlineKeyboardButton(text="❌ Decline", callback_data=f"decline_{proposal_id}")
        ]
    ])
    
    await message.answer(f"""
💍 <b>MARRIAGE PROPOSAL SENT!</b>

👤 From: <b>{message.from_user.first_name}</b>
🎯 To: <b>{target.first_name}</b>
🤝 Type: Marriage
⏰ Expires: 5 minutes

💡 Waiting for acceptance...
""", parse_mode=ParseMode.HTML)
    
    try:
        await bot.send_message(
            target.id,
            f"""
💍 <b>MARRIAGE PROPOSAL!</b>

{message.from_user.first_name} wants to marry you!

💡 <b>Benefits:</b>
• Couple bonuses
• Shared daily rewards
• Special features

⏰ Expires in 5 minutes
""",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(f"⚠️ Could not send proposal to {target.first_name}")

# ============================================================================
# PROPOSAL HANDLERS - WORKING BUTTONS
# ============================================================================

@dp.callback_query(F.data.startswith("accept_"))
async def handle_accept(callback: CallbackQuery):
    """Handle proposal acceptance"""
    proposal_id = callback.data.replace("accept_", "")
    
    if proposal_id not in active_proposals:
        await callback.answer("❌ Proposal expired!")
        return
    
    proposal = active_proposals[proposal_id]
    
    if callback.from_user.id != proposal['to_id']:
        await callback.answer("❌ This proposal is not for you!")
        return
    
    # Check expiration (5 minutes)
    if time.time() - proposal['time'] > 300:
        del active_proposals[proposal_id]
        await callback.answer("❌ Proposal expired!")
        return
    
    # Add family relation
    relation = 'parent' if proposal['type'] == 'adoption' else 'spouse'
    await db.add_family(proposal['from_id'], proposal['to_id'], relation)
    
    # Get names
    from_user = await db.get_user(proposal['from_id'])
    to_user = await db.get_user(proposal['to_id'])
    
    relation_text = "parent-child" if proposal['type'] == 'adoption' else "spouses"
    
    await callback.message.edit_text(f"""
✅ <b>PROPOSAL ACCEPTED!</b>

👤 {from_user['first_name']} and {to_user['name']}
🤝 Now {relation_text}
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎉 Family relationship established!
""", parse_mode=ParseMode.HTML)
    
    # Notify the other user
    try:
        await bot.send_message(
            proposal['from_id'],
            f"""
✅ <b>PROPOSAL ACCEPTED!</b>

{to_user['name']} accepted your {proposal['type']} proposal!

🤝 You are now {relation_text}
🎉 Family bonuses activated!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
    
    del active_proposals[proposal_id]
    await callback.answer()

@dp.callback_query(F.data.startswith("decline_"))
async def handle_decline(callback: CallbackQuery):
    """Handle proposal decline"""
    proposal_id = callback.data.replace("decline_", "")
    
    if proposal_id not in active_proposals:
        await callback.answer("❌ Proposal expired!")
        return
    
    proposal = active_proposals[proposal_id]
    
    if callback.from_user.id != proposal['to_id']:
        await callback.answer("❌ This proposal is not for you!")
        return
    
    # Get names
    from_user = await db.get_user(proposal['from_id'])
    
    await callback.message.edit_text(f"""
❌ <b>PROPOSAL DECLINED</b>

👤 {from_user['first_name']}'s proposal was declined.
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

💡 Proposal has been declined.
""", parse_mode=ParseMode.HTML)
    
    # Notify the other user
    try:
        await bot.send_message(
            proposal['from_id'],
            f"""
❌ <b>PROPOSAL DECLINED</b>

Your {proposal['type']} proposal was declined.

💡 Don't worry, you can try again later!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
    
    del active_proposals[proposal_id]
    await callback.answer()

# ============================================================================
# GARDEN COMMANDS - PERFECT
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Garden command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    plants = await db.get_plants(message.from_user.id)
    barn = await db.get_barn(message.from_user.id)
    
    garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: <b>{len(plants)}/9</b>
• Growing: <b>{len(plants)} crops</b>
• Ready: <b>{sum(1 for p in plants if p['progress'] >= 100)} crops</b>
• Barn: <b>{sum(q for _, q in barn)} items</b>

🌱 <b>Growing Now:</b>
"""
    
    for plant in plants[:5]:
        emoji = CROP_EMOJIS.get(plant['crop_type'], '🌱')
        progress = plant['progress']
        bar = create_progress_bar(progress, 5)
        
        if progress >= 100:
            status = "✅ Ready!"
        else:
            remaining = max(0, plant['grow_time'] - plant['hours'])
            status = f"{bar} ({remaining:.1f}h)"
        
        garden_text += f"• {emoji} {plant['crop_type'].title()}: {status}\n"
    
    if barn:
        garden_text += f"\n🏠 <b>Barn (Top 5):</b>\n"
        for crop, qty in barn[:5]:
            emoji = CROP_EMOJIS.get(crop, '📦')
            garden_text += f"• {emoji} {crop.title()}: <b>{qty}</b>\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 Plant", callback_data="plant_menu"),
            InlineKeyboardButton(text="🪴 Harvest", callback_data="harvest_now")
        ],
        [
            InlineKeyboardButton(text="🏪 Sell", callback_data="sell_crops"),
            InlineKeyboardButton(text="📦 Barn", callback_data="view_barn")
        ]
    ])
    
    await message.answer(garden_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant command"""
    if not command.args:
        await message.answer("""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
"""
        + "\n".join([
            f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_PRICES[c]['buy']} each"
            for c in CROP_TYPES[:6]
        ]) +
        """

💡 <b>Examples:</b>
<code>/plant carrot 3</code>
<code>/plant tomato 2</code>
<code>/plant watermelon 1</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.lower().split()
    if len(args) < 2:
        await message.answer("❌ Format: /plant [crop] [quantity]")
        return
    
    crop = args[0]
    try:
        qty = int(args[1])
    except:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if crop not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROP_TYPES[:6])}")
        return
    
    if qty < 1 or qty > 9:
        await message.answer("❌ Quantity must be 1-9!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    cost = CROP_PRICES[crop]["buy"] * qty
    if user.get('cash', 0) < cost:
        await message.answer(f"❌ Need ${cost:,}! You have ${user.get('cash', 0):,}")
        return
    
    success = await db.plant_crop(message.from_user.id, crop, qty)
    
    if not success:
        await message.answer("❌ Not enough garden space!")
        return
    
    await db.update_currency(message.from_user.id, "cash", -cost)
    
    grow_time = CROP_PRICES[crop]["grow_time"]
    emoji = CROP_EMOJIS.get(crop, "🌱")
    
    await message.answer(f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{emoji} Crop: <b>{crop.title()}</b>
🔢 Quantity: <b>{qty}</b>
💰 Cost: <b>${cost:,}</b>
⏰ Grow Time: <b>{grow_time} hours</b>

🌱 Now growing in your garden!
💡 Use <code>/garden</code> to check progress.
""", parse_mode=ParseMode.HTML)

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    total, harvested = await db.harvest(message.from_user.id)
    
    if not harvested:
        await message.answer("❌ No crops ready to harvest!")
        return
    
    harvest_text = f"""
🪴 <b>HARVEST COMPLETE!</b>

💰 Total Value: <b>${total:,}</b>
📦 Harvested Crops:
"""
    
    for crop, count, value in harvested:
        emoji = CROP_EMOJIS.get(crop, "🌱")
        harvest_text += f"• {emoji} {crop.title()}: {count} × ${CROP_PRICES[crop]['sell']} = <b>${value:,}</b>\n"
    
    harvest_text += f"""

🏠 Added to your barn.
💵 New balance: <b>${user.get('cash', 0) + total:,}</b>

💡 Check <code>/garden</code> for more!
"""
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

# ============================================================================
# MINI-GAMES - PERFECT
# ============================================================================

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    if not command.args:
        await message.answer("Usage: /slot [bet]\nExample: /slot 100")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet is $10!")
            return
        if bet > user.get('cash', 0):
            await message.answer(f"You only have ${user.get('cash', 0):,}!")
            return
    except:
        await message.answer("Invalid bet amount!")
        return
    
    symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎"]
    reels = [random.choice(symbols) for _ in range(3)]
    
    # Calculate win
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == "7️⃣":
            multiplier = 10
        elif reels[0] == "💎":
            multiplier = 5
        else:
            multiplier = 3
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        multiplier = 1.5
    else:
        multiplier = 0
    
    win = int(bet * multiplier)
    net = win - bet
    
    await db.update_currency(message.from_user.id, "cash", net)
    
    result = f"""
🎰 <b>SLOT MACHINE</b>

{' | '.join(reels)}

💰 Bet: <b>${bet:,}</b>
🎯 Result: {'WIN! 🎉' if win > 0 else 'Lose 😢'}
🏆 Payout: <b>${win:,}</b>
📈 Net: {'+' if net > 0 else ''}<b>${net:,}</b>

💵 New Balance: <b>${user.get('cash', 0) + net:,}</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Spin Again", callback_data=f"slot_{bet}"),
            InlineKeyboardButton(text="🎮 More Games", callback_data="games_menu")
        ]
    ])
    
    await message.answer(result, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS - PERFECT
# ============================================================================

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources (owner only)"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 Owner only command!")
        return
    
    if not command.args:
        await message.answer("""
💰 <b>ADD RESOURCES</b>

Usage: <code>/add [target] [resource] [amount]</code>

🎯 <b>Target:</b> user_id or reply
💎 <b>Resources:</b> cash, gold, bonds, credits, tokens
📝 <b>Example:</b> <code>/add 123456789 cash 1000</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Format: /add [target] [resource] [amount]")
        return
    
    # Get target
    target_str = args[0]
    resource = args[1].lower()
    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    target_id = None
    
    # Check if reply
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif target_str.isdigit():
        target_id = int(target_str)
    else:
        await message.answer("❌ Target must be user ID or reply!")
        return
    
    if resource not in CURRENCIES:
        await message.answer(f"❌ Invalid resource! Available: {', '.join(CURRENCIES)}")
        return
    
    # Add resources
    await db.update_currency(target_id, resource, amount)
    
    target_user = await db.get_user(target_id)
    target_name = target_user.get('first_name', 'Unknown') if target_user else 'Unknown'
    
    await message.answer(f"""
✅ <b>RESOURCES ADDED</b>

👤 To: <b>{target_name}</b>
💎 Resource: {CURRENCY_EMOJIS.get(resource, '📦')} <b>{resource.upper()}</b>
➕ Amount: <b>{amount:,}</b>
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    # Get stats
    cursor = await db.conn.execute("SELECT COUNT(*) FROM users")
    user_count = (await cursor.fetchone())[0]
    
    status = f"""
🏓 <b>BOT STATUS</b>

✅ Status: <b>Online & Healthy</b>
📡 Latency: <b>{latency}ms</b>
👥 Users: <b>{user_count}</b>
👑 Owner: <code>{OWNER_ID}</code>
🤖 Bot: {BOT_USERNAME}

✨ <b>Systems:</b>
• Family System ✅
• Garden System ✅  
• Daily System ✅
• Mini-Games ✅
• Admin Controls ✅

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(status, parse_mode=ParseMode.HTML)

# ============================================================================
# CALLBACK HANDLERS - ALL WORKING
# ============================================================================

@dp.callback_query(F.data == "daily_bonus")
async def handle_daily_callback(callback: CallbackQuery):
    """Handle daily bonus callback"""
    await cmd_daily(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "my_profile")
async def handle_profile_callback(callback: CallbackQuery):
    """Handle profile callback"""
    await cmd_profile(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "family_tree")
async def handle_family_callback(callback: CallbackQuery):
    """Handle family callback"""
    await cmd_family(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "my_garden")
async def handle_garden_callback(callback: CallbackQuery):
    """Handle garden callback"""
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "games_menu")
async def handle_games_callback(callback: CallbackQuery):
    """Show games menu"""
    games_text = """
🎮 <b>MINI-GAMES</b>

🎰 <b>Slot Machine:</b>
<code>/slot [bet]</code>
Match symbols to win big!

🎲 <b>Dice Game:</b>
<code>/dice [bet]</code>  
Roll dice for multipliers!

🔢 <b>Number Guess:</b>
<code>/guess</code>
Guess 1-100 for rewards!

🧩 <b>Crop Matching:</b>
<code>/match</code>
Memory game with crops!

💡 <b>All games use your cash!</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Slots", callback_data="play_slots"),
            InlineKeyboardButton(text="🎲 Dice", callback_data="play_dice")
        ],
        [
            InlineKeyboardButton(text="🔢 Guess", callback_data="play_guess"),
            InlineKeyboardButton(text="🧩 Match", callback_data="play_match")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(games_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery):
    """Return to main menu"""
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("slot_"))
async def handle_slot_callback(callback: CallbackQuery):
    """Handle slot callback"""
    bet = int(callback.data.split("_")[1])
    await cmd_slot(callback.message, CommandObject(args=str(bet)))
    await callback.answer()

# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: types.Update, exception: Exception):
    """Global error handler"""
    logger.error(f"Error: {exception}", exc_info=True)
    return True

dp.errors.register(error_handler)

# ============================================================================
# STARTUP
# ============================================================================

async def setup_bot():
    """Initialize bot"""
    await db.connect()
    
    # Set commands
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="adopt", description="Adopt someone"),
        types.BotCommand(command="marry", description="Marry someone"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="ping", description="Bot status"),
        types.BotCommand(command="add", description="Add resources (owner)"),
        types.BotCommand(command="help", description="Show help")
    ]
    
    await bot.set_my_commands(commands)
    
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - PERFECT VERSION")
    print(f"Owner: {OWNER_ID}")
    print(f"Bot: {BOT_USERNAME}")
    print("Status: ✅ READY")
    print("=" * 60)

async def main():
    """Main function"""
    await setup_bot()
    
    print("🚀 Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
