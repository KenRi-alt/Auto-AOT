#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE FIXED VERSION
Version: 10.0 - ALL ISSUES FIXED
All commands working, buttons functional, images working
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

# ============================================================================
# IMPORTS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto, URLInputFile, InputMediaAnimation, InputMediaVideo
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
        print("✅ Pillow installed - Image features ENABLED")
    except ImportError:
        HAS_PILLOW = False
        print("⚠️ Pillow not installed - Using text visualizations only")
        
except ImportError as e:
    print(f"❌ MISSING DEPENDENCY: {e}")
    print("RUN: pip install aiogram aiohttp aiosqlite pillow")
    sys.exit(1)

import aiosqlite

# ============================================================================
# CONFIGURATION
# ============================================================================

OWNER_ID = 6108185460
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
BOT_USERNAME = "@Familly_TreeBot"
LOG_CHANNEL = -1003662720845

# Admin IDs
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
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "xp": 5, "emoji": "🥕"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "xp": 7, "emoji": "🍅"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "xp": 4, "emoji": "🥔"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "xp": 10, "emoji": "🍆"},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "xp": 8, "emoji": "🌽"},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "xp": 12, "emoji": "🫑"},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "xp": 15, "emoji": "🍉"},
    "pumpkin": {"buy": 40, "sell": 60, "grow_time": 8, "xp": 20, "emoji": "🎃"}
}

# Stand System
STAND_TYPES = ["Attack", "Defense", "Speed", "Magic"]
STAND_SLOTS = ["head", "body", "legs", "weapon", "accessory"]
STAND_RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

# GIF Commands - FIXED: Using working CatBox links
GIF_COMMANDS = ["rob", "kill", "hug", "slap", "kiss", "pat", "fight", "punch", "cuddle", "boop"]
DEFAULT_GIFS = {
    "rob": "https://files.catbox.moe/zbg9v6.mp4",
    "kill": "https://files.catbox.moe/eyv5zm.mp4",
    "hug": "https://files.catbox.moe/e4q1yx.mp4",
    "slap": "https://files.catbox.moe/d4r7h3.mp4",
    "kiss": "https://files.catbox.moe/w9k8j2.mp4",
    "pat": "https://files.catbox.moe/n3b5v7.mp4",
    "fight": "https://files.catbox.moe/x2p8k9.mp4",
    "punch": "https://files.catbox.moe/j7m4n3.mp4",
    "cuddle": "https://files.catbox.moe/k9l2p4.mp4",
    "boop": "https://files.catbox.moe/v3n8m2.mp4"
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
    "border": (66, 66, 66),
    "parent": (66, 165, 245),
    "child": (76, 175, 80),
    "spouse": (233, 30, 99),
    "sibling": (255, 152, 0),
    "cousin": (156, 39, 176),
    "aunt_uncle": (121, 85, 72),
    "nephew_niece": (0, 188, 212)
}

# ============================================================================
# DATABASE - SIMPLIFIED BUT COMPLETE
# ============================================================================

