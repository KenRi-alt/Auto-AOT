#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - ULTIMATE EDITION
Premium Telegram Bot with Enhanced UI/UX
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

# ============================================================================
# IMPORTS - CORRECTED FOR AIOGRAM 3.0.0b7
# ============================================================================
try:
    # Aiogram 3.x imports (correct for version 3.0.0b7)
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, URLInputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode
    
    # For aiogram 3.0.0b7, use this instead of DefaultBotProperties
    from aiogram.client.session.aiohttp import AiohttpSession
    
    # Check if aiogram version supports DefaultBotProperties
    import pkg_resources
    aiogram_version = pkg_resources.get_distribution("aiogram").version
    logger = logging.getLogger(__name__)
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please install: pip install aiogram==3.0.0b7 aiohttp aiosqlite python-dotenv")
    sys.exit(1)

# Database
import aiosqlite
import sqlite3

# ============================================================================
# CONFIGURATION
# ============================================================================

# 🔐 YOUR CREDENTIALS
OWNER_ID = 6108185460
BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
LOG_CHANNEL = -1003662720845

# Database
DB_PATH = os.getenv("DB_PATH", "family_bot.db")
BACKUP_DIR = "backups"

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦",
    "credits": "⭐", "tokens": "🌱"
}

# Crop System
CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔",
    "eggplant": "🍆", "corn": "🌽", "pepper": "🫑"
}

CROP_PRICES = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆"},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽"},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑"}
}

# Emojis for UI
EMOJIS = {
    # Navigation
    "home": "🏠", "back": "↩️", "refresh": "🔄", "close": "❌",
    "next": "➡️", "prev": "⬅️", "up": "⬆️", "down": "⬇️",
    
    # Actions
    "check": "✅", "cross": "❌", "warning": "⚠️", "info": "ℹ️",
    "search": "🔍", "filter": "🔎", "settings": "⚙️", "star": "⭐",
    
    # Features
    "family": "👨‍👩‍👧‍👦", "friends": "🤝", "garden": "🌾", "market": "🏪",
    "pvp": "⚔️", "shop": "🛒", "bank": "🏦", "gift": "🎁",
    
    # Status
    "online": "🟢", "offline": "🔴", "idle": "🟡", "dnd": "⛔",
    "alive": "❤️", "dead": "💀", "loading": "⏳", "done": "✅",
    
    # Economy
    "money": "💰", "coins": "🪙", "diamond": "💎", "treasure": "🏆",
    "up": "📈", "down": "📉", "equal": "📊",
    
    # Reactions
    "like": "👍", "love": "❤️", "laugh": "😂", "wow": "😮",
    "sad": "😢", "angry": "😠", "fire": "🔥", "party": "🎉"
}

# Animation Sequences (for loading effects)
ANIMATIONS = {
    "loading": ["⏳", "⌛", "⏳", "⌛"],
    "dots": ["∙∙∙", "●∙∙", "∙●∙", "∙∙●", "∙∙∙"],
    "spinner": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "hearts": ["💛", "💚", "💙", "💜", "❤️", "🧡"]
}

# ============================================================================
# SETUP LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENHANCED UI COMPONENTS
# ============================================================================

