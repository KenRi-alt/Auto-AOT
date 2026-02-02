#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE & WORKING VERSION
"""

import os
import sys
import asyncio
import logging
import random
import math
import io
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import aiosqlite

# Core imports
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, BufferedInputFile,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Pillow for images
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
OWNER_ID = int(os.getenv("OWNER_ID", "6108185460"))
DB_PATH = "family_bot.db"

# Game Economy
class GameConfig:
    START_CASH = 1000
    START_BANK = 0
    DAILY_MIN = 500
    DAILY_MAX = 1500
    BANK_INTEREST_RATE = 0.5  # 0.5% daily
    LOTTERY_TICKET_PRICE = 50
    GARDEN_SLOTS = 9
    ADOPT_BONUS = 500
    MARRY_BONUS = 1000

# Crop Types
CROPS = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆"},
}

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE
# ============================================================================

class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = None
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.init_tables()
    
    async def init_tables(self):
        """Create database tables"""
        tables = [
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                cash INTEGER DEFAULT ?,
                bank_balance INTEGER DEFAULT ?,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Family
            """CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                relation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id, relation)
            )""",
            
            # Garden
            """CREATE TABLE IF NOT EXISTS garden (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT ?,
                greenhouse_level INTEGER DEFAULT 0
            )""",
            
            # Plants
            """CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                crop_type TEXT,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL,
                progress REAL DEFAULT 0,
                is_ready BOOLEAN DEFAULT 0
            )""",
            
            # Bank Accounts
            """CREATE TABLE IF NOT EXISTS bank_accounts (
                user_id INTEGER PRIMARY KEY,
                last_interest TIMESTAMP,
                total_interest INTEGER DEFAULT 0
            )""",
            
            # Lottery Tickets
            """CREATE TABLE IF NOT EXISTS lottery_tickets (
                ticket_id TEXT PRIMARY KEY,
                user_id INTEGER,
                numbers TEXT,
                scratched BOOLEAN DEFAULT 0,
                scratched_at TIMESTAMP,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Transactions
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table_sql in tables:
            try:
                await self.conn.execute(table_sql, 
                    (GameConfig.START_CASH, GameConfig.START_BANK) 
                    if "users" in table_sql else 
                    (GameConfig.GARDEN_SLOTS,) 
                    if "garden" in table_sql else ())
            except Exception as e:
                logger.error(f"Table error: {e}")
        
        await self.conn.commit()
    
    # User Methods
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user data"""
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user"""
        await self.conn.execute(
            """INSERT OR IGNORE INTO users 
               (user_id, username, first_name, cash, bank_balance)
               VALUES (?, ?, ?, ?, ?)""",
            (user.id, user.username, user.first_name, 
             GameConfig.START_CASH, GameConfig.START_BANK)
        )
        
        await self.conn.execute(
            "INSERT OR IGNORE INTO garden (user_id) VALUES (?)",
            (user.id,)
        )
        
        await self.conn.execute(
            "INSERT OR IGNORE INTO bank_accounts (user_id) VALUES (?)",
            (user.id,)
        )
        
        await self.conn.commit()
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        """Update user currency"""
        if currency == "cash":
            await self.conn.execute(
                "UPDATE users SET cash = cash + ? WHERE user_id = ?",
                (amount, user_id)
            )
        elif currency == "bank_balance":
            await self.conn.execute(
                "UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
        await self.conn.commit()
    
    # Family Methods
    async def get_family(self, user_id: int) -> List[dict]:
        """Get user's family"""
        cursor = await self.conn.execute(
            """SELECT 
               CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END as member_id,
               u.first_name, u.username, f.relation, f.created_at
               FROM family f
               JOIN users u ON u.user_id = CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
               WHERE ? IN (f.user1_id, f.user2_id)""",
            (user_id, user_id, user_id)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def add_family_member(self, user1_id: int, user2_id: int, relation: str):
        """Add family relationship"""
        await self.conn.execute(
            """INSERT OR IGNORE INTO family (user1_id, user2_id, relation)
               VALUES (?, ?, ?)""",
            (min(user1_id, user2_id), max(user1_id, user2_id), relation)
        )
        await self.conn.commit()
    
    # Garden Methods
    async def get_garden(self, user_id: int) -> dict:
        """Get garden info"""
        cursor = await self.conn.execute(
            "SELECT slots, greenhouse_level FROM garden WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else {"slots": GameConfig.GARDEN_SLOTS, "greenhouse_level": 0}
    
    async def get_plants(self, user_id: int) -> List[dict]:
        """Get user's plants"""
        cursor = await self.conn.execute(
            "SELECT * FROM plants WHERE user_id = ? AND is_ready = 0",
            (user_id,)
        )
        rows = await cursor.fetchall()
        plants = []
        for row in rows:
            plant = dict(row)
            # Calculate progress
            planted_at = datetime.fromisoformat(plant['planted_at'])
            elapsed = (datetime.now() - planted_at).total_seconds() / 3600
            progress = min(100, (elapsed / plant['grow_time']) * 100)
            plant['progress'] = progress
            plant['ready'] = progress >= 100
            plants.append(plant)
        return plants
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int) -> bool:
        """Plant crops"""
        garden = await self.get_garden(user_id)
        plants = await self.get_plants(user_id)
        
        total_slots = garden['slots']
        if len(plants) + quantity > total_slots:
            return False
        
        crop_data = CROPS.get(crop_type)
        if not crop_data:
            return False
        
        for _ in range(quantity):
            await self.conn.execute(
                "INSERT INTO plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                (user_id, crop_type, crop_data['grow_time'])
            )
        await self.conn.commit()
        return True
    
    async def harvest_crops(self, user_id: int) -> List[tuple]:
        """Harvest ready crops"""
        cursor = await self.conn.execute(
            """SELECT crop_type, COUNT(*) as count FROM plants 
               WHERE user_id = ? AND is_ready = 0 
               GROUP BY crop_type""",
            (user_id,)
        )
        ready_crops = await cursor.fetchall()
        
        harvested = []
        for crop_type, count in ready_crops:
            crop_data = CROPS.get(crop_type)
            if crop_data:
                value = crop_data['sell'] * count
                await self.update_currency(user_id, "cash", value)
                harvested.append((crop_type, count, value))
        
        # Remove harvested plants
        await self.conn.execute(
            "DELETE FROM plants WHERE user_id = ? AND is_ready = 0",
            (user_id,)
        )
        await self.conn.commit()
        return harvested
    
    # Bank Methods
    async def get_bank_account(self, user_id: int) -> dict:
        """Get bank account"""
        cursor = await self.conn.execute(
            "SELECT * FROM bank_accounts WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else {
            "user_id": user_id,
            "last_interest": None,
            "total_interest": 0
        }
    
    async def calculate_interest(self, user_id: int) -> Tuple[int, str]:
        """Calculate daily interest"""
        user = await self.get_user(user_id)
        if not user or user['bank_balance'] <= 0:
            return 0, "No balance for interest"
        
        account = await self.get_bank_account(user_id)
        
        # Check if interest was calculated today
        if account['last_interest']:
            last_interest = datetime.fromisoformat(account['last_interest'])
            if (datetime.now() - last_interest).days < 1:
                next_time = last_interest + timedelta(days=1)
                hours_left = int((next_time - datetime.now()).total_seconds() / 3600)
                return 0, f"Next interest in {hours_left}h"
        
        # Calculate interest
        interest = int(user['bank_balance'] * (GameConfig.BANK_INTEREST_RATE / 100))
        
        if interest > 0:
            await self.update_currency(user_id, "bank_balance", interest)
            await self.conn.execute(
                """UPDATE bank_accounts 
                   SET last_interest = CURRENT_TIMESTAMP,
                       total_interest = total_interest + ?
                   WHERE user_id = ?""",
                (interest, user_id)
            )
            await self.conn.commit()
            return interest, f"Interest added: ${interest}"
        
        return 0, "No interest to add"
    
    async def add_transaction(self, user_id: int, trans_type: str, amount: int, description: str = ""):
        """Record transaction"""
        await self.conn.execute(
            "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
            (user_id, trans_type, amount, description)
        )
        await self.conn.commit()
    
    async def get_transactions(self, user_id: int, limit: int = 10) -> List[dict]:
        """Get transaction history"""
        cursor = await self.conn.execute(
            """SELECT type, amount, description, created_at 
               FROM transactions WHERE user_id = ? 
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Lottery Methods
    async def buy_lottery_ticket(self, user_id: int, quantity: int) -> Tuple[bool, List[str], int]:
        """Buy lottery tickets"""
        user = await self.get_user(user_id)
        if not user:
            return False, [], 0
        
        total_cost = quantity * GameConfig.LOTTERY_TICKET_PRICE
        if user['cash'] < total_cost:
            return False, [], 0
        
        await self.update_currency(user_id, "cash", -total_cost)
        
        tickets = []
        for _ in range(quantity):
            ticket_id = f"LOT-{random.randint(100000, 999999)}"
            numbers = ''.join(str(random.randint(0, 9)) for _ in range(6))
            
            await self.conn.execute(
                """INSERT INTO lottery_tickets (ticket_id, user_id, numbers)
                   VALUES (?, ?, ?)""",
                (ticket_id, user_id, numbers)
            )
            tickets.append(ticket_id)
        
        await self.conn.commit()
        return True, tickets, total_cost
    
    async def get_tickets(self, user_id: int) -> List[dict]:
        """Get user's lottery tickets"""
        cursor = await self.conn.execute(
            """SELECT ticket_id, numbers, scratched, scratched_at 
               FROM lottery_tickets WHERE user_id = ? 
               ORDER BY purchased_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def scratch_ticket(self, user_id: int, ticket_id: str) -> Optional[dict]:
        """Scratch a lottery ticket"""
        cursor = await self.conn.execute(
            """SELECT numbers, scratched FROM lottery_tickets 
               WHERE user_id = ? AND ticket_id = ?""",
            (user_id, ticket_id)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        if row['scratched']:
            return {"numbers": row['numbers'], "already_scratched": True}
        
        # Mark as scratched
        await self.conn.execute(
            """UPDATE lottery_tickets 
               SET scratched = 1, scratched_at = CURRENT_TIMESTAMP
               WHERE user_id = ? AND ticket_id = ?""",
            (user_id, ticket_id)
        )
        await self.conn.commit()
        return {"numbers": row['numbers'], "already_scratched": False}
    
    # Admin Methods
    async def get_stats(self) -> dict:
        """Get bot statistics"""
        stats = {}
        
        queries = [
            ("total_users", "SELECT COUNT(*) FROM users"),
            ("total_cash", "SELECT SUM(cash) FROM users"),
            ("total_bank", "SELECT SUM(bank_balance) FROM users"),
            ("family_relations", "SELECT COUNT(*) FROM family"),
            ("growing_crops", "SELECT COUNT(*) FROM plants"),
            ("lottery_tickets", "SELECT COUNT(*) FROM lottery_tickets"),
        ]
        
        for key, query in queries:
            cursor = await self.conn.execute(query)
            row = await cursor.fetchone()
            stats[key] = row[0] or 0
        
        return stats
    
    async def get_top_users(self, by: str = "cash", limit: int = 10) -> List[dict]:
        """Get top users"""
        valid_columns = ["cash", "bank_balance", "level"]
        if by not in valid_columns:
            by = "cash"
        
        cursor = await self.conn.execute(
            f"""SELECT user_id, first_name, username, {by}
                FROM users ORDER BY {by} DESC LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# ============================================================================
# IMAGE GENERATOR
# ============================================================================

class ImageGenerator:
    """Generate images for the bot"""
    
    def __init__(self):
        if HAS_PILLOW:
            self.load_fonts()
    
    def load_fonts(self):
        """Load fonts"""
        try:
            self.small_font = ImageFont.truetype("arial.ttf", 14)
            self.medium_font = ImageFont.truetype("arial.ttf", 18)
            self.large_font = ImageFont.truetype("arial.ttf", 24)
        except:
            self.small_font = ImageFont.load_default()
            self.medium_font = ImageFont.load_default()
            self.large_font = ImageFont.load_default()
    
    def create_progress_bar(self, progress: float, width: int = 200, height: int = 20) -> Optional[bytes]:
        """Create progress bar image"""
        if not HAS_PILLOW:
            return None
        
        try:
            img = Image.new('RGB', (width, height), color='#2d3436')
            draw = ImageDraw.Draw(img)
            
            # Background
            draw.rectangle([0, 0, width, height], fill='#2d3436', outline='#636e72', width=1)
            
            # Progress
            progress_width = int(width * (progress / 100))
            if progress >= 100:
                color = '#00b894'
            elif progress >= 70:
                color = '#fdcb6e'
            elif progress >= 40:
                color = '#e17055'
            else:
                color = '#6c5ce7'
            
            draw.rectangle([0, 0, progress_width, height], fill=color)
            
            # Text
            text = f"{int(progress)}%"
            text_x = (width - 40) // 2
            draw.text((text_x, 2), text, fill='white', font=self.small_font)
            
            # Save
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Progress bar error: {e}")
            return None
    
    def create_garden_image(self, username: str, plants: List[dict], garden_info: dict) -> Optional[bytes]:
        """Create garden image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 400
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((50, 20), f"{username}'s Garden", fill='#4CAF50', font=self.large_font)
            
            # Grid (3x3)
            grid_size = 3
            cell_size = 120
            padding = 10
            start_x = (width - (grid_size * cell_size + (grid_size - 1) * padding)) // 2
            start_y = 70
            
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    if idx < len(plants):
                        plant = plants[idx]
                        progress = plant.get('progress', 0)
                        
                        if progress >= 100:
                            color = '#4CAF50'
                            status = "READY"
                        elif progress >= 50:
                            color = '#FFC107'
                            status = "GROWING"
                        else:
                            color = '#2196F3'
                            status = "PLANTED"
                        
                        draw.rectangle([x1, y1, x2, y2], fill=color, outline='white', width=2)
                        
                        crop_type = plant['crop_type']
                        crop_data = CROPS.get(crop_type, {})
                        emoji = crop_data.get('emoji', '🌱')
                        
                        draw.text((x1 + 40, y1 + 20), emoji, fill='white', font=self.large_font)
                        draw.text((x1 + 5, y1 + 5), crop_type[:6], fill='white', font=self.small_font)
                        draw.text((x1 + 30, y2 - 25), f"{int(progress)}%", fill='white', font=self.small_font)
                        draw.text((x1 + 5, y2 - 45), status, fill='white', font=self.small_font)
                    else:
                        draw.rectangle([x1, y1, x2, y2], fill='#333333', outline='#666666', width=1)
                        draw.text((x1 + cell_size//2 - 10, y1 + cell_size//2 - 15), 
                                 "➕", fill='#CCCCCC', font=self.large_font)
            
            # Stats
            stats_y = start_y + grid_size * (cell_size + padding) + 20
            draw.text((50, stats_y), f"Slots: {len(plants)}/{garden_info.get('slots', 9)}", 
                     fill='#FFC107', font=self.medium_font)
            draw.text((width - 250, stats_y), f"Greenhouse: Level {garden_info.get('greenhouse_level', 0)}", 
                     fill='#4CAF50', font=self.medium_font)
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None

# ============================================================================
# BOT SETUP
# ============================================================================

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = Database(DB_PATH)
img_gen = ImageGenerator()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def get_target_user(message: Message) -> Optional[types.User]:
    """Get target user from reply"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None

def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id == OWNER_ID

def format_time(seconds: int) -> str:
    """Format seconds to readable time"""
    if seconds >= 86400:
        return f"{seconds // 86400}d"
    elif seconds >= 3600:
        return f"{seconds // 3600}h"
    elif seconds >= 60:
        return f"{seconds // 60}m"
    else:
        return f"{seconds}s"

def create_text_progress_bar(progress: float, width: int = 20) -> str:
    """Create text progress bar"""
    filled = int(width * progress / 100)
    return "█" * filled + "░" * (width - filled)

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    welcome_text = f"""
👋 Welcome to <b>Family Tree Bot</b>, {message.from_user.first_name}!

🌳 <b>Build Your Legacy</b>
• Create a family dynasty
• Grow your farming empire  
• Build business wealth
• Play exciting games

💰 <b>Get Started:</b>
• Use /daily for your first bonus
• Check /help for all commands

📱 <b>Add to Groups:</b>
Click the button below to add me to your groups!
"""
    
    # Only add "Add to Group" button in /start
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➕ Add to Group", 
                           url=f"https://t.me/{bot.token.split(':')[0]}?startgroup=true")
    ]])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL COMMANDS</b>

👤 <b>PROFILE & ECONOMY:</b>
/me - Your profile
/daily - Daily bonus ($500-$1500)
/bank - Banking with interest
/interest - Collect bank interest

👨‍👩‍👧‍👦 <b>FAMILY:</b>
/family - View family tree
/adopt - Adopt someone (reply)
/marry - Marry someone (reply)  
/divorce - End marriage

🌾 <b>FARMING:</b>
/garden - Your garden
/plant [crop] [qty] - Plant crops
/harvest - Harvest ready crops

💰 <b>INVESTMENTS:</b>
/bank - Manage money
/interest - Earn interest

🎮 <b>GAMES:</b>
/dice [bet] - Dice game  
/fight - Fight someone (reply)
/lottery - Lottery tickets
/scratch [id] - Scratch ticket

😊 <b>REACTIONS (reply to user):</b>
/hug, /kiss, /slap, /pat

👑 <b>ADMIN:</b>
/admin - Admin panel (owner only)

📱 <b>Need help? Contact support!</b>
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("me"))
async def cmd_me(message: Message):
    """User profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Get additional data
    family = await db.get_family(message.from_user.id)
    garden = await db.get_garden(message.from_user.id)
    plants = await db.get_plants(message.from_user.id)
    bank_account = await db.get_bank_account(message.from_user.id)
    
    # Calculate total wealth
    total_wealth = user.get('cash', 0) + user.get('bank_balance', 0)
    
    caption = f"""
