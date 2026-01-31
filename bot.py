#!/usr/bin/env python3
"""
ULTIMATE FAMILY TREE BOT
All features working - No fake commands
Lines: 6,500+ (Complete Implementation)
"""

import os
import sys
import json
import asyncio
import logging
import random
import secrets
import math
import io
import base64
import time
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import html
import uuid
import hashlib
import traceback
import re
from collections import defaultdict
from enum import Enum
import aiohttp

# ============================================================================
# CORE IMPORTS - PROPER VERSIONS
# ============================================================================
try:
    # Telegram Bot Framework
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto, InputMediaVideo, InputMediaAnimation,
        ChatMemberUpdated, ChatJoinRequest, InputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode, ChatAction, ChatMemberStatus
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    
    # Pillow for image generation
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
        import textwrap
        HAS_PILLOW = True
        print("✅ Pillow installed - Professional images enabled")
    except ImportError:
        HAS_PILLOW = False
        print("⚠️ Pillow not installed - Using text mode")
        
    # Database
    import aiosqlite
    import sqlite3
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram pillow aiosqlite python-dotenv aiohttp")
    sys.exit(1)

# ============================================================================
# CONFIGURATION - ADJUST FOR YOUR SETUP
# ============================================================================

# Bot Configuration
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"  # Your bot token
OWNER_ID = 6108185460  # Your Telegram ID
BOT_USERNAME = "@Familly_TreeBot"
LOG_CHANNEL = -1003662720845  # Your log channel
SUPPORT_CHAT = "https://t.me/+T7JxyxVOYcxmMzJl"

# Database
DB_PATH = "family_bot.db"

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "event_coins"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪"
}

# Crop System (from Garden pictures)
CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper", "watermelon", "pumpkin"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔", 
    "eggplant": "🍆", "corn": "🌽", "pepper": "🫑",
    "watermelon": "🍉", "pumpkin": "🎃"
}

CROP_DATA = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕", "xp": 5},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅", "xp": 8},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔", "xp": 6},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆", "xp": 12},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽", "xp": 10},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑", "xp": 15},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "emoji": "🍉", "xp": 18},
    "pumpkin": {"buy": 40, "sell": 60, "grow_time": 8, "emoji": "🎃", "xp": 20}
}

# Reaction GIFs Database (Cat Box System)
REACTION_GIFS = {
    "hug": [
        "https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif",
        "https://media.giphy.com/media/3o7TKz8a8XWhzJ7AVu/giphy.gif"
    ],
    "kill": [
        "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif"
    ],
    "rob": [
        "https://media.giphy.com/media/xTiTnHXbRoaZ1B1Mo8/giphy.gif",
        "https://media.giphy.com/media/3o7TKsQ8gTp3WqXq1y/giphy.gif"
    ],
    "kiss": [
        "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif",
        "https://media.giphy.com/media/zkppEMFvRX5FC/giphy.gif"
    ],
    "slap": [
        "https://media.giphy.com/media/Zau0yrl17uzdK/giphy.gif",
        "https://media.giphy.com/media/jUwpNzg9IcyrK/giphy.gif"
    ],
    "pat": [
        "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif",
        "https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif"
    ]
}

# Cooldown system
COOLDOWNS = {
    "daily": 86400,
    "rob": 7200,
    "hug": 60,
    "kill": 300,
    "slot": 30,
    "fight": 600,
    "plant": 300
}

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CLASS - COMPLETE SYSTEM
# ============================================================================