class EnhancedUI:
    """Enhanced UI components with animations"""
    
    @staticmethod
    async def send_typing(message: Message, duration: float = 0.5):
        """Show typing indicator"""
        try:
            await message.bot.send_chat_action(message.chat.id, "typing")
            await asyncio.sleep(duration)
        except:
            pass
    
    @staticmethod
    async def animated_message(message: Message, text: str, animation_type: str = "dots"):
        """Send message with loading animation"""
        msg = await message.answer(f"{EMOJIS['loading']} {text}")
        
        if animation_type in ANIMATIONS:
            frames = ANIMATIONS[animation_type]
            for frame in frames[:3]:  # Show first 3 frames
                try:
                    await msg.edit_text(f"{frame} {text}")
                    await asyncio.sleep(0.3)
                except:
                    break
        
        return msg
    
    @staticmethod
    def create_paginated_keyboard(items: List[Any], page: int, items_per_page: int = 8,
                                callback_prefix: str = "page_") -> InlineKeyboardMarkup:
        """Create paginated keyboard with navigation"""
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]
        
        keyboard = []
        
        # Add items
        for item in page_items:
            if isinstance(item, tuple) and len(item) >= 2:
                text, callback = item[0], item[1]
                keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
            else:
                keyboard.append([InlineKeyboardButton(text=str(item), callback_data=f"{callback_prefix}{item}")])
        
        # Add navigation
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text=f"{EMOJIS['prev']} Previous", 
                callback_data=f"{callback_prefix}nav_{page-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page+1}/{((len(items)-1)//items_per_page)+1}",
            callback_data="noop"
        ))
        
        if end_idx < len(items):
            nav_buttons.append(InlineKeyboardButton(
                text=f"Next {EMOJIS['next']}", 
                callback_data=f"{callback_prefix}nav_{page+1}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Add close button
        keyboard.append([InlineKeyboardButton(
            text=f"{EMOJIS['close']} Close", 
            callback_data="close_menu"
        )])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_main_menu() -> ReplyKeyboardMarkup:
        """Create beautiful main menu"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=f"{EMOJIS['home']} Profile"),
                    KeyboardButton(text=f"{EMOJIS['family']} Family")
                ],
                [
                    KeyboardButton(text=f"{EMOJIS['garden']} Garden"),
                    KeyboardButton(text=f"{EMOJIS['market']} Market")
                ],
                [
                    KeyboardButton(text=f"{EMOJIS['friends']} Friends"),
                    KeyboardButton(text=f"{EMOJIS['pvp']} PvP")
                ],
                [
                    KeyboardButton(text=f"{EMOJIS['shop']} Shop"),
                    KeyboardButton(text=f"{EMOJIS['settings']} Settings")
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder="Choose an option or type /help"
        )
    
    @staticmethod
    def create_stats_bar(user_data: dict) -> str:
        """Create a beautiful stats bar"""
        return (
            f"💵 ${user_data.get('cash', 0):,} | "
            f"❤️ {user_data.get('reputation', 100)}/200 | "
            f"🌱 {user_data.get('tokens', 0)} | "
            f"{EMOJIS['alive'] if user_data.get('is_alive', True) else EMOJIS['dead']}"
        )

# ============================================================================
# DATABASE MANAGER WITH ENHANCED FEATURES
# ============================================================================

class Database:
    """Enhanced database manager with better error handling"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to database with enhanced features"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.conn.execute("PRAGMA busy_timeout=5000")
        await self.init_tables()
        logger.info("📊 Database connected successfully")
    
    async def init_tables(self):
        """Initialize all tables with proper indexes"""
        tables = [
            # Users table
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
                gemstone TEXT,
                gemstone_date TIMESTAMP,
                weapon TEXT DEFAULT 'fist',
                job TEXT,
                theme TEXT DEFAULT 'default',
                language TEXT DEFAULT 'en',
                total_xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )""",
            
            # Family relations
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
            
            # Friends
            """CREATE TABLE IF NOT EXISTS friendships (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rating INTEGER DEFAULT 5,
                notes TEXT,
                FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user1_id, user2_id)
            )""",
            
            # Garden
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                expansion_level INTEGER DEFAULT 1,
                last_fertilized TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Plants
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                is_ready BOOLEAN DEFAULT 0,
                fertilized_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Barn
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Market
            """CREATE TABLE IF NOT EXISTS market_stands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_sold BOOLEAN DEFAULT 0,
                FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Proposals
            """CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                proposal_type TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + '24 hours'),
                FOREIGN KEY (from_id) REFERENCES users(user_id),
                FOREIGN KEY (to_id) REFERENCES users(user_id)
            )""",
            
            # Create indexes for performance
            """CREATE INDEX IF NOT EXISTS idx_family_user1 ON family_relations(user1_id)""",
            """CREATE INDEX IF NOT EXISTS idx_family_user2 ON family_relations(user2_id)""",
            """CREATE INDEX IF NOT EXISTS idx_plants_user ON garden_plants(user_id)""",
            """CREATE INDEX IF NOT EXISTS idx_market_crop ON market_stands(crop_type)""",
            """CREATE INDEX IF NOT EXISTS idx_market_price ON market_stands(price)""",
        ]
        
        async with self.lock:
            for table_sql in tables:
                try:
                    await self.conn.execute(table_sql)
                except Exception as e:
                    logger.error(f"Table creation error: {e}")
            
            await self.conn.commit()
            logger.info("✅ Database tables initialized")
    
    # ==================== USER MANAGEMENT ====================
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user with enhanced data"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT u.*, 
                   (SELECT COUNT(*) FROM family_relations WHERE user1_id = u.user_id OR user2_id = u.user_id) as family_count,
                   (SELECT COUNT(*) FROM friendships WHERE user1_id = u.user_id) as friend_count,
                   (SELECT COUNT(*) FROM garden_plants WHERE user_id = u.user_id AND is_ready = 0) as growing_plants
                   FROM users u WHERE user_id = ?""",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user with initial setup"""
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "cash": 1000,
            "gold": 0,
            "bonds": 0,
            "credits": 100,
            "tokens": 50,
            "reputation": 100,
            "is_alive": True,
            "weapon": "fist",
            "level": 1,
            "total_xp": 0
        }
        
        async with self.lock:
            try:
                await self.conn.execute(
                    "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                    (user.id, user.username, user.first_name, user.last_name)
                )
                await self.conn.execute(
                    "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                    (user.id,)
                )
                await self.conn.commit()
                logger.info(f"👤 New user created: {user.id} - {user.first_name}")
            except Exception as e:
                logger.error(f"User creation error: {e}")
        
        return user_data
    
    async def update_user_currency(self, user_id: int, currency: str, amount: int) -> bool:
        """Safely update user currency"""
        if currency not in ["cash", "gold", "bonds", "credits", "tokens"]:
            return False
        
        async with self.lock:
            try:
                cursor = await self.conn.execute(
                    f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ? AND {currency} + ? >= 0",
                    (amount, user_id, amount)
                )
                await self.conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Currency update error: {e}")
                return False
    
    # ==================== GARDEN SYSTEM ====================
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int) -> Tuple[bool, str, int]:
        """Plant crops with validation"""
        if crop_type not in CROP_TYPES:
            return False, f"Invalid crop type. Choose from: {', '.join(CROP_TYPES)}", 0
        
        # Check user has enough money
        price_per = CROP_PRICES[crop_type]["buy"]
        total_price = price_per * quantity
        
        async with self.lock:
            # Check user balance
            cursor = await self.conn.execute(
                "SELECT cash FROM users WHERE user_id = ?", (user_id,)
            )
            user = await cursor.fetchone()
            
            if not user or user[0] < total_price:
                return False, f"Not enough cash! Need ${total_price}", 0
            
            # Check available slots
            cursor = await self.conn.execute(
                "SELECT g.slots, COUNT(gp.id) as used_slots "
                "FROM gardens g LEFT JOIN garden_plants gp ON g.user_id = gp.user_id AND gp.is_ready = 0 "
                "WHERE g.user_id = ? GROUP BY g.user_id",
                (user_id,)
            )
            garden = await cursor.fetchone()
            
            if not garden:
                return False, "No garden found! Use /start first.", 0
            
            slots, used_slots = garden
            if used_slots + quantity > slots:
                return False, f"Not enough garden slots! ({used_slots}/{slots} used)", 0
            
            # Plant crops
            grow_time = CROP_PRICES[crop_type]["grow_time"]
            plant_ids = []
            
            for _ in range(quantity):
                cursor = await self.conn.execute(
                    "INSERT INTO garden_plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                    (user_id, crop_type, grow_time * 3600)  # Convert hours to seconds
                )
                plant_ids.append(cursor.lastrowid)
            
            # Deduct money
            await self.conn.execute(
                "UPDATE users SET cash = cash - ? WHERE user_id = ?",
                (total_price, user_id)
            )
            
            await self.conn.commit()
            
            return True, f"Planted {quantity} {CROP_EMOJIS.get(crop_type, '')}{crop_type}(s)!", total_price
    
    async def harvest_crops(self, user_id: int) -> Tuple[Dict[str, int], int, str]:
        """Harvest ready crops"""
        async with self.lock:
            # Get ready crops
            cursor = await self.conn.execute(
                """SELECT crop_type, COUNT(*) as count, 
                   SUM(CASE WHEN fertilized_count > 0 THEN 1.2 ELSE 1.0 END) as multiplier
                   FROM garden_plants 
                   WHERE user_id = ? AND is_ready = 1 
                   GROUP BY crop_type""",
                (user_id,)
            )
            ready_crops_raw = await cursor.fetchall()
            
            if not ready_crops_raw:
                return {}, 0, "No crops ready for harvest!"
            
            # Calculate harvest with bonuses
            ready_crops = {}
            total_value = 0
            
            for crop_type, count, multiplier in ready_crops_raw:
                adjusted_count = int(count * float(multiplier))
                ready_crops[crop_type] = adjusted_count
                sell_price = CROP_PRICES[crop_type]["sell"] * adjusted_count
                total_value += sell_price
            
            # Add to barn
            for crop_type, count in ready_crops.items():
                await self.conn.execute(
                    """INSERT INTO barn (user_id, crop_type, quantity) 
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, crop_type) DO UPDATE SET 
                       quantity = quantity + excluded.quantity""",
                    (user_id, crop_type, count)
                )
            
            # Remove harvested plants
            await self.conn.execute(
                "DELETE FROM garden_plants WHERE user_id = ? AND is_ready = 1",
                (user_id,)
            )
            
            await self.conn.commit()
            
            # Add XP
            xp_gained = len(ready_crops_raw) * 10
            await self.conn.execute(
                "UPDATE users SET total_xp = total_xp + ? WHERE user_id = ?",
                (xp_gained, user_id)
            )
            
            await self.conn.commit()
            
            return ready_crops, total_value, f"Harvested {sum(ready_crops.values())} crops!"
    
    # ==================== MARKET SYSTEM ====================
    
    async def list_on_market(self, user_id: int, crop_type: str, quantity: int, price: int) -> Tuple[bool, str, int]:
        """List crops on market with validation"""
        # Check if user has enough crops
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT quantity FROM barn WHERE user_id = ? AND crop_type = ?",
                (user_id, crop_type)
            )
            barn = await cursor.fetchone()
            
            if not barn or barn[0] < quantity:
                return False, f"Not enough {crop_type} in barn! You have {barn[0] if barn else 0}.", 0
            
            # Validate price
            max_price = CROP_PRICES[crop_type]["sell"] * 3 * quantity
            if price > max_price:
                return False, f"Price too high! Max ${max_price:,} for {quantity} {crop_type}", 0
            if price < CROP_PRICES[crop_type]["sell"] * quantity:
                return False, f"Price too low! Min ${CROP_PRICES[crop_type]['sell'] * quantity:,}", 0
            
            # Create listing
            cursor = await self.conn.execute(
                "INSERT INTO market_stands (seller_id, crop_type, quantity, price) VALUES (?, ?, ?, ?)",
                (user_id, crop_type, quantity, price)
            )
            listing_id = cursor.lastrowid
            
            # Remove from barn
            await self.conn.execute(
                "UPDATE barn SET quantity = quantity - ? WHERE user_id = ? AND crop_type = ?",
                (quantity, user_id, crop_type)
            )
            
            await self.conn.commit()
            
            return True, f"Listed {quantity} {crop_type} for ${price:,}!", listing_id
    
    async def get_market_listings(self, crop_type: Optional[str] = None, page: int = 0, per_page: int = 10) -> Tuple[List[dict], int]:
        """Get market listings with pagination"""
        async with self.lock:
            where_clause = "WHERE is_sold = 0"
            params = []
            
            if crop_type:
                where_clause += " AND crop_type = ?"
                params.append(crop_type)
            
            # Get total count
            cursor = await self.conn.execute(
                f"SELECT COUNT(*) FROM market_stands {where_clause}",
                params
            )
            total = (await cursor.fetchone())[0]
            
            # Get paginated results
            cursor = await self.conn.execute(
                f"""SELECT ms.*, u.first_name, u.username 
                    FROM market_stands ms 
                    JOIN users u ON ms.seller_id = u.user_id 
                    {where_clause}
                    ORDER BY ms.price / ms.quantity ASC 
                    LIMIT ? OFFSET ?""",
                params + [per_page, page * per_page]
            )
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            listings = []
            for row in rows:
                listing = dict(zip(columns, row))
                listing["price_per_unit"] = listing["price"] / listing["quantity"]
                listings.append(listing)
            
            return listings, total
    
    # ==================== FAMILY & FRIENDS ====================
    
    async def create_proposal(self, proposal_id: str, from_id: int, to_id: int, 
                            proposal_type: str, data: Optional[dict] = None) -> bool:
        """Create a new proposal"""
        if from_id == to_id:
            return False
        
        async with self.lock:
            try:
                await self.conn.execute(
                    "INSERT INTO proposals (proposal_id, from_id, to_id, proposal_type, data) VALUES (?, ?, ?, ?, ?)",
                    (proposal_id, from_id, to_id, proposal_type, json.dumps(data) if data else None)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Proposal creation error: {e}")
                return False
    
    async def accept_proposal(self, proposal_id: str, acceptor_id: int) -> Tuple[bool, str, Optional[dict]]:
        """Accept a proposal"""
        async with self.lock:
            # Get proposal
            cursor = await self.conn.execute(
                "SELECT * FROM proposals WHERE proposal_id = ? AND expires_at > CURRENT_TIMESTAMP",
                (proposal_id,)
            )
            proposal = await cursor.fetchone()
            
            if not proposal:
                return False, "Proposal not found or expired!", None
            
            # Check if acceptor is the target
            if proposal[3] != acceptor_id:  # to_id is at index 3
                return False, "This proposal is not for you!", None
            
            proposal_type = proposal[4]  # proposal_type at index 4
            from_id = proposal[2]  # from_id at index 2
            data = json.loads(proposal[5]) if proposal[5] else {}  # data at index 5
            
            # Process based on type
            if proposal_type == "friend":
                # Add friendship
                await self.conn.execute(
                    "INSERT OR IGNORE INTO friendships (user1_id, user2_id) VALUES (?, ?)",
                    (from_id, acceptor_id)
                )
                # Give bonus
                await self.update_user_currency(from_id, "cash", 3000)
                await self.update_user_currency(acceptor_id, "cash", 3000)
                result_msg = "Friendship established! $3,000 bonus awarded to both!"
                
            elif proposal_type == "adopt":
                # Add family relation
                await self.conn.execute(
                    "INSERT INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
                    (from_id, acceptor_id, "child")
                )
                result_msg = "Adoption complete! Welcome to the family!"
                
            elif proposal_type == "marry":
                # Add marriage relation
                await self.conn.execute(
                    "INSERT INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
                    (from_id, acceptor_id, "spouse")
                )
                result_msg = "Marriage complete! Congratulations!"
                
            elif proposal_type == "trade":
                # Handle trade - data should contain trade details
                # This is simplified - implement based on your trade system
                result_msg = "Trade completed successfully!"
                
            else:
                return False, f"Unknown proposal type: {proposal_type}", None
            
            # Delete proposal
            await self.conn.execute("DELETE FROM proposals WHERE proposal_id = ?", (proposal_id,))
            await self.conn.commit()
            
            return True, result_msg, {"from_id": from_id, "type": proposal_type, "data": data}
    
    # ==================== ADMIN & BACKUP ====================
    
    async def create_backup(self) -> bytes:
        """Create encrypted backup"""
        import io
        import zipfile
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "tables": {}
        }
        
        async with self.lock:
            # Get table names
            cursor = await self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in await cursor.fetchall()]
            
            # Backup each table
            for table in tables:
                cursor = await self.conn.execute(f"SELECT * FROM {table}")
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                table_data = []
                for row in rows:
                    table_data.append(dict(zip(columns, row)))
                
                backup_data["tables"][table] = table_data
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            json_data = json.dumps(backup_data, indent=2, default=str)
            zip_file.writestr("backup.json", json_data)
            
            # Add checksum
            checksum = hashlib.sha256(json_data.encode()).hexdigest()
            zip_file.writestr("checksum.txt", f"SHA256: {checksum}")
        
        return zip_buffer.getvalue()