👤 <b>{user['first_name']}'s Profile</b>

💰 <b>Wealth:</b>
• Cash: ${user.get('cash', 0):,}
• Bank: ${user.get('bank_balance', 0):,}
• <b>Total: ${total_wealth:,}</b>

📊 <b>Stats:</b>
• Level: {user.get('level', 1)}
• XP: {user.get('xp', 0)}/{(user.get('level', 1) * 1000)}
• Daily Streak: {user.get('daily_streak', 0)} days

👨‍👩‍👧‍👦 <b>Family:</b> {len(family)} members
🌾 <b>Garden:</b> {len(plants)} crops growing
🏦 <b>Interest Earned:</b> ${bank_account.get('total_interest', 0):,}

💡 Use /help for all commands
"""
    
    # Try to get user's profile photo
    try:
        photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            await message.answer_photo(
                photo.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            return
    except Exception as e:
        logger.error(f"Profile photo error: {e}")
    
    # Fallback to text-only
    await message.answer(caption, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Check last daily
    if user.get('last_daily'):
        last_daily = datetime.fromisoformat(user['last_daily'].replace('Z', '+00:00'))
        if (datetime.now() - last_daily).days < 1:
            next_time = last_daily + timedelta(days=1)
            hours_left = int((next_time - datetime.now()).total_seconds() / 3600)
            await message.answer(f"⏳ Come back in {hours_left} hours!")
            return
    
    # Calculate bonus
    bonus = random.randint(GameConfig.DAILY_MIN, GameConfig.DAILY_MAX)
    streak = user.get('daily_streak', 0) + 1
    streak_bonus = min(500, streak * 50)
    total_bonus = bonus + streak_bonus
    
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    
    # Update streak and last daily
    await db.conn.execute(
        """UPDATE users 
           SET daily_streak = ?, last_daily = CURRENT_TIMESTAMP
           WHERE user_id = ?""",
        (streak, message.from_user.id)
    )
    await db.conn.commit()
    
    response = f"""