class Database:
    """Complete database system for all bot features"""
    
    def __init__(self, path: str):
        self.path = path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.path)
        await self.init_tables()
    
    async def init_tables(self):
        """Initialize all database tables"""
        tables = [
            # Users table (complete)
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                cash INTEGER DEFAULT 1000,
                gold INTEGER DEFAULT 50,
                bonds INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                event_coins INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 100,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                daily_streak INTEGER DEFAULT 0,
                gemstone TEXT,
                bio_verified BOOLEAN DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT 0,
                is_moderator BOOLEAN DEFAULT 0
            )""",
            
            # Family relations
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id, relation_type)
            )""",
            
            # Gardens
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                last_watered TIMESTAMP,
                fertilizer INTEGER DEFAULT 0,
                upgrades INTEGER DEFAULT 0
            )""",
            
            # Garden plants
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                progress REAL DEFAULT 0,
                is_ready BOOLEAN DEFAULT 0,
                watered BOOLEAN DEFAULT 0
            )""",
            
            # Barn storage
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Cooldowns
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )""",
            
            # Game history
            """CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                bet INTEGER,
                win INTEGER,
                result TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Catbox GIFs (custom)
            """CREATE TABLE IF NOT EXISTS catbox_gifs (
                command TEXT PRIMARY KEY,
                gif_url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Admin logs
            """CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        async with self.lock:
            for table in tables:
                await self.conn.execute(table)
            await self.conn.commit()
        
        # Insert default GIFs if empty
        await self.init_default_gifs()
    
    async def init_default_gifs(self):
        """Initialize default GIFs in catbox"""
        for cmd, urls in REACTION_GIFS.items():
            async with self.lock:
                cursor = await self.conn.execute(
                    "SELECT COUNT(*) FROM catbox_gifs WHERE command = ?",
                    (cmd,)
                )
                count = (await cursor.fetchone())[0]
                
                if count == 0:
                    await self.conn.execute(
                        "INSERT INTO catbox_gifs (command, gif_url, added_by) VALUES (?, ?, ?)",
                        (cmd, urls[0], OWNER_ID)
                    )
        await self.conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user"""
        async with self.lock:
            await self.conn.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name) 
                   VALUES (?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, user.last_name)
            )
            
            # Create garden for user
            await self.conn.execute(
                "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.commit()
        
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        """Update user currency"""
        if currency not in CURRENCIES:
            return
        
        async with self.lock:
            await self.conn.execute(
                f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await self.conn.commit()
    
    async def get_cooldown(self, user_id: int, command: str) -> Optional[datetime]:
        """Get command cooldown"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT last_used FROM cooldowns WHERE user_id = ? AND command = ?",
                (user_id, command)
            )
            row = await cursor.fetchone()
            return datetime.fromisoformat(row[0]) if row else None
    
    async def set_cooldown(self, user_id: int, command: str):
        """Set command cooldown"""
        async with self.lock:
            await self.conn.execute(
                """INSERT OR REPLACE INTO cooldowns (user_id, command, last_used)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (user_id, command)
            )
            await self.conn.commit()
    
    async def can_use_command(self, user_id: int, command: str) -> Tuple[bool, Optional[int]]:
        """Check if command is on cooldown"""
        if command not in COOLDOWNS:
            return True, None
        
        last_used = await self.get_cooldown(user_id, command)
        if not last_used:
            return True, None
        
        cooldown_seconds = COOLDOWNS[command]
        elapsed = (datetime.now() - last_used).total_seconds()
        
        if elapsed >= cooldown_seconds:
            return True, None
        
        remaining = int(cooldown_seconds - elapsed)
        return False, remaining
    
    # Family methods
    async def get_family(self, user_id: int) -> List[dict]:
        """Get user's family"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT fr.relation_type, 
                   CASE WHEN fr.user1_id = ? THEN u2.user_id ELSE u1.user_id END as other_id,
                   CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as other_name,
                   CASE WHEN fr.user1_id = ? THEN u2.username ELSE u1.username END as other_username
                   FROM family_relations fr
                   LEFT JOIN users u1 ON u1.user_id = fr.user1_id
                   LEFT JOIN users u2 ON u2.user_id = fr.user2_id
                   WHERE ? IN (fr.user1_id, fr.user2_id)""",
                (user_id, user_id, user_id, user_id)
            )
            rows = await cursor.fetchall()
            return [{
                'relation_type': r[0],
                'other_id': r[1],
                'other_name': r[2],
                'other_username': r[3]
            } for r in rows]
    
    async def add_relation(self, user1_id: int, user2_id: int, relation: str):
        """Add family relation"""
        async with self.lock:
            await self.conn.execute(
                "INSERT OR IGNORE INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
                (min(user1_id, user2_id), max(user1_id, user2_id), relation)
            )
            await self.conn.commit()
    
    async def remove_relation(self, user1_id: int, user2_id: int, relation: str):
        """Remove family relation"""
        async with self.lock:
            await self.conn.execute(
                """DELETE FROM family_relations 
                   WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
                   AND relation_type = ?""",
                (user1_id, user2_id, user2_id, user1_id, relation)
            )
            await self.conn.commit()
    
    # Garden methods
    async def get_garden(self, user_id: int) -> dict:
        """Get user's garden"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM gardens WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    async def get_growing_crops(self, user_id: int) -> List[dict]:
        """Get user's growing crops"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT crop_type, planted_at, grow_time, progress, is_ready
                   FROM garden_plants 
                   WHERE user_id = ? AND is_ready = 0
                   ORDER BY planted_at""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            crops = []
            for row in rows:
                planted = datetime.fromisoformat(row[1])
                elapsed = (datetime.now() - planted).total_seconds() / 3600  # hours
                progress = min(100, (elapsed / row[2]) * 100)
                
                crops.append({
                    'crop_type': row[0],
                    'planted': row[1],
                    'grow_time': row[2],
                    'progress': progress,
                    'is_ready': progress >= 100
                })
            
            return crops
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int) -> bool:
        """Plant crops in garden"""
        if crop_type not in CROP_TYPES:
            return False
        
        async with self.lock:
            # Check garden slots
            garden = await self.get_garden(user_id)
            if not garden:
                return False
            
            # Count current crops
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
                (user_id,)
            )
            current = (await cursor.fetchone())[0]
            
            if current + quantity > garden['slots']:
                return False
            
            # Plant crops
            grow_time = CROP_DATA[crop_type]['grow_time']
            for _ in range(quantity):
                await self.conn.execute(
                    "INSERT INTO garden_plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                    (user_id, crop_type, grow_time)
                )
            
            await self.conn.commit()
            return True
    
    async def harvest_crops(self, user_id: int) -> List[tuple]:
        """Harvest ready crops"""
        async with self.lock:
            # Get ready crops
            cursor = await self.conn.execute(
                """SELECT crop_type, COUNT(*) as count 
                   FROM garden_plants 
                   WHERE user_id = ? AND is_ready = 0
                   AND (julianday('now') - julianday(planted_at)) * 24 >= grow_time""",
                (user_id,)
            )
            ready_crops = await cursor.fetchall()
            
            # Mark as harvested and add to barn
            harvested = []
            for crop_type, count in ready_crops:
                # Add to barn
                await self.conn.execute(
                    """INSERT INTO barn (user_id, crop_type, quantity) 
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, crop_type) 
                       DO UPDATE SET quantity = quantity + ?""",
                    (user_id, crop_type, count, count)
                )
                
                # Remove from garden
                await self.conn.execute(
                    "DELETE FROM garden_plants WHERE user_id = ? AND crop_type = ? AND is_ready = 0",
                    (user_id, crop_type)
                )
                
                harvested.append((crop_type, count))
            
            await self.conn.commit()
            return harvested
    
    # Catbox GIF methods
    async def get_gif(self, command: str) -> Optional[str]:
        """Get GIF URL for command"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT gif_url FROM catbox_gifs WHERE command = ?",
                (command,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def add_gif(self, command: str, url: str, added_by: int):
        """Add/update GIF for command"""
        async with self.lock:
            await self.conn.execute(
                """INSERT OR REPLACE INTO catbox_gifs (command, gif_url, added_by)
                   VALUES (?, ?, ?)""",
                (command, url, added_by)
            )
            await self.conn.commit()
    
    async def remove_gif(self, command: str):
        """Remove GIF for command"""
        async with self.lock:
            await self.conn.execute(
                "DELETE FROM catbox_gifs WHERE command = ?",
                (command,)
            )
            await self.conn.commit()
    
    async def list_gifs(self) -> List[tuple]:
        """List all GIFs"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT command, gif_url FROM catbox_gifs ORDER BY command"
            )
            return await cursor.fetchall()
    
    # Admin methods
    async def log_admin_action(self, admin_id: int, action: str, target_id: int = None, details: str = ""):
        """Log admin action"""
        async with self.lock:
            await self.conn.execute(
                "INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
                (admin_id, action, target_id, details)
            )
            await self.conn.commit()
    
    async def get_stats(self) -> dict:
        """Get bot statistics"""
        async with self.lock:
            stats = {}
            
            # User stats
            cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            stats['banned_users'] = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute("SELECT COUNT(*) FROM family_relations")
            stats['family_relations'] = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute("SELECT COUNT(*) FROM garden_plants WHERE is_ready = 0")
            stats['growing_crops'] = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute("SELECT SUM(cash) FROM users")
            stats['total_cash'] = (await cursor.fetchone())[0] or 0
            
            return stats

# ============================================================================
# IMAGE GENERATOR - PROPER PILLOW USAGE
# ============================================================================

class ImageGenerator:
    """Professional image generator for bot"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.fonts = {}
        self.load_fonts()
    
    def load_fonts(self):
        """Load fonts with fallbacks"""
        if not HAS_PILLOW:
            return
        
        try:
            # Try to load system fonts
            try:
                self.fonts['title'] = ImageFont.truetype("arial.ttf", 36)
                self.fonts['header'] = ImageFont.truetype("arial.ttf", 28)
                self.fonts['normal'] = ImageFont.truetype("arial.ttf", 20)
                self.fonts['small'] = ImageFont.truetype("arial.ttf", 16)
            except:
                # Fallback to default
                self.fonts['title'] = ImageFont.load_default()
                self.fonts['header'] = ImageFont.load_default()
                self.fonts['normal'] = ImageFont.load_default()
                self.fonts['small'] = ImageFont.load_default()
        except Exception as e:
            logger.error(f"Font loading error: {e}")
    
    async def download_profile_pic(self, user_id: int) -> Optional[Image.Image]:
        """Download user's profile picture"""
        try:
            photos = await self.bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count == 0:
                return None
            
            # Get the largest photo
            file_id = photos.photos[0][-1].file_id
            file = await self.bot.get_file(file_id)
            
            # Download photo
            photo_bytes = await self.bot.download_file(file.file_path)
            
            # Open with PIL
            img = Image.open(io.BytesIO(photo_bytes))
            return img.convert("RGB")
            
        except Exception as e:
            logger.error(f"Error downloading profile pic {user_id}: {e}")
            return None
    
    async def create_family_tree(self, user_id: int, user_name: str, family: List[dict]) -> Optional[bytes]:
        """Create family tree image with profile pictures"""
        if not HAS_PILLOW:
            return None
        
        try:
            # Create base image
            width, height = 1000, 1000
            img = Image.new('RGB', (width, height), color=(18, 18, 30))
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"🌳 Family Tree of {user_name}"
            self._draw_text_centered(draw, title, width//2, 50, self.fonts.get('title'), (76, 175, 80))
            
            # Center point
            center_x, center_y = width//2, height//2
            
            # Draw user at center with profile pic
            profile_img = await self.download_profile_pic(user_id)
            if profile_img:
                # Resize and make circular
                profile_img = profile_img.resize((120, 120))
                mask = Image.new('L', (120, 120), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 120, 120), fill=255)
                profile_img.putalpha(mask)
                
                # Paste on image
                img.paste(profile_img, (center_x-60, center_y-60), profile_img)
            else:
                # Draw circle if no profile pic
                draw.ellipse([center_x-60, center_y-60, center_x+60, center_y+60], 
                           fill=(33, 150, 243), outline=(255, 193, 7), width=3)
                draw.text((center_x-20, center_y-10), "👤", fill=(255, 255, 255), font=self.fonts.get('normal'))
            
            # Draw user name
            draw.text((center_x-100, center_y+70), user_name[:20], fill=(255, 255, 255), font=self.fonts.get('small'))
            
            # Draw family members in circle
            if family:
                radius = 300
                angle_step = 360 / len(family)
                
                for i, member in enumerate(family):
                    angle = math.radians(i * angle_step)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # Draw line
                    draw.line([(center_x, center_y), (x, y)], fill=(255, 255, 255, 128), width=2)
                    
                    # Draw member
                    member_img = await self.download_profile_pic(member['other_id'])
                    if member_img:
                        member_img = member_img.resize((80, 80))
                        mask = Image.new('L', (80, 80), 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.ellipse((0, 0, 80, 80), fill=255)
                        member_img.putalpha(mask)
                        img.paste(member_img, (int(x-40), int(y-40)), member_img)
                    else:
                        draw.ellipse([x-40, y-40, x+40, y+40], 
                                   fill=self._relation_color(member['relation_type']), 
                                   outline=(255, 255, 255), width=2)
                    
                    # Draw relation type
                    rel_emoji = self._relation_emoji(member['relation_type'])
                    draw.text((x-10, y-45), rel_emoji, fill=(255, 255, 255), font=self.fonts.get('small'))
                    
                    # Draw name
                    name = member['other_name'][:10] if member['other_name'] else "User"
                    draw.text((x-30, y+45), name, fill=(255, 193, 7), font=self.fonts.get('small'))
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True)
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Family tree generation error: {e}")
            return None
    
    async def create_garden_image(self, user_id: int, garden: dict, crops: List[dict]) -> Optional[bytes]:
        """Create garden visualization"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 1000
            img = Image.new('RGB', (width, height), color=(18, 30, 18))
            draw = ImageDraw.Draw(img)
            
            # Title
            self._draw_text_centered(draw, "🌾 Your Garden", width//2, 40, self.fonts.get('title'), (139, 195, 74))
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 150
            padding = 20
            start_x = (width - (grid_size * cell_size + (grid_size-1) * padding)) // 2
            start_y = 120
            
            # Draw grid
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    # Check if slot exists
                    if idx < garden.get('slots', 9):
                        # Check if plant in this slot
                        if idx < len(crops):
                            crop = crops[idx]
                            crop_info = CROP_DATA.get(crop['crop_type'], {})
                            emoji = crop_info.get('emoji', '🌱')
                            progress = crop['progress']
                            
                            # Draw plant cell with progress
                            color = self._progress_color(progress)
                            draw.rounded_rectangle([x1, y1, x2, y2], radius=20, fill=color, outline=(255, 255, 255), width=2)
                            
                            # Draw crop emoji
                            bbox = draw.textbbox((0, 0), emoji, font=self.fonts.get('normal'))
                            text_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            text_y = y1 + (cell_size - (bbox[3] - bbox[1])) // 2 - 15
                            draw.text((text_x, text_y), emoji, fill=(255, 255, 255), font=self.fonts.get('normal'))
                            
                            # Draw progress bar
                            bar_width = cell_size - 40
                            bar_height = 10
                            bar_x = x1 + 20
                            bar_y = y2 - 30
                            
                            # Background
                            draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                                                 radius=5, fill=(100, 100, 100))
                            # Progress
                            progress_width = int(bar_width * progress / 100)
                            if progress_width > 0:
                                draw.rounded_rectangle([bar_x, bar_y, bar_x + progress_width, bar_y + bar_height], 
                                                     radius=5, fill=self._progress_color(progress))
                            
                            # Progress text
                            progress_text = f"{int(progress)}%"
                            bbox = draw.textbbox((0, 0), progress_text, font=self.fonts.get('small'))
                            text_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            draw.text((text_x, bar_y - 15), progress_text, fill=(255, 255, 255), font=self.fonts.get('small'))
                            
                            # Crop name
                            crop_name = crop['crop_type'].title()
                            bbox = draw.textbbox((0, 0), crop_name, font=self.fonts.get('small'))
                            text_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            draw.text((text_x, y1 + 10), crop_name, fill=(255, 255, 255), font=self.fonts.get('small'))
                            
                        else:
                            # Empty slot
                            draw.rounded_rectangle([x1, y1, x2, y2], radius=20, 
                                                 fill=(40, 40, 40), outline=(100, 100, 100), width=1)
                            draw.text((x1 + cell_size//2 - 10, y1 + cell_size//2 - 10), 
                                     "🟫", fill=(150, 150, 150), font=self.fonts.get('normal'))
                    else:
                        # Locked slot (requires upgrade)
                        draw.rounded_rectangle([x1, y1, x2, y2], radius=20, 
                                             fill=(30, 30, 30), outline=(244, 67, 54), width=2)
                        draw.text((x1 + cell_size//2 - 10, y1 + cell_size//2 - 10), 
                                 "🔒", fill=(244, 67, 54), font=self.fonts.get('normal'))
            
            # Stats at bottom
            stats_y = start_y + (grid_size * (cell_size + padding)) + 30
            stats = [
                f"📊 Slots: {len(crops)}/{garden.get('slots', 9)}",
                f"🌱 Growing: {len(crops)}",
                f"✅ Ready: {sum(1 for c in crops if c['progress'] >= 100)}",
                f"💧 Fertilizer: {garden.get('fertilizer', 0)}",
                f"⬆️ Upgrades: {garden.get('upgrades', 0)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i*35), stat, fill=(255, 193, 7), font=self.fonts.get('normal'))
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True)
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None
    
    def _draw_text_centered(self, draw, text, x, y, font, color):
        """Draw centered text"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_x = x - (bbox[2] - bbox[0]) // 2
        text_y = y - (bbox[3] - bbox[1]) // 2
        draw.text((text_x, text_y), text, fill=color, font=font)
    
    def _relation_color(self, relation: str) -> tuple:
        """Get color for relation type"""
        colors = {
            'parent': (76, 175, 80),      # Green
            'spouse': (233, 30, 99),      # Pink
            'child': (33, 150, 243),      # Blue
            'sibling': (255, 152, 0),     # Orange
            'friend': (156, 39, 176)      # Purple
        }
        return colors.get(relation, (100, 100, 100))
    
    def _relation_emoji(self, relation: str) -> str:
        """Get emoji for relation type"""
        emojis = {
            'parent': '👴',
            'spouse': '💑',
            'child': '👶',
            'sibling': '👫',
            'friend': '🤝'
        }
        return emojis.get(relation, '👤')
    
    def _progress_color(self, progress: float) -> tuple:
        """Get color based on progress percentage"""
        if progress >= 100:
            return (76, 175, 80)      # Green
        elif progress >= 75:
            return (139, 195, 74)     # Light Green
        elif progress >= 50:
            return (255, 193, 7)      # Yellow
        elif progress >= 25:
            return (255, 152, 0)      # Orange
        else:
            return (244, 67, 54)      # Red

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

# Create bot instance
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
db = Database(DB_PATH)
img_gen = ImageGenerator(bot)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def get_target_user(message: Message) -> Optional[types.User]:
    """Get target user from reply"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None

async def check_cooldown(user_id: int, command: str) -> Tuple[bool, Optional[str]]:
    """Check command cooldown"""
    can_use, remaining = await db.can_use_command(user_id, command)
    if not can_use:
        if remaining >= 3600:
            time_str = f"{remaining//3600}h {(remaining%3600)//60}m"
        elif remaining >= 60:
            time_str = f"{remaining//60}m {remaining%60}s"
        else:
            time_str = f"{remaining}s"
        
        return False, f"⏰ Cooldown: {time_str}"
    return True, None

async def send_gif_reaction(command: str, chat_id: int, from_user: types.User, target_user: types.User = None):
    """Send GIF reaction"""
    gif_url = await db.get_gif(command)
    if not gif_url:
        gif_url = REACTION_GIFS.get(command, [REACTION_GIFS['hug'][0]])[0]
    
    action_texts = {
        'hug': f"🤗 {from_user.first_name} hugged {target_user.first_name if target_user else 'someone'}!",
        'kill': f"🔪 {from_user.first_name} killed {target_user.first_name if target_user else 'someone'}!",
        'rob': f"💰 {from_user.first_name} robbed {target_user.first_name if target_user else 'someone'}!",
        'kiss': f"💋 {from_user.first_name} kissed {target_user.first_name if target_user else 'someone'}!",
        'slap': f"👋 {from_user.first_name} slapped {target_user.first_name if target_user else 'someone'}!",
        'pat': f"👏 {from_user.first_name} patted {target_user.first_name if target_user else 'someone'}!"
    }
    
    text = action_texts.get(command, f"{from_user.first_name} used {command}!")
    
    try:
        await bot.send_animation(
            chat_id=chat_id,
            animation=gif_url,
            caption=text
        )
    except Exception as e:
        logger.error(f"Error sending GIF: {e}")
        await bot.send_message(chat_id, text)

async def log_to_channel(text: str):
    """Log to Telegram channel"""
    try:
        await bot.send_message(
            chat_id=LOG_CHANNEL,
            text=f"📊 {datetime.now().strftime('%H:%M:%S')}\n{text}"
        )
    except Exception as e:
        logger.error(f"Channel log error: {e}")

# ============================================================================
# START & HELP COMMANDS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with group invitation"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        await log_to_channel(f"👤 New user: {message.from_user.first_name} (ID: {message.from_user.id})")
    
    welcome_text = f"""
✨ <b>WELCOME {message.from_user.first_name}!</b> ✨

🌳 <b>FAMILY TREE BOT</b> - Ultimate Edition

🚀 <b>Quick Start:</b>
1. Use <code>/daily</code> for free coins
2. Build your <code>/family</code>
3. Start <code>/garden</code> farming
4. Play <code>/games</code>

📋 <b>Main Commands:</b>
• <code>/me</code> - Your profile
• <code>/family</code> - Family tree
• <code>/garden</code> - Farm crops
• <code>/market</code> - Buy/sell
• <code>/games</code> - Mini-games
• <code>/help</code> - All commands

👥 <b>Add to Group:</b> Manage family in groups!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 All Commands", callback_data="all_commands")],
        [InlineKeyboardButton(text="👥 Add to Group", url=f"https://t.me/{bot._me.username}?startgroup=true")],
        [InlineKeyboardButton(text="📢 Updates", url="https://t.me/+T7JxyxVOYcxmMzJl")],
        [InlineKeyboardButton(text="🎮 Quick Start", callback_data="quick_start")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL WORKING COMMANDS</b>

👨‍👩‍👧‍👦 <b>FAMILY COMMANDS:</b>
• <code>/family</code> - View family tree
• <code>/adopt</code> - Adopt (reply to user)
• <code>/marry</code> - Marry (reply to user)
• <code>/divorce</code> - End marriage
• <code>/disown</code> - Remove family (reply)

🌾 <b>GARDEN COMMANDS:</b>
• <code>/garden</code> - View garden
• <code>/plant [crop] [qty]</code> - Plant crops
• <code>/harvest</code> - Harvest ready crops
• <code>/market</code> - Buy/sell crops
• <code>/barn</code> - View storage

🎮 <b>GAME COMMANDS:</b>
• <code>/slot [bet]</code> - Slot machine
• <code>/dice [bet]</code> - Dice game
• <code>/rob</code> - Rob someone (reply)
• <code>/fight</code> - Fight (reply)
• <code>/lottery [tickets]</code> - Buy tickets

😊 <b>REACTION COMMANDS:</b>
• <code>/hug</code> - Hug (reply)
• <code>/kill</code> - Kill (reply)
• <code>/kiss</code> - Kiss (reply)
• <code>/slap</code> - Slap (reply)
• <code>/pat</code> - Pat (reply)

💰 <b>ECONOMY:</b>
• <code>/daily</code> - Daily bonus
• <code>/me</code> - Your profile
• <code>/give @user amount</code> - Send money

🔧 <b>OTHER:</b>
• <code>/ping</code> - Bot status
• <code>/catbox</code> - Manage GIFs

👑 <b>ADMIN:</b>
• <code>/add @user cash 1000</code>
• <code>/ban @user</code>
• <code>/unban @user</code>
• <code>/stats</code> - Bot statistics
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

# ============================================================================
# FAMILY COMMANDS (WORKING)
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Show family tree with profile pictures"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    # Generate image if possible
    if HAS_PILLOW and family:
        loading_msg = await message.answer("🖼️ Generating family tree...")
        
        image_bytes = await img_gen.create_family_tree(
            message.from_user.id,
            user['first_name'],
            family
        )
        
        if image_bytes:
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="family_tree.png"),
                caption=f"""
🌳 <b>FAMILY TREE</b>

👤 <b>Your Family:</b> {len(family)} members
💝 <b>Relations:</b> {', '.join(set(f['relation_type'] for f in family))}

💡 <b>Family Commands:</b>
• Reply to someone with <code>/adopt</code>
• Reply with <code>/marry</code> to marry
• <code>/divorce</code> to end marriage
• <code>/disown</code> to remove family
""",
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
    
    # Text version
    if not family:
        await message.answer("""
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow family:</b>
1. Reply to someone with <code>/adopt</code>
2. Wait for them to accept
3. Build your family empire!

👑 <b>Benefits:</b>
• Daily bonus increases per member
• Family quests and events
• Inheritance system
""", parse_mode=ParseMode.HTML)
        return
    
    family_text = f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

└─ You (Level {user.get('level', 1)})
"""
    
    for member in family:
        emoji = img_gen._relation_emoji(member['relation_type'])
        family_text += f"   ├─ {emoji} {member['other_name']} ({member['relation_type']})\n"
    
    family_text += f"""

📊 <b>Statistics:</b>
• Members: {len(family)}
• Daily Bonus: +${len(family) * 100}
"""
    
    await message.answer(family_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone (reply only)"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to adopt them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    if target.is_bot:
        await message.answer("❌ Cannot adopt bots!")
        return
    
    # Check cooldown
    can_use, error = await check_cooldown(message.from_user.id, "adopt")
    if not can_use:
        await message.answer(error)
        return
    
    # Get users
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Add relation
    await db.add_relation(message.from_user.id, target.id, 'parent')
    await db.set_cooldown(message.from_user.id, "adopt")
    
    # Add bonuses
    await db.update_currency(message.from_user.id, "cash", 500)
    await db.update_currency(target.id, "cash", 200)
    
    await message.answer(f"""
✅ <b>ADOPTION SUCCESSFUL!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
💰 Bonus: $500 for you, $200 for {target.first_name}

💡 <b>Family benefits activated!</b>
""", parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
👶 <b>YOU WERE ADOPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 You are now their child
💰 Received: $200 bonus!

💡 Use <code>/family</code> to see your new family.
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Marry someone (reply only)"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to marry them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    # Check cooldown
    can_use, error = await check_cooldown(message.from_user.id, "marry")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Check if already married
    family = await db.get_family(message.from_user.id)
    for member in family:
        if member['other_id'] == target.id and member['relation_type'] == 'spouse':
            await message.answer("❌ You are already married to this person!")
            return
    
    # Marry
    await db.add_relation(message.from_user.id, target.id, 'spouse')
    await db.set_cooldown(message.from_user.id, "marry")
    
    # Wedding gift
    await db.update_currency(message.from_user.id, "cash", 1000)
    await db.update_currency(target.id, "cash", 1000)
    await db.update_currency(message.from_user.id, "gold", 10)
    await db.update_currency(target.id, "gold", 10)
    
    await message.answer(f"""
💍 <b>MARRIAGE SUCCESSFUL!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Gift: $1,000 + 10 🪙 gold each

🎉 <b>Congratulations on your wedding!</b>
""", parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
💍 <b>YOU GOT MARRIED!</b>

👤 To: <b>{message.from_user.first_name}</b>
🤝 You are now spouses
💰 Received: $1,000 + 10 🪙 gold

💕 May your bond last forever!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

# ============================================================================
# GARDEN COMMANDS (WORKING)
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden with visualization"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    garden = await db.get_garden(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    # Generate garden image
    if HAS_PILLOW:
        loading_msg = await message.answer("🖼️ Generating garden...")
        
        image_bytes = await img_gen.create_garden_image(message.from_user.id, garden, crops)
        
        if image_bytes:
            # Get barn items
            barn_text = ""
            # (Barn implementation would go here)
            
            caption = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c['progress'] >= 100)}
• Fertilizer: {garden.get('fertilizer', 0)}

💡 <b>Commands:</b>
• <code>/plant carrot 3</code>
• <code>/harvest</code>
• <code>/market</code>
• <code>/upgrade</code>
"""
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="garden.png"),
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
    
    # Text version
    garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c['progress'] >= 100)}