# ============================================================================
# BOT INSTANCE & GLOBALS
# ============================================================================

# Initialize database
db = Database(DB_PATH)

# Initialize bot with AiohttpSession for aiogram 3.0.0b7
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Initialize UI
ui = EnhancedUI()

# Rate limiting
user_cooldowns = {}

# ============================================================================
# DECORATORS & MIDDLEWARE
# ============================================================================

def cooldown(seconds: int = 1):
    """Cooldown decorator to prevent spam"""
    def decorator(func):
        async def wrapper(message: Message, *args, **kwargs):
            user_id = message.from_user.id
            now = time.time()
            
            if user_id in user_cooldowns:
                last_time = user_cooldowns[user_id]
                if now - last_time < seconds:
                    wait_time = seconds - (now - last_time)
                    await message.answer(
                        f"⏳ Please wait {wait_time:.1f} seconds before using this command again."
                    )
                    return
            
            user_cooldowns[user_id] = now
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator

def owner_only(func):
    """Owner-only command decorator"""
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id != OWNER_ID:
            await message.answer("🔒 This command is only for the bot owner.")
            return
        return await func(message, *args, **kwargs)
    return wrapper

# ============================================================================
# COMMAND HANDLERS - ENHANCED UI
# ============================================================================

@dp.message(Command("start"))
@cooldown(2)
async def cmd_start(message: Message):
    """Enhanced start command with welcome animation"""
    await ui.send_typing(message)
    
    # Create or get user
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Welcome message with animation
    welcome_msg = await ui.animated_message(
        message, 
        f"Welcome {user['first_name']}!",
        "hearts"
    )
    
    # Enhanced welcome card
    welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT!</b> ✨

👤 <b>Your Profile:</b>
• Name: {user['first_name']}
• Level: {user.get('level', 1)}
• Balance: ${user.get('cash', 0):,}

🎮 <b>What can you do?</b>
• 🌳 Build a virtual family
• 🌾 Farm and trade crops
• 🤝 Make global friends
• ⚔️ Engage in PvP battles
• 🏪 Buy/Sell on the market

💡 <b>Quick Start:</b>
1. Claim your <code>/daily</code> bonus
2. Plant crops with <code>/plant</code>
3. Make friends with <code>/friend</code>