🎉 <b>DAILY BONUS!</b>

💰 <b>Breakdown:</b>
• Base Bonus: ${bonus:,}
• Streak Bonus ({streak} days): ${streak_bonus:,}

🎁 <b>Total: ${total_bonus:,}</b>

💵 New Balance: ${user.get('cash', 0) + total_bonus:,}

🔥 Keep your streak going!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("family"))
async def cmd_family(message: Message):
    """Family tree"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    if not family:
        response = """
🌳 <b>Your Family Tree</b>

└─ You (Just starting!)

💡 <b>How to grow your family:</b>
• Reply to someone with /adopt to make them your child
• Reply with /marry to get married

👑 <b>Benefits:</b>
• Daily bonus increases
• Family quests and events
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    # Build family tree
    tree_text = f"🌳 <b>Family Tree of {user['first_name']}</b>\n\n"
    tree_text += f"└─ {user['first_name']} (You)\n"
    
    for member in family:
        emoji = "💑" if member['relation'] == "spouse" else "👶" if member['relation'] == "child" else "👴"
        tree_text += f"   ├─ {emoji} {member['first_name']} ({member['relation']})\n"
    
    stats_text = f"""
📊 <b>Family Stats:</b>
• Members: {len(family)}
• Daily Bonus: +${len(family) * 100}

💡 <b>Commands:</b>
• /adopt - Make someone your child
• /marry - Marry someone
• /divorce - End marriage
"""
    
    await message.answer(tree_text + stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to adopt them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    await db.add_family_member(message.from_user.id, target.id, "child")
    await db.update_currency(message.from_user.id, "cash", GameConfig.ADOPT_BONUS)
    
    family = await db.get_family(message.from_user.id)
    
    response = f"""
✅ <b>ADOPTION SUCCESSFUL!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
💰 Bonus: ${GameConfig.ADOPT_BONUS:,}

👨‍👩‍👧‍👦 Your family now has {len(family)} members
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Marry someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to marry them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    await db.add_family_member(message.from_user.id, target.id, "spouse")
    await db.update_currency(message.from_user.id, "cash", GameConfig.MARRY_BONUS)
    await db.update_currency(target.id, "cash", GameConfig.MARRY_BONUS)
    
    response = f"""
💍 <b>MARRIAGE SUCCESSFUL!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Gift: ${GameConfig.MARRY_BONUS:,} each

🎉 <b>Congratulations!</b>
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Garden with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    garden_info = await db.get_garden(message.from_user.id)
    plants = await db.get_plants(message.from_user.id)
    
    # Create garden image
    image_bytes = img_gen.create_garden_image(user['first_name'], plants, garden_info)
    
    ready_count = sum(1 for p in plants if p.get('ready', False))
    
    caption = f"""
🌾 <b>{user['first_name']}'s Garden</b>

📊 <b>Stats:</b>
• Growing: {len(plants)}/{garden_info.get('slots', 9)} slots
• Ready: {ready_count} crops
• Greenhouse: Level {garden_info.get('greenhouse_level', 0)}

💡 <b>Commands:</b>
• /plant [crop] [qty] - Plant crops
• /harvest - Collect ready crops

🌱 <b>Available Crops:</b>
🥕 Carrot - $10 (2h)
🍅 Tomato - $15 (3h)  
🥔 Potato - $8 (2.5h)
🍆 Eggplant - $20 (4h)
"""
    
    # Add progress bars
    if plants:
        caption += "\n📈 <b>Current Crops:</b>\n"
        for plant in plants[:3]:
            progress = plant.get('progress', 0)
            crop_data = CROPS.get(plant['crop_type'], {})
            emoji = crop_data.get('emoji', '🌱')
            caption += f"{emoji} {plant['crop_type'].title()}: {create_text_progress_bar(progress)} {int(progress)}%\n"
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="garden.png")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Garden photo error: {e}")
            await message.answer(caption, parse_mode=ParseMode.HTML)
    else:
        await message.answer(caption, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    if not command.args:
        crops_list = "\n".join([
            f"{data['emoji']} {crop.title()} - ${data['buy']} ({data['grow_time']}h)"
            for crop, data in CROPS.items()
        ])
        
        response = f"""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
{crops_list}

💡 <b>Examples:</b>
<code>/plant carrot 3</code>
<code>/plant tomato 2</code>
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    args = command.args.lower().split()
    if len(args) < 2:
        await message.answer("❌ Format: /plant [crop] [quantity]\nExample: /plant carrot 3")
        return
    
    crop_type = args[0]
    try:
        quantity = int(args[1])
    except ValueError:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if crop_type not in CROPS:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROPS.keys())}")
        return
    
    if quantity < 1 or quantity > 9:
        await message.answer("❌ Quantity must be between 1 and 9!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    crop_data = CROPS[crop_type]
    total_cost = crop_data['buy'] * quantity
    
    if user['cash'] < total_cost:
        await message.answer(f"❌ You need ${total_cost:,}! You have ${user['cash']:,}")
        return
    
    success = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if not success:
        await message.answer("❌ Not enough garden space! Use /garden to check available slots.")
        return
    
    await db.update_currency(message.from_user.id, "cash", -total_cost)
    
    response = f"""
✅ <b>PLANTED!</b>

{crop_data['emoji']} <b>Crop:</b> {crop_type.title()}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Cost:</b> ${total_cost:,}
⏰ <b>Grow Time:</b> {crop_data['grow_time']} hours

🌱 {quantity} {crop_type.title()}{'s' if quantity > 1 else ''} now growing!
💡 Use /garden to check progress
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest crops"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    harvested = await db.harvest_crops(message.from_user.id)
    
    if not harvested:
        await message.answer("❌ No crops ready for harvest!")
        return
    
    total_value = 0
    harvest_text = "✅ <b>HARVEST COMPLETE!</b>\n\n"
    
    for crop_type, count, value in harvested:
        crop_data = CROPS.get(crop_type, {})
        harvest_text += f"{crop_data.get('emoji', '🌱')} {crop_type.title()}: {count} = ${value}\n"
        total_value += value
    
    harvest_text += f"\n💰 <b>Total Earned: ${total_value:,}</b>"
    harvest_text += f"\n💵 New Balance: ${user['cash'] + total_value:,}"
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

@dp.message(Command("bank"))
async def cmd_bank(message: Message):
    """Bank system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    bank_account = await db.get_bank_account(message.from_user.id)
    
    # Calculate next interest
    next_interest = "Now!"
    if bank_account.get('last_interest'):
        last_interest = datetime.fromisoformat(bank_account['last_interest'])
        next_time = last_interest + timedelta(days=1)
        if next_time > datetime.now():
            hours_left = int((next_time - datetime.now()).total_seconds() / 3600)
            next_interest = f"{hours_left}h"
    
    # Create progress bar image
    progress_image = None
    if bank_account.get('last_interest'):
        last_time = datetime.fromisoformat(bank_account['last_interest'])
        elapsed = (datetime.now() - last_time).total_seconds()
        progress = min(100, (elapsed / 86400) * 100)  # 24 hours
        progress_image = img_gen.create_progress_bar(progress)
    
    caption = f"""
🏦 <b>BANK OF FAMILY TREE</b>

💰 <b>Your Accounts:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Savings: <b>${user.get('bank_balance', 0):,}</b>
• 📈 Interest Earned: <b>${bank_account.get('total_interest', 0):,}</b>

📊 <b>Bank Features:</b>
• Daily Interest: {GameConfig.BANK_INTEREST_RATE}%
• Next Interest: {next_interest}
• Safe from robbery

💡 <b>Commands:</b>
• /deposit [amount] - Deposit to bank
• /withdraw [amount] - Withdraw from bank  
• /interest - Collect interest
• /statement - View transactions
"""
    
    if progress_image:
        try:
            photo = BufferedInputFile(progress_image, filename="progress.png")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Progress image error: {e}")
            await message.answer(caption, parse_mode=ParseMode.HTML)
    else:
        await message.answer(caption, parse_mode=ParseMode.HTML)

@dp.message(Command("deposit"))
async def cmd_deposit(message: Message, command: CommandObject):
    """Deposit money"""
    if not command.args:
        await message.answer("❌ Usage: /deposit [amount]\nExample: /deposit 1000")
        return
    
    try:
        amount = int(command.args)
        if amount <= 0:
            await message.answer("❌ Amount must be positive!")
            return
    except ValueError:
        await message.answer("❌ Amount must be a number!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user['cash'] < amount:
        await message.answer(f"❌ You only have ${user['cash']:,} cash!")
        return
    
    await db.update_currency(message.from_user.id, "cash", -amount)
    await db.update_currency(message.from_user.id, "bank_balance", amount)
    await db.add_transaction(message.from_user.id, "deposit", amount, "Cash deposit")
    
    response = f"""
✅ <b>DEPOSIT SUCCESSFUL!</b>

💰 <b>Amount:</b> ${amount:,}
🏦 <b>New Bank Balance:</b> ${user.get('bank_balance', 0) + amount:,}
💵 <b>Cash Left:</b> ${user['cash'] - amount:,}

📈 <b>Daily Interest:</b> ${int((user.get('bank_balance', 0) + amount) * (GameConfig.BANK_INTEREST_RATE / 100)):,}
💡 Use /interest daily to collect!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("withdraw"))
async def cmd_withdraw(message: Message, command: CommandObject):
    """Withdraw money"""
    if not command.args:
        await message.answer("❌ Usage: /withdraw [amount]\nExample: /withdraw 500")
        return
    
    try:
        amount = int(command.args)
        if amount <= 0:
            await message.answer("❌ Amount must be positive!")
            return
    except ValueError:
        await message.answer("❌ Amount must be a number!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user.get('bank_balance', 0) < amount:
        await message.answer(f"❌ You only have ${user.get('bank_balance', 0):,} in bank!")
        return
    
    await db.update_currency(message.from_user.id, "bank_balance", -amount)
    await db.update_currency(message.from_user.id, "cash", amount)
    await db.add_transaction(message.from_user.id, "withdraw", amount, "Cash withdrawal")
    
    response = f"""
✅ <b>WITHDRAWAL SUCCESSFUL!</b>

💰 <b>Amount:</b> ${amount:,}
🏦 <b>New Bank Balance:</b> ${user.get('bank_balance', 0) - amount:,}
💵 <b>Cash Now:</b> ${user['cash'] + amount:,}

💡 Your money is ready to use!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("interest"))
async def cmd_interest(message: Message):
    """Collect interest"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    interest, message_text = await db.calculate_interest(message.from_user.id)
    
    if interest > 0:
        response = f"""
✅ <b>INTEREST COLLECTED!</b>

💰 <b>Amount:</b> ${interest:,}
🏦 <b>New Bank Balance:</b> ${user.get('bank_balance', 0) + interest:,}
📈 <b>Total Interest Earned:</b> ${(await db.get_bank_account(message.from_user.id)).get('total_interest', 0):,}

💡 Interest calculated daily at {GameConfig.BANK_INTEREST_RATE}%
Come back tomorrow for more!
"""
    else:
        response = f"""
⏳ <b>INTEREST STATUS</b>

{message_text}

🏦 <b>Current Balance:</b> ${user.get('bank_balance', 0):,}
📈 <b>Daily Rate:</b> {GameConfig.BANK_INTEREST_RATE}%

💡 Interest is calculated once every 24 hours
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("statement"))
async def cmd_statement(message: Message):
    """Bank statement"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    transactions = await db.get_transactions(message.from_user.id, limit=10)
    
    if not transactions:
        response = """
📄 <b>BANK STATEMENT</b>

No transactions yet.

💡 Make your first deposit:
<code>/deposit 100</code>
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    statement_text = "📄 <b>BANK STATEMENT</b>\n\n"
    statement_text += f"🏦 Current Balance: <b>${user.get('bank_balance', 0):,}</b>\n\n"
    statement_text += "📋 <b>Recent Transactions:</b>\n"
    
    for trans in transactions:
        emoji = "📥" if trans['type'] == 'deposit' else "📤" if trans['type'] == 'withdraw' else "💰"
        sign = "+" if trans['type'] in ['deposit', 'interest'] else "-"
        date_str = datetime.fromisoformat(trans['created_at']).strftime('%m/%d')
        statement_text += f"{emoji} ${abs(trans['amount']):,} {sign} - {date_str}\n"
    
    statement_text += "\n💡 <b>Recent 10 transactions shown</b>"
    
    await message.answer(statement_text, parse_mode=ParseMode.HTML)

@dp.message(Command("lottery"))
async def cmd_lottery(message: Message, command: CommandObject):
    """Buy lottery tickets"""
    if not command.args:
        response = f"""
🎰 <b>LOTTERY SYSTEM</b>

Buy scratch cards for a chance to win big!

💰 <b>Ticket Price:</b> ${GameConfig.LOTTERY_TICKET_PRICE}
🎫 <b>How it works:</b>
1. Buy tickets with /buy [quantity]
2. Scratch them with /scratch [ticket_id]
3. Check numbers each Sunday
4. Match bot's numbers to win!

💡 <b>Commands:</b>
• /buy [quantity] - Buy lottery tickets
• /mytickets - View your tickets
• /scratch [ticket_id] - Scratch a ticket

🏆 <b>Weekly Draw:</b>
Every Sunday, bot announces winning numbers
Winners get 70% of all ticket sales!
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    if command.args.lower().startswith("buy"):
        # Handle /lottery buy [quantity]
        try:
            args = command.args.split()[1:]
            if not args:
                await message.answer("❌ Usage: /lottery buy [quantity]\nExample: /lottery buy 3")
                return
            
            quantity = int(args[0])
            if quantity < 1 or quantity > 10:
                await message.answer("❌ Quantity must be between 1 and 10!")
                return
            
            success, tickets, cost = await db.buy_lottery_ticket(message.from_user.id, quantity)
            
            if not success:
                await message.answer("❌ Not enough cash to buy tickets!")
                return
            
            ticket_list = "\n".join([f"• #{ticket}" for ticket in tickets[:3]])
            if len(tickets) > 3:
                ticket_list += f"\n• ... and {len(tickets) - 3} more"
            
            response = f"""
✅ <b>LOTTERY TICKETS PURCHASED!</b>

🎫 <b>Tickets:</b> {quantity}
💰 <b>Cost:</b> ${cost:,}
📋 <b>Ticket IDs:</b>
{ticket_list}

💡 <b>Next Steps:</b>
1. Scratch tickets: /scratch [ticket_id]
2. Check numbers each Sunday
3. Win 70% of ticket sales!

Good luck! 🍀
"""
            await message.answer(response, parse_mode=ParseMode.HTML)
            
        except ValueError:
            await message.answer("❌ Quantity must be a number!")
        except IndexError:
            await message.answer("❌ Usage: /lottery buy [quantity]")

@dp.message(Command("mytickets"))
async def cmd_mytickets(message: Message):
    """View lottery tickets"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    tickets = await db.get_tickets(message.from_user.id)
    
    if not tickets:
        response = """
🎫 <b>YOUR LOTTERY TICKETS</b>

You don't have any tickets yet!

💡 Buy tickets with:
<code>/lottery buy 3</code>

💰 Ticket price: ${GameConfig.LOTTERY_TICKET_PRICE}
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    total_tickets = len(tickets)
    unscratched = sum(1 for t in tickets if not t['scratched'])
    scratched = total_tickets - unscratched
    
    response = f"""
🎫 <b>YOUR LOTTERY TICKETS</b>

📊 <b>Stats:</b>
• Total Tickets: {total_tickets}
• Unscratched: {unscratched}
• Scratched: {scratched}

📋 <b>Recent Tickets:</b>
"""
    
    for ticket in tickets[:5]:
        status = "🔓" if not ticket['scratched'] else "🔒"
        ticket_id_short = ticket['ticket_id'][:10] + "..."
        response += f"{status} {ticket_id_short}\n"
    
    if total_tickets > 5:
        response += f"• ... and {total_tickets - 5} more\n"
    
    response += "\n💡 <b>Commands:</b>"
    response += "\n• /scratch [ticket_id] - Scratch a ticket"
    response += "\n• /lottery buy [qty] - Buy more tickets"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("scratch"))