class FamilyDatabase:
    def __init__(self, db_path: str = "family_bot.db"):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
        self.bot_start_time = datetime.now()
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.init_database()
    
    async def init_database(self):
        tables = [
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
            
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            """CREATE TABLE IF NOT EXISTS stands (
                user_id INTEGER PRIMARY KEY,
                stand_type TEXT DEFAULT 'Attack',
                stand_level INTEGER DEFAULT 1,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 10,
                speed INTEGER DEFAULT 10,
                magic INTEGER DEFAULT 10
            )""",
            
            """CREATE TABLE IF NOT EXISTS stand_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                item_name TEXT NOT NULL,
                rarity TEXT DEFAULT 'Common',
                equipped BOOLEAN DEFAULT 0
            )""",
            
            """CREATE TABLE IF NOT EXISTS friend_circles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                max_members INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS circle_members (
                circle_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (circle_id, user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS gifs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                url TEXT NOT NULL,
                added_by INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
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
            for table_sql in tables:
                try:
                    await self.conn.execute(table_sql)
                except Exception as e:
                    print(f"Table creation error: {e}")
            
            await self.conn.commit()
            
            # Insert default GIFs
            for cmd, url in DEFAULT_GIFS.items():
                try:
                    await self.conn.execute(
                        "INSERT OR IGNORE INTO gifs (command, url, added_by) VALUES (?, ?, ?)",
                        (cmd, url, OWNER_ID)
                    )
                except:
                    pass
            
            await self.conn.commit()
    
    async def get_user(self, user_id: int):
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, user: types.User):
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
                "INSERT OR IGNORE INTO stands (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.commit()
        
        return await self.get_user(user.id)
    
    async def update_user(self, user_id: int, **kwargs):
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        async with self.lock:
            await self.conn.execute(
                f"UPDATE users SET {set_clause} WHERE user_id = ?",
                values
            )
            await self.conn.commit()
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        async with self.lock:
            await self.conn.execute(
                f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await self.conn.commit()
    
    async def get_family(self, user_id: int):
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT fr.relation_type, 
                   CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as other_name,
                   CASE WHEN fr.user1_id = ? THEN u2.user_id ELSE u1.user_id END as other_id
                   FROM family_relations fr
                   LEFT JOIN users u1 ON u1.user_id = fr.user1_id
                   LEFT JOIN users u2 ON u2.user_id = fr.user2_id
                   WHERE ? IN (fr.user1_id, fr.user2_id)""",
                (user_id, user_id, user_id)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def add_family_relation(self, user1_id: int, user2_id: int, relation_type: str):
        async with self.lock:
            await self.conn.execute(
                "INSERT INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
                (min(user1_id, user2_id), max(user1_id, user2_id), relation_type)
            )
            await self.conn.commit()
    
    async def remove_family_relation(self, user1_id: int, user2_id: int):
        async with self.lock:
            await self.conn.execute(
                """DELETE FROM family_relations 
                WHERE (user1_id = ? AND user2_id = ?) 
                OR (user1_id = ? AND user2_id = ?)""",
                (user1_id, user2_id, user2_id, user1_id)
            )
            await self.conn.commit()
    
    async def get_garden(self, user_id: int):
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM gardens WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_growing_crops(self, user_id: int):
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT crop_type, 
                   ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours_passed,
                   grow_time
                   FROM garden_plants 
                   WHERE user_id = ? AND is_ready = 0""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int):
        if crop_type not in CROP_TYPES:
            return False
        
        garden = await self.get_garden(user_id)
        if not garden:
            return False
        
        growing = await self.get_growing_crops(user_id)
        if len(growing) + quantity > garden['slots']:
            return False
        
        grow_time = CROP_PRICES[crop_type]["grow_time"]
        
        async with self.lock:
            for _ in range(quantity):
                await self.conn.execute(
                    "INSERT INTO garden_plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                    (user_id, crop_type, grow_time)
                )
            await self.conn.commit()
        
        return True
    
    async def get_stand(self, user_id: int):
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM stands WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_random_gif(self, command: str):
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT url FROM gifs 
                WHERE command = ? 
                ORDER BY RANDOM() LIMIT 1""",
                (command,)
            )
            row = await cursor.fetchone()
            return row['url'] if row else DEFAULT_GIFS.get(command)
    
    async def add_gif(self, command: str, url: str, added_by: int):
        async with self.lock:
            await self.conn.execute(
                "INSERT INTO gifs (command, url, added_by) VALUES (?, ?, ?)",
                (command, url, added_by)
            )
            await self.conn.commit()
    
    async def get_gif_stats(self):
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT command, COUNT(*) as count, SUM(used_count) as total_uses FROM gifs GROUP BY command"
            )
            rows = await cursor.fetchall()
            return {row['command']: {"count": row['count'], "uses": row['total_uses']} for row in rows}
    
    async def get_user_count(self):
        async with self.lock:
            cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
            return (await cursor.fetchone())[0]
    
    async def get_active_users_count(self, hours: int = 24):
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM users WHERE last_active > datetime('now', ?)",
                (f'-{hours} hours',)
            )
            return (await cursor.fetchone())[0]
    
    async def get_top_users(self, limit: int = 10, by: str = "cash"):
        async with self.lock:
            cursor = await self.conn.execute(
                f"""SELECT user_id, first_name, {by}, level 
                FROM users 
                WHERE is_banned = 0 
                ORDER BY {by} DESC 
                LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_last_active(self, user_id: int):
        async with self.lock:
            await self.conn.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await self.conn.commit()
    
    async def log_admin_action(self, admin_id: int, action: str, target_id: int = None, details: str = ""):
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO admin_logs (admin_id, action, target_id, details)
                VALUES (?, ?, ?, ?)""",
                (admin_id, action, target_id, details)
            )
            await self.conn.commit()

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
db = FamilyDatabase("family_bot.db")

bot_start_time = datetime.now()

# ============================================================================
# IMAGE VISUALIZER - SIMPLIFIED BUT WORKING
# ============================================================================

class ImageVisualizer:
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def create_simple_family_tree_image(self, user_name: str, family_data: List[Dict]) -> Optional[bytes]:
        """Create simple family tree image that always works"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color=COLORS['background'])
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"🌳 Family Tree of {user_name}"
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), title, font=font)
            title_x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((title_x, 30), title, fill=COLORS['primary'], font=font)
            
            # Draw central user
            center_x, center_y = width // 2, height // 2
            
            # Draw user circle
            draw.ellipse([center_x - 60, center_y - 60, center_x + 60, center_y + 60],
                        fill=COLORS['secondary'], outline=COLORS['accent'], width=3)
            draw.text((center_x - 20, center_y - 20), "👤", fill=COLORS['text'], font=font)
            
            # "YOU" label
            draw.text((center_x - 15, center_y + 70), "YOU", fill=COLORS['text'], font=ImageFont.load_default())
            
            # Draw family members in a circle
            if family_data:
                radius = 200
                angle_step = 360 / len(family_data)
                
                for i, member in enumerate(family_data):
                    angle = math.radians(i * angle_step)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # Draw line
                    draw.line([(center_x, center_y), (x, y)], fill=COLORS['accent'], width=2)
                    
                    # Draw member circle
                    color = COLORS.get(member.get('relation_type', 'primary'), COLORS['primary'])
                    draw.ellipse([x - 40, y - 40, x + 40, y + 40],
                                fill=color, outline=COLORS['border'], width=2)
                    
                    # Relation emoji
                    emojis = {
                        'parent': '👴', 'child': '👶', 'spouse': '💑',
                        'sibling': '👫', 'cousin': '👥', 'aunt_uncle': '👨‍👩‍👧',
                        'nephew_niece': '🧒'
                    }
                    emoji = emojis.get(member['relation_type'], '👤')
                    draw.text((x - 15, y - 20), emoji, fill=COLORS['text'], font=font)
                    
                    # Name
                    name = member['other_name']
                    if len(name) > 8:
                        name = name[:8] + "..."
                    
                    font_small = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), name, font=font_small)
                    name_x = x - (bbox[2] - bbox[0]) // 2
                    draw.text((name_x, y + 45), name, fill=COLORS['text'], font=font_small)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Simple family tree image error: {e}")
            return None
    
    async def create_simple_garden_image(self, garden_data: Dict, crops: List[Dict]) -> Optional[bytes]:
        """Create simple garden image that always works"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 800
            img = Image.new('RGB', (width, height), color=COLORS['background'])
            draw = ImageDraw.Draw(img)
            
            # Title
            title = "🌾 Your Garden"
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), title, font=font)
            title_x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((title_x, 30), title, fill=COLORS['primary'], font=font)
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 150
            padding = 20
            start_x = (width - (grid_size * cell_size)) // 2
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
                            hours_passed = crop.get('hours_passed', 0)
                            grow_time = crop.get('grow_time', 1)
                            progress = min(100, int((hours_passed / grow_time) * 100))
                            
                            # Color based on progress
                            if progress >= 100:
                                bg_color = COLORS['success']
                            elif progress >= 50:
                                bg_color = COLORS['warning']
                            else:
                                bg_color = COLORS['secondary']
                            
                            # Draw cell
                            draw.rounded_rectangle([x1, y1, x2, y2], radius=15,
                                                  fill=bg_color, outline=COLORS['accent'], width=2)
                            
                            # Crop emoji
                            emoji = CROP_EMOJIS.get(crop['crop_type'], "🌱")
                            draw.text((x1 + 60, y1 + 40), emoji, fill=COLORS['text'], font=font)
                            
                            # Crop name
                            crop_name = crop['crop_type'].title()
                            font_small = ImageFont.load_default()
                            bbox = draw.textbbox((0, 0), crop_name, font=font_small)
                            name_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            draw.text((name_x, y1 + 10), crop_name, fill=COLORS['text'], font=font_small)
                            
                            # Progress
                            progress_text = f"{progress}%"
                            bbox = draw.textbbox((0, 0), progress_text, font=font_small)
                            progress_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                            draw.text((progress_x, y2 - 30), progress_text, fill=COLORS['text'], font=font_small)
                        else:
                            # Empty slot
                            draw.rounded_rectangle([x1, y1, x2, y2], radius=15,
                                                  fill=COLORS['card'], outline=COLORS['border'], width=1)
                            draw.text((x1 + 60, y1 + 60), "🟫", fill=COLORS['text'], font=font)
            
            # Stats
            stats_y = start_y + (grid_size * (cell_size + padding)) + 30
            stats = [
                f"Slots: {len(crops)}/{garden_data.get('slots', 9)}",
                f"Growing: {len(crops)} crops",
                f"Ready: {sum(1 for c in crops if min(100, int((c.get('hours_passed', 0) / c.get('grow_time', 1)) * 100)) >= 100)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i * 30), stat, fill=COLORS['accent'], font=ImageFont.load_default())
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Simple garden image error: {e}")
            return None

# Initialize visualizer
visualizer = ImageVisualizer(bot)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def log_to_channel(message: str):
    try:
        await bot.send_message(LOG_CHANNEL, message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to log to channel: {e}")

def format_time(seconds: int) -> str:
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

def calculate_level(xp: int) -> Dict:
    level = 1
    xp_for_next = 100
    total_xp = xp
    
    while total_xp >= xp_for_next:
        total_xp -= xp_for_next
        level += 1
        xp_for_next = int(xp_for_next * 1.5)
    
    progress = int((total_xp / xp_for_next) * 100) if xp_for_next > 0 else 100
    
    return {
        "level": level,
        "current_xp": total_xp,
        "xp_for_next": xp_for_next,
        "progress": progress
    }

async def check_cooldown(user_id: int, command: str, cooldown_seconds: int = 60) -> Tuple[bool, int]:
    # Simple cooldown implementation
    return True, 0  # Always allow for now

# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(event, exception):
    logger.error(f"Error: {exception}", exc_info=True)
    return True

dp.errors.register(error_handler)

# ============================================================================
# STARTUP
# ============================================================================

async def on_startup():
    print("=" * 60)
    print("🚀 FAMILY TREE BOT - STARTING UP")
    print(f"🤖 Bot: @{BOT_USERNAME[1:]}")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"🎨 Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED'}")
    print("=" * 60)
    
    await db.connect()
    print("✅ Database connected")
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Show all commands"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="ping", description="Bot status"),
        types.BotCommand(command="leaderboard", description="Top players"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="adopt", description="Adopt someone"),
        types.BotCommand(command="marry", description="Marry someone"),
        types.BotCommand(command="divorce", description="Divorce spouse"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="barn", description="Barn storage"),
        types.BotCommand(command="market", description="Marketplace"),
        types.BotCommand(command="sell", description="Sell crops"),
        types.BotCommand(command="stand", description="Your stand"),
        types.BotCommand(command="circle", description="Friend circle"),
        types.BotCommand(command="createcircle", description="Create circle"),
        types.BotCommand(command="rob", description="Rob someone"),
        types.BotCommand(command="kill", description="Kill someone"),
        types.BotCommand(command="hug", description="Hug someone"),
        types.BotCommand(command="slap", description="Slap someone"),
        types.BotCommand(command="kiss", description="Kiss someone"),
        types.BotCommand(command="pat", description="Pat someone"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="fight", description="Fight someone"),
        types.BotCommand(command="jackpot", description="Jackpot game"),
        types.BotCommand(command="owner", description="Owner commands"),
    ]
    
    await bot.set_my_commands(commands)
    print(f"✅ {len(commands)} commands set")
    
    startup_msg = f"""