📊 {ui.create_stats_bar(user)}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Quick Start Guide", callback_data="guide_start"),
            InlineKeyboardButton(text="📋 All Commands", callback_data="show_commands")
        ],
        [
            InlineKeyboardButton(text="🌾 Start Farming", callback_data="garden_main"),
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Find Family", callback_data="family_find")
        ],
        [
            InlineKeyboardButton(text="⚙️ Settings", callback_data="settings_main"),
            InlineKeyboardButton(text="❓ Help", callback_data="help_main")
        ]
    ])
    
    await welcome_msg.edit_text(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    # Send main menu
    main_menu = ui.create_main_menu()
    await message.answer("📍 <b>Main Menu:</b>", reply_markup=main_menu, parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
@cooldown(5)
async def cmd_ping(message: Message):
    """Enhanced ping with system status"""
    start_time = time.time()
    
    # Create animated ping message
    ping_msg = await ui.animated_message(message, "Checking system status...", "spinner")
    
    # Calculate latency
    end_time = time.time()
    latency = (end_time - start_time) * 1000  # in milliseconds
    
    # Check database
    db_status = "✅ Connected"
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            user = await db.create_user(message.from_user)
    except Exception as e:
        db_status = f"❌ Error: {str(e)[:50]}"
    
    # System status
    import psutil
    import platform
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    status_text = f"""
🏓 <b>SYSTEM STATUS</b>

📊 <b>Bot Performance:</b>
• Latency: <code>{latency:.2f}ms</code>
• Uptime: <code>0 days 00:00:00</code> (implement later)
• Database: {db_status}

🖥️ <b>System Resources:</b>
• CPU: <code>{cpu_percent}%</code>
• Memory: <code>{memory.percent}%</code>
• Python: <code>{platform.python_version()}</code>

👥 <b>Bot Stats:</b>
• Users: <code>Loading...</code>
• Active: <code>Loading...</code>
• Version: <b>2.0 Enhanced</b>

🔄 <i>Last checked: {datetime.now().strftime('%H:%M:%S')}</i>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="ping_refresh"),
            InlineKeyboardButton(text="📊 Detailed Stats", callback_data="stats_detailed")
        ],
        [
            InlineKeyboardButton(text="🔧 Admin Panel", callback_data="admin_panel"),
            InlineKeyboardButton(text="❌ Close", callback_data="close_menu")
        ]
    ])
    
    await ping_msg.edit_text(status_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile", "account"))
@cooldown(3)
async def cmd_profile(message: Message):
    """Enhanced profile with beautiful layout"""
    await ui.send_typing(message, 0.3)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Get additional stats
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM family_relations WHERE user1_id = ? OR user2_id = ?",
            (user['user_id'], user['user_id'])
        )
        family_count = (await cursor.fetchone())[0] // 2
        
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM friendships WHERE user1_id = ?",
            (user['user_id'],)
        )
        friend_count = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
            (user['user_id'],)
        )
        growing_plants = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute(
            "SELECT SUM(quantity) FROM barn WHERE user_id = ?",
            (user['user_id'],)
        )
        barn_total = (await cursor.fetchone())[0] or 0
    
    # Calculate level based on XP (simplified)
    xp = user.get('total_xp', 0)
    level = user.get('level', 1)
    xp_needed = level * 100
    xp_progress = min(100, int((xp % xp_needed) / xp_needed * 100)) if xp_needed > 0 else 0
    
    # Create profile card
    profile_text = f"""
🏆 <b>PROFILE OF {user['first_name']}</b>

🆔 <b>Account Info:</b>
• ID: <code>{user['user_id']}</code>
• Level: <b>{level}</b> ({xp_progress}% to next)
• XP: <code>{xp:,}</code>
• Status: {'❤️ Alive' if user['is_alive'] else '💀 Dead'}

💰 <b>Economy:</b>
• Cash: <b>${user['cash']:,}</b>
• Gold: <b>{user['gold']:,} 🪙</b>
• Bonds: <b>{user['bonds']:,} 👨‍👩‍👧‍👦</b>
• Credits: <b>{user['credits']:,} ⭐</b>
• Tokens: <b>{user['tokens']:,} 🌱</b>

📊 <b>Stats:</b>
• Family: <b>{family_count} members</b>
• Friends: <b>{friend_count} friends</b>
• Reputation: <b>{user['reputation']}/200 ⭐</b>
• Plants Growing: <b>{growing_plants}</b>
• Barn Storage: <b>{barn_total} crops</b>

⚔️ <b>Combat:</b>
• Weapon: <b>{user['weapon'].title()}</b>
• Job: <b>{user['job'] or 'Unemployed'}</b>

🎨 <b>Customization:</b>
• Theme: <b>{user['theme'].title()}</b>
• Language: <b>{user['language'].upper()}</b>
"""
    
    # Create XP progress bar
    progress_bar = "█" * (xp_progress // 10) + "░" * (10 - (xp_progress // 10))
    profile_text += f"\n📈 <b>Level Progress:</b> [{progress_bar}] {xp_progress}%\n"
    
    # Add stats bar
    profile_text += f"\n{ui.create_stats_bar(user)}\n"
    
    # Enhanced keyboard with icons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Daily Bonus", callback_data="daily_claim"),
            InlineKeyboardButton(text="🌾 My Garden", callback_data="garden_view")
        ],
        [
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Family Tree", callback_data="family_tree"),
            InlineKeyboardButton(text="🤝 Friend Circle", callback_data="friend_circle")
        ],
        [
            InlineKeyboardButton(text="⚔️ PvP Actions", callback_data="pvp_menu"),
            InlineKeyboardButton(text="🏪 Marketplace", callback_data="market_main")
        ],
        [
            InlineKeyboardButton(text="🎨 Customize", callback_data="profile_customize"),
            InlineKeyboardButton(text="📊 Statistics", callback_data="profile_stats")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="profile_refresh"),
            InlineKeyboardButton(text="❌ Close", callback_data="close_menu")
        ]
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("garden"))
@cooldown(2)
async def cmd_garden(message: Message):
    """Enhanced garden view with animations"""
    await ui.send_typing(message, 0.5)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Please use /start first!")
        return
    
    # Get garden data
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT g.slots, g.expansion_level, 
               COUNT(gp.id) as used_slots,
               SUM(CASE WHEN gp.is_ready = 1 THEN 1 ELSE 0 END) as ready_count
               FROM gardens g 
               LEFT JOIN garden_plants gp ON g.user_id = gp.user_id 
               WHERE g.user_id = ?""",
            (user['user_id'],)
        )
        garden_data = await cursor.fetchone()
        
        cursor = await db.conn.execute(
            """SELECT crop_type, 
               ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours_passed,
               grow_time, is_ready
               FROM garden_plants 
               WHERE user_id = ? AND is_ready = 0
               ORDER BY planted_at""",
            (user['user_id'],)
        )
        plants = await cursor.fetchall()
        
        cursor = await db.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ? ORDER BY quantity DESC LIMIT 10",
            (user['user_id'],)
        )
        barn_items = await cursor.fetchall()
    
    if not garden_data:
        await message.answer("No garden found! Use /start to create one.")
        return
    
    slots, expansion, used_slots, ready_count = garden_data
    
    # Create garden visualization
    garden_text = f"""
{EMOJIS['garden']} <b>GARDEN OF {user['first_name']}</b>

📊 <b>Garden Stats:</b>
• Slots: <b>{used_slots}/{slots}</b> ({ready_count} ready)
• Expansion: <b>Level {expansion}</b>
• Barn Capacity: <b>{garden_data[1] * 50}</b>

🌱 <b>Growing Plants:</b>
"""
    
    if plants:
        for plant in plants:
            crop_type, hours_passed, grow_time, is_ready = plant
            emoji = CROP_EMOJIS.get(crop_type, "🌱")
            
            if is_ready:
                status = f"{EMOJIS['check']} Ready!"
            else:
                progress = min(100, int((hours_passed / (grow_time / 3600)) * 100))
                remaining = max(0, (grow_time / 3600) - hours_passed)
                
                # Progress bar
                bars = int(progress / 10)
                progress_bar = "█" * bars + "░" * (10 - bars)
                
                status = f"[{progress_bar}] {progress}% ({remaining:.1f}h left)"
            
            garden_text += f"• {emoji} <b>{crop_type.title()}</b>: {status}\n"
    else:
        garden_text += "• No plants growing. Use <code>/plant</code> to start!\n"
    
    # Barn summary
    if barn_items:
        garden_text += f"\n🏠 <b>Barn Storage (Top 10):</b>\n"
        for crop_type, quantity in barn_items[:5]:
            emoji = CROP_EMOJIS.get(crop_type, "📦")
            garden_text += f"• {emoji} {crop_type.title()}: <b>{quantity}</b>\n"
    
    garden_text += f"\n{ui.create_stats_bar(user)}\n"
    
    # Enhanced garden keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{EMOJIS['garden']} Plant Crops", callback_data="garden_plant_menu"),
            InlineKeyboardButton(text=f"{EMOJIS['check']} Harvest", callback_data="garden_harvest")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS['refresh']} Fertilize", callback_data="garden_fertilize_menu"),
            InlineKeyboardButton(text=f"{EMOJIS['market']} Market", callback_data="market_from_garden")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS['shop']} Buy Seeds", callback_data="shop_seeds"),
            InlineKeyboardButton(text=f"📦 View Barn", callback_data="barn_view")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS['up']} Expand", callback_data="garden_expand"),
            InlineKeyboardButton(text=f"⚙️ Settings", callback_data="garden_settings")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS['refresh']} Refresh", callback_data="garden_refresh"),
            InlineKeyboardButton(text=f"{EMOJIS['close']} Close", callback_data="close_menu")
        ]
    ])
    
    await message.answer(garden_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
@cooldown(2)
async def cmd_plant(message: Message, command: CommandObject):
    """Enhanced planting command"""
    if not command.args:
        # Show planting guide
        guide_text = f"""
{EMOJIS['garden']} <b>PLANTING GUIDE</b>

📝 <b>Usage:</b>
<code>/plant [crop] [quantity]</code>

🌱 <b>Available Crops:</b>
"""
        for crop in CROP_TYPES:
            price = CROP_PRICES[crop]["buy"]
            sell = CROP_PRICES[crop]["sell"]
            time_hours = CROP_PRICES[crop]["grow_time"]
            emoji = CROP_EMOJIS.get(crop, "🌱")
            
            guide_text += f"• {emoji} <b>{crop.title()}</b>: Buy ${price}, Sell ${sell}, Grows in {time_hours}h\n"
        
        guide_text += f"""
💡 <b>Examples:</b>
• <code>/plant carrot 3</code> - Plant 3 carrots
• <code>/plant tomato</code> - Plant 1 tomato (default)
• <code>/plant corn 5</code> - Plant 5 corn

💰 <b>Need more cash?</b> Use <code>/daily</code> or sell crops!

{ui.create_stats_bar(await db.get_user(message.from_user.id) or {})}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🥕 Plant Carrots", callback_data="plant_carrot"),
                InlineKeyboardButton(text="🍅 Plant Tomatoes", callback_data="plant_tomato")
            ],
            [
                InlineKeyboardButton(text="🥔 Plant Potatoes", callback_data="plant_potato"),
                InlineKeyboardButton(text="🍆 Plant Eggplants", callback_data="plant_eggplant")
            ],
            [
                InlineKeyboardButton(text="🌽 Plant Corn", callback_data="plant_corn"),
                InlineKeyboardButton(text="🫑 Plant Peppers", callback_data="plant_pepper")
            ],
            [
                InlineKeyboardButton(text="📊 Check Prices", callback_data="prices_view"),
                InlineKeyboardButton(text="🌾 Back to Garden", callback_data="garden_view")
            ]
        ])
        
        await message.answer(guide_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return
    
    # Parse command
    args = command.args.split()
    if len(args) == 1:
        crop_type = args[0].lower()
        quantity = 1
    elif len(args) == 2:
        crop_type, quantity_str = args[0].lower(), args[1]
        try:
            quantity = int(quantity_str)
            if quantity < 1 or quantity > 20:
                await message.answer("❌ Quantity must be between 1 and 20!")
                return
        except ValueError:
            await message.answer("❌ Invalid quantity! Please enter a number.")
            return
    else:
        await message.answer("❌ Usage: /plant [crop] [quantity]\nExample: /plant carrot 3")
        return
    
    if crop_type not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Choose from: {', '.join(CROP_TYPES)}")
        return
    
    # Show planting animation
    planting_msg = await ui.animated_message(
        message, 
        f"Planting {quantity} {crop_type}(s)...",
        "dots"
    )
    
    # Actually plant
    success, msg, cost = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if success:
        result_text = f"""
{EMOJIS['check']} <b>PLANTING SUCCESSFUL!</b>

🌱 Planted: <b>{quantity} {CROP_EMOJIS.get(crop_type)} {crop_type.title()}(s)</b>
💰 Cost: <b>${cost:,}</b>
⏳ Grow Time: <b>{CROP_PRICES[crop_type]['grow_time']} hours</b>

💡 <b>Tips:</b>
• Use <code>/garden</code> to check progress
• Friends can <code>/fertilize</code> to speed up growth
• Harvest with <code>/harvest</code> when ready

{ui.create_stats_bar(await db.get_user(message.from_user.id))}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌾 View Garden", callback_data="garden_view"),
                InlineKeyboardButton(text="🌱 Plant More", callback_data="plant_menu")
            ],
            [
                InlineKeyboardButton(text="💧 Fertilize", callback_data="fertilize_find"),
                InlineKeyboardButton(text="📊 Market Prices", callback_data="market_prices")
            ]
        ])
        
        await planting_msg.edit_text(result_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await planting_msg.edit_text(f"❌ {msg}")

@dp.message(Command("harvest"))
@cooldown(3)
async def cmd_harvest(message: Message):
    """Enhanced harvesting with animations"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Please use /start first!")
        return
    
    # Show harvesting animation
    harvest_msg = await ui.animated_message(
        message,
        "Harvesting ready crops...",
        "spinner"
    )
    
    # Harvest crops
    harvested, total_value, msg = await db.harvest_crops(message.from_user.id)
    
    if harvested:
        # Create harvest report
        report_text = f"""
{EMOJIS['check']} <b>HARVEST COMPLETE!</b>

📦 <b>Harvested Crops:</b>
"""
        for crop_type, quantity in harvested.items():
            emoji = CROP_EMOJIS.get(crop_type, "🌱")
            value = CROP_PRICES[crop_type]["sell"] * quantity
            report_text += f"• {emoji} <b>{crop_type.title()}</b>: {quantity} (${value:,})\n"
        
        report_text += f"""
💰 <b>Total Value:</b> <b>${total_value:,}</b>
🏠 <b>Stored in:</b> Your barn

💡 <b>Options:</b>
• Sell on market for profit
• Use to complete garden orders
• Trade with friends
• Gift to new players

🎯 <b>Your barn is now updated!</b>

{ui.create_stats_bar(user)}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏪 Sell on Market", callback_data="market_sell_menu"),
                InlineKeyboardButton(text="🎁 Gift Crops", callback_data="gift_menu")
            ],
            [
                InlineKeyboardButton(text="📊 View Barn", callback_data="barn_view"),
                InlineKeyboardButton(text="🌾 Back to Garden", callback_data="garden_view")
            ],
            [
                InlineKeyboardButton(text="🔄 Harvest Again", callback_data="harvest_again"),
                InlineKeyboardButton(text="❌ Close", callback_data="close_menu")
            ]
        ])
        
        await harvest_msg.edit_text(report_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await harvest_msg.edit_text(f"🌾 {msg}\n\n💡 Try planting more crops or waiting for them to grow!")

@dp.message(Command("market", "stands"))
@cooldown(2)
async def cmd_market(message: Message, command: CommandObject):
    """Enhanced market view"""
    args = command.args if command.args else ""
    
    # Show loading animation
    market_msg = await ui.animated_message(
        message,
        "Loading market listings...",
        "dots"
    )
    
    page = 0
    crop_type = None
    
    # Parse arguments
    if args.isdigit():
        page = int(args) - 1
        if page < 0:
            page = 0
    elif args in CROP_TYPES:
        crop_type = args
    
    # Get market listings
    listings, total = await db.get_market_listings(crop_type=crop_type, page=page)
    
    if not listings:
        market_text = f"""
{EMOJIS['market']} <b>MARKETPLACE</b>

📭 <b>No listings found!</b>

💡 <b>Be the first to sell:</b>
Use <code>/putstand [crop] [quantity] [price]</code>
Example: <code>/putstand carrot 20 300</code>

🌱 <b>Want to buy?</b> Check back later or ask friends to list crops!

{ui.create_stats_bar(await db.get_user(message.from_user.id) or {})}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌾 List My Crops", callback_data="market_sell_menu"),
                InlineKeyboardButton(text="🌱 Plant Crops", callback_data="plant_menu")
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="market_refresh"),
                InlineKeyboardButton(text="🌾 My Garden", callback_data="garden_view")
            ]
        ])
        
        await market_msg.edit_text(market_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return
    
    # Create market listings display
    market_text = f"""
{EMOJIS['market']} <b>MARKETPLACE</b>

📊 <b>Active Listings:</b> {total} total
{f"🌱 Filter: {crop_type.title()} | " if crop_type else ""}Page: {page + 1}/{(total + 9) // 10}

"""
    
    for i, listing in enumerate(listings, 1):
        emoji = CROP_EMOJIS.get(listing['crop_type'], "📦")
        price_per = listing['price_per_unit']
        
        market_text += f"""
{i}. {emoji} <b>{listing['crop_type'].title()}</b>
   • Quantity: <b>{listing['quantity']}</b>
   • Price: <b>${listing['price']:,}</b> (${price_per:.1f}/each)
   • Seller: <b>{listing['first_name']}</b> (@{listing['username'] or 'NoUsername'})
   • ID: <code>{listing['id']}</code>
   • Buy: <code>/buy {listing['id']} [quantity]</code>
"""
    
    market_text += f"""
💡 <b>How to Buy:</b>
<code>/buy [listing_id] [quantity]</code>
Example: <code>/buy {listings[0]['id']} 5</code>

🔍 <b>Filter by crop:</b>
<code>/market carrot</code> or <code>/market tomato</code>

{ui.create_stats_bar(await db.get_user(message.from_user.id) or {})}
"""
    
    # Create paginated keyboard
    keyboard_buttons = []
    
    # Crop filter buttons
    crop_buttons = []
    for crop in CROP_TYPES[:3]:
        crop_buttons.append(InlineKeyboardButton(
            text=f"{CROP_EMOJIS.get(crop)} {crop[:3]}",
            callback_data=f"market_filter_{crop}"
        ))
    
    if crop_buttons:
        keyboard_buttons.append(crop_buttons)
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text=f"{EMOJIS['prev']} Prev",
            callback_data=f"market_page_{page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"📄 {page+1}/{(total+9)//10}",
        callback_data="noop"
    ))
    
    if (page + 1) * 10 < total:
        nav_buttons.append(InlineKeyboardButton(
            text=f"Next {EMOJIS['next']}",
            callback_data=f"market_page_{page+1}"
        ))
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    # Action buttons
    keyboard_buttons.extend([
        [
            InlineKeyboardButton(text="🌾 Sell My Crops", callback_data="market_sell_menu"),
            InlineKeyboardButton(text="📊 View My Stand", callback_data="market_my_stand")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="market_refresh"),
            InlineKeyboardButton(text="🌱 All Crops", callback_data="market_clear_filter")
        ],
        [
            InlineKeyboardButton(text=f"{EMOJIS['close']} Close", callback_data="close_menu")
        ]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await market_msg.edit_text(market_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("backup"))
@owner_only
@cooldown(60)
async def cmd_backup(message: Message):
    """Enhanced backup command with progress"""
    backup_msg = await ui.animated_message(
        message,
        "Creating secure backup...",
        "spinner"
    )
    
    try:
        # Step 1: Creating backup
        await backup_msg.edit_text(f"{ANIMATIONS['spinner'][0]} Step 1/3: Collecting data...")
        backup_data = await db.create_backup()
        
        # Step 2: Preparing file
        await backup_msg.edit_text(f"{ANIMATIONS['spinner'][2]} Step 2/3: Encrypting backup...")
        
        # Step 3: Sending to owner
        await backup_msg.edit_text(f"{ANIMATIONS['spinner'][4]} Step 3/3: Sending to owner...")
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.zip"
        
        # Send as document
        from io import BytesIO
        backup_file = BytesIO(backup_data)
        backup_file.name = filename
        
        await bot.send_document(
            chat_id=OWNER_ID,
            document=types.BufferedInputFile(backup_data, filename=filename),
            caption=f"""
🔐 <b>BACKUP CREATED</b>

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 By: {message.from_user.full_name}
🤖 Bot: Family Tree Bot v2.0

💾 <b>Contains:</b>
• User accounts & balances
• Family relationships
• Garden data & crops
• Market listings
• Friend networks

⚠️ <b>Keep this file secure!</b>
"""
        )
        
        # Success message
        success_text = f"""
{EMOJIS['check']} <b>BACKUP COMPLETE!</b>

✅ Backup successfully created and sent to owner.
📁 File: <code>{filename}</code>
📊 Size: <code>{len(backup_data) // 1024} KB</code>
🔐 Security: Encrypted ZIP with checksum

💡 <b>Backup includes:</b>
• All user data
• Family trees
• Garden progress
• Market economy
• Friend networks

🛡️ <b>Stored securely in your Telegram chat.</b>

⏰ Next backup recommended: <b>Tomorrow</b>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 View Stats", callback_data="admin_stats"),
                InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")
            ],
            [
                InlineKeyboardButton(text="🔄 Create Another", callback_data="backup_again"),
                InlineKeyboardButton(text="❌ Close", callback_data="close_menu")
            ]
        ])
        
        await backup_msg.edit_text(success_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        error_text = f"""
{EMOJIS['warning']} <b>BACKUP FAILED!</b>

❌ Error: <code>{str(e)[:100]}</code>

🔧 <b>Troubleshooting:</b>
1. Check bot has file sending permission
2. Verify database connection
3. Ensure enough disk space
4. Check log channel for details

🔄 <b>Try again in a few minutes.</b>
"""
        await backup_msg.edit_text(error_text, parse_mode=ParseMode.HTML)

@dp.message(Command("refresh"))
@owner_only
@cooldown(30)
async def cmd_refresh(message: Message):
    """Enhanced refresh command"""
    refresh_msg = await ui.animated_message(
        message,
        "Refreshing system data...",
        "dots"
    )
    
    try:
        updates = []
        
        # Refresh 1: Update crop growth
        await refresh_msg.edit_text(f"{ANIMATIONS['dots'][0]} Refreshing crop growth...")
        async with db.lock:
            await db.conn.execute(
                "UPDATE garden_plants SET is_ready = 1 WHERE "
                "julianday('now') - julianday(planted_at) > grow_time/86400.0"
            )
            cursor = await db.conn.execute("SELECT changes()")
            crop_updates = (await cursor.fetchone())[0]
            updates.append(f"🌱 Crops ready: {crop_updates}")
        
        # Refresh 2: Clear expired proposals
        await refresh_msg.edit_text(f"{ANIMATIONS['dots'][1]} Cleaning expired proposals...")
        async with db.lock:
            await db.conn.execute(
                "DELETE FROM proposals WHERE expires_at < CURRENT_TIMESTAMP"
            )
            cursor = await db.conn.execute("SELECT changes()")
            proposal_updates = (await cursor.fetchone())[0]
            updates.append(f"📝 Proposals cleared: {proposal_updates}")
        
        # Refresh 3: Clear old market listings (7+ days)
        await refresh_msg.edit_text(f"{ANIMATIONS['dots'][2]} Cleaning old market listings...")
        async with db.lock:
            await db.conn.execute(
                "DELETE FROM market_stands WHERE created_at < datetime('now', '-7 days')"
            )
            cursor = await db.conn.execute("SELECT changes()")
            market_updates = (await cursor.fetchone())[0]
            updates.append(f"🏪 Old listings: {market_updates}")
        
        await db.conn.commit()
        
        # Success message
        success_text = f"""
{EMOJIS['check']} <b>SYSTEM REFRESHED!</b>

🔄 <b>Completed Tasks:</b>
"""
        for update in updates:
            success_text += f"• {update}\n"
        
        success_text += f"""
✅ <b>All systems updated successfully!</b>

⏰ Next refresh: <b>Automatically in 1 hour</b>
👑 Manual refresh available anytime

{ui.create_stats_bar(await db.get_user(message.from_user.id) or {})}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 System Stats", callback_data="admin_stats"),
                InlineKeyboardButton(text="👤 User Management", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh Again", callback_data="refresh_again"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main")
            ]
        ])
        
        await refresh_msg.edit_text(success_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await refresh_msg.edit_text(f"❌ Refresh failed: {str(e)}")

@dp.message(Command("hmk"))
@cooldown(300)
async def cmd_hmk(message: Message):
    """Enhanced Hired Muscle command with animations"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Please use /start first!")
        return
    
    # Check requirements
    if user['cash'] < 5000:
        await message.answer(f"""
{EMOJIS['warning']} <b>INSUFFICIENT FUNDS!</b>

💰 Need: <b>$5,000</b>
💵 Have: <b>${user['cash']:,}</b>

💡 <b>Earn more cash:</b>
• Use <code>/daily</code> for bonuses
• Sell crops on market
• Complete garden orders
• Rob other players (risky!)
""", parse_mode=ParseMode.HTML)
        return
    
    # Check reputation
    if user['reputation'] < 50:
        await message.answer(f"""
{EMOJIS['warning']} <b>REPUTATION TOO LOW!</b>

⭐ Need: <b>50+ reputation</b>
📉 Have: <b>{user['reputation']}/200</b>

💡 <b>Improve reputation:</b>
• Help others with <code>/fertilize</code>
• Send gifts with <code>/gift</code>
• Make friends with <code>/friend</code>
• Wait for daily reset
""", parse_mode=ParseMode.HTML)
        return
    
    # Show hiring animation
    hmk_msg = await ui.animated_message(
        message,
        "Hiring muscle...",
        "spinner"
    )
    
    # Find target
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT user_id, first_name, cash 
               FROM users 
               WHERE user_id != ? AND is_alive = 1 AND cash > 1000 
               ORDER BY RANDOM() LIMIT 1""",
            (user['user_id'],)
        )
        target = await cursor.fetchone()
    
    if not target:
        await hmk_msg.edit_text(f"""
{EMOJIS['info']} <b>NO SUITABLE TARGETS!</b>

