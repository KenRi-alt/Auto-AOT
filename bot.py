#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - ULTIMATE EDITION
With Visualizations, Mini-Games & Enhanced Features
Bot Username: @Familly_TreeBot
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
from collections import defaultdict

# ============================================================================
# CORRECT IMPORTS FOR AIOGRAM 3.0.0b7
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # CORRECT: Using parse_mode directly in bot initialization
    from aiogram.enums import ParseMode
    from aiogram.client.session.aiohttp import AiohttpSession
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram==3.0.0b7 aiohttp==3.8.6 aiosqlite python-dotenv")
    sys.exit(1)

import aiosqlite
import sqlite3

# ============================================================================
# CONFIGURATION
# ============================================================================

OWNER_ID = 6108185460
BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
LOG_CHANNEL = -1003662720845
BOT_USERNAME = "@Familly_TreeBot"
DB_PATH = os.getenv("DB_PATH", "family_bot.db")

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens"]
CURRENCY_EMOJIS = {"cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", "credits": "⭐", "tokens": "🌱"}

CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper"]
CROP_EMOJIS = {"carrot": "🥕", "tomato": "🍅", "potato": "🥔", "eggplant": "🍆", "corn": "🌽", "pepper": "🫑"}

CROP_PRICES = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆"},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽"},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑"}
}

# ============================================================================
# ENHANCED VISUALIZATION SYSTEM
# ============================================================================