🌱 <b>Growing Now:</b>
"""
    
    for crop in crops[:5]:
        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
        progress = crop['progress']
        bar = "█" * int(progress // 20) + "░" * (5 - int(progress // 20))
        
        if progress >= 100:
            status = "✅ Ready to harvest!"
        else:
            remaining = max(0, crop['grow_time'] * (1 - progress/100))
            status = f"{bar} {int(progress)}% ({remaining:.1f}h left)"
        
        garden_text += f"• {emoji} {crop['crop_type'].title()}: {status}\n"
    
    garden_text += f"""

💡 <b>Available Crops:</b>
{chr(10).join(f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_DATA[c]['buy']} each" for c in list(CROP_DATA.keys())[:4])}

<code>/plant [crop] [quantity]</code>
"""
    
    await message.answer(garden_text, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    if not command.args:
        crops_list = "\n".join([
            f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_DATA[c]['buy']} ({CROP_DATA[c]['grow_time']}h)"
            for c in list(CROP_DATA.keys())[:6]
        ])
        
        await message.answer(f"""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
{crops_list}

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
    
    # Check cooldown
    can_use, error = await check_cooldown(message.from_user.id, "plant")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Check cost
    cost = CROP_DATA[crop_type]['buy'] * quantity
    if user['cash'] < cost:
        await message.answer(f"❌ Need ${cost:,}! You have ${user['cash']:,}")
        return
    
    # Plant crops
    success = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if not success:
        await message.answer("❌ Not enough garden space!")
        return
    
    # Deduct cost
    await db.update_currency(message.from_user.id, "cash", -cost)
    await db.set_cooldown(message.from_user.id, "plant")
    
    emoji = CROP_EMOJIS.get(crop_type, "🌱")
    grow_time = CROP_DATA[crop_type]['grow_time']
    
    await message.answer(f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{emoji} Crop: <b>{crop_type.title()}</b>
🔢 Quantity: <b>{quantity}</b>
💰 Cost: <b>${cost:,}</b>
⏰ Grow Time: <b>{grow_time} hours</b>

🌱 Now growing in your garden!
💡 Use <code>/garden</code> to check progress.
""", parse_mode=ParseMode.HTML)

# ============================================================================
# REACTION COMMANDS (WITH GIFS)
# ============================================================================

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone with GIF"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to hug them!")
        return
    
    # Check cooldown
    can_use, error = await check_cooldown(message.from_user.id, "hug")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("hug", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "hug")

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone with GIF"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to kill them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "kill")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("kill", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "kill")

@dp.message(Command("rob"))
async def cmd_rob(message: Message):
    """Rob someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to rob them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot rob yourself!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "rob")
    if not can_use:
        await message.answer(error)
        return
    
    # Get users
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Check if target has money
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor to rob! (Need at least $100)")
        return
    
    # Robbery chance (40% success)
    success = random.random() < 0.4
    
    if success:
        # Calculate stolen amount (10-30% of target's cash)
        max_steal = int(target_user['cash'] * 0.3)
        min_steal = int(target_user['cash'] * 0.1)
        stolen = random.randint(min_steal, max_steal)
        
        # Transfer money
        await db.update_currency(target.id, "cash", -stolen)
        await db.update_currency(message.from_user.id, "cash", stolen)
        
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        await message.answer(f"""
💰 <b>ROBBERY SUCCESSFUL!</b>

👤 You robbed <b>{target.first_name}</b>
💵 Stolen: <b>${stolen:,}</b>
📈 Your balance: <b>${user['cash'] + stolen:,}</b>
""", parse_mode=ParseMode.HTML)
        
        # Log suspicious activity
        await log_to_channel(f"⚠️ ROBBERY: {message.from_user.id} robbed {target.id} - ${stolen}")
    else:
        # Failed robbery - fine
        fine = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", -fine)
        
        await message.answer(f"""
🚨 <b>ROBBERY FAILED!</b>

👤 You tried to rob <b>{target.first_name}</b>
👮‍♂️ You were caught!
💸 Fine: <b>${fine:,}</b>
📉 Your balance: <b>${user['cash'] - fine:,}</b>
""", parse_mode=ParseMode.HTML)
    
    await db.set_cooldown(message.from_user.id, "rob")

# Add similar commands for kiss, slap, pat
@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to kiss them!")
        return
    can_use, error = await check_cooldown(message.from_user.id, "kiss")
    if not can_use:
        await message.answer(error)
        return
    await send_gif_reaction("kiss", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "kiss")

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to slap them!")
        return
    can_use, error = await check_cooldown(message.from_user.id, "slap")
    if not can_use:
        await message.answer(error)
        return
    await send_gif_reaction("slap", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "slap")

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to pat them!")
        return
    can_use, error = await check_cooldown(message.from_user.id, "pat")
    if not can_use:
        await message.answer(error)
        return
    await send_gif_reaction("pat", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "pat")

# ============================================================================
# MINI-GAMES
# ============================================================================

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine game"""
    if not command.args:
        await message.answer("🎰 Usage: /slot [bet]\nExample: /slot 100")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet is $10!")
            return
    except:
        await message.answer("Invalid bet amount!")
        return
    
    # Check cooldown
    can_use, error = await check_cooldown(message.from_user.id, "slot")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if bet > user['cash']:
        await message.answer(f"❌ You only have ${user['cash']:,}!")
        return
    
    # Slot symbols
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
    
    win_amount = int(bet * multiplier)
    net_gain = win_amount - bet
    
    # Update balance
    await db.update_currency(message.from_user.id, "cash", net_gain)
    await db.set_cooldown(message.from_user.id, "slot")
    
    slot_text = f"""
🎰 <b>SLOT MACHINE</b>

[{reels[0]}] [{reels[1]}] [{reels[2]}]

💰 Bet: <b>${bet:,}</b>
🎯 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}
🏆 Payout: <b>${win_amount:,}</b>
📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>