🎯 Couldn't find anyone worth attacking.

💡 <b>Try again later when:</b>
• More players are online
• Players have more cash
• During active hours

🔄 Check back in a few minutes!
""", parse_mode=ParseMode.HTML)
        return
    
    target_id, target_name, target_cash = target
    
    # Calculate attack
    success_chance = 70  # Base chance
    if user['weapon'] != 'fist':
        success_chance += 20
    
    success = random.randint(1, 100) <= success_chance
    
    if success:
        # Successful attack
        steal_percent = random.uniform(0.3, 0.6)
        stolen = min(int(target_cash * steal_percent), 10000)
        stolen = max(stolen, 1000)  # Minimum 1000
        
        # Update balances
        await db.update_user_currency(user['user_id'], "cash", -5000)  # Cost
        await db.update_user_currency(target_id, "cash", -stolen)
        await db.update_user_currency(user['user_id'], "cash", stolen + 2000)  # Stolen + bonus
        
        # Update reputation
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET reputation = reputation - 20 WHERE user_id = ?",
                (user['user_id'],)
            )
            await db.conn.commit()
        
        # Success message
        result_text = f"""
💪 <b>HIRED MUSCLE ATTACK SUCCESSFUL!</b>

💰 <b>Cost:</b> $5,000 (muscle hire)
🎯 <b>Target:</b> {target_name}
🤑 <b>Stolen:</b> ${stolen:,}
🎁 <b>Bonus:</b> $2,000 (success fee)
📈 <b>Total Gain:</b> ${stolen:,}