class Visualizations:
    """Generate visual representations for data"""
    
    @staticmethod
    def create_progress_bar(percentage: int, length: int = 10) -> str:
        """Create text progress bar"""
        filled = int(length * percentage / 100)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}] {percentage}%"
    
    @staticmethod
    def create_family_tree_visual(family_data: List[dict]) -> str:
        """Create ASCII family tree"""
        if not family_data:
            return "└─ You (No family yet)"
        
        tree_lines = ["└─ You"]
        for member in family_data:
            rel_type = member.get('relation_type', 'unknown')
            name = member.get('first_name', 'Unknown')
            emoji = {"parent": "👴", "spouse": "💑", "child": "👶", "sibling": "👫"}.get(rel_type, "👤")
            tree_lines.append(f"   ├─ {emoji} {name} ({rel_type})")
        
        return "\n".join(tree_lines)
    
    @staticmethod
    def create_garden_grid(slots: int, used: int, plants: List[tuple]) -> str:
        """Create garden grid visualization"""
        grid = []
        plants_dict = {(i % 3, i // 3): plant for i, plant in enumerate(plants)}
        
        for y in range(3):
            row = []
            for x in range(3):
                idx = y * 3 + x
                if idx < slots:
                    if idx < used and (x, y) in plants_dict:
                        crop_type, progress = plants_dict[(x, y)]
                        emoji = CROP_EMOJIS.get(crop_type, "🌱")
                        row.append(f"{emoji}")
                    else:
                        row.append("🟫")
                else:
                    row.append("🔒")
            grid.append(" ".join(row))
        
        return "\n".join(grid)
    
    @staticmethod
    def create_wealth_graph(cash: int, max_cash: int = 10000) -> str:
        """Create wealth visualization"""
        bars = min(20, int(cash / max_cash * 20))
        return f"[{'💰' * bars}{'─' * (20 - bars)}] ${cash:,}"

# ============================================================================
# MINI-GAMES SYSTEM
# ============================================================================

class MiniGames:
    """Collection of mini-games for daily engagement"""
    
    @staticmethod
    async def slot_machine(bet: int) -> Tuple[int, str, List[str]]:
        """Slot machine game"""
        symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎"]
        reels = [random.choice(symbols) for _ in range(3)]
        
        # Calculate payout
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
        
        win_amount = int(bet * multiplier)
        win_text = f"🎰 {' | '.join(reels)} 🎰"
        
        return win_amount, win_text, reels
    
    @staticmethod
    async def number_guess() -> Tuple[bool, int, str]:
        """Number guessing game"""
        secret = random.randint(1, 100)
        return False, secret, "Guess a number between 1-100!"
    
    @staticmethod
    async def crop_matching() -> List[str]:
        """Crop matching memory game"""
        crops = random.sample(CROP_TYPES * 2, 6)
        random.shuffle(crops)
        return crops
    
    @staticmethod
    async def dice_roll(bet: int) -> Tuple[int, str]:
        """Dice rolling game"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        if total == 7:
            multiplier = 3
        elif total in [6, 8]:
            multiplier = 2
        elif total in [2, 12]:
            multiplier = 5
        else:
            multiplier = 0
        
        win = bet * multiplier
        dice_text = f"🎲 {dice1} + {dice2} = {total}"
        
        return win, dice_text

# ============================================================================
# ENHANCED DATABASE WITH DAILY LIMITS
# ============================================================================

class EnhancedDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.init_tables()
        logging.info("Database connected")
    
    async def init_tables(self):
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
                level INTEGER DEFAULT 1,
                group_promotion_shown BOOLEAN DEFAULT 0
            )""",
            
            """CREATE TABLE IF NOT EXISTS daily_limits (
                user_id INTEGER PRIMARY KEY,
                last_daily_date DATE,
                daily_count INTEGER DEFAULT 0,
                bio_required_since DATE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
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
            
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                last_fertilized TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                is_ready BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            """CREATE TABLE IF NOT EXISTS mini_game_scores (
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                PRIMARY KEY (user_id, game_type)
            )""",
            
            """CREATE TABLE IF NOT EXISTS user_groups (
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                PRIMARY KEY (user_id, group_id)
            )"""
        ]
        
        async with self.lock:
            for table in tables:
                await self.conn.execute(table)
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
            await self.conn.execute(
                "INSERT OR IGNORE INTO daily_limits (user_id) VALUES (?)",
                (user.id,)
            )
            await self.conn.commit()
        
        return user_data
    
    async def check_daily_limit(self, user_id: int) -> Tuple[bool, str, bool]:
        """Check if user can claim daily (with bio requirement after 5 days)"""
        today = datetime.now().date()
        
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT dl.last_daily_date, dl.daily_count, dl.bio_required_since,
                          u.bio_verified
                   FROM daily_limits dl
                   JOIN users u ON dl.user_id = u.user_id
                   WHERE dl.user_id = ?""",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return True, "", False
            
            last_date_str, count, bio_required_str, bio_verified = row
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date() if last_date_str else None
            bio_required = bool(bio_required_str)
            
            # Reset if new day
            if last_date != today:
                await self.conn.execute(
                    "UPDATE daily_limits SET daily_count = 0 WHERE user_id = ?",
                    (user_id,)
                )
                count = 0
                await self.conn.commit()
            
            # Check bio requirement (after 5 days)
            if count >= 5 and not bio_verified:
                if not bio_required:
                    await self.conn.execute(
                        "UPDATE daily_limits SET bio_required_since = ? WHERE user_id = ?",
                        (today.isoformat(), user_id)
                    )
                    await self.conn.commit()
                
                return False, "bio_required", True
            
            return count < 10, f"Daily claims: {count}/10", bio_required
    
    async def update_daily_claim(self, user_id: int):
        """Update daily claim count"""
        today = datetime.now().date()
        
        async with self.lock:
            await self.conn.execute(
                """INSERT OR REPLACE INTO daily_limits 
                   (user_id, last_daily_date, daily_count)
                   VALUES (?, ?, COALESCE(
                       (SELECT daily_count + 1 FROM daily_limits WHERE user_id = ?),
                       1
                   ))""",
                (user_id, today.isoformat(), user_id)
            )
            await self.conn.execute(
                "UPDATE users SET last_daily = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await self.conn.commit()
    
    async def verify_bio(self, user_id: int) -> bool:
        """Verify user has added bot to bio"""
        # This would require checking via Telegram API
        # For now, we'll simulate verification when user shows proof
        async with self.lock:
            await self.conn.execute(
                "UPDATE users SET bio_verified = 1 WHERE user_id = ?",
                (user_id,)
            )
            await self.conn.commit()
        return True

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize with correct session for aiogram 3.0.0b7
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

db = EnhancedDatabase(DB_PATH)
visual = Visualizations()
games = MiniGames()

# ============================================================================
# ENHANCED COMMAND HANDLERS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Enhanced start with group promotion option"""
    user = await db.get_user(message.from_user.id)
    
    # Create user if doesn't exist
    if not user:
        user = await db.create_user(message.from_user)
    
    # Check if we should show group promotion
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT group_promotion_shown FROM users WHERE user_id = ?",
            (message.from_user.id,)
        )
        row = await cursor.fetchone()
        promotion_shown = row[0] if row else 0
    
    welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT! {BOT_USERNAME}</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🎮 <b>What you can do:</b>
• 🌳 Build virtual families
• 🌾 Farm & trade crops  
• 🤝 Make global friends
• 🎮 Play mini-games
• ⚔️ Engage in PvP battles

💰 <b>Start with:</b>
<code>/daily</code> - Claim daily bonus
<code>/me</code> - Check your profile
<code>/garden</code> - Start farming

📊 <b>Visual Features:</b>
• Family tree diagrams
• Garden progress grids
• Wealth graphs
• Mini-game animations
"""
    
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="🎮 Quick Start", callback_data="quick_start"),
            InlineKeyboardButton(text="📋 Commands", callback_data="show_commands")
        ],
        [
            InlineKeyboardButton(text="💰 Daily Bonus", callback_data="daily_claim"),
            InlineKeyboardButton(text="🌾 Start Farming", callback_data="garden_main")
        ]
    ]
    
    # Add group promotion button if not shown yet
    if not promotion_shown:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="👥 Add to Group", 
                url=f"https://t.me/{BOT_USERNAME[1:]}?startgroup=true"
            )
        ])
        # Mark promotion as shown
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET group_promotion_shown = 1 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await db.conn.commit()
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="⚙️ Settings", callback_data="settings"),
        InlineKeyboardButton(text="❓ Help", callback_data="help")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    # Also show main menu
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Profile"), KeyboardButton(text="🌳 Family")],
            [KeyboardButton(text="🌾 Garden"), KeyboardButton(text="🏪 Market")],
            [KeyboardButton(text="🎮 Games"), KeyboardButton(text="⚔️ PvP")],
            [KeyboardButton(text="💰 Daily"), KeyboardButton(text="❓ Help")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option..."
    )
    
    await message.answer("📍 <b>Main Menu:</b>", reply_markup=main_menu, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Enhanced daily command with bio requirement after 5 uses"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Check daily limits
    can_claim, limit_msg, bio_required = await db.check_daily_limit(message.from_user.id)
    
    if bio_required:
        # Bio verification required
        bio_text = f"""
⚠️ <b>BIO VERIFICATION REQUIRED!</b>

You've claimed daily bonuses 5 times! To continue receiving bonuses:

<b>STEP 1:</b> Add both usernames to your Telegram bio:
1. {BOT_USERNAME}
2. Your username (or name)

<b>STEP 2:</b> Take a screenshot
<b>STEP 3:</b> Send the screenshot here

🔒 <b>Why this is required:</b>
• Prevents bot abuse
• Ensures active users
• Unlocks premium features

✅ <b>After verification, you'll get:</b>
• Double daily rewards
• Access to mini-games
• Premium garden boosts
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Send Screenshot", callback_data="verify_bio"),
                InlineKeyboardButton(text="❓ How to add bio", callback_data="bio_help")
            ],
            [
                InlineKeyboardButton(text="🔄 Check Again", callback_data="check_bio"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
            ]
        ])
        
        await message.answer(bio_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return
    
    if not can_claim:
        await message.answer(f"""
⏳ <b>DAILY LIMIT REACHED!</b>

{limit_msg}

💡 <b>Come back tomorrow for:</b>
• New daily bonus
• Fresh gemstone
• Family bonuses
• Mini-game tokens

🎮 <b>Play mini-games while waiting:</b>
<code>/games</code> - List all games
<code>/slot</code> - Slot machine
<code>/dice</code> - Dice game
""", parse_mode=ParseMode.HTML)
        return
    
    # Process daily bonus
    bonus = random.randint(500, 1500)
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    # Add family bonus
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM family_relations WHERE user1_id = ? OR user2_id = ?",
            (message.from_user.id, message.from_user.id)
        )
        family_count = (await cursor.fetchone())[0] // 2
    
    family_bonus = family_count * 100
    total_bonus = bonus + family_bonus
    
    # Update user
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET cash = cash + ?, gemstone = ?, gemstone_date = CURRENT_TIMESTAMP WHERE user_id = ?",
            (total_bonus, gemstone, message.from_user.id)
        )
        await db.conn.commit()
    
    await db.update_daily_claim(message.from_user.id)
    
    # Create visual progress bar
    _, limit_msg, _ = await db.check_daily_limit(message.from_user.id)
    daily_count = int(limit_msg.split(": ")[1].split("/")[0]) if "/" in limit_msg else 0
    progress = min(100, int(daily_count / 5 * 100))
    progress_bar = visual.create_progress_bar(progress)
    
    daily_text = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base Bonus: <b>${bonus:,}</b>