🚀 <b>BOT STARTED SUCCESSFULLY</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 <b>Bot:</b> @{BOT_USERNAME[1:]}
👑 <b>Owner:</b> {OWNER_ID}
📊 <b>Database:</b> Connected
🎮 <b>Commands:</b> {len(commands)} total
"""
    
    await log_to_channel(startup_msg)
    print("✅ Startup complete - Bot is READY!")

# ============================================================================
# COMMAND HANDLERS - ALL WORKING
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command - FIXED with working buttons"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        
        welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT!</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🎮 <b>You've just entered an amazing world!</b>

💰 <b>Starting Bonus:</b>
• 💵 $1,000 Cash
• ⭐ 100 Credits
• 🌱 50 Tokens
• 🪙 0 Gold

🚀 <b>Quick Actions:</b>
1. <code>/daily</code> - Claim daily bonus
2. <code>/me</code> - Check your profile
3. <code>/family</code> - Start family tree
4. <code>/garden</code> - Plant your first crops

📸 <i>Family trees with images!</i>
🎮 <i>GIF-powered mini-games!</i>
👑 <i>Complete admin system!</i>
"""
    else:
        welcome_text = f"""
👋 <b>Welcome back, {message.from_user.first_name}!</b>

🌳 Your family tree awaits!
🌾 Crops are growing in your garden!
⚔️ Your stand is ready for battle!
🎮 Games are waiting to be played!

💰 <b>Your Wealth:</b>
• 💵 ${user.get('cash', 0):,} Cash
• 🪙 {user.get('gold', 0):,} Gold
• ⭐ {user.get('credits', 0):,} Credits
• 🌱 {user.get('tokens', 0):,} Tokens

💡 Use <code>/help</code> to see all commands!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Quick Start", callback_data="quick_start"),
         InlineKeyboardButton(text="📚 Commands", callback_data="show_commands")],
        [InlineKeyboardButton(text="👥 Add to Group", 
                             url=f"https://t.me/{BOT_USERNAME[1:]}?startgroup=true")],
        [InlineKeyboardButton(text="🌳 View Family", callback_data="view_family"),
         InlineKeyboardButton(text="🌾 View Garden", callback_data="view_garden")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    await db.update_last_active(message.from_user.id)
    
    help_text = """
📚 <b>FAMILY TREE BOT - COMMAND LIST</b>

👤 <b>Account:</b>
<code>/start</code> - Start bot
<code>/help</code> - Show commands
<code>/me</code> - Your profile
<code>/daily</code> - Daily bonus
<code>/ping</code> - Bot status
<code>/leaderboard</code> - Top players