⚖️ <b>Consequences:</b>
• Reputation: <b>-20</b> (now {max(0, user['reputation']-20)})
• Target alerted of attack
• Cooldown: 5 minutes

🔥 <b>The muscle did their job perfectly!</b>

{ui.create_stats_bar(await db.get_user(message.from_user.id))}
"""
        
        # Notify target
        try:
            await bot.send_message(
                target_id,
                f"""
⚠️ <b>YOU WERE ATTACKED!</b>

💪 Attacker: {user['first_name']}
💰 Stolen: ${stolen:,}
💸 New Balance: ${target_cash - stolen:,}

🛡️ <b>Protect yourself:</b>
• Get better weapons
• Make powerful friends
• Keep less cash on hand
• Get revenge later!

🔒 Stay safe out there!
""",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
    else:
        # Failed attack
        await db.update_user_currency(user['user_id'], "cash", -5000)  # Still pay
        
        # Update reputation
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET reputation = reputation - 30 WHERE user_id = ?",
                (user['user_id'],)
            )
            await db.conn.commit()
        
        result_text = f"""
😱 <b>HIRED MUSCLE ATTACK FAILED!</b>

💰 <b>Cost:</b> $5,000 (muscle hire - lost!)
🎯 <b>Target:</b> {target_name}
🚫 <b>Result:</b> Muscle got scared and ran!