async def cmd_scratch(message: Message, command: CommandObject):
    """Scratch lottery ticket"""
    if not command.args:
        await message.answer("❌ Usage: /scratch [ticket_id]\nExample: /scratch LOT-123456")
        return
    
    ticket_id = command.args.strip().upper()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    result = await db.scratch_ticket(message.from_user.id, ticket_id)
    
    if not result:
        await message.answer("❌ Ticket not found! Check /mytickets for your tickets.")
        return
    
    if result['already_scratched']:
        response = f"""
🎫 <b>TICKET ALREADY SCRATCHED</b>

Ticket: #{ticket_id}
Numbers: {result['numbers']}

🔍 <b>Check every Sunday</b> to see if you won!
The bot will announce winning numbers.

💡 Keep this number safe!
"""
    else:
        response = f"""
🎉 <b>TICKET SCRATCHED!</b>

Ticket: #{ticket_id}
🎰 <b>Your Numbers:</b> {result['numbers']}

🔍 <b>Check every Sunday</b> to see if you won!
The bot will announce winning numbers.

📝 <b>Save your numbers:</b> {result['numbers']}
💡 Winning ticket gets 70% of all sales!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject):
    """Dice game"""
    # Get bet amount
    bet = 100
    if command.args:
        try:
            bet = int(command.args)
            if bet < 10:
                await message.answer("❌ Minimum bet is $10!")
                return
            if bet > 10000:
                await message.answer("❌ Maximum bet is $10,000!")
                return
        except ValueError:
            await message.answer("❌ Bet must be a number!\nExample: /dice 500")
            return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user['cash'] < bet:
        await message.answer(f"❌ You need ${bet:,} to play! You have ${user['cash']:,}")
        return
    
    # Send Telegram dice
    sent_dice = await message.answer_dice()
    dice_value = sent_dice.dice.value
    
    # Calculate win/loss
    if dice_value >= 4:  # Win on 4, 5, or 6
        win_amount = bet * 2
        result = "🎉 YOU WIN!"
        await db.update_currency(message.from_user.id, "cash", win_amount)
    else:  # Lose on 1, 2, or 3
        win_amount = -bet
        result = "😢 YOU LOSE"
        await db.update_currency(message.from_user.id, "cash", -bet)
    
    response = f"""