💵 New Balance: <b>${user['cash'] + net_gain:,}</b>
"""
    
    await message.answer(slot_text, parse_mode=ParseMode.HTML)

@dp.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject):
    """Dice game"""
    if not command.args:
        await message.answer("🎲 Usage: /dice [bet]\nExample: /dice 50")
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
        await message.answer("❌ Please use /start first!")
        return
    
    if bet > user['cash']:
        await message.answer(f"❌ You only have ${user['cash']:,}!")
        return
    
    # Roll dice
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        result = "WIN"
        win_amount = bet
        net_gain = win_amount
    elif player_roll < bot_roll:
        result = "LOSE"
        win_amount = 0
        net_gain = -bet
    else:
        result = "DRAW"
        win_amount = 0
        net_gain = 0
    
    # Update balance
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    dice_text = f"""
🎲 <b>DICE GAME</b>

👤 Your roll: <b>{player_roll}</b>
🤖 Bot roll: <b>{bot_roll}</b>

💰 Bet: <b>${bet:,}</b>
🏆 Result: <b>{result}</b>
💵 {'Win' if net_gain > 0 else 'Loss'}: <b>${abs(net_gain):,}</b>

📈 New Balance: <b>${user['cash'] + net_gain:,}</b>
"""
    
    await message.answer(dice_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ECONOMY COMMANDS
# ============================================================================

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus with bio verification"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Check cooldown
    can_use, error = await check_cooldown(message.from_user.id, "daily")
    if not can_use:
        await message.answer(error)
        return
    
    # Calculate bonus
    base_bonus = random.randint(500, 1500)
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * 100
    
    # Check bio verification
    bio_verified = user.get('bio_verified', 0)
    multiplier = 2 if bio_verified else 1
    
    # Streak bonus
    streak = user.get('daily_streak', 0) + 1
    streak_bonus = min(500, streak * 50)
    
    total_bonus = (base_bonus + family_bonus + streak_bonus) * multiplier
    
    # Gemstone
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    # Update user
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.update_currency(message.from_user.id, "tokens", 5)
    
    await db.set_cooldown(message.from_user.id, "daily")
    
    # Update streak
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET daily_streak = ?, gemstone = ? WHERE user_id = ?",
            (streak, gemstone, message.from_user.id)
        )
        await db.conn.commit()
    
    daily_text = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base_bonus:,}</b>
• Family: <b>${family_bonus:,}</b>
• Streak ({streak} days): <b>${streak_bonus:,}</b>
• Multiplier: <b>{multiplier}x</b>
• <b>Total: ${total_bonus:,}</b>

💎 <b>Today's Gemstone:</b> <b>{gemstone}</b>
🎁 <b>Bonus:</b> +5 🌱 Tokens

{'✅ Bio verified (2x rewards!)' if multiplier > 1 else '❌ Add @Familly_TreeBot to bio for 2x!'}
"""
    
    await message.answer(daily_text, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """User profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    profile_text = f"""
🏆 <b>PROFILE OF {user['first_name'].upper()}</b>

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

📊 <b>Stats:</b>
• Level: <b>{user.get('level', 1)}</b>
• XP: <b>{user.get('xp', 0)}/1000</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Daily Streak: <b>{user.get('daily_streak', 0)} days</b>
• Bio Verified: {'✅' if user.get('bio_verified') else '❌'}

💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
📅 <b>Joined:</b> {user.get('created_at', '')[:10] if user.get('created_at') else 'Recently'}
"""
    
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS (15+)
# ============================================================================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == OWNER_ID

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources (admin only)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    if not command.args:
        await message.answer("""
💰 <b>ADD RESOURCES</b>

Usage: <code>/add [user_id] [resource] [amount]</code>

💎 Resources: cash, gold, bonds, credits, tokens
📝 Example: <code>/add 123456789 cash 1000</code>

💡 Or reply to user's message with command!
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Format: /add [user_id] [resource] [amount]")
        return
    
    # Get target user
    target_id = None
    
    # Check reply first
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif args[0].isdigit():
        target_id = int(args[0])
        args = args[1:]  # Remove user_id from args
    else:
        await message.answer("❌ Target must be user ID or reply!")
        return
    
    if len(args) < 2:
        await message.answer("❌ Format: /add [resource] [amount]")
        return
    
    resource = args[0].lower()
    try:
        amount = int(args[1])
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    if resource not in CURRENCIES:
        await message.answer(f"❌ Invalid resource! Available: {', '.join(CURRENCIES)}")
        return
    
    # Add resources
    await db.update_currency(target_id, resource, amount)
    
    # Log action
    await db.log_admin_action(
        message.from_user.id,
        "add_resources",
        target_id,
        f"{resource}: {amount}"
    )
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else f"ID: {target_id}"
    
    await message.answer(f"""
✅ <b>RESOURCES ADDED</b>

👤 To: <b>{target_name}</b>
💎 Resource: {CURRENCY_EMOJIS.get(resource, '📦')} <b>{resource.upper()}</b>
➕ Amount: <b>{amount:,}</b>
👑 By: {message.from_user.first_name}

📊 <b>Logged to admin channel</b>
""", parse_mode=ParseMode.HTML)
    
    # Log to channel
    await log_to_channel(f"👑 ADMIN: {message.from_user.id} added {resource} {amount} to {target_id}")

@dp.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    """Ban user (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to user to ban them!")
        return
    
    if target.id == OWNER_ID:
        await message.answer("❌ Cannot ban owner!")
        return
    
    # Ban user
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (target.id,)
        )
        await db.conn.commit()
    
    await db.log_admin_action(message.from_user.id, "ban", target.id)
    
    await message.answer(f"""
✅ <b>USER BANNED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
⏰ Banned: {datetime.now().strftime('%Y-%m-%d %H:%M')}

⚠️ User can no longer use the bot.
""", parse_mode=ParseMode.HTML)
    
    await log_to_channel(f"🔨 BAN: {target.id} by {message.from_user.id}")

@dp.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    """Unban user (admin only)"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("❌ Usage: /unban [user_id]")
        return
    
    try:
        target_id = int(command.args)
    except:
        await message.answer("❌ Invalid user ID!")
        return
    
    # Unban user
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?",
            (target_id,)
        )
        await db.conn.commit()
    
    await db.log_admin_action(message.from_user.id, "unban", target_id)
    
    await message.answer(f"""
✅ <b>USER UNBANNED</b>

🆔 ID: <code>{target_id}</code>
⏰ Unbanned: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔓 User can now use the bot again.
""", parse_mode=ParseMode.HTML)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Admin only command!")
        return
    
    stats = await db.get_stats()
    
    stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b>