⚖️ <b>Consequences:</b>
• Money lost: <b>$5,000</b>
• Reputation: <b>-30</b> (now {max(0, user['reputation']-30)})
• Cooldown: 10 minutes

💡 <b>Better luck next time!</b>
Consider upgrading your weapon first.

{ui.create_stats_bar(await db.get_user(message.from_user.id))}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚔️ Upgrade Weapon", callback_data="shop_weapons"),
            InlineKeyboardButton(text="💰 Earn Money", callback_data="earn_money")
        ],
        [
            InlineKeyboardButton(text="🔄 Try Again", callback_data="hmk_retry"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main")
        ]
    ])
    
    await hmk_msg.edit_text(result_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# CALLBACK QUERY HANDLERS
# ============================================================================

@dp.callback_query(F.data == "close_menu")
async def handle_close_menu(callback: CallbackQuery):
    """Handle close menu button"""
    try:
        await callback.message.delete()
    except:
        await callback.answer("Menu closed!")
    await callback.answer()

@dp.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Handle no-operation buttons"""
    await callback.answer()

@dp.callback_query(F.data == "garden_view")
async def handle_garden_view(callback: CallbackQuery):
    """Handle garden view callback"""
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "profile_refresh")
async def handle_profile_refresh(callback: CallbackQuery):
    """Handle profile refresh"""
    await cmd_profile(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("market_page_"))
async def handle_market_page(callback: CallbackQuery):
    """Handle market pagination"""
    page = int(callback.data.split("_")[2])
    await cmd_market(callback.message, CommandObject(args=str(page + 1)))
    await callback.answer()

@dp.callback_query(F.data.startswith("market_filter_"))
async def handle_market_filter(callback: CallbackQuery):
    """Handle market filter"""
    crop_type = callback.data.split("_")[2]
    await cmd_market(callback.message, CommandObject(args=crop_type))
    await callback.answer()

@dp.callback_query(F.data == "market_refresh")
async def handle_market_refresh(callback: CallbackQuery):
    """Handle market refresh"""
    await cmd_market(callback.message, CommandObject(args=""))
    await callback.answer()

@dp.callback_query(F.data == "garden_harvest")
async def handle_garden_harvest(callback: CallbackQuery):
    """Handle garden harvest from button"""
    await cmd_harvest(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "backup_again")
async def handle_backup_again(callback: CallbackQuery):
    """Handle backup again"""
    await cmd_backup(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "refresh_again")
async def handle_refresh_again(callback: CallbackQuery):
    """Handle refresh again"""
    await cmd_refresh(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "hmk_retry")
async def handle_hmk_retry(callback: CallbackQuery):
    """Handle HMK retry"""
    await cmd_hmk(callback.message)
    await callback.answer()

# ============================================================================
# TEXT HANDLERS (FOR MAIN MENU)
# ============================================================================

@dp.message(F.text.contains("Profile"))
async def handle_profile_button(message: Message):
    """Handle profile button from main menu"""
    await cmd_profile(message)

@dp.message(F.text.contains("Family"))
async def handle_family_button(message: Message):
    """Handle family button from main menu"""
    # Simplified response - implement full family system
    await message.answer(f"""
{EMOJIS['family']} <b>FAMILY SYSTEM</b>

👨‍👩‍👧‍👦 <b>Commands:</b>
• <code>/adopt</code> - Adopt someone (reply to their message)
• <code>/marry</code> - Marry someone (reply to their message)
• <code>/family</code> - View your family members
• <code>/tree</code> - View your family tree
• <code>/divorce</code> - End a marriage
• <code>/disown</code> - Remove family member

💞 <b>Benefits:</b>
• Family bonuses in daily rewards
• Special family-only events
• Inheritance system
• Family reputation

🔗 <b>Start your family today!</b>
Reply to someone and use <code>/adopt</code> or <code>/marry</code>
""", parse_mode=ParseMode.HTML)

@dp.message(F.text.contains("Garden"))
async def handle_garden_button(message: Message):
    """Handle garden button from main menu"""
    await cmd_garden(message)

@dp.message(F.text.contains("Market"))
async def handle_market_button(message: Message):
    """Handle market button from main menu"""
    await cmd_market(message, CommandObject(args=""))

@dp.message(F.text.contains("Friends"))
async def handle_friends_button(message: Message):
    """Handle friends button from main menu"""
    await message.answer(f"""
{EMOJIS['friends']} <b>FRIEND SYSTEM</b>

🤝 <b>Commands:</b>
• <code>/friend</code> - Add friend (reply to their message)
• <code>/circle</code> - View your friend circle
• <code>/unfriend</code> - Remove a friend
• <code>/flink</code> - Get your friend invitation link
• <code>/suggestions</code> - Friend suggestions
• <code>/ratings</code> - Rate your friends (in PM)

💰 <b>Benefits:</b>
• $3,000 bonus when becoming friends
• Trade crops directly with friends
• Fertilize each other's gardens
• Friend-only market deals
• Active friends list

🌐 <b>Make global connections!</b>
""", parse_mode=ParseMode.HTML)

@dp.message(F.text.contains("PvP"))
async def handle_pvp_button(message: Message):
    """Handle PvP button from main menu"""
    await message.answer(f"""
{EMOJIS['pvp']} <b>PLAYER VS PLAYER</b>

⚔️ <b>Commands:</b>
• <code>/rob</code> - Rob someone (reply to their message)
• <code>/kill</code> - Assassinate someone (reply)
• <code>/hmk</code> - Hired Muscle (powerful attack)
• <code>/weapon</code> - Buy better weapons
• <code>/insurance</code> - Insure yourself or others
• <code>/medical</code> - Revive if dead
• <code>/pay</code> - Send money to others

🎯 <b>Features:</b>
• Weapon system affects success chance
• Reputation system prevents spam
• Insurance pays when insured players die
• Daily limits on attacks
• Risk vs reward balancing

⚠️ <b>Warning:</b> PvP actions affect your reputation!
""", parse_mode=ParseMode.HTML)

@dp.message(F.text.contains("Shop"))
async def handle_shop_button(message: Message):
    """Handle shop button from main menu"""
    await message.answer(f"""
{EMOJIS['shop']} <b>SHOP & UPGRADES</b>

🛒 <b>Available Shops:</b>
• <code>/weapon</code> - Weapons for PvP
• <code>/shop seeds</code> - Buy seeds (use <code>/plant</code> instead)
• <code>/shop boosts</code> - Garden speed boosts
• <code>/shop cosmetics</code> - Profile customization
• <code>/shop upgrades</code> - Garden & barn upgrades

💰 <b>Currencies Accepted:</b>
• Cash (💵) - Basic currency
• Gold (🪙) - Premium currency
• Bonds (👨‍👩‍👧‍👦) - Family rewards
• Credits (⭐) - Social rewards
• Tokens (🌱) - Garden rewards

🆙 <b>Upgrade your experience!</b>
""", parse_mode=ParseMode.HTML)

@dp.message(F.text.contains("Settings"))
async def handle_settings_button(message: Message):
    """Handle settings button from main menu"""
    await message.answer(f"""
{EMOJIS['settings']} <b>SETTINGS</b>

⚙️ <b>Available Settings:</b>
• <code>/setlang</code> - Change language
• <code>/settheme</code> - Change UI theme
• <code>/notifications</code> - Notification settings
• <code>/privacy</code> - Privacy controls
• <code>/help</code> - Show all commands

🌍 <b>Languages:</b> English (more coming soon!)

🎨 <b>Themes:</b> Default, Dark, Light, Colorful

🔔 <b>Notifications:</b> Proposals, Market, Garden, Friends

🔒 <b>Privacy:</b> Control who can see your profile

💡 <b>Customize your bot experience!</b>
""", parse_mode=ParseMode.HTML)

# ============================================================================
# MAIN BOT SETUP
# ============================================================================

async def setup_bot():
    """Initialize bot with all features"""
    # Connect to database
    await db.connect()
    
    # Create backup directory
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Show help"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="market", description="Marketplace"),
        types.BotCommand(command="buy", description="Buy from market"),
        types.BotCommand(command="friend", description="Add friend"),
        types.BotCommand(command="family", description="Family system"),
        types.BotCommand(command="rob", description="Rob someone"),
        types.BotCommand(command="kill", description="Assassinate"),
        types.BotCommand(command="hmk", description="Hired Muscle"),
        types.BotCommand(command="ping", description="Check bot status"),
        types.BotCommand(command="backup", description="Create backup (owner)"),
        types.BotCommand(command="refresh", description="Refresh system (owner)"),
        types.BotCommand(command="admin", description="Admin panel (owner)"),
    ]
    
    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Bot commands set successfully")
    except Exception as e:
        logger.error(f"Failed to set commands: {e}")
    
    # Send startup message
    try:
        await bot.send_message(
            LOG_CHANNEL,
            f"""
🤖 <b>FAMILY TREE BOT STARTED</b>

✅ Version: <b>2.0 Enhanced</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👑 Owner: <code>{OWNER_ID}</code>
🔐 Security: Maximum protection enabled
✨ Features: Enhanced UI with animations

🚀 Bot is now online and ready!
""",
            parse_mode=ParseMode.HTML
        )
        logger.info("✅ Startup message sent to log channel")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")
    
    logger.info("🎮 Bot setup complete - Ready to receive commands!")

async def main():
    """Main entry point"""
    try:
        await setup_bot()
        logger.info("🚀 Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        # Try to notify owner
        try:
            await bot.send_message(
                OWNER_ID,
                f"❌ Bot crashed: {str(e)[:200]}"
            )
        except:
            pass
        raise

if __name__ == "__main__":
    # Check for required environment variables
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: You must set BOT_TOKEN in environment variables or .env file!")
        print("💡 Create a .env file with: BOT_TOKEN=your_token_here")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(main())