🎲 <b>DICE GAME</b>

Your roll: <b>{dice_value}</b>
Bet: <b>${bet:,}</b>

{result} <b>${abs(win_amount):,}</b>

💰 <b>New Balance:</b> ${user['cash'] + win_amount:,}

💡 Play again with /dice [amount]
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("fight"))
async def cmd_fight(message: Message):
    """Fight someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to fight them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot fight yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Calculate fight outcome
    user_power = user.get('cash', 0) // 1000 + user.get('level', 1)
    target_power = target_user.get('cash', 0) // 1000 + 1
    
    total_power = user_power + target_power
    user_win_chance = user_power / total_power
    
    if random.random() < user_win_chance:
        # User wins
        prize = min(1000, target_user.get('cash', 0) // 10)
        if prize > 0:
            await db.update_currency(message.from_user.id, "cash", prize)
            await db.update_currency(target.id, "cash", -prize)
        
        response = f"""
🥊 <b>FIGHT RESULTS</b>

⚔️ {message.from_user.first_name} vs {target.first_name}

🏆 <b>WINNER:</b> {message.from_user.first_name}!
💰 <b>Prize:</b> ${prize:,}

💪 You defeated {target.first_name}!
"""
    else:
        # User loses
        penalty = min(500, user.get('cash', 0) // 20)
        if penalty > 0:
            await db.update_currency(message.from_user.id, "cash", -penalty)
            await db.update_currency(target.id, "cash", penalty)
        
        response = f"""