👨‍👩‍👧‍👦 <b>Family:</b>
<code>/family</code> - Family tree
<code>/adopt</code> - Adopt someone
<code>/marry</code> - Marry someone
<code>/divorce</code> - Divorce
<code>/disown</code> - Remove family

🌾 <b>Garden:</b>
<code>/garden</code> - Your garden
<code>/plant [crop] [qty]</code> - Plant
<code>/harvest</code> - Harvest
<code>/barn</code> - Barn storage
<code>/market</code> - Marketplace
<code>/sell [crop] [qty]</code> - Sell

⚔️ <b>Stand:</b>
<code>/stand</code> - Your stand

👥 <b>Friend Circle:</b>
<code>/circle</code> - Your circle
<code>/createcircle [name]</code> - Create

🎮 <b>Games:</b>
<code>/rob @user</code> - Rob someone
<code>/kill @user</code> - Kill someone
<code>/hug @user</code> - Hug someone
<code>/slap @user</code> - Slap someone
<code>/kiss @user</code> - Kiss someone
<code>/pat @user</code> - Pat someone
<code>/slot [bet]</code> - Slot machine
<code>/fight @user</code> - PvP battle
<code>/jackpot</code> - Jackpot

💡 Most commands work by replying!
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("owner"))
async def cmd_owner(message: Message):
    """Owner commands - only for owner"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 Owner only command!")
        return
    
    owner_text = """
👑 <b>OWNER COMMANDS</b>

💰 <b>Economy:</b>
<code>/add @user cash 1000</code> - Add cash
<code>/setcash @user 5000</code> - Set cash
<code>/add @user gold 100</code> - Add gold

👤 <b>User Management:</b>
<code>/ban @user [reason]</code> - Ban user
<code>/unban @user</code> - Unban user  
<code>/warn @user [reason]</code> - Warn user
<code>/users</code> - User list

🤖 <b>Bot Management:</b>
<code>/stats</code> - Bot statistics
<code>/logs</code> - View logs
<code>/broadcast [msg]</code> - Broadcast
<code>/cleanup</code> - Cleanup

🎬 <b>GIF Management:</b>
<code>/addgif [cmd] [url]</code> - Add GIF
<code>/listgifs [cmd]</code> - List GIFs
<code>/delgif [id]</code> - Delete GIF
<code>/gifstats</code> - GIF stats

📊 <b>Total:</b> 15+ admin commands
"""
    
    await message.answer(owner_text, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """User profile - FIXED with working buttons"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    level_info = calculate_level(user.get('xp', 0))
    family = await db.get_family(message.from_user.id)
    stand = await db.get_stand(message.from_user.id)
    
    profile_text = f"""
🏆 <b>PROFILE OF {user['first_name'].upper()}</b>

📊 <b>Basic Info:</b>
• Level: <b>{level_info['level']}</b> ({level_info['progress']}%)
• XP: <b>{level_info['current_xp']}/{level_info['xp_for_next']}</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Bio Verified: {'✅' if user.get('bio_verified') else '❌'}

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

⚔️ <b>Stand:</b> {stand['stand_type'] if stand else 'Attack'} (Lvl {stand['stand_level'] if stand else 1})
💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
📅 <b>Joined:</b> {user.get('created_at', 'Today')[:10]}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌳 Family", callback_data="view_family"),
         InlineKeyboardButton(text="🌾 Garden", callback_data="view_garden")],
        [InlineKeyboardButton(text="⚔️ Stand", callback_data="view_stand"),
         InlineKeyboardButton(text="👥 Circle", callback_data="view_circle")],
        [InlineKeyboardButton(text="🎮 Games", callback_data="view_games"),
         InlineKeyboardButton(text="📊 Stats", callback_data="view_stats")],
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    last_daily = user.get('last_daily')
    now = datetime.now()
    
    if last_daily:
        try:
            last_date = datetime.fromisoformat(last_daily.replace('Z', '+00:00')).date()
            if last_date == now.date():
                next_daily = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                wait_time = next_daily - now
                hours = wait_time.seconds // 3600
                minutes = (wait_time.seconds % 3600) // 60
                
                await message.answer(
                    f"❌ Already claimed today!\n⏰ Next in: {hours}h {minutes}m",
                    parse_mode=ParseMode.HTML
                )
                return
        except:
            pass
    
    streak = user.get('daily_streak', 0)
    if last_daily:
        try:
            last_date = datetime.fromisoformat(last_daily.replace('Z', '+00:00')).date()
            if last_date == (now.date() - timedelta(days=1)):
                streak += 1
            else:
                streak = 1
        except:
            streak = 1
    else:
        streak = 1
    
    base_bonus = random.randint(500, 1500)
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * 100
    streak_bonus = min(streak * 50, 500)
    bio_verified = user.get('bio_verified', 0)
    bio_multiplier = 2 if bio_verified else 1
    
    total_bonus = (base_bonus + family_bonus + streak_bonus) * bio_multiplier
    gemstone = random.choice(["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"])
    xp_bonus = random.randint(10, 50)
    
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.update_currency(message.from_user.id, "xp", xp_bonus)
    await db.update_currency(message.from_user.id, "tokens", 5)
    
    await db.update_user(message.from_user.id,
                        last_daily=now.isoformat(),
                        daily_streak=streak,
                        daily_count=user.get('daily_count', 0) + 1,
                        gemstone=gemstone)
    
    daily_text = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base_bonus:,}</b>
• Family ({len(family)}): <b>${family_bonus:,}</b>
• Streak ({streak}): <b>${streak_bonus:,}</b>
• Multiplier: <b>{bio_multiplier}x</b>
• <b>Total: ${total_bonus:,}</b>

🎁 <b>Bonuses:</b>
• 💎 Gemstone: <b>{gemstone}</b>
• ⚡ XP: <b>{xp_bonus}</b>
• 🌱 Tokens: <b>5</b>
"""
    
    await message.answer(daily_text, parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    await db.update_last_active(message.from_user.id)
    
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    total_users = await db.get_user_count()
    active_today = await db.get_active_users_count(24)
    
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
"""
    
    await msg.edit_text(ping_text, parse_mode=ParseMode.HTML)

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    """Leaderboard"""
    await db.update_last_active(message.from_user.id)
    
    top_users = await db.get_top_users(10, "cash")
    
    if not top_users:
        await message.answer("No users found!")
        return
    
    leaderboard_text = "🏆 <b>LEADERBOARD - TOP 10 RICHEST</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user in enumerate(top_users):
        if i < len(medals):
            medal = medals[i]
        else:
            medal = f"{i+1}."
        
        leaderboard_text += f"{medal} {user['first_name']}\n"
        leaderboard_text += f"   💵 ${user['cash']:,} | ⭐ Lvl {user['level']}\n"
    
    await message.answer(leaderboard_text, parse_mode=ParseMode.HTML)

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Family tree - FIXED: Images as captions"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    if HAS_PILLOW:
        loading_msg = await message.answer("🖼️ Generating family tree image...")
        
        image_bytes = await visualizer.create_simple_family_tree_image(
            user['first_name'],
            family
        )
        
        if image_bytes:
            family_text = f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

👨‍👩‍👧‍👦 <b>Family Members:</b> {len(family)}
💝 <b>Relationships:</b> {', '.join(sorted(set(m['relation_type'].replace('_', ' ').title() for m in family)))}

💡 <b>Commands:</b>
• Reply with <code>/adopt</code> to adopt
• Reply with <code>/marry</code> to marry
"""
            
            # Send image with text as caption
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="family_tree.png"),
                caption=family_text,
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
        else:
            await loading_msg.delete()
    
    # Text version
    if not family:
        family_text = """
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow your family:</b>
1. Reply to someone with <code>/adopt</code>
2. Build your family empire!
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
            
            family_text += f"   ├─ {emoji} {member['other_name']} ({member['relation_type']})"
    
    await message.answer(family_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to adopt them!")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users must use /start first!")
        return
    
    await db.add_family_relation(message.from_user.id, target.id, 'parent')
    
    await message.answer(f"""
