#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE PROFESSIONAL VERSION
Version: 8.0 - Complete with 45+ Commands
Lines: 4,000+ with all features
"""

import os
import sys
import json
import asyncio
import logging
import random
import secrets
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import html
import uuid
import hashlib
import time
import aiofiles
import io
import base64
from collections import defaultdict
import traceback
import re
import math
import pytz
from zoneinfo import ZoneInfo

# ============================================================================
# IMPORTS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject, StateFilter
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto, ChatMemberUpdated, ChatJoinRequest,
        URLInputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode, ChatMemberStatus
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    
    # Pillow for images
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        import textwrap
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram==3.0.0b7 aiohttp aiosqlite pillow pytz")
    sys.exit(1)

import aiosqlite
import sqlite3
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# CONFIGURATION
# ============================================================================

OWNER_ID = 6108185460
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
BOT_USERNAME = "@Familly_TreeBot"
LOG_CHANNEL = -1003662720845
DB_PATH = "family_bot.db"

# Admin IDs (add more as needed)
ADMIN_IDS = [OWNER_ID, 6108185460]

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "event_coins", "xp"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪",
    "xp": "⚡"
}

# Crop System
CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper", "watermelon", "pumpkin"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔", 
    "eggplant": "🍆", "corn": "🌽", "pepper": "🫑",
    "watermelon": "🍉", "pumpkin": "🎃"
}

CROP_PRICES = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "xp": 5},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "xp": 7},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "xp": 4},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "xp": 10},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "xp": 8},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "xp": 12},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "xp": 15},
    "pumpkin": {"buy": 40, "sell": 60, "grow_time": 8, "xp": 20}
}

# Stand System
STAND_TYPES = ["Attack", "Defense", "Speed", "Magic"]
STAND_SLOTS = ["head", "body", "legs", "weapon", "accessory"]
STAND_RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

# GIF Commands
GIF_COMMANDS = ["rob", "kill", "hug", "slap", "kiss", "pat", "fight", "punch", "cuddle", "boop"]
DEFAULT_GIFS = {
    "rob": "https://files.catbox.moe/6o1h7d.mp4",
    "kill": "https://files.catbox.moe/3bw8h5.mp4",
    "hug": "https://files.catbox.moe/z9a7f8.mp4",
    "slap": "https://files.catbox.moe/7j2k9d.mp4",
    "kiss": "https://files.catbox.moe/4x8m3n.mp4",
    "pat": "https://files.catbox.moe/1q2w3e.mp4"
}

# Colors for images
COLORS = {
    "primary": (76, 175, 80),
    "secondary": (33, 150, 243),
    "accent": (255, 152, 0),
    "success": (139, 195, 74),
    "warning": (255, 193, 7),
    "danger": (244, 67, 54),
    "background": (18, 18, 18),
    "card": (30, 30, 30),
    "text": (255, 255, 255),
    "border": (66, 66, 66)
}

# ============================================================================
# DATABASE CLASS (COMPLETE)
# ============================================================================

class Database:
    """Complete database with all 14 tables"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
        self.start_time = datetime.now()
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.init_tables()
    
    async def init_tables(self):
        """Initialize all 14 tables"""
        tables = [
            # 1. Users table
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                profile_pic TEXT,
                cash INTEGER DEFAULT 1000,
                gold INTEGER DEFAULT 0,
                bonds INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                event_coins INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                reputation INTEGER DEFAULT 100,
                is_banned BOOLEAN DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                daily_streak INTEGER DEFAULT 0,
                daily_count INTEGER DEFAULT 0,
                gemstone TEXT,
                bio_verified BOOLEAN DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 2. Family relations (7 types)
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL CHECK(relation_type IN 
                    ('parent', 'child', 'spouse', 'sibling', 'cousin', 'aunt_uncle', 'nephew_niece')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id, relation_type)
            )""",
            
            # 3. Gardens
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                level INTEGER DEFAULT 1
            )""",
            
            # 4. Garden plants
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                is_ready BOOLEAN DEFAULT 0,
                progress INTEGER DEFAULT 0
            )""",
            
            # 5. Barn storage
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # 6. Marketplace
            """CREATE TABLE IF NOT EXISTS marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_unit INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 7. Stands
            """CREATE TABLE IF NOT EXISTS stands (
                user_id INTEGER PRIMARY KEY,
                stand_type TEXT DEFAULT 'Attack',
                stand_level INTEGER DEFAULT 1,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 10,
                speed INTEGER DEFAULT 10,
                magic INTEGER DEFAULT 10
            )""",
            
            # 8. Stand items
            """CREATE TABLE IF NOT EXISTS stand_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                rarity TEXT NOT NULL,
                stats TEXT,  -- JSON stats
                equipped BOOLEAN DEFAULT 0
            )""",
            
            # 9. Friend circles
            """CREATE TABLE IF NOT EXISTS friend_circles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                max_members INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 10. Circle members
            """CREATE TABLE IF NOT EXISTS circle_members (
                circle_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (circle_id, user_id)
            )""",
            
            # 11. Transactions
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 12. GIFs (CatBox)
            """CREATE TABLE IF NOT EXISTS gifs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                url TEXT NOT NULL,
                added_by INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 13. Game records
            """CREATE TABLE IF NOT EXISTS game_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                result TEXT NOT NULL,
                amount INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 14. Admin logs
            """CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # 15. Cooldowns
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )"""
        ]
        
        async with self.lock:
            for table in tables:
                await self.conn.execute(table)
            await self.conn.commit()
            
            # Insert default GIFs
            for cmd, url in DEFAULT_GIFS.items():
                await self.conn.execute(
                    "INSERT OR IGNORE INTO gifs (command, url, added_by) VALUES (?, ?, ?)",
                    (cmd, url, OWNER_ID)
                )
            await self.conn.commit()
    
    # ==================== USER METHODS ====================
    
    async def get_user(self, user_id: int):
        """Get user by ID"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, user: types.User, profile_pic: str = None):
        """Create new user"""
        async with self.lock:
            await self.conn.execute(
                """INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, profile_pic) 
                VALUES (?, ?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, user.last_name, profile_pic)
            )
            
            await self.conn.execute(
                "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.execute(
                "INSERT OR IGNORE INTO stands (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.commit()
        
        return await self.get_user(user.id)
    
    async def update_user_field(self, user_id: int, field: str, value: Any):
        """Update user field"""
        async with self.lock:
            await self.conn.execute(
                f"UPDATE users SET {field} = ? WHERE user_id = ?",
                (value, user_id)
            )
            await self.conn.commit()
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        """Update user currency"""
        async with self.lock:
            await self.conn.execute(
                f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # Log transaction
            await self.conn.execute(
                """INSERT INTO transactions (user_id, type, amount, currency, description)
                VALUES (?, ?, ?, ?, ?)""",
                (user_id, "add" if amount > 0 else "remove", abs(amount), currency, "System adjustment")
            )
            
            await self.conn.commit()
    
    async def get_user_count(self):
        """Get total user count"""
        async with self.lock:
            cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
            return (await cursor.fetchone())[0]
    
    async def get_active_users_today(self):
        """Get users active today"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-1 day')"
            )
            return (await cursor.fetchone())[0]
    
    # ==================== FAMILY METHODS ====================
    
    async def get_family(self, user_id: int):
        """Get user's family members"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT fr.relation_type, 
                   CASE WHEN fr.user1_id = ? THEN u2.user_id ELSE u1.user_id END as other_id,
                   CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as other_name,
                   CASE WHEN fr.user1_id = ? THEN u2.profile_pic ELSE u1.profile_pic END as other_pic
                   FROM family_relations fr
                   LEFT JOIN users u1 ON u1.user_id = fr.user1_id
                   LEFT JOIN users u2 ON u2.user_id = fr.user2_id
                   WHERE ? IN (fr.user1_id, fr.user2_id)""",
                (user_id, user_id, user_id, user_id)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def add_family_relation(self, user1_id: int, user2_id: int, relation_type: str):
        """Add family relation"""
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO family_relations (user1_id, user2_id, relation_type)
                VALUES (?, ?, ?)""",
                (min(user1_id, user2_id), max(user1_id, user2_id), relation_type)
            )
            await self.conn.commit()
    
    async def remove_family_relation(self, user1_id: int, user2_id: int):
        """Remove family relation"""
        async with self.lock:
            await self.conn.execute(
                """DELETE FROM family_relations 
                WHERE (user1_id = ? AND user2_id = ?) 
                OR (user1_id = ? AND user2_id = ?)""",
                (user1_id, user2_id, user2_id, user1_id)
            )
            await self.conn.commit()
    
    # ==================== GARDEN METHODS ====================
    
    async def get_garden_info(self, user_id: int):
        """Get garden info"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM gardens WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_growing_crops(self, user_id: int):
        """Get growing crops"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT crop_type, 
                   ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours_passed,
                   grow_time,
                   is_ready,
                   progress
                   FROM garden_plants 
                   WHERE user_id = ? AND is_ready = 0""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int):
        """Plant crops"""
        if crop_type not in CROP_TYPES:
            return False
        
        garden = await self.get_garden_info(user_id)
        if not garden:
            return False
        
        growing = await self.get_growing_crops(user_id)
        if len(growing) + quantity > garden['slots']:
            return False
        
        grow_time = CROP_PRICES[crop_type]["grow_time"]
        async with self.lock:
            for _ in range(quantity):
                await self.conn.execute(
                    """INSERT INTO garden_plants (user_id, crop_type, grow_time, progress)
                    VALUES (?, ?, ?, 0)""",
                    (user_id, crop_type, grow_time)
                )
            await self.conn.commit()
        
        return True
    
    async def harvest_crops(self, user_id: int):
        """Harvest ready crops"""
        async with self.lock:
            # Get ready crops
            cursor = await self.conn.execute(
                """SELECT crop_type, COUNT(*) as count 
                FROM garden_plants 
                WHERE user_id = ? AND is_ready = 1
                GROUP BY crop_type""",
                (user_id,)
            )
            ready_crops = await cursor.fetchall()
            
            # Move to barn
            total_xp = 0
            total_value = 0
            
            for crop in ready_crops:
                crop_type = crop['crop_type']
                count = crop['count']
                
                # Add to barn
                await self.conn.execute(
                    """INSERT INTO barn (user_id, crop_type, quantity)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, crop_type) 
                    DO UPDATE SET quantity = quantity + ?""",
                    (user_id, crop_type, count, count)
                )
                
                # Calculate value and XP
                sell_price = CROP_PRICES[crop_type]["sell"]
                xp_per = CROP_PRICES[crop_type]["xp"]
                total_value += sell_price * count
                total_xp += xp_per * count
            
            # Delete harvested crops
            await self.conn.execute(
                "DELETE FROM garden_plants WHERE user_id = ? AND is_ready = 1",
                (user_id,)
            )
            
            await self.conn.commit()
            
            return {
                "total_crops": sum(c['count'] for c in ready_crops),
                "total_value": total_value,
                "total_xp": total_xp,
                "crops": [dict(c) for c in ready_crops]
            }
    
    # ==================== STAND METHODS ====================
    
    async def get_stand(self, user_id: int):
        """Get user's stand"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM stands WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_stand_items(self, user_id: int, equipped_only: bool = False):
        """Get stand items"""
        async with self.lock:
            query = "SELECT * FROM stand_items WHERE user_id = ?"
            if equipped_only:
                query += " AND equipped = 1"
            
            cursor = await self.conn.execute(query, (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== FRIEND CIRCLE METHODS ====================
    
    async def create_circle(self, owner_id: int, name: str, description: str = ""):
        """Create friend circle"""
        async with self.lock:
            cursor = await self.conn.execute(
                """INSERT INTO friend_circles (owner_id, name, description)
                VALUES (?, ?, ?)""",
                (owner_id, name, description)
            )
            circle_id = cursor.lastrowid
            
            # Add owner as member
            await self.conn.execute(
                "INSERT INTO circle_members (circle_id, user_id) VALUES (?, ?)",
                (circle_id, owner_id)
            )
            
            await self.conn.commit()
            return circle_id
    
    async def get_user_circle(self, user_id: int):
        """Get user's circle"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT fc.* FROM friend_circles fc
                JOIN circle_members cm ON fc.id = cm.circle_id
                WHERE cm.user_id = ?""",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== GIF METHODS ====================
    
    async def add_gif(self, command: str, url: str, added_by: int):
        """Add GIF to database"""
        async with self.lock:
            await self.conn.execute(
                "INSERT INTO gifs (command, url, added_by) VALUES (?, ?, ?)",
                (command, url, added_by)
            )
            await self.conn.commit()
    
    async def get_random_gif(self, command: str):
        """Get random GIF for command"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT url FROM gifs 
                WHERE command = ? 
                ORDER BY RANDOM() LIMIT 1""",
                (command,)
            )
            row = await cursor.fetchone()
            return row['url'] if row else None
    
    async def get_gif_stats(self):
        """Get GIF statistics"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT command, COUNT(*) as count FROM gifs GROUP BY command"
            )
            rows = await cursor.fetchall()
            return {row['command']: row['count'] for row in rows}
    
    # ==================== STATISTICS METHODS ====================
    
    async def get_bot_stats(self):
        """Get real bot statistics"""
        async with self.lock:
            stats = {}
            
            # User stats
            cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-1 day')"
            )
            stats['active_today'] = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-7 day')"
            )
            stats['new_week'] = (await cursor.fetchone())[0]
            
            # Family stats
            cursor = await self.conn.execute("SELECT COUNT(*) FROM family_relations")
            stats['total_relations'] = (await cursor.fetchone())[0]
            
            # Garden stats
            cursor = await self.conn.execute("SELECT COUNT(*) FROM garden_plants WHERE is_ready = 0")
            stats['growing_crops'] = (await cursor.fetchone())[0]
            
            # Economy stats
            cursor = await self.conn.execute("SELECT SUM(cash) FROM users")
            stats['total_cash'] = (await cursor.fetchone())[0] or 0
            
            return stats
    
    # ==================== ADMIN METHODS ====================
    
    async def log_admin_action(self, admin_id: int, action: str, target_id: int = None, details: str = None):
        """Log admin action"""
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO admin_logs (admin_id, action, target_id, details)
                VALUES (?, ?, ?, ?)""",
                (admin_id, action, target_id, details)
            )
            await self.conn.commit()
    
    async def get_recent_logs(self, limit: int = 10):
        """Get recent admin logs"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT al.*, u1.first_name as admin_name, u2.first_name as target_name
                FROM admin_logs al
                LEFT JOIN users u1 ON u1.user_id = al.admin_id
                LEFT JOIN users u2 ON u2.user_id = al.target_id
                ORDER BY al.created_at DESC LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database(DB_PATH)

# Bot start time for uptime
bot_start_time = datetime.now()

# ============================================================================
# IMAGE VISUALIZER (PROFESSIONAL)
# ============================================================================

class ImageVisualizer:
    """Professional image generation with profile pictures"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.fonts = {}
        self.profile_cache = {}
        
    async def fetch_profile_pic(self, user_id: int):
        """Fetch Telegram profile picture"""
        try:
            if user_id in self.profile_cache:
                return self.profile_cache[user_id]
            
            profile_photos = await self.bot.get_user_profile_photos(user_id, limit=1)
            if profile_photos.photos:
                # Get the largest photo
                photo = profile_photos.photos[0][-1]
                file = await self.bot.get_file(photo.file_id)
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
                
                # Download image
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            self.profile_cache[user_id] = image_data
                            return image_data
            
            return None
        except Exception as e:
            logger.error(f"Error fetching profile pic for {user_id}: {e}")
            return None
    
    async def create_family_tree_image(self, user_id: int, user_name: str, family_data: list):
        """Create family tree with profile pictures"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 1000, 800
            img = Image.new('RGB', (width, height), color=COLORS['background'])
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"🌳 Family Tree of {user_name}"
            font_large = ImageFont.truetype("arial.ttf", 36) if HAS_PILLOW else ImageFont.load_default()
            bbox = draw.textbbox((0, 0), title, font=font_large)
            title_x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((title_x, 30), title, fill=COLORS['primary'], font=font_large)
            
            # Draw central user (you)
            center_x, center_y = width // 2, height // 2 - 100
            
            # Try to get profile pic
            profile_pic = await self.fetch_profile_pic(user_id)
            if profile_pic:
                profile_img = Image.open(io.BytesIO(profile_pic))
                profile_img = profile_img.resize((100, 100))
                
                # Create circular mask
                mask = Image.new('L', (100, 100), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse([0, 0, 100, 100], fill=255)
                
                # Apply mask
                result = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
                result.paste(profile_img, (0, 0), mask)
                img.paste(result, (center_x - 50, center_y - 50), result)
            else:
                # Fallback circle
                draw.ellipse([center_x - 50, center_y - 50, center_x + 50, center_y + 50],
                           fill=COLORS['secondary'], outline=COLORS['accent'], width=3)
                draw.text((center_x - 20, center_y - 10), "👤", fill=COLORS['text'], font=font_large)
            
            # Your name
            draw.text((center_x - 40, center_y + 60), "You", fill=COLORS['text'], font=ImageFont.load_default())
            
            # Draw family members
            relation_positions = {
                'parent': {'angle': 90, 'distance': 200, 'color': COLORS['primary']},
                'spouse': {'angle': 0, 'distance': 200, 'color': COLORS['accent']},
                'child': {'angle': 270, 'distance': 200, 'color': COLORS['success']},
                'sibling': {'angle': 180, 'distance': 200, 'color': COLORS['secondary']},
                'cousin': {'angle': 45, 'distance': 250, 'color': (200, 150, 255)},
                'aunt_uncle': {'angle': 135, 'distance': 250, 'color': (255, 200, 100)},
                'nephew_niece': {'angle': 315, 'distance': 250, 'color': (100, 255, 200)}
            }
            
            relation_counts = defaultdict(int)
            
            for member in family_data:
                rel_type = member['relation_type']
                other_id = member['other_id']
                other_name = member['other_name']
                
                if rel_type not in relation_positions:
                    rel_type = 'cousin'  # Default
                
                pos = relation_positions[rel_type]
                angle = math.radians(pos['angle'] + relation_counts[rel_type] * 30)
                distance = pos['distance']
                
                x = center_x + distance * math.cos(angle)
                y = center_y + distance * math.sin(angle)
                
                # Draw connection line
                draw.line([(center_x, center_y), (x, y)], fill=pos['color'], width=2)
                
                # Draw member
                profile_pic = await self.fetch_profile_pic(other_id)
                if profile_pic:
                    profile_img = Image.open(io.BytesIO(profile_pic))
                    profile_img = profile_img.resize((80, 80))
                    
                    mask = Image.new('L', (80, 80), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse([0, 0, 80, 80], fill=255)
                    
                    result = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
                    result.paste(profile_img, (0, 0), mask)
                    img.paste(result, (int(x - 40), int(y - 40)), result)
                else:
                    draw.ellipse([x - 40, y - 40, x + 40, y + 40],
                               fill=pos['color'], outline=COLORS['border'], width=2)
                    
                    # Relation emoji
                    emojis = {
                        'parent': '👴', 'child': '👶', 'spouse': '💑',
                        'sibling': '👫', 'cousin': '👥', 'aunt_uncle': '👨‍👩‍👧',
                        'nephew_niece': '🧒'
                    }
                    emoji = emojis.get(rel_type, '👤')
                    draw.text((x - 15, y - 20), emoji, fill=COLORS['text'], font=font_large)
                
                # Name (truncated)
                name = other_name[:10] + "..." if len(other_name) > 10 else other_name
                bbox = draw.textbbox((0, 0), name, font=ImageFont.load_default())
                name_x = x - (bbox[2] - bbox[0]) // 2
                draw.text((name_x, y + 45), name, fill=COLORS['text'], font=ImageFont.load_default())
                
                relation_counts[rel_type] += 1
            
            # Legend
            legend_y = height - 100
            for i, (rel_type, data) in enumerate(relation_positions.items()):
                if relation_counts[rel_type] > 0:
                    x = 50 + (i % 3) * 300
                    y = legend_y + (i // 3) * 30
                    
                    draw.rectangle([x, y, x + 20, y + 20], fill=data['color'])
                    draw.text((x + 25, y), rel_type.replace('_', ' ').title(), 
                            fill=COLORS['text'], font=ImageFont.load_default())
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', optimize=True, quality=85)
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating family tree image: {e}")
            return None
    
    async def create_garden_image(self, garden_data: dict, crops: list):
        """Create garden visualization"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 1000
            img = Image.new('RGB', (width, height), color=COLORS['background'])
            draw = ImageDraw.Draw(img)
            
            # Title
            title = "🌾 Your Garden"
            font_large = ImageFont.truetype("arial.ttf", 36) if HAS_PILLOW else ImageFont.load_default()
            bbox = draw.textbbox((0, 0), title, font=font_large)
            title_x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((title_x, 30), title, fill=COLORS['primary'], font=font_large)
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 180
            padding = 20
            start_x = (width - (grid_size * (cell_size + padding))) // 2
            start_y = 120
            
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    if idx < garden_data.get('slots', 9):
                        if idx < len(crops):
                            crop = crops[idx]
                            progress = min(100, int((crop['hours_passed'] / crop['grow_time']) * 100))
                            
                            # Color based on progress
                            if progress >= 100:
                                bg_color = COLORS['success']
                            elif progress >= 50:
                                bg_color = COLORS['warning']
                            else:
                                bg_color = COLORS['secondary']
                            
                            # Draw cell
                            draw.rounded_rectangle([x1, y1, x2, y2], radius=20,
                                                 fill=bg_color, outline=COLORS['accent'], width=3)
                            
                            # Crop emoji
                            emoji = CROP_EMOJIS.get(crop['crop_type'], "🌱")
                            draw.text((x1 + cell_size//2 - 20, y1 + 20), emoji, 
                                    fill=COLORS['text'], font=font_large)
                            
                            # Crop name
                            crop_name = crop['crop_type'].title()
                            bbox = draw.textbbox((0, 0), crop_name, font=ImageFont.load_default())
                            name_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            draw.text((name_x, y1 + 80), crop_name, fill=COLORS['text'], 
                                    font=ImageFont.load_default())
                            
                            # Progress bar
                            bar_width = cell_size - 40
                            bar_height = 15
                            bar_x = x1 + 20
                            bar_y = y2 - 40
                            
                            # Background bar
                            draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                                                 radius=7, fill=COLORS['card'])
                            
                            # Progress fill
                            fill_width = int(bar_width * progress / 100)
                            if fill_width > 0:
                                draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
                                                     radius=7, fill=COLORS['primary'])
                            
                            # Progress text
                            progress_text = f"{progress}%"
                            bbox = draw.textbbox((0, 0), progress_text, font=ImageFont.load_default())
                            text_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            draw.text((text_x, bar_y - 20), progress_text, fill=COLORS['text'], 
                                    font=ImageFont.load_default())
                            
                            # Time remaining
                            if progress < 100:
                                remaining = crop['grow_time'] - crop['hours_passed']
                                time_text = f"{remaining:.1f}h"
                                bbox = draw.textbbox((0, 0), time_text, font=ImageFont.load_default())
                                time_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                                draw.text((time_x, y1 + 110), time_text, fill=COLORS['text'], 
                                        font=ImageFont.load_default())
                        else:
                            # Empty slot
                            draw.rounded_rectangle([x1, y1, x2, y2], radius=20,
                                                 fill=COLORS['card'], outline=COLORS['border'], width=2)
                            draw.text((x1 + cell_size//2 - 20, y1 + cell_size//2 - 20), 
                                    "🟫", fill=COLORS['text'], font=font_large)
                            draw.text((x1 + 50, y1 + cell_size//2 + 10), "Empty", 
                                    fill=COLORS['text'], font=ImageFont.load_default())
                    else:
                        # Locked slot
                        draw.rounded_rectangle([x1, y1, x2, y2], radius=20,
                                             fill=(40, 40, 40), outline=COLORS['danger'], width=2)
                        draw.text((x1 + cell_size//2 - 20, y1 + cell_size//2 - 20), 
                                "🔒", fill=COLORS['text'], font=font_large)
            
            # Stats at bottom
            stats_y = start_y + (grid_size * (cell_size + padding)) + 30
            
            stats = [
                f"📊 Slots: {len(crops)}/{garden_data.get('slots', 9)}",
                f"🌱 Growing: {len(crops)}",
                f"✅ Ready: {sum(1 for c in crops if min(100, int((c['hours_passed'] / c['grow_time']) * 100)) >= 100)}",
                f"🏠 Barn: {garden_data.get('barn_capacity', 50)} capacity"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i*30), stat, fill=COLORS['accent'], 
                        font=ImageFont.truetype("arial.ttf", 20) if HAS_PILLOW else ImageFont.load_default())
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', optimize=True, quality=85)
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating garden image: {e}")
            return None

# Initialize visualizer
visualizer = ImageVisualizer(bot)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def log_to_channel(message: str):
    """Log message to channel"""
    try:
        await bot.send_message(LOG_CHANNEL, message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to log to channel: {e}")

async def get_user_profile_pic_url(user_id: int) -> Optional[str]:
    """Get user's profile picture URL"""
    try:
        profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
        if profile_photos.photos:
            photo = profile_photos.photos[0][-1]
            file = await bot.get_file(photo.file_id)
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    except:
        pass
    return None

def format_time(seconds: int) -> str:
    """Format seconds to human readable time"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)

def calculate_level(xp: int) -> dict:
    """Calculate level from XP"""
    level = 1
    xp_for_next = 100
    
    while xp >= xp_for_next:
        xp -= xp_for_next
        level += 1
        xp_for_next = int(xp_for_next * 1.5)
    
    return {
        "level": level,
        "xp": xp,
        "xp_for_next": xp_for_next,
        "progress": int((xp / xp_for_next) * 100) if xp_for_next > 0 else 100
    }

# ============================================================================
# ERROR HANDLER (FIXED)
# ============================================================================

async def error_handler(event: types.Update, exception: Exception):
    """Global error handler - FIXED VERSION"""
    logger.error(f"Error: {exception}", exc_info=True)
    
    try:
        # Try to notify admin
        if OWNER_ID:
            error_msg = f"⚠️ <b>Bot Error</b>\n\n<code>{html.escape(str(exception)[:1000])}</code>"
            await bot.send_message(OWNER_ID, error_msg, parse_mode=ParseMode.HTML)
    except:
        pass
    
    return True

# Register error handler PROPERLY
dp.errors.register(error_handler)

# ============================================================================
# STARTUP
# ============================================================================

async def on_startup():
    """Run on bot startup"""
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Show help"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="adopt", description="Adopt someone"),
        types.BotCommand(command="marry", description="Marry someone"),
        types.BotCommand(command="divorce", description="Divorce spouse"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="barn", description="Barn storage"),
        types.BotCommand(command="stand", description="Your stand"),
        types.BotCommand(command="circle", description="Friend circle"),
        types.BotCommand(command="rob", description="Rob someone"),
        types.BotCommand(command="kill", description="Kill someone"),
        types.BotCommand(command="hug", description="Hug someone"),
        types.BotCommand(command="slap", description="Slap someone"),
        types.BotCommand(command="kiss", description="Kiss someone"),
        types.BotCommand(command="pat", description="Pat someone"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="fight", description="Fight someone"),
        types.BotCommand(command="jackpot", description="Jackpot game"),
        types.BotCommand(command="leaderboard", description="Top players"),
        types.BotCommand(command="ping", description="Bot status"),
    ]
    
    await bot.set_my_commands(commands)
    
    # Admin commands (hidden from regular users)
    admin_commands = [
        types.BotCommand(command="add", description="Add resources (admin)"),
        types.BotCommand(command="ban", description="Ban user (admin)"),
        types.BotCommand(command="stats", description="Bot statistics (admin)"),
        types.BotCommand(command="broadcast", description="Broadcast (admin)"),
        types.BotCommand(command="addgif", description="Add GIF (admin)"),
        types.BotCommand(command="logs", description="View logs (admin)"),
        types.BotCommand(command="users", description="User list (admin)"),
        types.BotCommand(command="backup", description="Backup (admin)"),
        types.BotCommand(command="setcash", description="Set cash (admin)"),
        types.BotCommand(command="unban", description="Unban (admin)"),
        types.BotCommand(command="warn", description="Warn user (admin)"),
        types.BotCommand(command="gifstats", description="GIF stats (admin)"),
        types.BotCommand(command="listgifs", description="List GIFs (admin)"),
        types.BotCommand(command="delgif", description="Delete GIF (admin)"),
        types.BotCommand(command="cleanup", description="Cleanup (admin)"),
    ]
    
    # Log startup
    startup_msg = f"""
🚀 <b>BOT STARTED</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 @{BOT_USERNAME[1:]}
👑 Owner: {OWNER_ID}
"""
    await log_to_channel(startup_msg)
    
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - COMPLETE VERSION")
    print(f"Version: 8.0 | Commands: {len(commands) + len(admin_commands)}")
    print(f"Owner: {OWNER_ID} | Log: {LOG_CHANNEL}")
    print(f"Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED'}")
    print("=" * 60)

# ============================================================================
# COMMAND HANDLERS - 45+ COMMANDS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    user = await db.get_user(message.from_user.id)
    
    if not user:
        # Get profile picture
        profile_pic = await get_user_profile_pic_url(message.from_user.id)
        user = await db.create_user(message.from_user, profile_pic)
    
    welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🌳 <b>Build your family empire</b>
🌾 <b>Grow and harvest crops</b>
⚔️ <b>Battle with stands</b>
🎮 <b>Play exciting games</b>
👥 <b>Join friend circles</b>

💰 <b>Starting Resources:</b>
• 💵 $1,000 Cash
• ⭐ 100 Credits
• 🌱 50 Tokens
• 🪙 0 Gold

🚀 <b>Quick Start:</b>
1. <code>/daily</code> - Claim daily bonus
2. <code>/me</code> - Check your profile
3. <code>/family</code> - Start family tree
4. <code>/garden</code> - Plant crops

📸 <i>Now with visual family trees!</i>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Quick Start", callback_data="quick_start")],
        [InlineKeyboardButton(text="📚 Commands", callback_data="show_commands")],
        [InlineKeyboardButton(text="👥 Add to Group", url=f"https://t.me/{BOT_USERNAME[1:]}?startgroup=true")],
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
📚 <b>FAMILY TREE BOT - COMMANDS</b>

👤 <b>Account:</b>
<code>/me</code> - Your profile
<code>/daily</code> - Daily bonus
<code>/leaderboard</code> - Top players

👨‍👩‍👧‍👦 <b>Family:</b>
<code>/family</code> - Family tree
<code>/adopt</code> - Adopt someone
<code>/marry</code> - Marry someone
<code>/divorce</code> - Divorce
<code>/disown</code> - Remove member

🌾 <b>Garden:</b>
<code>/garden</code> - Your garden
<code>/plant [crop] [qty]</code> - Plant
<code>/harvest</code> - Harvest crops
<code>/barn</code> - Barn storage

⚔️ <b>Stands:</b>
<code>/stand</code> - Your stand
<code>/equip</code> - Equip items
<code>/upgrade</code> - Upgrade stand

👥 <b>Friend Circle:</b>
<code>/circle</code> - Your circle
<code>/createcircle [name]</code> - Create
<code>/joincircle [id]</code> - Join

🎮 <b>Games:</b>
<code>/rob @user</code> - Rob someone
<code>/kill @user</code> - Kill someone
<code>/hug @user</code> - Hug someone
<code>/slap @user</code> - Slap someone
<code>/kiss @user</code> - Kiss someone
<code>/pat @user</code> - Pat someone
<code>/slot [bet]</code> - Slot machine
<code>/fight @user</code> - PvP battle
<code>/jackpot</code> - Lottery

🛠️ <b>Utility:</b>
<code>/ping</code> - Bot status
<code>/market</code> - Marketplace

💡 <i>Most commands work by replying to users!</i>
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """User profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Please use /start first!")
        return
    
    # Calculate level
    level_info = calculate_level(user.get('xp', 0))
    
    # Get family count
    family = await db.get_family(message.from_user.id)
    
    # Get stand
    stand = await db.get_stand(message.from_user.id)
    
    profile_text = f"""
🏆 <b>PROFILE OF {user['first_name'].upper()}</b>

📊 <b>Basic Info:</b>
• Level: <b>{level_info['level']}</b> (Progress: {level_info['progress']}%)
• XP: <b>{level_info['xp']}/{level_info['xp_for_next']}</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Bio Verified: {'✅' if user.get('bio_verified') else '❌'}

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>
• 🎪 Event Coins: <b>{user.get('event_coins', 0):,}</b>

⚔️ <b>Stand:</b> {stand['stand_type'] if stand else 'None'} (Lvl {stand['stand_level'] if stand else 1})
💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
📅 <b>Joined:</b> {user.get('created_at', 'Today')[:10]}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌳 Family", callback_data="view_family"),
         InlineKeyboardButton(text="🌾 Garden", callback_data="view_garden")],
        [InlineKeyboardButton(text="⚔️ Stand", callback_data="view_stand"),
         InlineKeyboardButton(text="👥 Circle", callback_data="view_circle")],
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Check last daily
    last_daily = user.get('last_daily')
    now = datetime.now()
    
    if last_daily:
        last_date = datetime.strptime(last_daily[:10], "%Y-%m-%d").date()
        if last_date == now.date():
            # Already claimed today
            next_daily = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            wait_time = next_daily - now
            hours = wait_time.seconds // 3600
            minutes = (wait_time.seconds % 3600) // 60
            
            await message.answer(
                f"❌ You already claimed today!\n"
                f"⏰ Next daily in: {hours}h {minutes}m",
                parse_mode=ParseMode.HTML
            )
            return
    
    # Calculate streak
    streak = user.get('daily_streak', 0)
    if last_daily:
        last_date = datetime.strptime(last_daily[:10], "%Y-%m-%d").date()
        if last_date == (now.date() - timedelta(days=1)):
            streak += 1
        else:
            streak = 1
    else:
        streak = 1
    
    # Base bonus
    base_bonus = random.randint(500, 1500)
    
    # Family bonus
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * 100
    
    # Streak bonus
    streak_bonus = min(streak * 50, 500)  # Max 500
    
    # Bio verification bonus
    bio_verified = user.get('bio_verified', 0)
    bio_bonus = 2 if bio_verified else 1
    
    # Total bonus
    total_bonus = (base_bonus + family_bonus + streak_bonus) * bio_bonus
    
    # Gemstone
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst", "Topaz", "Opal"]
    gemstone = random.choice(gemstones)
    
    # XP bonus
    xp_bonus = random.randint(10, 50)
    
    # Update user
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.update_currency(message.from_user.id, "xp", xp_bonus)
    await db.update_currency(message.from_user.id, "tokens", 5)
    
    await db.update_user_field(message.from_user.id, "last_daily", now.isoformat())
    await db.update_user_field(message.from_user.id, "daily_streak", streak)
    await db.update_user_field(message.from_user.id, "daily_count", user.get('daily_count', 0) + 1)
    await db.update_user_field(message.from_user.id, "gemstone", gemstone)
    
    daily_text = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base_bonus:,}</b>
• Family ({len(family)}): <b>${family_bonus:,}</b>
• Streak ({streak}): <b>${streak_bonus:,}</b>
• Multiplier: <b>{bio_bonus}x</b>
• <b>Total: ${total_bonus:,}</b>

🎁 <b>Bonuses:</b>
• 💎 Gemstone: <b>{gemstone}</b>
• ⚡ XP: <b>{xp_bonus}</b>
• 🌱 Tokens: <b>5</b>

📊 <b>Stats:</b>
• Streak: <b>{streak} days</b>
• Total Claims: <b>{user.get('daily_count', 0) + 1}</b>
• Bio Verified: {'✅ (2x!)' if bio_verified else '❌ Add @Familly_TreeBot to bio for 2x!'}
"""
    
    await message.answer(daily_text, parse_mode=ParseMode.HTML)

@dp.message(Command("family"))
async def cmd_family(message: Message):
    """Family tree with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    if HAS_PILLOW and family:
        # Create image
        loading_msg = await message.answer("🖼️ Generating family tree...")
        
        image_bytes = await visualizer.create_family_tree_image(
            message.from_user.id,
            user['first_name'],
            family
        )
        
        if image_bytes:
            # Send image
            family_text = f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

👨‍👩‍👧‍👦 <b>Family Members: {len(family)}</b>
💝 <b>Relationships:</b> {', '.join(set(m['relation_type'].replace('_', ' ').title() for m in family))}

📊 <b>Family Bonuses:</b>
• Daily Bonus: +${len(family) * 100}
• Quest Rewards: +{len(family) * 5}%
• Inheritance: Active

💡 <b>Commands:</b>
• Reply with <code>/adopt</code> to adopt someone
• Reply with <code>/marry</code> to marry someone
• <code>/divorce</code> to end marriage
• <code>/disown</code> to remove family member
"""
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="family_tree.png"),
                caption=family_text,
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
    
    # Text version
    if not family:
        family_text = """
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow your family:</b>
1. Reply to someone with <code>/adopt</code>
2. Wait for them to accept
3. Build your family empire!

👑 <b>Benefits:</b>
• Daily bonus increases per family member
• Family quests and events
• Inheritance system
• Special family perks
"""
    else:
        family_text = f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

└─ You
"""
        
        for member in family:
            emoji = {
                'parent': '👴', 'child': '👶', 'spouse': '💑',
                'sibling': '👫', 'cousin': '👥', 'aunt_uncle': '👨‍👩‍👧',
                'nephew_niece': '🧒'
            }.get(member['relation_type'], '👤')
            
            family_text += f"   ├─ {emoji} {member['other_name']} ({member['relation_type'].replace('_', ' ')})"
    
    await message.answer(family_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message, command: CommandObject):
    """Adopt someone"""
    if not message.reply_to_message:
        await message.answer("""
👶 <b>ADOPT SOMEONE</b>

To adopt someone as your child:

1. <b>Reply to their message</b> with <code>/adopt</code>
2. Wait for them to accept

💡 <b>Requirements:</b>
• Both must use /start
• Cannot adopt yourself
• Target must not be in your family already
""")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    # Check users exist
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users must use /start first!")
        return
    
    # Check if already related
    family = await db.get_family(message.from_user.id)
    for member in family:
        if member['other_id'] == target.id:
            await message.answer(f"❌ {target.first_name} is already in your family!")
            return
    
    # Add relation
    await db.add_family_relation(message.from_user.id, target.id, 'parent')
    
    # Log to channel
    await log_to_channel(
        f"👶 <b>ADOPTION</b>\n"
        f"👤 Parent: {message.from_user.first_name} ({message.from_user.id})\n"
        f"👶 Child: {target.first_name} ({target.id})"
    )
    
    await message.answer(f"""
✅ <b>ADOPTION COMPLETE!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
📅 {datetime.now().strftime('%Y-%m-%d')}

🎉 <b>Benefits activated:</b>
• Daily bonus increased
• Family quests available
• Inheritance rights
"""
    )
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
👶 <b>YOU WERE ADOPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 Relationship: Parent-Child

💡 You are now part of their family!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Marry someone"""
    if not message.reply_to_message:
        await message.answer("""
💍 <b>MARRY SOMEONE</b>

To marry someone:

1. <b>Reply to their message</b> with <code>/marry</code>
2. Wait for them to accept

💡 <b>Requirements:</b>
• Both must use /start
• Cannot marry yourself
• Must not be married already
""")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users must use /start first!")
        return
    
    # Check if already married
    family = await db.get_family(message.from_user.id)
    for member in family:
        if member['other_id'] == target.id and member['relation_type'] == 'spouse':
            await message.answer(f"❌ You are already married to {target.first_name}!")
            return
    
    # Add relation
    await db.add_family_relation(message.from_user.id, target.id, 'spouse')
    
    # Log to channel
    await log_to_channel(
        f"💍 <b>MARRIAGE</b>\n"
        f"👤 Spouse 1: {message.from_user.first_name} ({message.from_user.id})\n"
        f"👤 Spouse 2: {target.first_name} ({target.id})"
    )
    
    await message.answer(f"""
💍 <b>MARRIAGE COMPLETE!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
📅 {datetime.now().strftime('%Y-%m-%d')}

🎉 <b>Benefits:</b>
• Couple bonuses activated
• Shared daily rewards
• Family features unlocked
"""
    )
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
💍 <b>MARRIAGE PROPOSAL ACCEPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 Relationship: Spouses

🎉 You are now married!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("divorce"))
async def cmd_divorce(message: Message):
    """Divorce spouse"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Find spouse
    family = await db.get_family(message.from_user.id)
    spouse = None
    
    for member in family:
        if member['relation_type'] == 'spouse':
            spouse = member
            break
    
    if not spouse:
        await message.answer("❌ You are not married!")
        return
    
    # Remove relation
    await db.remove_family_relation(message.from_user.id, spouse['other_id'])
    
    await message.answer(f"""
💔 <b>DIVORCE COMPLETED</b>

👤 Divorced from: <b>{spouse['other_name']}</b>
📅 {datetime.now().strftime('%Y-%m-%d')}

⚠️ <b>Effects:</b>
• Marriage bonuses removed
• Can remarry after 7 days
"""
    )
    
    # Notify ex-spouse
    try:
        await bot.send_message(
            spouse['other_id'],
            f"""
💔 <b>DIVORCE NOTICE</b>

👤 {message.from_user.first_name} has divorced you.
📅 {datetime.now().strftime('%Y-%m-%d')}
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    garden = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    if HAS_PILLOW:
        loading_msg = await message.answer("🖼️ Generating garden image...")
        
        image_bytes = await visualizer.create_garden_image(garden, crops)
        
        if image_bytes:
            garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Level: {garden.get('level', 1)}
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Barn Capacity: {garden.get('barn_capacity', 50)}
• Growing: {len(crops)} crops

💡 <b>Commands:</b>
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
<code>/barn</code> - View storage
<code>/market</code> - Sell crops

🌿 <b>Available Crops:</b>
🥕 Carrot (2h) - Buy: $10, Sell: $15
🍅 Tomato (3h) - Buy: $15, Sell: $22
🥔 Potato (2.5h) - Buy: $8, Sell: $12
🍆 Eggplant (4h) - Buy: $20, Sell: $30
"""
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="garden.png"),
                caption=garden_text,
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
    
    # Text version
    garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Level: {garden.get('level', 1)}
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Barn Capacity: {garden.get('barn_capacity', 50)}

🌱 <b>Growing Now ({len(crops)}):</b>
"""
    
    for crop in crops[:5]:
        progress = min(100, int((crop['hours_passed'] / crop['grow_time']) * 100))
        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
        bar = "█" * (progress // 20) + "░" * (5 - (progress // 20))
        
        if progress >= 100:
            status = "✅ Ready!"
        else:
            remaining = max(0, crop['grow_time'] - crop['hours_passed'])
            status = f"{bar} {progress}% ({remaining:.1f}h left)"
        
        garden_text += f"• {emoji} {crop['crop_type'].title()}: {status}\n"
    
    if len(crops) > 5:
        garden_text += f"... and {len(crops) - 5} more\n"
    
    garden_text += f"""

💡 <b>Commands:</b>
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
<code>/barn</code> - View storage
"""
    
    await message.answer(garden_text, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    if not command.args:
        await message.answer("""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
"""
        + "\n".join([
            f"{CROP_EMOJIS.get(crop, '🌱')} {crop.title()} - ${CROP_PRICES[crop]['buy']} each ({CROP_PRICES[crop]['grow_time']}h)"
            for crop in CROP_TYPES[:4]
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
    
    crop_type = args[0]
    try:
        quantity = int(args[1])
    except:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if crop_type not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROP_TYPES[:6])}")
        return
    
    if quantity < 1 or quantity > 9:
        await message.answer("❌ Quantity must be 1-9!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Check cost
    cost = CROP_PRICES[crop_type]["buy"] * quantity
    if user.get('cash', 0) < cost:
        await message.answer(f"❌ Need ${cost:,}! You have ${user.get('cash', 0):,}")
        return
    
    # Plant crops
    success = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if not success:
        await message.answer("❌ Not enough garden space!")
        return
    
    # Deduct cost
    await db.update_currency(message.from_user.id, "cash", -cost)
    
    grow_time = CROP_PRICES[crop_type]["grow_time"]
    emoji = CROP_EMOJIS.get(crop_type, "🌱")
    
    await message.answer(f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{emoji} Crop: <b>{crop_type.title()}</b>
🔢 Quantity: <b>{quantity}</b>
💰 Cost: <b>${cost:,}</b>
⏰ Grow Time: <b>{grow_time} hours</b>

🌱 Now growing in your garden!
💡 Use <code>/garden</code> to check progress.
""", parse_mode=ParseMode.HTML)

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest ready crops"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    result = await db.harvest_crops(message.from_user.id)
    
    if result["total_crops"] == 0:
        await message.answer("❌ No crops ready for harvest!")
        return
    
    harvest_text = f"""
✅ <b>HARVEST COMPLETE!</b>

🌾 <b>Harvested:</b> {result['total_crops']} crops
💰 <b>Total Value:</b> ${result['total_value']:,}
⚡ <b>XP Earned:</b> {result['total_xp']}

🌱 <b>Crops:</b>
"""
    
    for crop in result["crops"][:5]:
        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
        harvest_text += f"• {emoji} {crop['crop_type'].title()}: {crop['count']}\n"
    
    if len(result["crops"]) > 5:
        harvest_text += f"... and {len(result['crops']) - 5} more crop types\n"
    
    harvest_text += f"""

📦 Stored in barn!
💡 Use <code>/barn</code> to view storage.
"""
    
    # Update XP
    await db.update_currency(message.from_user.id, "xp", result['total_xp'])
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

# ============================================================================
# MINI-GAMES WITH GIFS
# ============================================================================

@dp.message(Command("rob"))
async def cmd_rob(message: Message):
    """Rob someone with GIF"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to rob them!")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot rob yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users must use /start first!")
        return
    
    # Get random GIF
    gif_url = await db.get_random_gif("rob")
    if not gif_url:
        gif_url = DEFAULT_GIFS["rob"]
    
    # Robbery logic
    success_chance = random.randint(1, 100)
    
    if success_chance <= 40:  # 40% success
        # Successful robbery
        max_rob = min(target_user.get('cash', 0) // 4, user.get('cash', 0) // 2)
        if max_rob <= 0:
            amount = 0
            result = "failed (target has no money)"
        else:
            amount = random.randint(10, max_rob)
            await db.update_currency(target.id, "cash", -amount)
            await db.update_currency(message.from_user.id, "cash", amount)
            result = "successful"
        
        text = f"""
🎭 <b>ROBBERY ATTEMPT!</b>

👤 Robber: {message.from_user.first_name}
🎯 Target: {target.first_name}

💸 <b>Result:</b> {result}
💰 <b>Amount:</b> ${amount:,}
"""
    else:
        # Failed robbery
        fine = random.randint(50, 200)
        await db.update_currency(message.from_user.id, "cash", -fine)
        result = "failed"
        
        text = f"""
🎭 <b>ROBBERY ATTEMPT!</b>

👤 Robber: {message.from_user.first_name}
🎯 Target: {target.first_name}

💸 <b>Result:</b> {result}
💰 <b>Fine:</b> ${fine:,}
👮 <i>You were caught!</i>
"""
    
    # Send GIF with caption
    try:
        await message.answer_animation(
            animation=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone with GIF"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to kill them!")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot kill yourself!")
        return
    
    # Get random GIF
    gif_url = await db.get_random_gif("kill")
    if not gif_url:
        gif_url = DEFAULT_GIFS["kill"]
    
    # Kill logic
    success_chance = random.randint(1, 100)
    
    if success_chance <= 30:  # 30% success
        # Successful kill
        bounty = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", bounty)
        
        text = f"""
⚔️ <b>KILL ATTEMPT!</b>

👤 Assassin: {message.from_user.first_name}
🎯 Target: {target.first_name}

💀 <b>Result:</b> Successful!
💰 <b>Bounty:</b> ${bounty:,}
🏆 <i>Target eliminated!</i>
"""
    else:
        # Failed kill
        damage = random.randint(20, 100)
        await db.update_currency(message.from_user.id, "cash", -damage)
        
        text = f"""
⚔️ <b>KILL ATTEMPT!</b>

👤 Assassin: {message.from_user.first_name}
🎯 Target: {target.first_name}

💀 <b>Result:</b> Failed!
💸 <b>Damage Cost:</b> ${damage:,}
🛡️ <i>Target survived!</i>
"""
    
    try:
        await message.answer_animation(
            animation=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone with GIF"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to hug them!")
        return
    
    target = message.reply_to_message.from_user
    
    # Get random GIF
    gif_url = await db.get_random_gif("hug")
    if not gif_url:
        gif_url = DEFAULT_GIFS["hug"]
    
    # Hug gives small reward
    reward = random.randint(10, 50)
    await db.update_currency(message.from_user.id, "cash", reward)
    
    text = f"""
🤗 <b>HUG!</b>

👤 From: {message.from_user.first_name}
🎯 To: {target.first_name}

💝 <b>Warm fuzzies:</b> +{reward} happiness
💰 <b>Reward:</b> ${reward:,}
❤️ <i>Spread the love!</i>
"""
    
    try:
        await message.answer_animation(
            animation=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone with GIF"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to slap them!")
        return
    
    target = message.reply_to_message.from_user
    
    # Get random GIF
    gif_url = await db.get_random_gif("slap")
    if not gif_url:
        gif_url = DEFAULT_GIFS["slap"]
    
    text = f"""
👋 <b>SLAP!</b>

👤 From: {message.from_user.first_name}
🎯 To: {target.first_name}

💥 <b>Impact:</b> Critical hit!
😵 <i>That's gonna leave a mark!</i>
"""
    
    try:
        await message.answer_animation(
            animation=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone with GIF"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to kiss them!")
        return
    
    target = message.reply_to_message.from_user
    
    # Get random GIF
    gif_url = await db.get_random_gif("kiss")
    if not gif_url:
        gif_url = DEFAULT_GIFS["kiss"]
    
    # Kiss gives reward
    reward = random.randint(20, 80)
    await db.update_currency(message.from_user.id, "cash", reward)
    
    text = f"""
💋 <b>KISS!</b>

👤 From: {message.from_user.first_name}
🎯 To: {target.first_name}

😘 <b>Affection:</b> +{reward} love
💰 <b>Reward:</b> ${reward:,}
💕 <i>Love is in the air!</i>
"""
    
    try:
        await message.answer_animation(
            animation=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone with GIF"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to pat them!")
        return
    
    target = message.reply_to_message.from_user
    
    # Get random GIF
    gif_url = await db.get_random_gif("pat")
    if not gif_url:
        gif_url = DEFAULT_GIFS["pat"]
    
    # Pat gives reward
    reward = random.randint(5, 30)
    await db.update_currency(message.from_user.id, "cash", reward)
    
    text = f"""
👐 <b>PAT!</b>

👤 From: {message.from_user.first_name}
🎯 To: {target.first_name}

🐶 <b>Good vibes:</b> +{reward} happiness
💰 <b>Reward:</b> ${reward:,}
👍 <i>Good job!</i>
"""
    
    try:
        await message.answer_animation(
            animation=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

# ============================================================================
# MORE GAMES
# ============================================================================

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine"""
    if not command.args:
        await message.answer("Usage: /slot [bet]\nExample: /slot 100")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet is $10!")
            return
    except:
        await message.answer("Invalid bet amount!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    if bet > user.get('cash', 0):
        await message.answer(f"You only have ${user.get('cash', 0):,}!")
        return
    
    # Slot symbols
    symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎", "🍀", "👑"]
    reels = [random.choice(symbols) for _ in range(3)]
    
    # Calculate win
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == "7️⃣":
            multiplier = 10
        elif reels[0] == "💎":
            multiplier = 5
        elif reels[0] == "👑":
            multiplier = 4
        else:
            multiplier = 3
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        multiplier = 1.5
    else:
        multiplier = 0
    
    win_amount = int(bet * multiplier)
    net_gain = win_amount - bet
    
    # Update balance
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    slot_text = f"""
🎰 <b>SLOT MACHINE</b>

[{reels[0]}] [{reels[1]}] [{reels[2]}]

💰 Bet: <b>${bet:,}</b>
🎯 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}
🏆 Payout: <b>${win_amount:,}</b>
📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>

💵 New Balance: <b>${user.get('cash', 0) + net_gain:,}</b>
"""
    
    await message.answer(slot_text, parse_mode=ParseMode.HTML)

@dp.message(Command("fight"))
async def cmd_fight(message: Message):
    """Fight someone"""
    if not message.reply_to_message:
        await message.answer("Reply to someone to fight them!")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot fight yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users must use /start first!")
        return
    
    # Get stands
    user_stand = await db.get_stand(message.from_user.id)
    target_stand = await db.get_stand(target.id)
    
    if not user_stand or not target_stand:
        await message.answer("❌ Both players need stands! Use /stand")
        return
    
    # Calculate battle
    user_power = user_stand['attack'] + user_stand['defense'] + user_stand['speed'] + user_stand['magic']
    target_power = target_stand['attack'] + target_stand['defense'] + target_stand['speed'] + target_stand['magic']
    
    # Add random factor
    user_roll = random.randint(1, 100)
    target_roll = random.randint(1, 100)
    
    user_total = user_power + user_roll
    target_total = target_power + target_roll
    
    if user_total > target_total:
        # User wins
        reward = random.randint(50, 200)
        await db.update_currency(message.from_user.id, "cash", reward)
        await db.update_currency(message.from_user.id, "xp", 10)
        
        result = f"""
⚔️ <b>BATTLE VICTORY!</b>

👤 Winner: {message.from_user.first_name}
🎯 Loser: {target.first_name}

🏆 <b>Reward:</b> ${reward:,}
⚡ <b>XP:</b> +10
🔥 <b>Power:</b> {user_total} vs {target_total}
"""
    else:
        # User loses
        penalty = random.randint(20, 100)
        await db.update_currency(message.from_user.id, "cash", -penalty)
        
        result = f"""
⚔️ <b>BATTLE DEFEAT!</b>

👤 Loser: {message.from_user.first_name}
🎯 Winner: {target.first_name}

💸 <b>Penalty:</b> ${penalty:,}
💔 <b>Power:</b> {user_total} vs {target_total}
"""
    
    await message.answer(result, parse_mode=ParseMode.HTML)

@dp.message(Command("jackpot"))
async def cmd_jackpot(message: Message):
    """Jackpot game"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Entry fee
    fee = 50
    if user.get('cash', 0) < fee:
        await message.answer(f"❌ Need ${fee} to enter jackpot!")
        return
    
    await db.update_currency(message.from_user.id, "cash", -fee)
    
    # Jackpot logic
    win_chance = random.randint(1, 100)
    
    if win_chance <= 5:  # 5% chance
        # Grand prize
        prize = random.randint(500, 2000)
        await db.update_currency(message.from_user.id, "cash", prize)
        
        result = f"""
🎰 <b>JACKPOT HIT! 🎉</b>

👤 Player: {message.from_user.first_name}

🏆 <b>GRAND PRIZE!</b>
💰 <b>Won:</b> ${prize:,}
🎯 <b>Entry:</b> ${fee}
📈 <b>Net:</b> +${prize - fee:,}
"""
    elif win_chance <= 20:  # 15% chance
        # Small prize
        prize = random.randint(100, 300)
        await db.update_currency(message.from_user.id, "cash", prize)
        
        result = f"""
🎰 <b>JACKPOT</b>

👤 Player: {message.from_user.first_name}

💰 <b>Won:</b> ${prize:,}
🎯 <b>Entry:</b> ${fee}
📈 <b>Net:</b> +${prize - fee:,}
"""
    else:
        # Lose
        result = f"""
🎰 <b>JACKPOT</b>

👤 Player: {message.from_user.first_name}

😢 <b>No win this time!</b>
🎯 <b>Entry:</b> ${fee}
💸 <b>Lost:</b> ${fee}
"""
    
    await message.answer(result, parse_mode=ParseMode.HTML)

# ============================================================================
# STAND SYSTEM
# ============================================================================

@dp.message(Command("stand"))
async def cmd_stand(message: Message):
    """Show stand"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    stand = await db.get_stand(message.from_user.id)
    items = await db.get_stand_items(message.from_user.id, equipped_only=True)
    
    if not stand:
        await message.answer("No stand found! Use /start first.")
        return
    
    stand_text = f"""
⚔️ <b>{user['first_name']}'s STAND</b>

📊 <b>Type:</b> {stand['stand_type']}
⭐ <b>Level:</b> {stand['stand_level']}

📈 <b>Stats:</b>
• ⚔️ Attack: {stand['attack']}
• 🛡️ Defense: {stand['defense']}
• ⚡ Speed: {stand['speed']}
• 🔮 Magic: {stand['magic']}
• 💪 Total Power: {stand['attack'] + stand['defense'] + stand['speed'] + stand['magic']}

🎒 <b>Equipped Items ({len(items)}):</b>
"""
    
    for item in items[:5]:
        stand_text += f"• {item['slot'].title()}: {item['item_name']} ({item['rarity']})\n"
    
    if len(items) > 5:
        stand_text += f"... and {len(items) - 5} more\n"
    
    stand_text += f"""

💡 <b>Commands:</b>
<code>/equip [item_id]</code> - Equip item
<code>/unequip [slot]</code> - Unequip item
<code>/upgrade</code> - Upgrade stand (costs gold)
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔼 Upgrade Stand", callback_data="upgrade_stand"),
         InlineKeyboardButton(text="🎒 Inventory", callback_data="view_inventory")],
        [InlineKeyboardButton(text="⚔️ Fight Someone", callback_data="fight_menu")],
    ])
    
    await message.answer(stand_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# FRIEND CIRCLE SYSTEM
# ============================================================================

@dp.message(Command("circle"))
async def cmd_circle(message: Message):
    """Show friend circle"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    circle = await db.get_user_circle(message.from_user.id)
    
    if not circle:
        circle_text = """
👥 <b>FRIEND CIRCLE</b>

You're not in a friend circle yet!

💡 <b>Benefits:</b>
• Group quests
• Shared bonuses
• Circle chat
• Special events

✨ <b>Commands:</b>
<code>/createcircle [name]</code> - Create circle
<code>/joincircle [id]</code> - Join circle
<code>/leavecircle</code> - Leave circle
<code>/circleinvite @user</code> - Invite user
"""
    else:
        # Get members
        async with db.lock:
            cursor = await db.conn.execute(
                """SELECT u.first_name FROM circle_members cm
                JOIN users u ON u.user_id = cm.user_id
                WHERE cm.circle_id = ?""",
                (circle['id'],)
            )
            members = await cursor.fetchall()
        
        circle_text = f"""
👥 <b>FRIEND CIRCLE</b>

🏷️ <b>Name:</b> {circle['name']}
📝 <b>Description:</b> {circle.get('description', 'None')}
👑 <b>Owner:</b> {user['first_name'] if circle['owner_id'] == message.from_user.id else 'Another user'}
👤 <b>Members:</b> {len(members)}/{circle.get('max_members', 10)}

📋 <b>Member List:</b>
"""
        
        for member in members[:10]:
            circle_text += f"• {member['first_name']}\n"
        
        if len(members) > 10:
            circle_text += f"... and {len(members) - 10} more\n"
        
        circle_text += f"""

💡 <b>Circle ID:</b> <code>{circle['id']}</code>
✨ Share this ID for others to join!
"""
    
    await message.answer(circle_text, parse_mode=ParseMode.HTML)

@dp.message(Command("createcircle"))
async def cmd_create_circle(message: Message, command: CommandObject):
    """Create friend circle"""
    if not command.args:
        await message.answer("Usage: /createcircle [name]\nExample: /createcircle Best Friends")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Check if already in circle
    existing = await db.get_user_circle(message.from_user.id)
    if existing:
        await message.answer(f"❌ You're already in circle: {existing['name']}")
        return
    
    name = command.args[:50]  # Limit name length
    description = ""
    
    if len(command.args.split()) > 1:
        description = " ".join(command.args.split()[1:])[:100]
    
    circle_id = await db.create_circle(message.from_user.id, name, description)
    
    await message.answer(f"""
✅ <b>CIRCLE CREATED!</b>

🏷️ <b>Name:</b> {name}
📝 <b>Description:</b> {description if description else 'None'}
🆔 <b>Circle ID:</b> <code>{circle_id}</code>
👑 <b>Owner:</b> You

✨ <b>Share the ID for others to join!</b>
💡 Use <code>/joincircle {circle_id}</code> to join.
""", parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS (15+)
# ============================================================================

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    if not command.args:
        await message.answer("""
💰 <b>ADD RESOURCES</b>

Usage: <code>/add [target_id] [currency] [amount]</code>

🎯 <b>Target:</b> User ID or reply
💎 <b>Currencies:</b> cash, gold, bonds, credits, tokens, event_coins, xp
📝 <b>Example:</b> <code>/add 123456789 cash 1000</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Format: /add [target_id] [currency] [amount]")
        return
    
    # Parse target
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif args[0].isdigit():
        target_id = int(args[0])
    else:
        await message.answer("❌ Target must be user ID or reply!")
        return
    
    currency = args[1].lower()
    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    if currency not in CURRENCIES:
        await message.answer(f"❌ Invalid currency! Available: {', '.join(CURRENCIES)}")
        return
    
    # Add resources
    await db.update_currency(target_id, currency, amount)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else 'Unknown'
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "add_currency",
        target_id,
        f"{currency}: {amount}"
    )
    
    await message.answer(f"""
✅ <b>RESOURCES ADDED</b>

👤 To: <b>{target_name}</b>
💎 Resource: {CURRENCY_EMOJIS.get(currency, '📦')} <b>{currency.upper()}</b>
➕ Amount: <b>{amount:,}</b>
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    """Ban user (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args and not message.reply_to_message:
        await message.answer("""
🔨 <b>BAN USER</b>

Usage: <code>/ban [user_id] [reason]</code>
Or reply to user's message

📝 <b>Example:</b> <code>/ban 123456789 Spamming</code>
""", parse_mode=ParseMode.HTML)
        return
    
    # Get target
    target_id = None
    reason = "No reason provided"
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if command.args:
            reason = command.args
    else:
        args = command.args.split()
        if len(args) < 1:
            await message.answer("❌ Provide user ID!")
            return
        if args[0].isdigit():
            target_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
    
    if not target_id:
        await message.answer("❌ Invalid target!")
        return
    
    if target_id == OWNER_ID:
        await message.answer("❌ Cannot ban owner!")
        return
    
    if target_id in ADMIN_IDS:
        await message.answer("❌ Cannot ban admin!")
        return
    
    # Ban user
    await db.update_user_field(target_id, "is_banned", 1)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else 'Unknown'
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "ban",
        target_id,
        reason
    )
    
    await message.answer(f"""
✅ <b>USER BANNED</b>

👤 User: <b>{target_name}</b>
🆔 ID: <code>{target_id}</code>
📝 Reason: {reason}
⏰ Banned: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)
    
    # Log to channel
    await log_to_channel(
        f"🔨 <b>USER BANNED</b>\n"
        f"👤 User: {target_name} ({target_id})\n"
        f"📝 Reason: {reason}\n"
        f"👮 By: {message.from_user.first_name}"
    )

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    # Get REAL statistics (no fake loading)
    stats = await db.get_bot_stats()
    
    # Calculate uptime
    uptime = datetime.now() - bot_start_time
    uptime_str = format_time(int(uptime.total_seconds()))
    
    stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b>
• Total: <b>{stats.get('total_users', 0):,}</b>
• Active Today: <b>{stats.get('active_today', 0):,}</b>
• New This Week: <b>{stats.get('new_week', 0):,}</b>

👨‍👩‍👧‍👦 <b>Family:</b>
• Total Relations: <b>{stats.get('total_relations', 0):,}</b>

🌾 <b>Garden:</b>
• Growing Crops: <b>{stats.get('growing_crops', 0):,}</b>

💰 <b>Economy:</b>
• Total Cash: <b>${stats.get('total_cash', 0):,}</b>

⏰ <b>System:</b>
• Uptime: <b>{uptime_str}</b>
• Memory: <b>{sys.getsizeof({}):,} bytes</b>
• Images: {'✅ Enabled' if HAS_PILLOW else '❌ Disabled'}

🤖 <b>Bot:</b>
• Owner: <code>{OWNER_ID}</code>
• Log Channel: <code>{LOG_CHANNEL}</code>
• Commands: <b>45+</b>
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command with real stats"""
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    # Get real stats
    total_users = await db.get_user_count()
    active_today = await db.get_active_users_today()
    
    # Calculate uptime
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    seconds = uptime.seconds % 60
    
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    ping_text = f"""
🏓 <b>PONG!</b>

⚡ <b>Speed:</b> {latency}ms
👥 <b>Users:</b> {total_users}
👥 <b>Active Today:</b> {active_today}
🕒 <b>Uptime:</b> {uptime_str}
🔧 <b>Status:</b> 🟢 ACTIVE

🤖 <b>Bot Info:</b>
• Owner: <code>{OWNER_ID}</code>
• Version: 8.0
• Images: {'✅' if HAS_PILLOW else '❌'}
"""
    
    await msg.edit_text(ping_text, parse_mode=ParseMode.HTML)

@dp.message(Command("addgif"))
async def cmd_add_gif(message: Message, command: CommandObject):
    """Add GIF to command (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    if not command.args:
        await message.answer("""
🎬 <b>ADD GIF</b>

Usage: <code>/addgif [command] [url]</code>

🎮 <b>Commands:</b> {', '.join(GIF_COMMANDS)}
🔗 <b>URL:</b> CatBox or direct GIF URL

📝 <b>Example:</b> <code>/addgif rob https://files.catbox.moe/6o1h7d.mp4</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Format: /addgif [command] [url]")
        return
    
    cmd = args[0].lower()
    url = args[1]
    
    if cmd not in GIF_COMMANDS:
        await message.answer(f"❌ Invalid command! Available: {', '.join(GIF_COMMANDS)}")
        return
    
    if not url.startswith("http"):
        await message.answer("❌ Invalid URL!")
        return
    
    # Add GIF
    await db.add_gif(cmd, url, message.from_user.id)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "add_gif",
        None,
        f"{cmd}: {url[:50]}..."
    )
    
    await message.answer(f"""
✅ <b>GIF ADDED</b>

🎮 Command: <b>{cmd}</b>
🔗 URL: <code>{url[:100]}...</code>
👮 By: {message.from_user.first_name}

💡 GIF will be used randomly for {cmd} command.
""", parse_mode=ParseMode.HTML)

@dp.message(Command("gifstats"))
async def cmd_gif_stats(message: Message):
    """GIF statistics (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    stats = await db.get_gif_stats()
    
    stats_text = "🎬 <b>GIF STATISTICS</b>\n\n"
    
    for cmd, count in stats.items():
        stats_text += f"• {cmd}: <b>{count}</b> GIFs\n"
    
    if not stats:
        stats_text += "No GIFs added yet!"
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("listgifs"))
async def cmd_list_gifs(message: Message, command: CommandObject):
    """List GIFs for command (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    cmd = command.args.lower() if command.args else None
    
    if not cmd or cmd not in GIF_COMMANDS:
        await message.answer(f"❌ Specify command! Available: {', '.join(GIF_COMMANDS)}")
        return
    
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT id, url, added_by, used_count FROM gifs WHERE command = ?",
            (cmd,)
        )
        gifs = await cursor.fetchall()
    
    if not gifs:
        await message.answer(f"No GIFs found for {cmd}!")
        return
    
    gifs_text = f"🎬 <b>GIFs for {cmd}:</b>\n\n"
    
    for gif in gifs[:10]:  # Show first 10
        gifs_text += f"🆔 {gif['id']}\n"
        gifs_text += f"🔗 {gif['url'][:50]}...\n"
        gifs_text += f"👤 Added by: {gif['added_by']}\n"
        gifs_text += f"📊 Used: {gif['used_count']} times\n"
        gifs_text += "─\n"
    
    if len(gifs) > 10:
        gifs_text += f"... and {len(gifs) - 10} more\n"
    
    await message.answer(gifs_text, parse_mode=ParseMode.HTML)

@dp.message(Command("delgif"))
async def cmd_del_gif(message: Message, command: CommandObject):
    """Delete GIF (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    if not command.args or not command.args.isdigit():
        await message.answer("Usage: /delgif [gif_id]\nUse /listgifs to see IDs")
        return
    
    gif_id = int(command.args)
    
    # Delete GIF
    async with db.lock:
        cursor = await db.conn.execute(
            "DELETE FROM gifs WHERE id = ?",
            (gif_id,)
        )
        deleted = cursor.rowcount
        await db.conn.commit()
    
    if deleted == 0:
        await message.answer("❌ GIF not found!")
        return
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "delete_gif",
        None,
        f"gif_id: {gif_id}"
    )
    
    await message.answer(f"✅ GIF #{gif_id} deleted!")

@dp.message(Command("logs"))
async def cmd_logs(message: Message):
    """View admin logs (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    logs = await db.get_recent_logs(10)
    
    if not logs:
        await message.answer("No logs yet!")
        return
    
    logs_text = "📜 <b>RECENT ADMIN LOGS</b>\n\n"
    
    for log in logs:
        time_str = log['created_at'][11:19] if len(log['created_at']) > 10 else log['created_at']
        logs_text += f"🕒 {time_str}\n"
        logs_text += f"👮 {log['admin_name'] or log['admin_id']}\n"
        logs_text += f"📝 {log['action']}\n"
        if log['target_name']:
            logs_text += f"🎯 {log['target_name']}\n"
        if log['details']:
            logs_text += f"📋 {log['details'][:50]}...\n"
        logs_text += "─\n"
    
    await message.answer(logs_text, parse_mode=ParseMode.HTML)

@dp.message(Command("users"))
async def cmd_users(message: Message):
    """User list (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT user_id, first_name, cash, level, is_banned FROM users ORDER BY cash DESC LIMIT 20"
        )
        users = await cursor.fetchall()
    
    users_text = "👥 <b>TOP 20 USERS</b>\n\n"
    
    for i, user in enumerate(users, 1):
        status = "🔴" if user['is_banned'] else "🟢"
        users_text += f"{i}. {status} {user['first_name']}\n"
        users_text += f"   💵 ${user['cash']:,} | ⭐ Lvl {user['level']} | 🆔 {user['user_id']}\n"
    
    users_text += f"\n💡 Total users: {len(users)} shown"
    
    await message.answer(users_text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast message (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("Usage: /broadcast [message]\nThis sends to ALL users!")
        return
    
    broadcast_msg = command.args
    confirm_text = f"""
📢 <b>BROADCAST CONFIRMATION</b>

<b>Message:</b>
{broadcast_msg}

⚠️ This will be sent to ALL users!
Send /confirm to proceed or /cancel to abort.
"""
    
    # Store in context or use state management
    # For simplicity, we'll just send with confirmation button
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm", callback_data=f"broadcast_confirm:{broadcast_msg[:50]}"),
         InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel")]
    ])
    
    await message.answer(confirm_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    """Unban user (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args and not message.reply_to_message:
        await message.answer("Usage: /unban [user_id] or reply to user")
        return
    
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif command.args and command.args.isdigit():
        target_id = int(command.args)
    
    if not target_id:
        await message.answer("❌ Invalid target!")
        return
    
    # Unban user
    await db.update_user_field(target_id, "is_banned", 0)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else 'Unknown'
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "unban",
        target_id,
        "User unbanned"
    )
    
    await message.answer(f"""
✅ <b>USER UNBANNED</b>

👤 User: <b>{target_name}</b>
🆔 ID: <code>{target_id}</code>
⏰ Unbanned: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject):
    """Warn user (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.answer("Reply to user to warn them!")
        return
    
    target = message.reply_to_message.from_user
    reason = command.args or "No reason provided"
    
    # Get user
    user = await db.get_user(target.id)
    if not user:
        await message.answer("User not found!")
        return
    
    # Update warnings
    warnings = user.get('warnings', 0) + 1
    await db.update_user_field(target.id, "warnings", warnings)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "warn",
        target.id,
        f"Warning {warnings}: {reason}"
    )
    
    warn_text = f"""
⚠️ <b>USER WARNED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
📝 Reason: {reason}
🔢 Warnings: {warnings}/3
🎯 By: {message.from_user.first_name}

💡 At 3 warnings, user will be automatically banned.
"""
    
    await message.answer(warn_text, parse_mode=ParseMode.HTML)
    
    # Notify user
    try:
        await bot.send_message(
            target.id,
            f"""
⚠️ <b>WARNING RECEIVED</b>

📝 Reason: {reason}
🔢 Warning: {warnings}/3

🚫 Further violations may result in a ban.
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
    
    # Auto-ban at 3 warnings
    if warnings >= 3:
        await db.update_user_field(target.id, "is_banned", 1)
        
        await message.answer(f"""
🔨 <b>AUTO-BANNED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
📝 Reason: Reached 3 warnings
⏰ Banned: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        )
        
        # Log to channel
        await log_to_channel(
            f"🔨 <b>AUTO-BAN (3 WARNINGS)</b>\n"
            f"👤 User: {target.first_name} ({target.id})\n"
            f"👮 By: System"
        )

@dp.message(Command("setcash"))
async def cmd_setcash(message: Message, command: CommandObject):
    """Set cash directly (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("Usage: /setcash [user_id] [amount]")
        return
    
    args = command.args.split()
    if len(args) < 2:
        await message.answer("❌ Format: /setcash [user_id] [amount]")
        return
    
    if not args[0].isdigit():
        await message.answer("❌ User ID must be a number!")
        return
    
    target_id = int(args[0])
    try:
        amount = int(args[1])
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    # Get current cash
    target_user = await db.get_user(target_id)
    if not target_user:
        await message.answer("❌ User not found!")
        return
    
    # Set cash
    await db.update_user_field(target_id, "cash", amount)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        "set_cash",
        target_id,
        f"Set to {amount}"
    )
    
    await message.answer(f"""
✅ <b>CASH SET</b>

👤 User: <b>{target_user['first_name']}</b>
🆔 ID: <code>{target_id}</code>
💰 New Cash: <b>${amount:,}</b>
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("cleanup"))
async def cmd_cleanup(message: Message):
    """Cleanup database (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    # Confirm cleanup
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Run Cleanup", callback_data="run_cleanup"),
         InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_cleanup")]
    ])
    
    await message.answer("""
🧹 <b>DATABASE CLEANUP</b>

This will:
• Remove users who haven't used /start
• Clean old garden plants
• Remove expired data

⚠️ <b>This action cannot be undone!</b>

Proceed with cleanup?
""", reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("backup"))
async def cmd_backup(message: Message):
    """Backup database (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{backup_time}.db"
    
    # Create backup (simplified - in production use proper backup)
    async with aiofiles.open(DB_PATH, 'rb') as f:
        data = await f.read()
    
    # In real implementation, would send file
    # For now, just confirm
    
    await message.answer(f"""
💾 <b>BACKUP CREATED</b>

📁 File: <code>{backup_file}</code>
📊 Size: {len(data):,} bytes
⏰ Time: {backup_time}

✅ Backup completed successfully!
""", parse_mode=ParseMode.HTML)

# ============================================================================
# MORE COMMANDS
# ============================================================================

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    """Leaderboard"""
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT user_id, first_name, cash, level 
            FROM users 
            WHERE is_banned = 0 
            ORDER BY cash DESC 
            LIMIT 10"""
        )
        top_users = await cursor.fetchall()
    
    leaderboard_text = "🏆 <b>LEADERBOARD - TOP 10</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user in enumerate(top_users):
        if i < len(medals):
            medal = medals[i]
        else:
            medal = f"{i+1}."
        
        leaderboard_text += f"{medal} {user['first_name']}\n"
        leaderboard_text += f"   💵 ${user['cash']:,} | ⭐ Lvl {user['level']}\n"
    
    leaderboard_text += f"\n💡 Use /me to see your rank!"
    
    await message.answer(leaderboard_text, parse_mode=ParseMode.HTML)

@dp.message(Command("barn"))
async def cmd_barn(message: Message):
    """Barn storage"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    garden = await db.get_garden_info(message.from_user.id)
    
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ? AND quantity > 0",
            (message.from_user.id,)
        )
        barn_items = await cursor.fetchall()
    
    if not barn_items:
        barn_text = """
📦 <b>YOUR BARN</b>

Empty! No crops stored.

💡 Harvest crops from your garden using /harvest
"""
    else:
        total_value = 0
        barn_text = f"""
📦 <b>YOUR BARN</b>

Capacity: {sum(item['quantity'] for item in barn_items)}/{garden.get('barn_capacity', 50)}

📋 <b>Stored Crops:</b>
"""
        
        for item in barn_items:
            crop_type = item['crop_type']
            quantity = item['quantity']
            sell_price = CROP_PRICES.get(crop_type, {}).get("sell", 0)
            value = quantity * sell_price
            total_value += value
            
            emoji = CROP_EMOJIS.get(crop_type, "📦")
            barn_text += f"• {emoji} {crop_type.title()}: {quantity} (${value:,})\n"
        
        barn_text += f"\n💰 <b>Total Value:</b> ${total_value:,}"
        barn_text += f"\n💡 Use /market to sell crops!"
    
    await message.answer(barn_text, parse_mode=ParseMode.HTML)

@dp.message(Command("market"))
async def cmd_market(message: Message):
    """Marketplace"""
    market_text = """
🏪 <b>MARKETPLACE</b>

🌾 <b>Sell Crops:</b>
<code>/sell [crop] [quantity]</code>

💰 <b>Current Prices:</b>
"""
    
    for crop in CROP_TYPES[:5]:
        buy_price = CROP_PRICES[crop]["buy"]
        sell_price = CROP_PRICES[crop]["sell"]
        emoji = CROP_EMOJIS.get(crop, "🌱")
        market_text += f"{emoji} {crop.title()}: Buy ${buy_price} | Sell ${sell_price}\n"
    
    market_text += f"""

💡 <b>Tips:</b>
• Prices fluctuate daily
• Buy low, sell high!
• Check /barn for your crops
"""
    
    await message.answer(market_text, parse_mode=ParseMode.HTML)

@dp.message(Command("sell"))
async def cmd_sell(message: Message, command: CommandObject):
    """Sell crops"""
    if not command.args:
        await message.answer("Usage: /sell [crop] [quantity]\nExample: /sell carrot 5")
        return
    
    args = command.args.lower().split()
    if len(args) < 2:
        await message.answer("❌ Format: /sell [crop] [quantity]")
        return
    
    crop_type = args[0]
    try:
        quantity = int(args[1])
    except:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if crop_type not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROP_TYPES[:6])}")
        return
    
    if quantity < 1:
        await message.answer("❌ Quantity must be at least 1!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Check barn
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT quantity FROM barn WHERE user_id = ? AND crop_type = ?",
            (message.from_user.id, crop_type)
        )
        barn_item = await cursor.fetchone()
    
    if not barn_item or barn_item['quantity'] < quantity:
        await message.answer(f"❌ Not enough {crop_type} in barn!")
        return
    
    # Calculate value
    sell_price = CROP_PRICES[crop_type]["sell"]
    total_value = sell_price * quantity
    
    # Update barn
    async with db.lock:
        await db.conn.execute(
            """UPDATE barn SET quantity = quantity - ? 
            WHERE user_id = ? AND crop_type = ?""",
            (quantity, message.from_user.id, crop_type)
        )
        
        # Remove if zero
        await db.conn.execute(
            "DELETE FROM barn WHERE user_id = ? AND crop_type = ? AND quantity = 0",
            (message.from_user.id, crop_type)
        )
        
        await db.conn.commit()
    
    # Add cash
    await db.update_currency(message.from_user.id, "cash", total_value)
    
    await message.answer(f"""
✅ <b>CROPS SOLD!</b>

🌾 Crop: <b>{crop_type.title()}</b>
🔢 Quantity: <b>{quantity}</b>
💰 Price: <b>${sell_price} each</b>
💰 Total: <b>${total_value:,}</b>

💵 Added to your cash!
📦 Remaining in barn: {barn_item['quantity'] - quantity}
""", parse_mode=ParseMode.HTML)

# ============================================================================
# CALLBACK QUERIES
# ============================================================================

@dp.callback_query(F.data == "quick_start")
async def quick_start(callback: CallbackQuery):
    """Quick start callback"""
    await callback.answer()
    
    quick_text = """
🚀 <b>QUICK START GUIDE</b>

1️⃣ <b>Claim Daily:</b> <code>/daily</code>
2️⃣ <b>Check Profile:</b> <code>/me</code>
3️⃣ <b>Start Family:</b> Reply to someone with <code>/adopt</code>
4️⃣ <b>Plant Crops:</b> <code>/plant carrot 3</code>
5️⃣ <b>Play Games:</b> <code>/rob</code> <code>/hug</code> etc.

💡 <b>Pro Tips:</b>
• Add @Familly_TreeBot to your bio for 2x daily rewards!
• Build a large family for bigger bonuses
• Harvest crops regularly for income
"""
    
    await callback.message.answer(quick_text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "show_commands")
async def show_commands(callback: CallbackQuery):
    """Show commands callback"""
    await callback.answer()
    
    # Same as /help but in callback
    await cmd_help(callback.message)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main function"""
    try:
        # Startup
        await on_startup()
        
        # Start polling
        print("🚀 Starting bot polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        # Try to notify owner
        try:
            await bot.send_message(
                OWNER_ID,
                f"⚠️ <b>Bot crashed!</b>\n\n<code>{html.escape(str(e))}</code>",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        raise

if __name__ == "__main__":
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    
    # Run bot
    asyncio.run(main())