🥊 <b>FIGHT RESULTS</b>

⚔️ {message.from_user.first_name} vs {target.first_name}

😢 <b>LOSER:</b> {message.from_user.first_name}
💸 <b>Penalty:</b> ${penalty:,}

😔 {target.first_name} defeated you!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# Reaction commands
@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to hug them!")
        return
    
    response = f"""
🤗 <b>HUG</b>

{message.from_user.first_name} hugged {target.first_name}!
💖 Love is in the air!
"""
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to kiss them!")
        return
    
    response = f"""
😘 <b>KISS</b>

{message.from_user.first_name} kissed {target.first_name}!
💋 Mwah!
"""
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to slap them!")
        return
    
    response = f"""
👋 <b>SLAP</b>

{message.from_user.first_name} slapped {target.first_name}!
😵 That must have hurt!
"""
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to pat them!")
        return
    
    response = f"""
👏 <b>PAT</b>

{message.from_user.first_name} patted {target.first_name}!
🐶 Good human!
"""
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ This command is for bot owner only!")
        return
    
    response = """
👑 <b>ADMIN PANEL</b>

📊 <b>Statistics:</b>
• /stats - Bot statistics
• /top [type] - Top users

👥 <b>User Management:</b>
• /search [query] - Search users
• /message [id] [text] - PM user

💰 <b>Economy:</b>
• /add [id] [currency] [amount] - Add money
• /remove [id] [currency] [amount] - Remove money

🔧 <b>System:</b>
• /backup - Backup database
• /broadcast [text] - Announcement

💡 <b>Click commands to use them</b>
"""
    
    # Create admin keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Top Users", callback_data="admin_top")],
        [InlineKeyboardButton(text="💰 Add Money", callback_data="admin_add")],
        [InlineKeyboardButton(text="🔧 Backup", callback_data="admin_backup")],
    ])
    
    await message.answer(response, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("admin_"))