• Family Bonus: <b>${family_bonus:,}</b> ({family_count} members)
• <b>Total: ${total_bonus:,}</b>

💎 <b>Today's Gemstone:</b> <b>{gemstone}</b>
💡 Find someone with same gemstone and use <code>/fuse</code>

📊 <b>Daily Progress:</b>
{progress_bar}
{daily_count}/5 days until bio verification

🎮 <b>Bonus Mini-Game Token!</b>
Use <code>/slot 100</code> to play slots!

{visual.create_wealth_graph(user.get('cash', 0) + total_bonus)}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Find Gem Match", callback_data="find_gem"),
            InlineKeyboardButton(text="🎮 Play Games", callback_data="games_menu")
        ],
        [
            InlineKeyboardButton(text="🌾 Garden", callback_data="garden_view"),
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Family", callback_data="family_view")
        ]
    ])
    
    await message.answer(daily_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """Enhanced profile with visualizations"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Get stats
    async with db.lock:
        # Family count
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM family_relations WHERE user1_id = ? OR user2_id = ?",
            (message.from_user.id, message.from_user.id)
        )
        family_count = (await cursor.fetchone())[0] // 2
        
        # Friend count
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM (
                SELECT user2_id FROM family_relations WHERE user1_id = ?
                UNION
                SELECT user1_id FROM family_relations WHERE user2_id = ?
            )",
            (message.from_user.id, message.from_user.id)
        )
        friend_count = (await cursor.fetchone())[0]
        
        # Garden stats
        cursor = await db.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?",
            (message.from_user.id,)
        )
        garden_row = await cursor.fetchone()
        slots = garden_row[0] if garden_row else 9
        
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
            (message.from_user.id,)
        )
        growing = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute(
            "SELECT crop_type, planted_at, grow_time FROM garden_plants WHERE user_id = ? AND is_ready = 0",
            (message.from_user.id,)
        )
        plants = await cursor.fetchall()
    
    # Create garden visualization
    garden_vis = visual.create_garden_grid(slots, growing, [
        (plant[0], 50) for plant in plants[:slots]
    ])
    
    # Create wealth graph
    wealth_graph = visual.create_wealth_graph(user.get('cash', 0))
    
    profile_text = f"""
🏆 <b>PROFILE OF {user.get('first_name', 'User')}</b>

📊 <b>Stats:</b>
• Level: <b>{user.get('level', 1)}</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{family_count} members</b>
• Friends: <b>{friend_count}</b>

💰 <b>Economy:</b>
• Cash: <b>${user.get('cash', 0):,}</b>
• Gold: <b>{user.get('gold', 0):,}</b>
• Daily Claims: <b>{user.get('daily_count', 0)}</b>

🌾 <b>Garden:</b>
{garden_vis}
<b>Slots:</b> {growing}/{slots}

📈 <b>Wealth Graph:</b>
{wealth_graph}

💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
⚔️ <b>Weapon:</b> {user.get('weapon', 'Fist').title()}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌳 Family Tree", callback_data="family_tree"),
            InlineKeyboardButton(text="📊 Detailed Stats", callback_data="stats_detailed")
        ],
        [
            InlineKeyboardButton(text="🎮 Mini-Games", callback_data="games_menu"),
            InlineKeyboardButton(text="⚔️ PvP Arena", callback_data="pvp_arena")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_profile"),
            InlineKeyboardButton(text="🎨 Customize", callback_data="customize_profile")
        ]
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Enhanced garden with visualization"""
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
            """SELECT gp.crop_type, 
               ROUND((julianday('now') - julianday(gp.planted_at)) * 24, 1) as hours_passed,
               gp.grow_time,
               CASE WHEN (julianday('now') - julianday(gp.planted_at)) * 24 >= gp.grow_time THEN 1 ELSE 0 END as progress
               FROM garden_plants gp
               WHERE gp.user_id = ? AND gp.is_ready = 0
               ORDER BY gp.planted_at""",
            (message.from_user.id,)
        )
        plants = await cursor.fetchall()
        
        cursor = await db.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ? ORDER BY quantity DESC LIMIT 5",
            (message.from_user.id,)
        )
        barn = await cursor.fetchall()
    
    if not garden:
        await message.answer("No garden found!")
        return
    
    slots = garden[0]
    used = len(plants)
    
    # Create garden grid
    garden_grid = visual.create_garden_grid(slots, used, [
        (plant[0], int(plant[3] * 100)) for plant in plants
    ])
    
    garden_text = f"""