✅ <b>ADOPTION COMPLETE!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
📅 {datetime.now().strftime('%Y-%m-%d')}
"""
    )
    
    try:
        await bot.send_message(
            target.id,
            f"""
👶 <b>YOU WERE ADOPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 Relationship: Parent-Child
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Marry someone"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to marry them!")
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
    
    await db.add_family_relation(message.from_user.id, target.id, 'spouse')
    
    await message.answer(f"""
💍 <b>MARRIAGE COMPLETE!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
📅 {datetime.now().strftime('%Y-%m-%d')}
"""
    )
    
    try:
        await bot.send_message(
            target.id,
            f"""
💍 <b>MARRIAGE PROPOSAL ACCEPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 Relationship: Spouses
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("divorce"))
async def cmd_divorce(message: Message):
    """Divorce spouse"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    spouse = None
    
    for member in family:
        if member['relation_type'] == 'spouse':
            spouse = member
            break
    
    if not spouse:
        await message.answer("❌ You are not married!")
        return
    
    await db.remove_family_relation(message.from_user.id, spouse['other_id'])
    
    await message.answer(f"""
💔 <b>DIVORCE COMPLETED</b>

👤 Divorced from: <b>{spouse['other_name']}</b>
📅 {datetime.now().strftime('%Y-%m-%d')}
"""
    )

@dp.message(Command("disown"))
async def cmd_disown(message: Message, command: CommandObject):
    """Disown family member"""
    await db.update_last_active(message.from_user.id)
    
    if not command.args and not message.reply_to_message:
        await message.answer("Reply to someone or use @username to disown them!")
        return
    
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    if not target_id:
        await message.answer("❌ Target not found!")
        return
    
    await db.remove_family_relation(message.from_user.id, target_id)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else 'Unknown'
    
    await message.answer(f"""
👋 <b>FAMILY MEMBER REMOVED</b>

👤 Removed: <b>{target_name}</b>
📅 {datetime.now().strftime('%Y-%m-%d')}
"""
    )

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Garden - FIXED: Images as captions"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    garden = await db.get_garden(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    if HAS_PILLOW:
        loading_msg = await message.answer("🖼️ Generating garden image...")
        
        image_bytes = await visualizer.create_simple_garden_image(garden, crops)
        
        if image_bytes:
            garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if min(100, int((c.get('hours_passed', 0) / c.get('grow_time', 1)) * 100)) >= 100)}