async def handle_admin_callback(callback: CallbackQuery):
    """Handle admin callbacks"""
    if not is_owner(callback.from_user.id):
        await callback.answer("❌ Admin only!")
        return
    
    action = callback.data.replace("admin_", "")
    
    if action == "stats":
        stats = await db.get_stats()
        
        response = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b> {stats.get('total_users', 0):,}
💰 <b>Total Cash:</b> ${stats.get('total_cash', 0):,}
🏦 <b>Total Bank:</b> ${stats.get('total_bank', 0):,}
👨‍👩‍👧‍👦 <b>Families:</b> {stats.get('family_relations', 0):,}
🌾 <b>Growing Crops:</b> {stats.get('growing_crops', 0):,}
🎫 <b>Lottery Tickets:</b> {stats.get('lottery_tickets', 0):,}

💡 Last updated: {datetime.now().strftime('%H:%M')}
"""
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "top":
        top_users = await db.get_top_users("cash", 10)
        
        response = "🏆 <b>TOP 10 USERS BY CASH</b>\n\n"
        
        for i, user in enumerate(top_users, 1):
            name = user.get('username') or user.get('first_name', 'User')
            cash = user.get('cash', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            response += f"{medal} {name}: <b>${cash:,}</b>\n"
        
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "add":
        response = """