🌾 <b>YOUR GARDEN</b>

{garden_grid}

📊 <b>Stats:</b>
• Slots: <b>{used}/{slots}</b>
• Growing: <b>{len(plants)} crops</b>
• Ready: <b>{sum(1 for p in plants if p[3] >= 100)} crops</b>

🌱 <b>Growing Now:</b>
"""
    
    for plant in plants[:5]:
        crop_type, hours, grow_time, progress = plant
        emoji = CROP_EMOJIS.get(crop_type, "🌱")
        progress_pct = min(100, int(hours / grow_time * 100))
        progress_bar = visual.create_progress_bar(progress_pct, 5)
        
        if progress >= 100:
            status = "✅ Ready!"
        else:
            remaining = max(0, grow_time - hours)
            status = f"{progress_bar} ({remaining:.1f}h)"
        
        garden_text += f"• {emoji} {crop_type.title()}: {status}\n"
    
    if barn:
        garden_text += f"\n🏠 <b>Barn (Top 5):</b>\n"
        for crop, qty in barn:
            emoji = CROP_EMOJIS.get(crop, "📦")
            garden_text += f"• {emoji} {crop.title()}: <b>{qty}</b>\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 Plant Crops", callback_data="plant_menu"),
            InlineKeyboardButton(text="🪴 Harvest", callback_data="harvest_all")
        ],
        [
            InlineKeyboardButton(text="🏪 Sell Crops", callback_data="sell_crops"),
            InlineKeyboardButton(text="📦 View Barn", callback_data="view_barn")
        ],
        [
            InlineKeyboardButton(text="⚙️ Garden Upgrades", callback_data="garden_upgrades"),
            InlineKeyboardButton(text="💧 Fertilize", callback_data="fertilize_menu")
        ]
    ])
    
    await message.answer(garden_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("games"))
async def cmd_games(message: Message):
    """Show available mini-games"""
    games_text = """