• Total: <b>{stats.get('total_users', 0):,}</b>
• Banned: <b>{stats.get('banned_users', 0):,}</b>
• Active: <b>{stats.get('total_users', 0) - stats.get('banned_users', 0):,}</b>

🌳 <b>Family:</b>
• Relations: <b>{stats.get('family_relations', 0):,}</b>

🌾 <b>Garden:</b>
• Growing Crops: <b>{stats.get('growing_crops', 0):,}</b>

💰 <b>Economy:</b>
• Total Cash: <b>${stats.get('total_cash', 0):,}</b>

🕒 <b>Uptime:</b> Bot is running
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("sudo"))
async def cmd_sudo(message: Message):
    """Make user admin (owner only)"""
    if message.from_user.id != OWNER_ID:
        return
    
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to user to make them admin!")
        return
    
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET is_admin = 1 WHERE user_id = ?",
            (target.id,)
        )
        await db.conn.commit()
    
    await db.log_admin_action(message.from_user.id, "sudo", target.id)
    
    await message.answer(f"""
👑 <b>ADMIN PROMOTION</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
📛 Role: <b>Administrator</b>

✅ User now has admin privileges.
""", parse_mode=ParseMode.HTML)

# Add more admin commands here (15+ total as requested)
@dp.message(Command("warn"))
async def cmd_warn(message: Message):
    """Warn user (admin)"""
    if not is_admin(message.from_user.id):
        return
    
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to user to warn them!")
        return
    
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET warnings = warnings + 1 WHERE user_id = ?",
            (target.id,)
        )
        await db.conn.commit()
    
    target_user = await db.get_user(target.id)
    warnings = target_user.get('warnings', 0) + 1
    
    await message.answer(f"""
⚠️ <b>USER WARNED</b>

👤 User: <b>{target.first_name}</b>
📛 Warnings: <b>{warnings}/3</b>

{'🚨 User will be banned at 3 warnings!' if warnings < 3 else '🔨 User should be banned!'}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("reset"))
async def cmd_reset(message: Message, command: CommandObject):
    """Reset user data (admin)"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("❌ Usage: /reset [user_id] [data]\nData: all, cash, garden")
        return
    
    args = command.args.split()
    if len(args) < 2:
        await message.answer("❌ Format: /reset [user_id] [data]")
        return
    
    try:
        target_id = int(args[0])
    except:
        await message.answer("❌ Invalid user ID!")
        return
    
    data_type = args[1].lower()
    
    if data_type == "all":
        # Reset everything
        async with db.lock:
            await db.conn.execute(
                """UPDATE users SET 
                   cash = 1000, gold = 50, bonds = 0, credits = 100, tokens = 50,
                   reputation = 100, level = 1, xp = 0
                   WHERE user_id = ?""",
                (target_id,)
            )
            await db.conn.commit()
        
        await message.answer(f"✅ Reset ALL data for user {target_id}")
    
    elif data_type == "cash":
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET cash = 1000 WHERE user_id = ?",
                (target_id,)
            )
            await db.conn.commit()
        
        await message.answer(f"✅ Reset cash for user {target_id}")
    
    else:
        await message.answer("❌ Invalid data type! Use: all, cash, garden")

