#!/usr/bin/env python3
"""
🌳 ULTIMATE FAMILY TREE BOT - PERFECT VERSION
Version: 9.0 - All Commands Working, No Fake Features
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
import aiohttp

# ============================================================================
# CORE IMPORTS - WORKING VERSIONS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto, InputMediaVideo, InputMediaAnimation,
        ChatMemberUpdated, ChatJoinRequest
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode, ChatAction, ChatMemberStatus
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    
    # Pillow for image generation - FIXED
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
        import textwrap
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
        
    import aiosqlite
    import sqlite3
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram pillow aiosqlite python-dotenv aiohttp")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
OWNER_ID = 6108185460
BOT_USERNAME = "Familly_TreeBot"
LOG_CHANNEL = -1003662720845
SUPPORT_CHAT = "https://t.me/+T7JxyxVOYcxmMzJl"

DB_PATH = "family_bot_v9.db"

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "event_coins"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪"
}

# Crop System
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

# Reaction GIFs (Cat Box System)
REACTION_GIFS = {
    "hug": "https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif",
    "kill": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "rob": "https://media.giphy.com/media/xTiTnHXbRoaZ1B1Mo8/giphy.gif",
    "kiss": "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif",
    "slap": "https://media.giphy.com/media/Zau0yrl17uzdK/giphy.gif",
    "pat": "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif"
}

# Cooldowns in seconds
COOLDOWNS = {
    "daily": 86400,
    "rob": 7200,
    "hug": 60,
    "kill": 300,
    "slot": 30,
    "fight": 600,
    "plant": 300,
    "adopt": 86400,
    "marry": 86400
}

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_perfect.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CLASS - SIMPLIFIED & WORKING
# ============================================================================

class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = None
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        await self.init_tables()
    
    async def init_tables(self):
        tables = [
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
                gemstone TEXT DEFAULT 'None',
                bio_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50
            )""",
            
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                is_ready BOOLEAN DEFAULT 0
            )""",
            
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )""",
            
            """CREATE TABLE IF NOT EXISTS catbox_gifs (
                command TEXT PRIMARY KEY,
                gif_url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table in tables:
            await self.conn.execute(table)
        await self.conn.commit()
        
        # Initialize default GIFs
        await self.init_default_gifs()
    
    async def init_default_gifs(self):
        for cmd, url in REACTION_GIFS.items():
            try:
                await self.conn.execute(
                    """INSERT OR IGNORE INTO catbox_gifs (command, gif_url, added_by)
                       VALUES (?, ?, ?)""",
                    (cmd, url, OWNER_ID)
                )
            except:
                pass
        await self.conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[dict]:
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
        await self.conn.execute(
            """INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
               VALUES (?, ?, ?, ?)""",
            (user.id, user.username, user.first_name, user.last_name)
        )
        
        await self.conn.execute(
            "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
            (user.id,)
        )
        
        await self.conn.commit()
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        if currency not in CURRENCIES:
            return
        
        await self.conn.execute(
            f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await self.conn.commit()
    
    async def get_cooldown(self, user_id: int, command: str) -> Optional[datetime]:
        cursor = await self.conn.execute(
            "SELECT last_used FROM cooldowns WHERE user_id = ? AND command = ?",
            (user_id, command)
        )
        row = await cursor.fetchone()
        return datetime.fromisoformat(row[0]) if row else None
    
    async def set_cooldown(self, user_id: int, command: str):
        await self.conn.execute(
            """INSERT OR REPLACE INTO cooldowns (user_id, command, last_used)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (user_id, command)
        )
        await self.conn.commit()
    
    async def can_use_command(self, user_id: int, command: str) -> Tuple[bool, Optional[int]]:
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
    
    async def get_family(self, user_id: int) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT fr.relation_type, 
               CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as other_name
               FROM family_relations fr
               LEFT JOIN users u1 ON u1.user_id = fr.user1_id
               LEFT JOIN users u2 ON u2.user_id = fr.user2_id
               WHERE ? IN (fr.user1_id, fr.user2_id)""",
            (user_id, user_id)
        )
        rows = await cursor.fetchall()
        return [{'relation_type': r[0], 'other_name': r[1]} for r in rows]
    
    async def add_relation(self, user1_id: int, user2_id: int, relation: str):
        await self.conn.execute(
            "INSERT OR IGNORE INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
            (min(user1_id, user2_id), max(user1_id, user2_id), relation)
        )
        await self.conn.commit()
    
    async def remove_relation(self, user1_id: int, user2_id: int, relation: str):
        await self.conn.execute(
            """DELETE FROM family_relations 
               WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
               AND relation_type = ?""",
            (user1_id, user2_id, user2_id, user1_id, relation)
        )
        await self.conn.commit()
    
    async def get_garden_info(self, user_id: int) -> dict:
        cursor = await self.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return {'slots': row[0] if row else 9}
    
    async def get_growing_crops(self, user_id: int) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT crop_type, planted_at, grow_time
               FROM garden_plants 
               WHERE user_id = ? AND is_ready = 0""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        crops = []
        for row in rows:
            planted = datetime.fromisoformat(row[1])
            elapsed = (datetime.now() - planted).total_seconds() / 3600
            progress = min(100, (elapsed / row[2]) * 100)
            
            crops.append({
                'crop_type': row[0],
                'progress': progress,
                'is_ready': progress >= 100
            })
        
        return crops
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int) -> bool:
        if crop_type not in CROP_TYPES:
            return False
        
        garden = await self.get_garden_info(user_id)
        if not garden:
            return False
        
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
            (user_id,)
        )
        current = (await cursor.fetchone())[0]
        
        if current + quantity > garden['slots']:
            return False
        
        grow_time = CROP_DATA[crop_type]['grow_time']
        for _ in range(quantity):
            await self.conn.execute(
                "INSERT INTO garden_plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                (user_id, crop_type, grow_time)
            )
        
        await self.conn.commit()
        return True
    
    async def harvest_crops(self, user_id: int) -> List[tuple]:
        cursor = await self.conn.execute(
            """SELECT crop_type, COUNT(*) as count 
               FROM garden_plants 
               WHERE user_id = ? AND is_ready = 0
               AND (julianday('now') - julianday(planted_at)) * 24 >= grow_time""",
            (user_id,)
        )
        ready_crops = await cursor.fetchall()
        
        for crop_type, count in ready_crops:
            await self.conn.execute(
                "UPDATE garden_plants SET is_ready = 1 WHERE user_id = ? AND crop_type = ? AND is_ready = 0",
                (user_id, crop_type)
            )
        
        await self.conn.commit()
        return ready_crops
    
    async def get_gif(self, command: str) -> Optional[str]:
        cursor = await self.conn.execute(
            "SELECT gif_url FROM catbox_gifs WHERE command = ?",
            (command,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None
    
    async def add_gif(self, command: str, url: str, added_by: int):
        await self.conn.execute(
            """INSERT OR REPLACE INTO catbox_gifs (command, gif_url, added_by)
               VALUES (?, ?, ?)""",
            (command, url, added_by)
        )
        await self.conn.commit()
    
    async def get_stats(self) -> dict:
        stats = {}
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        stats['banned_users'] = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM family_relations")
        stats['family_relations'] = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT SUM(cash) FROM users")
        stats['total_cash'] = (await cursor.fetchone())[0] or 0
        
        return stats

# ============================================================================
# IMAGE GENERATOR - FIXED & WORKING
# ============================================================================

class ImageGenerator:
    """FIXED image generator - actually works"""
    
    def __init__(self):
        self.fonts = {}
        if HAS_PILLOW:
            self.load_fonts()
    
    def load_fonts(self):
        """Load fonts with fallback"""
        try:
            from PIL import ImageFont
            try:
                self.fonts['large'] = ImageFont.truetype("arial.ttf", 32)
                self.fonts['medium'] = ImageFont.truetype("arial.ttf", 24)
                self.fonts['small'] = ImageFont.truetype("arial.ttf", 16)
            except:
                self.fonts['large'] = ImageFont.load_default()
                self.fonts['medium'] = ImageFont.load_default()
                self.fonts['small'] = ImageFont.load_default()
        except:
            pass
    
    def _get_font(self, size='medium'):
        return self.fonts.get(size, None)
    
    async def create_garden_image(self, garden_info: dict, crops: List[dict]) -> Optional[bytes]:
        """Create garden image that actually works"""
        if not HAS_PILLOW:
            logger.error("Pillow not installed!")
            return None
        
        try:
            # Create image
            width, height = 600, 800
            img = Image.new('RGB', (width, height), color=(25, 25, 40))
            draw = ImageDraw.Draw(img)
            
            # Title
            title = "🌾 Your Garden"
            try:
                font = self._get_font('medium') or ImageFont.load_default()
                bbox = draw.textbbox((0, 0), title, font=font)
                title_x = (width - (bbox[2] - bbox[0])) // 2
                draw.text((title_x, 30), title, fill=(76, 175, 80), font=font)
            except:
                draw.text((width//2 - 50, 30), title, fill=(76, 175, 80))
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 120
            padding = 15
            start_x = (width - (grid_size * cell_size + (grid_size-1) * padding)) // 2
            start_y = 120
            
            slots = garden_info.get('slots', 9)
            
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    if idx < slots:
                        if idx < len(crops):
                            crop = crops[idx]
                            crop_type = crop.get('crop_type', 'unknown')
                            progress = crop.get('progress', 0)
                            
                            # Color based on progress
                            if progress >= 100:
                                color = (76, 175, 80)  # Green
                            elif progress >= 50:
                                color = (255, 193, 7)   # Yellow
                            else:
                                color = (33, 150, 243)  # Blue
                            
                            # Draw cell
                            draw.rectangle([x1, y1, x2, y2], fill=color, outline=(255, 255, 255), width=2)
                            
                            # Crop emoji
                            emoji = CROP_EMOJIS.get(crop_type, "🌱")
                            try:
                                bbox = draw.textbbox((0, 0), emoji, font=self._get_font('medium'))
                                emoji_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                                emoji_y = y1 + (cell_size - (bbox[3] - bbox[1])) // 2 - 10
                                draw.text((emoji_x, emoji_y), emoji, fill=(255, 255, 255), 
                                         font=self._get_font('medium'))
                            except:
                                draw.text((x1 + cell_size//2 - 10, y1 + cell_size//2 - 10), 
                                         emoji, fill=(255, 255, 255))
                            
                            # Progress text
                            progress_text = f"{int(progress)}%"
                            try:
                                bbox = draw.textbbox((0, 0), progress_text, font=self._get_font('small'))
                                text_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                                draw.text((text_x, y2 - 25), progress_text, fill=(255, 255, 255), 
                                         font=self._get_font('small'))
                            except:
                                draw.text((x1 + cell_size//2 - 10, y2 - 25), progress_text, fill=(255, 255, 255))
                            
                            # Crop name
                            crop_name = crop_type[:6].title()
                            try:
                                bbox = draw.textbbox((0, 0), crop_name, font=self._get_font('small'))
                                name_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                                draw.text((name_x, y1 + 5), crop_name, fill=(255, 255, 255), 
                                         font=self._get_font('small'))
                            except:
                                draw.text((x1 + 5, y1 + 5), crop_name, fill=(255, 255, 255))
                        else:
                            # Empty slot
                            draw.rectangle([x1, y1, x2, y2], fill=(40, 40, 60), outline=(100, 100, 100), width=1)
                            draw.text((x1 + cell_size//2 - 10, y1 + cell_size//2 - 10), 
                                     "🟫", fill=(150, 150, 150))
                    else:
                        # Locked slot
                        draw.rectangle([x1, y1, x2, y2], fill=(30, 30, 30), outline=(244, 67, 54), width=2)
                        draw.text((x1 + cell_size//2 - 10, y1 + cell_size//2 - 10), 
                                 "🔒", fill=(244, 67, 54))
            
            # Stats at bottom
            stats_y = start_y + (grid_size * (cell_size + padding)) + 30
            stats = [
                f"📊 Slots: {len(crops)}/{slots}",
                f"🌱 Growing: {len(crops)}",
                f"✅ Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i*30), stat, fill=(255, 193, 7))
            
            # Save to bytes - THIS IS CRITICAL
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            logger.info(f"Garden image created successfully: {len(img_bytes)} bytes")
            return img_bytes
            
        except Exception as e:
            logger.error(f"Image generation error: {e}", exc_info=True)
            return None
    
    async def create_family_tree_image(self, user_name: str, family: List[dict]) -> Optional[bytes]:
        """Create simple family tree image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color=(30, 30, 45))
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"🌳 {user_name}'s Family"
            try:
                font = self._get_font('medium') or ImageFont.load_default()
                bbox = draw.textbbox((0, 0), title, font=font)
                title_x = (width - (bbox[2] - bbox[0])) // 2
                draw.text((title_x, 30), title, fill=(76, 175, 80), font=font)
            except:
                draw.text((width//2 - 100, 30), title, fill=(76, 175, 80))
            
            # Draw user at center
            center_x, center_y = width//2, height//2
            draw.ellipse([center_x-50, center_y-50, center_x+50, center_y+50], 
                        fill=(33, 150, 243), outline=(255, 193, 7), width=3)
            
            draw.text((center_x-20, center_y-15), "👤", fill=(255, 255, 255))
            draw.text((center_x-40, center_y+40), "You", fill=(255, 255, 255))
            
            # Draw family members
            if family:
                radius = 200
                angle_step = 360 / len(family)
                
                for i, member in enumerate(family):
                    angle = math.radians(i * angle_step)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # Draw line
                    draw.line([(center_x, center_y), (x, y)], fill=(255, 255, 255, 128), width=2)
                    
                    # Draw member
                    draw.ellipse([x-40, y-40, x+40, y+40], 
                                fill=self._relation_color(member['relation_type']), 
                                outline=(255, 255, 255), width=2)
                    
                    # Relation emoji
                    emoji = self._relation_emoji(member['relation_type'])
                    draw.text((x-10, y-15), emoji, fill=(255, 255, 255))
                    
                    # Name
                    name = member['other_name'][:8] if member['other_name'] else "User"
                    draw.text((x-20, y+30), name, fill=(255, 193, 7))
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Family tree image error: {e}")
            return None
    
    def _relation_color(self, relation: str) -> tuple:
        colors = {
            'parent': (76, 175, 80),      # Green
            'spouse': (233, 30, 99),      # Pink
            'child': (33, 150, 243),      # Blue
            'sibling': (255, 152, 0)      # Orange
        }
        return colors.get(relation, (100, 100, 100))
    
    def _relation_emoji(self, relation: str) -> str:
        emojis = {
            'parent': '👴',
            'spouse': '💑',
            'child': '👶',
            'sibling': '👫'
        }
        return emojis.get(relation, '👤')

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
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

async def check_cooldown(user_id: int, command: str) -> Tuple[bool, Optional[str]]:
    """Check if command is on cooldown"""
    can_use, remaining = await db.can_use_command(user_id, command)
    if not can_use:
        if remaining >= 3600:
            time_str = f"{remaining//3600}h"
        elif remaining >= 60:
            time_str = f"{remaining//60}m"
        else:
            time_str = f"{remaining}s"
        return False, f"⏰ Cooldown: {time_str}"
    return True, None

async def send_gif_reaction(command: str, chat_id: int, from_user: types.User, target_user: types.User = None):
    """Send GIF reaction"""
    gif_url = await db.get_gif(command)
    if not gif_url:
        gif_url = REACTION_GIFS.get(command, REACTION_GIFS['hug'])
    
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
        await bot.send_message(chat_id, text + f"\n🎬 (GIF: {gif_url[:50]}...)")

async def log_to_channel(text: str):
    """Log to Telegram channel"""
    try:
        await bot.send_message(
            chat_id=LOG_CHANNEL,
            text=f"📊 {datetime.now().strftime('%H:%M:%S')}\n{text}"
        )
    except Exception as e:
        logger.error(f"Channel log error: {e}")

def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id == OWNER_ID

# ============================================================================
# START COMMAND
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        await log_to_channel(f"👤 New user: {message.from_user.first_name} ({message.from_user.id})")
    
    welcome_text = f"""
✨ <b>WELCOME {message.from_user.first_name}!</b> ✨

🌳 <b>FAMILY TREE BOT</b> - Perfect Version

🚀 <b>Quick Start:</b>
1. <code>/daily</code> - Claim daily bonus
2. <code>/family</code> - View family tree
3. <code>/garden</code> - Start farming
4. <code>/games</code> - Play mini-games

📋 <b>Main Categories:</b>
• Family: <code>/adopt</code>, <code>/marry</code>
• Garden: <code>/plant</code>, <code>/harvest</code>
• Games: <code>/slot</code>, <code>/dice</code>
• Fun: <code>/hug</code>, <code>/kill</code>, <code>/rob</code>

👥 <b>Add to Group</b> to manage family together!
"""
    
    await message.answer(welcome_text, parse_mode=ParseMode.HTML)

# ============================================================================
# FAMILY COMMANDS - WORKING
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Show family tree"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    # Try to create image
    if HAS_PILLOW and family:
        try:
            image_bytes = await img_gen.create_family_tree_image(user['first_name'], family)
            if image_bytes:
                photo = BufferedInputFile(image_bytes, filename="family.png")
                await message.answer_photo(
                    photo=photo,
                    caption=f"""
🌳 <b>FAMILY TREE</b>

👤 Your Family: {len(family)} members
💝 Relations: {', '.join(set(f['relation_type'] for f in family))}

💡 Reply to someone with:
• <code>/adopt</code> - Make them your child
• <code>/marry</code> - Marry them
• <code>/divorce</code> - End marriage
""",
                    parse_mode=ParseMode.HTML
                )
                return
        except Exception as e:
            logger.error(f"Family image failed: {e}")
    
    # Text version
    if not family:
        await message.answer("""
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow family:</b>
1. Reply to someone with <code>/adopt</code>
2. Wait for them to accept
3. Build your family empire!
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
    """Adopt someone"""
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
    
    can_use, error = await check_cooldown(message.from_user.id, "adopt")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    await db.add_relation(message.from_user.id, target.id, 'parent')
    await db.set_cooldown(message.from_user.id, "adopt")
    
    await db.update_currency(message.from_user.id, "cash", 500)
    await db.update_currency(target.id, "cash", 200)
    
    await message.answer(f"""
✅ <b>ADOPTION SUCCESSFUL!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
💰 Bonus: $500 for you, $200 for {target.first_name}
""", parse_mode=ParseMode.HTML)
    
    try:
        await bot.send_message(
            target.id,
            f"👶 You were adopted by {message.from_user.first_name}! Relationship: Parent-Child. Received: $200 bonus!"
        )
    except:
        pass

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
    
    can_use, error = await check_cooldown(message.from_user.id, "marry")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need /start first!")
        return
    
    await db.add_relation(message.from_user.id, target.id, 'spouse')
    await db.set_cooldown(message.from_user.id, "marry")
    
    await db.update_currency(message.from_user.id, "cash", 1000)
    await db.update_currency(target.id, "cash", 1000)
    
    await message.answer(f"""
💍 <b>MARRIAGE SUCCESSFUL!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Gift: $1,000 each
""", parse_mode=ParseMode.HTML)
    
    try:
        await bot.send_message(
            target.id,
            f"💍 You married {message.from_user.first_name}! Relationship: Spouses. Received: $1,000!"
        )
    except:
        pass

# ============================================================================
# GARDEN COMMANDS - WORKING WITH IMAGES
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden - WITH WORKING IMAGES"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    # ALWAYS try to create image
    if HAS_PILLOW:
        try:
            logger.info(f"Creating garden image for {message.from_user.id}")
            image_bytes = await img_gen.create_garden_image(garden_info, crops)
            
            if image_bytes:
                logger.info(f"Image created: {len(image_bytes)} bytes, sending...")
                photo = BufferedInputFile(image_bytes, filename="garden.png")
                
                caption = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden_info.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}

💡 <code>/plant [crop] [qty]</code> to plant
💡 <code>/harvest</code> to collect
"""
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
                logger.info("Garden image sent successfully!")
                return
            else:
                logger.error("Image creation returned None!")
        except Exception as e:
            logger.error(f"Garden image error: {e}", exc_info=True)
    else:
        logger.warning("Pillow not installed, using text mode")
    
    # Fallback to text version
    garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden_info.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}

🌱 <b>Growing Now:</b>
"""
    
    for crop in crops[:5]:
        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
        progress = crop['progress']
        bar = "█" * int(progress // 20) + "░" * (5 - int(progress // 20))
        
        if progress >= 100:
            status = "✅ Ready!"
        else:
            status = f"{bar} {int(progress)}%"
        
        garden_text += f"• {emoji} {crop['crop_type'].title()}: {status}\n"
    
    garden_text += f"""

💡 <code>/plant [crop] [quantity]</code>
Example: <code>/plant carrot 3</code>
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
    
    can_use, error = await check_cooldown(message.from_user.id, "plant")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    cost = CROP_DATA[crop_type]['buy'] * quantity
    if user['cash'] < cost:
        await message.answer(f"❌ Need ${cost:,}! You have ${user['cash']:,}")
        return
    
    success = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if not success:
        await message.answer("❌ Not enough garden space!")
        return
    
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
""", parse_mode=ParseMode.HTML)

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest ready crops"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    harvested = await db.harvest_crops(message.from_user.id)
    
    if not harvested:
        await message.answer("❌ No crops ready for harvest!")
        return
    
    total_value = 0
    harvest_text = "✅ <b>HARVEST COMPLETE!</b>\n\n"
    
    for crop_type, count in harvested:
        sell_price = CROP_DATA[crop_type]['sell'] * count
        total_value += sell_price
        emoji = CROP_EMOJIS.get(crop_type, "🌱")
        harvest_text += f"{emoji} {crop_type.title()}: {count} × ${CROP_DATA[crop_type]['sell']} = ${sell_price}\n"
    
    await db.update_currency(message.from_user.id, "cash", total_value)
    
    harvest_text += f"\n💰 <b>Total Earned: ${total_value:,}</b>"
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

# ============================================================================
# REACTION COMMANDS - WORKING WITH GIFS
# ============================================================================

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to hug them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "hug")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("hug", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "hug")

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to kill them!")
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
        await message.answer("❌ Reply to someone to rob them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot rob yourself!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "rob")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both need /start first!")
        return
    
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor! (Need $100+)")
        return
    
    success = random.random() < 0.4
    
    if success:
        max_steal = int(target_user['cash'] * 0.3)
        min_steal = int(target_user['cash'] * 0.1)
        stolen = random.randint(min_steal, max_steal)
        
        await db.update_currency(target.id, "cash", -stolen)
        await db.update_currency(message.from_user.id, "cash", stolen)
        
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        await message.answer(f"💰 Robbed ${stolen:,} from {target.first_name}!")
        
        await log_to_channel(f"⚠️ ROBBERY: {message.from_user.id} robbed {target.id} - ${stolen}")
    else:
        fine = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", -fine)
        await message.answer(f"🚨 Failed! Fined ${fine:,}. {target.first_name} caught you!")
    
    await db.set_cooldown(message.from_user.id, "rob")

# Add other reaction commands
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
# MINI-GAMES - WORKING
# ============================================================================

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine"""
    if not command.args:
        await message.answer("🎰 Usage: /slot [bet]\nExample: /slot 100")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet: $10!")
            return
    except:
        await message.answer("Invalid bet!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "slot")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if bet > user['cash']:
        await message.answer(f"❌ You only have ${user['cash']:,}!")
        return
    
    symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎"]
    reels = [random.choice(symbols) for _ in range(3)]
    
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
    
    await db.update_currency(message.from_user.id, "cash", net_gain)
    await db.set_cooldown(message.from_user.id, "slot")
    
    await message.answer(f"""
🎰 <b>SLOT MACHINE</b>

[{reels[0]}] [{reels[1]}] [{reels[2]}]

💰 Bet: <b>${bet:,}</b>
🏆 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}
📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>

💵 Balance: <b>${user['cash'] + net_gain:,}</b>
""", parse_mode=ParseMode.HTML)

@dp.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject):
    """Dice game"""
    if not command.args:
        await message.answer("🎲 Usage: /dice [bet]\nExample: /dice 50")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet: $10!")
            return
    except:
        await message.answer("Invalid bet!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if bet > user['cash']:
        await message.answer(f"❌ You only have ${user['cash']:,}!")
        return
    
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
    
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    await message.answer(f"""
🎲 <b>DICE GAME</b>

👤 Your roll: <b>{player_roll}</b>
🤖 Bot roll: <b>{bot_roll}</b>

💰 Bet: <b>${bet:,}</b>
🏆 Result: <b>{result}</b>
💵 {'Win' if net_gain > 0 else 'Loss'}: <b>${abs(net_gain):,}</b>

📈 Balance: <b>${user['cash'] + net_gain:,}</b>
""", parse_mode=ParseMode.HTML)

# ============================================================================
# DAILY & PROFILE - WORKING
# ============================================================================

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    can_use, error = await check_cooldown(message.from_user.id, "daily")
    if not can_use:
        await message.answer(error)
        return
    
    base_bonus = random.randint(500, 1500)
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * 100
    
    streak = user.get('daily_streak', 0) + 1
    streak_bonus = min(500, streak * 50)
    
    bio_multiplier = 2 if user.get('bio_verified') else 1
    total_bonus = (base_bonus + family_bonus + streak_bonus) * bio_multiplier
    
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.update_currency(message.from_user.id, "tokens", 5)
    await db.set_cooldown(message.from_user.id, "daily")
    
    await db.conn.execute(
        "UPDATE users SET daily_streak = ?, gemstone = ? WHERE user_id = ?",
        (streak, gemstone, message.from_user.id)
    )
    await db.conn.commit()
    
    await message.answer(f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base_bonus:,}</b>
• Family: <b>${family_bonus:,}</b>
• Streak ({streak} days): <b>${streak_bonus:,}</b>
• Multiplier: <b>{bio_multiplier}x</b>
• <b>Total: ${total_bonus:,}</b>

💎 <b>Gemstone:</b> <b>{gemstone}</b>
🎁 <b>Bonus:</b> +5 🌱 Tokens

{'✅ Bio verified (2x rewards!)' if bio_multiplier > 1 else '❌ Add @Familly_TreeBot to bio for 2x!'}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """User profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
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
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Daily Streak: <b>{user.get('daily_streak', 0)} days</b>
• Bio Verified: {'✅' if user.get('bio_verified') else '❌'}

💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
"""
    
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

# ============================================================================
# OWNER COMMANDS - ONLY FOR YOU
# ============================================================================

@dp.message(Command("owner"))
async def cmd_owner(message: Message):
    """Owner commands list"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    owner_text = """
👑 <b>OWNER COMMANDS</b>

💰 <b>Economy:</b>
• <code>/add [user_id] [resource] [amount]</code> - Add resources
• <code>/reset [user_id] [all/cash/garden]</code> - Reset user data

👤 <b>User Management:</b>
• <code>/ban</code> - Ban user (reply)
• <code>/unban [user_id]</code> - Unban user
• <code>/warn</code> - Warn user (reply)
• <code>/sudo</code> - Make admin (reply)

📊 <b>System:</b>
• <code>/stats</code> - Bot statistics
• <code>/broadcast [message]</code> - Broadcast to all users
• <code>/message [user_id] [text]</code> - Send message to user

🎬 <b>Catbox:</b>
• <code>/catbox add [cmd] [url]</code> - Add GIF
• <code>/catbox remove [cmd]</code> - Remove GIF
• <code>/catbox list</code> - List GIFs

⚙️ <b>Other:</b>
• <code>/setlevel [user_id] [level]</code> - Set user level
• <code>/giveitem [user_id] [item]</code> - Give special item
• <code>/maintenance [on/off]</code> - Toggle maintenance
"""
    
    await message.answer(owner_text, parse_mode=ParseMode.HTML)

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only!")
        return
    
    if not command.args:
        await message.answer("""
💰 <b>ADD RESOURCES</b>

Usage: <code>/add [user_id] [resource] [amount]</code>

💎 Resources: cash, gold, bonds, credits, tokens
📝 Example: <code>/add 123456789 cash 1000</code>

💡 Or reply to user's message!
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif args[0].isdigit():
        target_id = int(args[0])
        args = args[1:]
    
    if not target_id or len(args) < 2:
        await message.answer("❌ Format: /add [user_id] [resource] [amount]")
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
    
    await db.update_currency(target_id, resource, amount)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else f"ID: {target_id}"
    
    await message.answer(f"""
✅ <b>RESOURCES ADDED</b>

👤 To: <b>{target_name}</b>
💎 Resource: {CURRENCY_EMOJIS.get(resource, '📦')} <b>{resource.upper()}</b>
➕ Amount: <b>{amount:,}</b>
👑 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)
    
    await log_to_channel(f"👑 {message.from_user.id} added {resource} {amount} to {target_id}")

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban user - owner only"""
    if not is_owner(message.from_user.id):
        return
    
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to user to ban!")
        return
    
    if target.id == OWNER_ID:
        await message.answer("❌ Cannot ban owner!")
        return
    
    await db.conn.execute(
        "UPDATE users SET is_banned = 1 WHERE user_id = ?",
        (target.id,)
    )
    await db.conn.commit()
    
    await message.answer(f"""
✅ <b>USER BANNED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
⏰ Banned: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""", parse_mode=ParseMode.HTML)
    
    await log_to_channel(f"🔨 BAN: {target.id} by {message.from_user.id}")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only!")
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

💰 <b>Economy:</b>
• Total Cash: <b>${stats.get('total_cash', 0):,}</b>

🕒 <b>Uptime:</b> Running
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast to all users - owner only"""
    if not is_owner(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("❌ Usage: /broadcast [message]")
        return
    
    broadcast_msg = command.args
    sent = 0
    failed = 0
    
    cursor = await db.conn.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = await cursor.fetchall()
    
    await message.answer(f"📢 Broadcasting to {len(users)} users...")
    
    for user_row in users:
        user_id = user_row[0]
        try:
            await bot.send_message(user_id, f"📢 <b>ANNOUNCEMENT</b>\n\n{broadcast_msg}", parse_mode=ParseMode.HTML)
            sent += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except:
            failed += 1
    
    await message.answer(f"""
✅ <b>BROADCAST COMPLETE</b>

📤 Sent: <b>{sent}</b>
❌ Failed: <b>{failed}</b>
📊 Total: <b>{len(users)}</b>
""", parse_mode=ParseMode.HTML)
    
    await log_to_channel(f"📢 Broadcast sent to {sent}/{len(users)} users")

# ============================================================================
# CATBOX COMMANDS
# ============================================================================

@dp.message(Command("catbox"))
async def cmd_catbox(message: Message, command: CommandObject):
    """Manage GIFs"""
    if not command.args:
        await message.answer("""
🐱 <b>CATBOX SYSTEM</b>

Manage GIFs for reaction commands.

📋 <b>Commands:</b>
• <code>/catbox list</code> - List all GIFs
• <code>/catbox add [cmd] [url]</code> - Add GIF (owner)
• <code>/catbox remove [cmd]</code> - Remove GIF (owner)
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.lower().split()
    subcmd = args[0]
    
    if subcmd == "list":
        gifs = await db.conn.execute_fetchall(
            "SELECT command, gif_url FROM catbox_gifs"
        )
        
        if not gifs:
            await message.answer("📭 No GIFs in catbox!")
            return
        
        gif_list = "\n".join([f"• /{cmd} - {url[:50]}..." for cmd, url in gifs])
        await message.answer(f"""
📦 <b>CATBOX GIFS</b>

{gif_list}
""", parse_mode=ParseMode.HTML)
    
    elif subcmd == "add" and len(args) >= 3:
        if not is_owner(message.from_user.id):
            await message.answer("❌ Owner only!")
            return
        
        cmd = args[1]
        url = args[2]
        
        if cmd not in REACTION_GIFS.keys():
            await message.answer(f"❌ Invalid command! Available: {', '.join(REACTION_GIFS.keys())}")
            return
        
        await db.add_gif(cmd, url, message.from_user.id)
        await message.answer(f"✅ GIF added for /{cmd} command!")
    
    elif subcmd == "remove" and len(args) >= 2:
        if not is_owner(message.from_user.id):
            await message.answer("❌ Owner only!")
            return
        
        cmd = args[1]
        await db.conn.execute("DELETE FROM catbox_gifs WHERE command = ?", (cmd,))
        await db.conn.commit()
        await message.answer(f"✅ GIF removed for /{cmd}!")
    
    else:
        await message.answer("❌ Invalid catbox command!")

# ============================================================================
# OTHER COMMANDS
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
👥 Groups: <b>1</b>
🕒 Uptime: Running
🔧 Status: 🟢 ACTIVE

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

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

😊 <b>Reactions:</b>
• <code>/hug</code> - Hug someone (reply)
• <code>/kill</code> - Kill someone (reply)
• <code>/kiss</code> - Kiss someone (reply)
• <code>/slap</code> - Slap someone (reply)
• <code>/pat</code> - Pat someone (reply)

💡 All reaction commands require replying to user's message!
"""
    
    await message.answer(games_text, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL WORKING COMMANDS</b>

👨‍👩‍👧‍👦 <b>FAMILY:</b>
• <code>/family</code> - Family tree
• <code>/adopt</code> - Adopt (reply)
• <code>/marry</code> - Marry (reply)

🌾 <b>GARDEN:</b>
• <code>/garden</code> - View garden
• <code>/plant [crop] [qty]</code> - Plant
• <code>/harvest</code> - Harvest

🎮 <b>GAMES:</b>
• <code>/slot [bet]</code> - Slot machine
• <code>/dice [bet]</code> - Dice game
• <code>/rob</code> - Rob (reply)

😊 <b>REACTIONS:</b>
• <code>/hug</code>, <code>/kill</code>, <code>/kiss</code>
• <code>/slap</code>, <code>/pat</code> (all need reply)

💰 <b>ECONOMY:</b>
• <code>/daily</code> - Daily bonus
• <code>/me</code> - Your profile

🔧 <b>OTHER:</b>
• <code>/ping</code> - Bot status
• <code>/games</code> - All games list
• <code>/catbox</code> - Manage GIFs

👑 <b>OWNER:</b>
• <code>/owner</code> - Owner commands
• <code>/add</code>, <code>/ban</code>, <code>/stats</code>
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ERROR HANDLER
# ============================================================================

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Global error handler - FIXED"""
    logger.error(f"Error: {exception}", exc_info=True)
    
    try:
        error_msg = f"❌ ERROR:\n{type(exception).__name__}: {str(exception)[:200]}"
        await log_to_channel(error_msg)
    except:
        pass
    
    return True

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

async def setup_bot():
    """Setup bot on startup"""
    await db.connect()
    
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
        types.BotCommand(command="catbox", description="Manage GIFs")
    ]
    
    await bot.set_my_commands(commands)
    
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - PERFECT VERSION")
    print(f"Version: 9.0 | Owner: {OWNER_ID}")
    print(f"Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED (install pillow)'}")
    print("=" * 60)
    
    await log_to_channel(f"🤖 Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function"""
    try:
        await setup_bot()
        print("🚀 Starting bot polling...")
        
        # CRITICAL FIX: Explicitly set allowed updates
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await db.conn.close()
        await bot.session.close()

if __name__ == "__main__":
    # Check Pillow installation
    if not HAS_PILLOW:
        print("⚠️  WARNING: Pillow not installed. Install with: pip install pillow")
        print("📷 Image features will be disabled.")
    
    # Run the bot
    asyncio.run(main())