🎮 <b>MINI-GAMES COLLECTION</b>

Earn extra cash and have fun with these games:

🎰 <b>Slot Machine:</b>
<code>/slot [bet]</code>
Example: <code>/slot 100</code>
Match symbols to win big!

🎲 <b>Dice Game:</b>
<code>/dice [bet]</code>
Roll dice and get multipliers!

🔢 <b>Number Guess:</b>
<code>/guess</code>
Guess the number 1-100 for rewards!

🧩 <b>Crop Matching:</b>
<code>/match</code>
Memory game with crop emojis!

🏆 <b>Daily Tournament:</b>
<code>/tournament</code>
Compete with other players!

💰 <b>All games use your cash as bets!</b>
💡 Start small and build your wealth!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Play Slots", callback_data="play_slots"),
            InlineKeyboardButton(text="🎲 Roll Dice", callback_data="play_dice")
        ],
        [
            InlineKeyboardButton(text="🔢 Number Game", callback_data="play_guess"),
            InlineKeyboardButton(text="🧩 Match Game", callback_data="play_match")
        ],
        [
            InlineKeyboardButton(text="🏆 Tournament", callback_data="join_tournament"),
            InlineKeyboardButton(text="📊 Leaderboard", callback_data="games_leaderboard")
        ]
    ])
    
    await message.answer(games_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine game"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    if not command.args:
        await message.answer("Usage: /slot [bet amount]\nExample: /slot 100")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet is $10!")
            return
        if bet > user.get('cash', 0):
            await message.answer(f"You only have ${user.get('cash', 0):,}! Bet less.")
            return
    except:
        await message.answer("Invalid bet amount! Use numbers only.")
        return
    
    # Play slot machine
    win_amount, win_text, reels = await games.slot_machine(bet)
    
    # Update user balance
    net_gain = win_amount - bet
    new_balance = user.get('cash', 0) + net_gain
    
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET cash = cash + ? WHERE user_id = ?",
            (net_gain, message.from_user.id)
        )
        await db.conn.commit()
    
    # Create slot visualization
    slot_display = f"""
{win_text}

{'🎰' * 3}
{' | '.join(reels)}
{'🎰' * 3}
"""
    
    result_text = f"""
🎰 <b>SLOT MACHINE RESULTS</b>

{slot_display}

💰 <b>Bet:</b> ${bet:,}
🎯 <b>Result:</b> {'WIN!' if win_amount > 0 else 'Lose'}
🏆 <b>Payout:</b> ${win_amount:,}
📈 <b>Net:</b> {'+' if net_gain > 0 else ''}${net_gain:,}

💵 <b>New Balance:</b> ${new_balance:,}

💡 <b>Tip:</b> {'Try again!' if net_gain < 0 else 'Good job!'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Spin Again", callback_data=f"slot_{bet}"),
            InlineKeyboardButton(text="🎮 More Games", callback_data="games_menu")
        ],
        [
            InlineKeyboardButton(text="💰 Double Bet", callback_data=f"slot_{bet*2}"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        ]
    ])
    
    await message.answer(result_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Enhanced family tree with visualization"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT fr.relation_type, 
               CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as name,
               CASE WHEN fr.user1_id = ? THEN u2.user_id ELSE u1.user_id END as id
               FROM family_relations fr
               LEFT JOIN users u1 ON u1.user_id = fr.user1_id
               LEFT JOIN users u2 ON u2.user_id = fr.user2_id
               WHERE ? IN (fr.user1_id, fr.user2_id)
               ORDER BY fr.relation_type, fr.created_at""",
            (message.from_user.id, message.from_user.id, message.from_user.id)
        )
        family = await cursor.fetchall()
    
    if not family:
        family_text = """
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow your family:</b>
1. Use <code>/adopt</code> (reply to someone) to adopt them as child
2. Use <code>/marry</code> (reply to someone) to marry them
3. Wait for them to accept your proposal

👨‍👩‍👧‍👦 <b>Family Benefits:</b>
• Daily bonus increases with family size
• Special family events
• Family chat features
• Inheritance system
"""
    else:
        # Create family tree visualization
        tree_lines = ["└─ You"]
        for relation, name, member_id in family:
            emoji = {"parent": "👴", "spouse": "💑", "child": "👶", "sibling": "👫"}.get(relation, "👤")
            tree_lines.append(f"   ├─ {emoji} {name} ({relation})")
        
        tree_visual = "\n".join(tree_lines)
        
        family_count = len(family)
        bonus = family_count * 100
        
        family_text = f"""
🌳 <b>YOUR FAMILY TREE</b>

{tree_visual}

📊 <b>Family Stats:</b>
• Members: <b>{family_count}</b>
• Daily Bonus: <b>+${bonus}</b> per day
• Relations: {', '.join(set([r[0] for r in family]))}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 Adopt Someone", callback_data="adopt_menu"),
            InlineKeyboardButton(text="💑 Marry Someone", callback_data="marry_menu")
        ],
        [
            InlineKeyboardButton(text="📊 Family Stats", callback_data="family_stats"),
            InlineKeyboardButton(text="👥 Find Family", callback_data="find_family")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh Tree", callback_data="refresh_family"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        ]
    ])
    
    await message.answer(family_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("backup"))
async def cmd_backup(message: Message):
    """Backup command - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Owner only command!")
        return
    
    backup_msg = await message.answer("🔄 Creating backup...")
    
    try:
        # Create backup data
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "users": [],
            "tables": {}
        }
        
        async with db.lock:
            # Get all tables
            cursor = await db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]
            
            for table in tables:
                cursor = await db.conn.execute(f"SELECT * FROM {table}")
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                table_data = []
                for row in rows:
                    table_data.append(dict(zip(columns, row)))
                
                backup_data["tables"][table] = table_data
        
        # Create backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
        
        # Send to owner
        backup_json = json.dumps(backup_data, indent=2, default=str)
        
        await bot.send_document(
            chat_id=OWNER_ID,
            document=BufferedInputFile(
                backup_json.encode(),
                filename=filename
            ),
            caption=f"🔐 Backup created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await backup_msg.edit_text("✅ Backup created and sent to owner!")
        
    except Exception as e:
        await backup_msg.edit_text(f"❌ Backup failed: {str(e)}")

@dp.message(Command("refresh"))
async def cmd_refresh(message: Message):
    """Refresh command - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Owner only command!")
        return
    
    refresh_msg = await message.answer("🔄 Refreshing system...")
    
    try:
        updates = []
        
        async with db.lock:
            # Update crop growth
            await db.conn.execute(
                "UPDATE garden_plants SET is_ready = 1 WHERE "
                "julianday('now') - julianday(planted_at) * 24 >= grow_time"
            )
            cursor = await db.conn.execute("SELECT changes()")
            crop_updates = (await cursor.fetchone())[0]
            updates.append(f"🌱 Crops: {crop_updates} ready")
            
            # Clear old proposals
            await db.conn.execute(
                "DELETE FROM proposals WHERE expires_at < CURRENT_TIMESTAMP"
            )
            cursor = await db.conn.execute("SELECT changes()")
            prop_updates = (await cursor.fetchone())[0]
            updates.append(f"📝 Proposals: {prop_updates} cleared")
            
            await db.conn.commit()
        
        result = f"""
✅ <b>SYSTEM REFRESHED</b>

{' | '.join(updates)}

🔄 Automatic refresh in 1 hour
"""
        
        await refresh_msg.edit_text(result, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await refresh_msg.edit_text(f"❌ Refresh failed: {str(e)}")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    status_text = f"""
🏓 <b>BOT STATUS</b>

✅ Bot: <b>Online</b>
📡 Latency: <b>{latency}ms</b>
👤 Users: <b>Loading...</b>
💾 Database: <b>Connected</b>
🎮 Games: <b>Ready</b>
🌾 Garden: <b>Active</b>

🔄 Last checked: {datetime.now().strftime('%H:%M:%S')}
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
        await message.answer("Need $5,000 to hire muscle!")
        return
    
    # Find target
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT user_id, first_name, cash FROM users WHERE user_id != ? AND cash > 1000 ORDER BY RANDOM() LIMIT 1",
            (message.from_user.id,)
        )
        target = await cursor.fetchone()
    
    if not target:
        await message.answer("No suitable targets found!")
        return
    
    target_id, target_name, target_cash = target
    
    # Calculate attack
    success = random.random() > 0.3  # 70% success
    stolen = min(int(target_cash * 0.3), 5000) if success else 0
    
    if success:
        # Update balances
        await db.update_user_currency(message.from_user.id, "cash", stolen - 5000)
        await db.update_user_currency(target_id, "cash", -stolen)
        
        result = f"""
💪 <b>HMK ATTACK SUCCESSFUL!</b>

💰 Cost: $5,000
🎯 Target: {target_name}
🤑 Stolen: ${stolen:,}
📈 Net Gain: ${stolen - 5000:,}

⚔️ Reputation decreased!
"""
    else:
        await db.update_user_currency(message.from_user.id, "cash", -5000)
        
        result = f"""
😱 <b>HMK ATTACK FAILED!</b>

💰 Lost: $5,000
🎯 Target: {target_name}
🚫 Muscle got scared!

💡 Better luck next time!
"""
    
    await message.answer(result, parse_mode=ParseMode.HTML)