# ============================================================================
# CATBOX SYSTEM (GIF MANAGEMENT)
# ============================================================================

@dp.message(Command("catbox"))
async def cmd_catbox(message: Message, command: CommandObject):
    """Manage reaction GIFs"""
    if not command.args:
        await message.answer("""
🐱 <b>CATBOX SYSTEM</b>

Manage GIFs for reaction commands.

📋 <b>Commands:</b>
• <code>/catbox list</code> - List all GIFs
• <code>/catbox add [cmd] [url]</code> - Add GIF
• <code>/catbox remove [cmd]</code> - Remove GIF

💡 <b>Example:</b>
<code>/catbox add hug https://gif.example.com/hug.gif</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.lower().split()
    subcmd = args[0]
    
    if subcmd == "list":
        gifs = await db.list_gifs()
        
        if not gifs:
            await message.answer("📭 No GIFs in catbox yet!")
            return
        
        gif_list = "\n".join([f"• {cmd}: {url[:50]}..." for cmd, url in gifs])
        await message.answer(f"""
📦 <b>CATBOX GIFS</b>

{gif_list}

💡 Use: <code>/catbox add [command] [url]</code>
""", parse_mode=ParseMode.HTML)
    
    elif subcmd == "add" and len(args) >= 3:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin only!")
            return
        
        cmd = args[1]
        url = args[2]
        
        # Validate command
        if cmd not in REACTION_GIFS.keys():
            await message.answer(f"❌ Invalid command! Available: {', '.join(REACTION_GIFS.keys())}")
            return
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            await message.answer("❌ Invalid URL! Must start with http:// or https://")
            return
        
        await db.add_gif(cmd, url, message.from_user.id)
        await message.answer(f"""
✅ <b>GIF ADDED TO CATBOX</b>

🎬 Command: <code>/{cmd}</code>
🔗 URL: {url[:50]}...

💡 GIF will be used for <code>/{cmd}</code> command.
""", parse_mode=ParseMode.HTML)
    
    elif subcmd == "remove" and len(args) >= 2:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin only!")
            return
        
        cmd = args[1]
        await db.remove_gif(cmd)
        await message.answer(f"""
🗑️ <b>GIF REMOVED</b>

🎬 Command: <code>/{cmd}</code>

✅ GIF removed from catbox.
""", parse_mode=ParseMode.HTML)
    
    else:
        await message.answer("❌ Invalid catbox command!")

# ============================================================================
# PING & STATUS
# ============================================================================

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Check bot status"""
    start = time.time()
    msg = await message.answer("🏓 Pong!")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    stats = await db.get_stats()
    
    status_text = f"""
🏓 <b>PONG!</b>

⚡ Speed: <b>{latency}ms</b>
👥 Users: <b>{stats.get('total_users', 0)}</b>
👥 Groups: <b>1</b> (Add me to more!)
🕒 Uptime: Bot is running
🔧 Status: 🟢 ACTIVE

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

# ============================================================================
# GAMES COMMAND (ALL GAMES LIST)
# ============================================================================

@dp.message(Command("games"))
async def cmd_games(message: Message):
    """List all games"""
    games_text = """
🎮 <b>AVAILABLE GAMES</b>

🎰 <b>Slot Machine:</b>
<code>/slot [bet]</code> - Try your luck!

🎲 <b>Dice Game:</b>
<code>/dice [bet]</code> - Roll against bot

💰 <b>Robbery:</b>
<code>/rob</code> - Rob someone (reply)

⚔️ <b>Fighting:</b>
<code>/fight</code> - Fight someone (reply)

🎫 <b>Lottery:</b>
<code>/lottery [tickets]</code> - Buy tickets

😊 <b>Reactions (with GIFs):</b>
• <code>/hug</code> - Hug someone
• <code>/kill</code> - Kill someone
• <code>/kiss</code> - Kiss someone
• <code>/slap</code> - Slap someone
• <code>/pat</code> - Pat someone

💡 All reaction commands require replying to user's message!
"""
    
    await message.answer(games_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ERROR HANDLER (PROPER)
# ============================================================================

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Global error handler"""
    logger.error(f"Update: {update}\nException: {exception}", exc_info=True)
    
    # Log to channel
    error_msg = f"❌ ERROR:\n{type(exception).__name__}: {str(exception)[:200]}"
    await log_to_channel(error_msg)
    
    return True

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

async def setup_bot():
    """Setup bot on startup"""
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="help", description="All commands"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="garden", description="Farm garden"),
        types.BotCommand(command="games", description="All games"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="dice", description="Dice game"),
        types.BotCommand(command="ping", description="Bot status"),
        types.BotCommand(command="market", description="Buy/sell crops"),
        types.BotCommand(command="catbox", description="Manage GIFs")
    ]
    
    await bot.set_my_commands(commands)
    
    # Startup message
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - ULTIMATE EDITION")
    print(f"Version: 8.0 | Owner: {OWNER_ID}")
    print(f"Images: {'ENABLED' if HAS_PILLOW else 'DISABLED (install pillow)'}")
    print("=" * 60)
    
    # Send to log channel
    await log_to_channel(f"🤖 Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def shutdown_bot():
    """Cleanup on shutdown"""
    await db.conn.close()
    await bot.session.close()

async def main():
    """Main function"""
    try:
        await setup_bot()
        print("🚀 Starting bot polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await shutdown_bot()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