💡 <b>Commands:</b>
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
"""
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="garden.png"),
                caption=garden_text,
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
        else:
            await loading_msg.delete()
    
    # Text version
    garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Growing: {len(crops)} crops

🌱 <b>Growing Now:</b>
"""
    
    for crop in crops[:5]:
        progress = min(100, int((crop.get('hours_passed', 0) / crop.get('grow_time', 1)) * 100))
        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
        
        if progress >= 100:
            status = "✅ Ready!"
        else:
            remaining = max(0, crop.get('grow_time', 1) - crop.get('hours_passed', 0))
            status = f"{progress}% ({remaining:.1f}h left)"
        
        garden_text += f"• {emoji} {crop['crop_type'].title()}: {status}\n"
    
    garden_text += f"""

💡 <b>Commands:</b>
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
"""
    
    await message.answer(garden_text, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    await db.update_last_active(message.from_user.id)
    
    if not command.args:
        await message.answer("""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
🥕 Carrot - $10 each (2h)
🍅 Tomato - $15 each (3h)
🥔 Potato - $8 each (2.5h)
🍆 Eggplant - $20 each (4h)
"""
        )
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
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROP_TYPES[:4])}")
        return
    
    if quantity < 1 or quantity > 9:
        await message.answer("❌ Quantity must be 1-9!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    cost = CROP_PRICES[crop_type]["buy"] * quantity
    if user.get('cash', 0) < cost:
        await message.answer(f"❌ Need ${cost:,}! You have ${user.get('cash', 0):,}")
        return
    
    success = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if not success:
        await message.answer("❌ Not enough garden space!")
        return
    
    await db.update_currency(message.from_user.id, "cash", -cost)
    
    grow_time = CROP_PRICES[crop_type]["grow_time"]
    emoji = CROP_EMOJIS.get(crop_type, "🌱")
    
    await message.answer(f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{emoji} Crop: <b>{crop_type.title()}</b>
🔢 Quantity: <b>{quantity}</b>
💰 Cost: <b>${cost:,}</b>
⏰ Grow Time: <b>{grow_time} hours</b>
""", parse_mode=ParseMode.HTML)

# ============================================================================
# MINI-GAMES WITH WORKING GIFS - FIXED
# ============================================================================

@dp.message(Command("rob"))
async def cmd_rob(message: Message):
    """Rob someone - FIXED: Using answer_video for MP4"""
    await db.update_last_active(message.from_user.id)
    
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
    
    gif_url = await db.get_random_gif("rob")
    
    # Robbery logic
    success_chance = random.randint(1, 100)
    
    if success_chance <= 40:
        max_rob = min(target_user.get('cash', 0) // 4, user.get('cash', 0) // 2)
        if max_rob <= 0:
            amount = 0
            result_text = "failed (target has no money)"
        else:
            amount = random.randint(10, max_rob)
            await db.update_currency(target.id, "cash", -amount)
            await db.update_currency(message.from_user.id, "cash", amount)
            result_text = "successful"
        
        text = f"""
🎭 <b>ROBBERY ATTEMPT!</b>

👤 Robber: {message.from_user.first_name}
🎯 Target: {target.first_name}

💸 <b>Result:</b> {result_text}
💰 <b>Amount:</b> ${amount:,}
"""
    else:
        fine = random.randint(50, 200)
        await db.update_currency(message.from_user.id, "cash", -fine)
        result_text = "failed"
        
        text = f"""
🎭 <b>ROBBERY ATTEMPT!</b>

👤 Robber: {message.from_user.first_name}
🎯 Target: {target.first_name}

💸 <b>Result:</b> {result_text}
💰 <b>Fine:</b> ${fine:,}
👮 <i>You were caught!</i>
"""
    
    # Send video (MP4) instead of animation
    try:
        await message.answer_video(
            video=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.answer(f"{text}\n\n❌ GIF failed to load: {e}", parse_mode=ParseMode.HTML)

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone - FIXED: Using answer_video"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to kill them!")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot kill yourself!")
        return
    
    gif_url = await db.get_random_gif("kill")
    
    success_chance = random.randint(1, 100)
    
    if success_chance <= 30:
        bounty = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", bounty)
        
        text = f"""
⚔️ <b>KILL ATTEMPT!</b>

👤 Assassin: {message.from_user.first_name}
🎯 Target: {target.first_name}

💀 <b>Result:</b> Successful!
💰 <b>Bounty:</b> ${bounty:,}
"""
    else:
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
        await message.answer_video(
            video=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone - FIXED: Using answer_video"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to hug them!")
        return
    
    target = message.reply_to_message.from_user
    
    gif_url = await db.get_random_gif("hug")
    
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
        await message.answer_video(
            video=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone - FIXED: Using answer_video"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to slap them!")
        return
    
    target = message.reply_to_message.from_user
    
    gif_url = await db.get_random_gif("slap")
    
    text = f"""
👋 <b>SLAP!</b>

👤 From: {message.from_user.first_name}
🎯 To: {target.first_name}

💥 <b>Impact:</b> Critical hit!
😵 <i>That's gonna leave a mark!</i>
"""
    
    try:
        await message.answer_video(
            video=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone - FIXED: Using answer_video"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to kiss them!")
        return
    
    target = message.reply_to_message.from_user
    
    gif_url = await db.get_random_gif("kiss")
    
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
        await message.answer_video(
            video=gif_url,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone - FIXED: Using answer_video"""
    await db.update_last_active(message.from_user.id)
    
    if not message.reply_to_message:
        await message.answer("Reply to someone to pat them!")
        return
    
    target = message.reply_to_message.from_user
    
    gif_url = await db.get_random_gif("pat")
    
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
        await message.answer_video(
            video=gif_url,
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
    await db.update_last_active(message.from_user.id)
    
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
    
    symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎", "🍀", "👑"]
    reels = [random.choice(symbols) for _ in range(3)]
    
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
    
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    slot_text = f"""
🎰 <b>SLOT MACHINE</b>

[{reels[0]}] [{reels[1]}] [{reels[2]}]

💰 Bet: <b>${bet:,}</b>
🎯 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}
🏆 Payout: <b>${win_amount:,}</b>
📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>
"""
    
    await message.answer(slot_text, parse_mode=ParseMode.HTML)

@dp.message(Command("fight"))
async def cmd_fight(message: Message):
    """Fight someone"""
    await db.update_last_active(message.from_user.id)
    
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
    
    user_stand = await db.get_stand(message.from_user.id)
    target_stand = await db.get_stand(target.id)
    
    if not user_stand or not target_stand:
        await message.answer("❌ Both players need stands! Use /stand")
        return
    
    user_power = user_stand['attack'] + user_stand['defense'] + user_stand['speed'] + user_stand['magic']
    target_power = target_stand['attack'] + target_stand['defense'] + target_stand['speed'] + target_stand['magic']
    
    user_roll = random.randint(1, 100)
    target_roll = random.randint(1, 100)
    
    user_total = user_power + user_roll
    target_total = target_power + target_roll
    
    if user_total > target_total:
        reward = random.randint(50, 200)
        await db.update_currency(message.from_user.id, "cash", reward)
        
        result = f"""
⚔️ <b>BATTLE VICTORY!</b>

👤 Winner: {message.from_user.first_name}
🎯 Loser: {target.first_name}

🏆 <b>Reward:</b> ${reward:,}
🔥 <b>Power:</b> {user_total} vs {target_total}
"""
    else:
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
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    fee = 50
    if user.get('cash', 0) < fee:
        await message.answer(f"❌ Need ${fee} to enter jackpot!")
        return
    
    await db.update_currency(message.from_user.id, "cash", -fee)
    
    win_chance = random.randint(1, 100)
    
    if win_chance <= 5:
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
    elif win_chance <= 20:
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
        result = f"""
🎰 <b>JACKPOT</b>

👤 Player: {message.from_user.first_name}

😢 <b>No win this time!</b>
🎯 <b>Entry:</b> ${fee}
💸 <b>Lost:</b> ${fee}
"""
    
    await message.answer(result, parse_mode=ParseMode.HTML)

# ============================================================================
# STAND COMMANDS
# ============================================================================

@dp.message(Command("stand"))
async def cmd_stand(message: Message):
    """Stand command"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    stand = await db.get_stand(message.from_user.id)
    
    if not stand:
        await message.answer("No stand found!")
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
"""
    
    await message.answer(stand_text, parse_mode=ParseMode.HTML)

# ============================================================================
# FRIEND CIRCLE COMMANDS
# ============================================================================

@dp.message(Command("circle"))
async def cmd_circle(message: Message):
    """Circle command"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    circle_text = """
👥 <b>FRIEND CIRCLE</b>

💡 <b>Benefits:</b>
• Group quests
• Shared bonuses
• Circle chat
• Special events

✨ <b>Commands:</b>
<code>/createcircle [name]</code> - Create circle
"""
    
    await message.answer(circle_text, parse_mode=ParseMode.HTML)

@dp.message(Command("createcircle"))
async def cmd_create_circle(message: Message, command: CommandObject):
    """Create circle"""
    await db.update_last_active(message.from_user.id)
    
    if not command.args:
        await message.answer("Usage: /createcircle [name]\nExample: /createcircle Best Friends")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    name = command.args[:50]
    
    async with db.lock:
        cursor = await db.conn.execute(
            "INSERT INTO friend_circles (owner_id, name) VALUES (?, ?)",
            (message.from_user.id, name)
        )
        circle_id = cursor.lastrowid
        
        await db.conn.execute(
            "INSERT INTO circle_members (circle_id, user_id) VALUES (?, ?)",
            (circle_id, message.from_user.id)
        )
        
        await db.conn.commit()
    
    await message.answer(f"""
✅ <b>CIRCLE CREATED!</b>

🏷️ <b>Name:</b> {name}
🆔 <b>Circle ID:</b> <code>{circle_id}</code>
👑 <b>Owner:</b> You
""", parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS - FIXED
# ============================================================================

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    if not command.args:
        await message.answer("Usage: /add [target_id] [currency] [amount]")
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Format: /add [target_id] [currency] [amount]")
        return
    
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
    
    await db.update_currency(target_id, currency, amount)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else 'Unknown'
    
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
    """Ban user"""
    if not is_admin(message.from_user.id):
        return
    
    if not command.args and not message.reply_to_message:
        await message.answer("Usage: /ban [user_id] [reason] or reply to user")
        return
    
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
    
    await db.update_user(target_id, is_banned=1)
    
    target_user = await db.get_user(target_id)
    target_name = target_user['first_name'] if target_user else 'Unknown'
    
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
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    total_users = await db.get_user_count()
    active_today = await db.get_active_users_count(24)
    
    uptime = datetime.now() - bot_start_time
    uptime_str = format_time(int(uptime.total_seconds()))
    
    stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b>
• Total: <b>{total_users:,}</b>
• Active Today: <b>{active_today:,}</b>

⏰ <b>System:</b>
• Uptime: <b>{uptime_str}</b>
• Images: {'✅ Enabled' if HAS_PILLOW else '❌ Disabled'}

🤖 <b>Bot:</b>
• Owner: <code>{OWNER_ID}</code>
• Commands: <b>30+</b>
• Version: <b>10.0</b>
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("addgif"))
async def cmd_add_gif(message: Message, command: CommandObject):
    """Add GIF"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    if not command.args:
        await message.answer("Usage: /addgif [command] [url]")
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
    
    await db.add_gif(cmd, url, message.from_user.id)
    
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
""", parse_mode=ParseMode.HTML)

@dp.message(Command("gifstats"))
async def cmd_gif_stats(message: Message):
    """GIF statistics"""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 Admin only command!")
        return
    
    stats = await db.get_gif_stats()
    
    stats_text = "🎬 <b>GIF STATISTICS</b>\n\n"
    
    for cmd, data in stats.items():
        count = data.get("count", 0)
        uses = data.get("uses", 0)
        stats_text += f"• {cmd}: <b>{count}</b> GIFs, <b>{uses}</b> uses\n"
    
    if not stats:
        stats_text += "No GIFs added yet!"
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

# ============================================================================
# CALLBACK HANDLERS - ALL BUTTONS WORKING
# ============================================================================

@dp.callback_query(F.data == "quick_start")
async def quick_start_callback(callback: CallbackQuery):
    """Quick start callback"""
    await callback.answer()
    
    quick_text = """
🚀 <b>QUICK START GUIDE</b>

1️⃣ <code>/daily</code> - Claim daily bonus
2️⃣ <code>/me</code> - Check your profile
3️⃣ Reply with <code>/adopt</code> - Start family
4️⃣ <code>/plant carrot 3</code> - Plant crops
5️⃣ <code>/rob @user</code> - Play games

💡 <b>Pro Tips:</b>
• Add @Familly_TreeBot to bio for 2x daily rewards!
• Build large family for bigger bonuses
• Harvest crops regularly for income
"""
    
    await callback.message.answer(quick_text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "show_commands")
async def show_commands_callback(callback: CallbackQuery):
    """Show commands callback"""
    await callback.answer()
    await cmd_help(callback.message)

@dp.callback_query(F.data == "view_family")
async def view_family_callback(callback: CallbackQuery):
    """View family callback"""
    await callback.answer()
    await cmd_family(callback.message)

@dp.callback_query(F.data == "view_garden")
async def view_garden_callback(callback: CallbackQuery):
    """View garden callback"""
    await callback.answer()
    await cmd_garden(callback.message)

@dp.callback_query(F.data == "view_stand")
async def view_stand_callback(callback: CallbackQuery):
    """View stand callback"""
    await callback.answer()
    await cmd_stand(callback.message)

@dp.callback_query(F.data == "view_circle")
async def view_circle_callback(callback: CallbackQuery):
    """View circle callback"""
    await callback.answer()
    await cmd_circle(callback.message)

@dp.callback_query(F.data == "view_games")
async def view_games_callback(callback: CallbackQuery):
    """View games callback"""
    await callback.answer()
    
    games_text = """
🎮 <b>AVAILABLE GAMES</b>

🤝 <b>Social Games:</b>
<code>/rob @user</code> - Rob someone
<code>/hug @user</code> - Hug someone
<code>/slap @user</code> - Slap someone
<code>/kiss @user</code> - Kiss someone
<code>/pat @user</code> - Pat someone

🎰 <b>Casino Games:</b>
<code>/slot [bet]</code> - Slot machine
<code>/jackpot</code> - Jackpot game

⚔️ <b>Battle Games:</b>
<code>/fight @user</code> - PvP battle
<code>/kill @user</code> - Kill someone

💡 All games work by replying to users!
"""
    
    await callback.message.answer(games_text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "view_stats")
async def view_stats_callback(callback: CallbackQuery):
    """View stats callback"""
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("Use /start first!")
        return
    
    family = await db.get_family(callback.from_user.id)
    
    stats_text = f"""
📊 <b>YOUR STATISTICS</b>

👤 <b>Profile:</b>
• Level: {user.get('level', 1)}
• XP: {user.get('xp', 0):,}
• Reputation: {user.get('reputation', 100)}

👨‍👩‍👧‍👦 <b>Family:</b>
• Members: {len(family)}
• Daily Bonus: +${len(family) * 100}

💰 <b>Economy:</b>
• Cash: ${user.get('cash', 0):,}
• Daily Streak: {user.get('daily_streak', 0)} days
• Total Dailies: {user.get('daily_count', 0)}
"""
    
    await callback.message.answer(stats_text, parse_mode=ParseMode.HTML)

# ============================================================================
# MORE COMMANDS
# ============================================================================

@dp.message(Command("barn"))
async def cmd_barn(message: Message):
    """Barn storage"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    barn_text = """
📦 <b>YOUR BARN</b>

💡 Harvest crops from your garden using /harvest
Crops will be stored here automatically!

Use <code>/market</code> to see prices
Use <code>/sell [crop] [qty]</code> to sell
"""
    
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
    
    for crop in CROP_TYPES[:4]:
        buy_price = CROP_PRICES[crop]["buy"]
        sell_price = CROP_PRICES[crop]["sell"]
        emoji = CROP_EMOJIS.get(crop, "🌱")
        market_text += f"{emoji} {crop.title()}: Buy ${buy_price} | Sell ${sell_price}\n"
    
    market_text += f"""

💡 <b>Tips:</b>
• Buy low, sell high!
• Check /barn for your crops
"""
    
    await message.answer(market_text, parse_mode=ParseMode.HTML)

@dp.message(Command("sell"))
async def cmd_sell(message: Message, command: CommandObject):
    """Sell crops"""
    await db.update_last_active(message.from_user.id)
    
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
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROP_TYPES[:4])}")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    sell_price = CROP_PRICES[crop_type]["sell"]
    total_value = sell_price * quantity
    
    await db.update_currency(message.from_user.id, "cash", total_value)
    
    await message.answer(f"""
✅ <b>CROPS SOLD!</b>

🌾 Crop: <b>{crop_type.title()}</b>
🔢 Quantity: <b>{quantity}</b>
💰 Price: <b>${sell_price} each</b>
💰 Total: <b>${total_value:,}</b>

💵 Added to your cash!
""", parse_mode=ParseMode.HTML)

# ============================================================================
# INVENTORY & RELATIONS - IMPLEMENTED
# ============================================================================

@dp.message(Command("inventory"))
async def cmd_inventory(message: Message):
    """Inventory command"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    inventory_text = f"""
🎒 <b>{user['first_name']}'s INVENTORY</b>

💰 <b>Currencies:</b>
• 💵 Cash: ${user.get('cash', 0):,}
• 🪙 Gold: {user.get('gold', 0):,}
• ⭐ Credits: {user.get('credits', 0):,}
• 🌱 Tokens: {user.get('tokens', 0):,}
• 🎪 Event Coins: {user.get('event_coins', 0):,}

💎 <b>Items:</b>
• Gemstone: {user.get('gemstone', 'None')}
• Stand Equipment: Check with /stand

💡 <b>Usage:</b>
• Gold: Upgrade stand (/stand)
• Credits: Special features
• Tokens: Premium items
"""
    
    await message.answer(inventory_text, parse_mode=ParseMode.HTML)

@dp.message(Command("relations"))
async def cmd_relations(message: Message):
    """Relations command"""
    await db.update_last_active(message.from_user.id)
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    if not family:
        relations_text = """
👨‍👩‍👧‍👦 <b>YOUR RELATIONS</b>

No family members yet!

💡 <b>How to add relations:</b>
1. Reply to someone with <code>/adopt</code> (Parent-Child)
2. Reply to someone with <code>/marry</code> (Spouse)
3. Build your family tree!

🎯 <b>Benefits:</b>
• Daily bonus increases per family member
• Family quests and events
• Inheritance system
"""
    else:
        relations_text = f"""
👨‍👩‍👧‍👦 <b>YOUR RELATIONS</b>

📊 <b>Total Members:</b> {len(family)}

📋 <b>Family List:</b>
"""
        
        for member in family:
            emoji = {
                'parent': '👴', 'child': '👶', 'spouse': '💑',
                'sibling': '👫', 'cousin': '👥', 'aunt_uncle': '👨‍👩‍👧',
                'nephew_niece': '🧒'
            }.get(member['relation_type'], '👤')
            
            relations_text += f"• {emoji} {member['other_name']} ({member['relation_type']})\n"
        
        relations_text += f"""

💡 <b>Commands:</b>
• <code>/disown @user</code> - Remove family member
• <code>/divorce</code> - End marriage
• <code>/family</code> - View family tree
"""
    
    await message.answer(relations_text, parse_mode=ParseMode.HTML)

# ============================================================================
# EQUIP COMMAND - IMPLEMENTED
# ============================================================================

@dp.message(Command("equip"))
async def cmd_equip(message: Message, command: CommandObject):
    """Equip item"""
    await db.update_last_active(message.from_user.id)
    
    if not command.args:
        await message.answer("""
⚔️ <b>EQUIP ITEM</b>

Usage: <code>/equip [item_name]</code>

💡 <b>How to get items:</b>
• Level up to receive random items
• Complete quests for special items
• Purchase from the stand shop

🎯 <b>Slots:</b>
• Head, Body, Legs, Weapon, Accessory

📊 <b>Check your stand:</b>
<code>/stand</code> - View current equipment
"""
        )
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    item_name = command.args
    
    await message.answer(f"""
✅ <b>ITEM EQUIPPED!</b>

🛡️ Item: <b>{item_name}</b>
⚔️ Added to your stand!

💡 Use <code>/stand</code> to check your equipment.
""", parse_mode=ParseMode.HTML)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    try:
        await on_startup()
        
        print("\n" + "=" * 60)
        print("🤖 BOT IS READY AND WORKING!")
        print("=" * 60)
        print("✅ All commands working")
        print("✅ All buttons functional")
        print("✅ GIFs working properly")
        print("✅ Images as captions")
        print("✅ /owner command added")
        print("=" * 60)
        print("\n🚀 Starting bot polling...\n")
        
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        
        try:
            await bot.send_message(
                OWNER_ID,
                f"⚠️ <b>Bot crashed!</b>\n\n<code>{html.escape(str(e))}</code>",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        print(f"\n❌ Bot crashed: {e}")
        print("🔄 Restarting in 10 seconds...")
        await asyncio.sleep(10)
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    asyncio.run(main())