# ============================================================================
# HELPER METHODS
# ============================================================================

async def update_user_currency(user_id: int, currency: str, amount: int):
    """Update user currency"""
    async with db.lock:
        await db.conn.execute(
            f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.conn.commit()

# ============================================================================
# CALLBACK QUERY HANDLERS
# ============================================================================

@dp.callback_query(F.data == "quick_start")
async def handle_quick_start(callback: CallbackQuery):
    await callback.message.answer("""
🚀 <b>QUICK START GUIDE</b>

1. <b>Claim Daily Bonus:</b>
   <code>/daily</code> - Get cash & gemstone

2. <b>Start Farming:</b>
   <code>/garden</code> - View your garden
   <code>/plant carrot 3</code> - Plant crops

3. <b>Make Friends:</b>
   <code>/friend</code> - Reply to someone

4. <b>Build Family:</b>
   <code>/adopt</code> or <code>/marry</code>

5. <b>Earn More:</b>
   <code>/market</code> - Buy/sell crops
   <code>/games</code> - Play mini-games

💡 <b>Pro Tip:</b> Complete the tutorial for bonus rewards!
""", parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "daily_claim")
async def handle_daily_claim(callback: CallbackQuery):
    await cmd_daily(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "garden_view")
async def handle_garden_view(callback: CallbackQuery):
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("slot_"))
async def handle_slot_callback(callback: CallbackQuery):
    bet = int(callback.data.split("_")[1])
    await cmd_slot(callback.message, CommandObject(args=str(bet)))
    await callback.answer()