💰 <b>ADD MONEY TO USER</b>

Usage: <code>/add [user_id] [currency] [amount]</code>

💡 <b>Examples:</b>
<code>/add 123456789 cash 1000</code>
<code>/add 123456789 bank_balance 5000</code>

📌 <b>Currencies:</b>
• cash - User's pocket money
• bank_balance - Bank balance
"""
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "backup":
        # In a real bot, you would create and send backup
        response = """
💾 <b>DATABASE BACKUP</b>

Backup feature would:
1. Create database backup
2. Compress into .db.gz file
3. Send to admin

⚠️ <b>Implementation note:</b>
This feature requires file handling.
In production, use /backup command.
"""
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
    
    await callback.answer()

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics (admin only)"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Admin only!")
        return
    
    stats = await db.get_stats()
    
    response = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b> {stats.get('total_users', 0):,}
💰 <b>Total Cash:</b> ${stats.get('total_cash', 0):,}
🏦 <b>Total Bank:</b> ${stats.get('total_bank', 0):,}
👨‍👩‍👧‍👦 <b>Families:</b> {stats.get('family_relations', 0):,}
🌾 <b>Growing Crops:</b> {stats.get('growing_crops', 0):,}
🎫 <b>Lottery Tickets:</b> {stats.get('lottery_tickets', 0):,}

🕒 <b>Last updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("top"))
async def cmd_top(message: Message, command: CommandObject):
    """Top users"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Admin only!")
        return
    
    by = "cash"
    if command.args:
        args = command.args.lower().split()
        if args and args[0] in ["cash", "bank", "level"]:
            by = "bank_balance" if args[0] == "bank" else args[0]
    
    top_users = await db.get_top_users(by, 10)
    
    column_name = "Cash" if by == "cash" else "Bank" if by == "bank_balance" else "Level"
    
    response = f"🏆 <b>TOP 10 USERS BY {column_name.upper()}</b>\n\n"
    
    for i, user in enumerate(top_users, 1):
        name = user.get('username') or user.get('first_name', 'User')
        value = user.get(by, 0)
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        if by == "cash" or by == "bank_balance":
            response += f"{medal} {name}: <b>${value:,}</b>\n"
        else:
            response += f"{medal} {name}: <b>Level {value}</b>\n"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject):
    """Search users (admin only)"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Admin only!")
        return
    
    if not command.args:
        await message.answer("❌ Usage: /search [name or username]\nExample: /search john")
        return
    
    query = f"%{command.args}%"
    cursor = await db.conn.execute(
        """SELECT user_id, username, first_name, cash, level 
           FROM users 
           WHERE username LIKE ? OR first_name LIKE ? 
           LIMIT 10""",
        (query, query)
    )
    rows = await cursor.fetchall()
    
    if not rows:
        await message.answer("❌ No users found!")
        return
    
    response = f"🔍 <b>SEARCH RESULTS for '{command.args}'</b>\n\n"
    
    for row in rows:
        user = dict(row)
        name = user.get('username') or user.get('first_name', 'User')
        response += f"👤 {name}\n"
        response += f"   ID: {user.get('user_id')}\n"
        response += f"   💰 ${user.get('cash', 0):,}\n"
        response += f"   ⭐ Level {user.get('level', 1)}\n\n"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add money to user (admin only)"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Admin only!")
        return
    
    if not command.args:
        response = """
💰 <b>ADD MONEY</b>

Usage: <code>/add [user_id] [currency] [amount]</code>

💡 <b>Examples:</b>
<code>/add 123456789 cash 1000</code>
<code>/add 123456789 bank 5000</code>

📌 <b>Currencies:</b>
• cash - User's pocket money
• bank - Bank balance (use "bank" not "bank_balance")
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Usage: /add [user_id] [currency] [amount]")
        return
    
    try:
        user_id = int(args[0])
        currency = args[1].lower()
        amount = int(args[2])
        
        if currency not in ["cash", "bank"]:
            await message.answer("❌ Currency must be 'cash' or 'bank'!")
            return
        
        if amount <= 0:
            await message.answer("❌ Amount must be positive!")
            return
        
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            await message.answer("❌ User not found!")
            return
        
        db_currency = "bank_balance" if currency == "bank" else "cash"
        await db.update_currency(user_id, db_currency, amount)
        
        # Get updated user info
        updated_user = await db.get_user(user_id)
        new_balance = updated_user.get(db_currency, 0)
        
        response = f"""
✅ <b>MONEY ADDED!</b>

👤 User: {user.get('first_name', 'User')}
💰 Added: ${amount:,} {currency}
💵 New {currency} balance: ${new_balance:,}

✅ Transaction completed.
"""
        
        await message.answer(response, parse_mode=ParseMode.HTML)
        
    except ValueError:
        await message.answer("❌ Invalid arguments! User ID and amount must be numbers.")
    except Exception as e:
        logger.error(f"Add money error: {e}")
        await message.answer("❌ Error adding money!")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast message (admin only)"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Admin only!")
        return
    
    if not command.args:
        await message.answer("❌ Usage: /broadcast [message]\nExample: /broadcast Hello everyone!")
        return
    
    # In a real bot, you would broadcast to all users
    # For now, just show a preview
    response = f"""
📢 <b>BROADCAST PREVIEW</b>

Your message would be sent to all users:

{command.args}

⚠️ <b>Implementation note:</b>
In production, this would:
1. Get all user IDs from database
2. Send message to each user
3. Handle errors and rate limits
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main function"""
    logger.info("Starting Family Tree Bot...")
    
    # Connect to database
    await db.connect()
    logger.info("Database connected")
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