@dp.callback_query(F.data == "verify_bio")
async def handle_verify_bio(callback: CallbackQuery):
    await callback.message.answer("📸 Please send a screenshot of your Telegram bio showing both usernames!")
    await callback.answer()

# ============================================================================
# MAIN BOT SETUP
# ============================================================================

async def setup_bot():
    """Initialize bot"""
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start bot & tutorial"),
        types.BotCommand(command="help", description="Show help"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="market", description="Marketplace"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="friend", description="Add friend"),
        types.BotCommand(command="games", description="Mini-games"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="ping", description="Check bot status"),
        types.BotCommand(command="backup", description="Backup (owner)"),
        types.BotCommand(command="refresh", description="Refresh (owner)"),
        types.BotCommand(command="hmk", description="Hired muscle attack"),
    ]
    
    await bot.set_my_commands(commands)
    
    # Send startup message
    try:
        await bot.send_message(
            LOG_CHANNEL,
            f"""
🤖 <b>FAMILY TREE BOT STARTED</b>

✅ Version: <b>Ultimate Edition</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👑 Owner: <code>{OWNER_ID}</code>
✨ Features: Visualizations + Mini-Games
👥 Bot: {BOT_USERNAME}

🚀 Ready for users!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
    
    logger.info("Bot setup complete!")

async def main():
    await setup_bot()
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Set BOT_TOKEN in .env file!")
        sys.exit(1)
    
    asyncio.run(main())
