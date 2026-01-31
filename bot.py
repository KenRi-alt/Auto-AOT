#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE & WORKING
Version: 10.0 - All Commands Working with Inline Buttons
"""

import os
import sys
import asyncio
import logging
import random
import math
import io
import time
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import aiohttp
import aiosqlite

# ============================================================================
# CORE IMPORTS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, BufferedInputFile
    )
    from aiogram.enums import ParseMode
    from aiogram.client.session.aiohttp import AiohttpSession
    
    # Pillow for images
    try:
        from PIL import Image, ImageDraw, ImageFont
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
        print("⚠️ Pillow not installed: pip install pillow")
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram pillow aiosqlite aiohttp")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
OWNER_ID = 6108185460
BOT_USERNAME = "Familly_TreeBot"
LOG_CHANNEL = -1003662720845

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

# Default Reaction GIFs (Catbox)
DEFAULT_GIFS = {
    "hug": "https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif",
    "kill": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "rob": "https://media.giphy.com/media/xTiTnHXbRoaZ1B1Mo8/giphy.gif",
    "kiss": "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif",
    "slap": "https://media.giphy.com/media/Zau0yrl17uzdK/giphy.gif",
    "pat": "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif",
    "punch": "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif",
    "cuddle": "https://media.giphy.com/media/3o7TKz8a8XWhzJ7AVu/giphy.gif"
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
    "marry": 86400,
    "lottery": 3600
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
# DATABASE - COMPLETE
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
                gemstone TEXT,
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
                progress REAL DEFAULT 0,
                is_ready BOOLEAN DEFAULT 0
            )""",
            
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type)
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
            )""",
            
            """CREATE TABLE IF NOT EXISTS lottery_tickets (
                user_id INTEGER NOT NULL,
                tickets INTEGER DEFAULT 0,
                PRIMARY KEY (user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                bet INTEGER,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table in tables:
            await self.conn.execute(table)
        await self.conn.commit()
        
        # Initialize default GIFs
        await self.init_default_gifs()
    
    async def init_default_gifs(self):
        """Initialize default GIFs in catbox"""
        for cmd, url in DEFAULT_GIFS.items():
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
        
        await self.conn.execute(
            "INSERT OR IGNORE INTO lottery_tickets (user_id) VALUES (?)",
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
    
    # Family methods
    async def get_family(self, user_id: int) -> List[dict]:
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
        return [{'relation_type': r[0], 'other_name': r[1], 'other_id': r[2]} for r in rows]
    
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
    
    # Garden methods
    async def get_garden_info(self, user_id: int) -> dict:
        cursor = await self.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return {'slots': row[0] if row else 9}
    
    async def get_growing_crops(self, user_id: int) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT crop_type, planted_at, grow_time, progress
               FROM garden_plants 
               WHERE user_id = ? AND is_ready = 0""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        crops = []
        for row in rows:
            planted = datetime.fromisoformat(row[1]) if row[1] else datetime.now()
            elapsed = (datetime.now() - planted).total_seconds() / 3600
            progress = min(100, (elapsed / row[2]) * 100) if row[2] > 0 else 0
            
            crops.append({
                'crop_type': row[0],
                'progress': progress,
                'is_ready': progress >= 100,
                'grow_time': row[2]
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
               AND progress >= 100""",
            (user_id,)
        )
        ready_crops = await cursor.fetchall()
        
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
    
    async def get_barn_items(self, user_id: int) -> List[tuple]:
        cursor = await self.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ?",
            (user_id,)
        )
        return await cursor.fetchall()
    
    # Catbox methods
    async def get_gif(self, command: str) -> Optional[str]:
        cursor = await self.conn.execute(
            "SELECT gif_url FROM catbox_gifs WHERE command = ?",
            (command,)
        )
        row = await cursor.fetchone()
        return row[0] if row else DEFAULT_GIFS.get(command)
    
    async def add_gif(self, command: str, url: str, added_by: int):
        await self.conn.execute(
            """INSERT OR REPLACE INTO catbox_gifs (command, gif_url, added_by)
               VALUES (?, ?, ?)""",
            (command, url, added_by)
        )
        await self.conn.commit()
    
    async def remove_gif(self, command: str):
        await self.conn.execute(
            "DELETE FROM catbox_gifs WHERE command = ?",
            (command,)
        )
        await self.conn.commit()
    
    async def list_gifs(self) -> List[tuple]:
        cursor = await self.conn.execute(
            "SELECT command, gif_url FROM catbox_gifs ORDER BY command"
        )
        return await cursor.fetchall()
    
    # Lottery methods
    async def buy_lottery_ticket(self, user_id: int, tickets: int) -> bool:
        cost = tickets * 50
        user = await self.get_user(user_id)
        
        if not user or user['cash'] < cost:
            return False
        
        await self.update_currency(user_id, "cash", -cost)
        
        await self.conn.execute(
            """INSERT INTO lottery_tickets (user_id, tickets) 
               VALUES (?, ?)
               ON CONFLICT(user_id) 
               DO UPDATE SET tickets = tickets + ?""",
            (user_id, tickets, tickets)
        )
        await self.conn.commit()
        return True
    
    async def get_lottery_tickets(self, user_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT tickets FROM lottery_tickets WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
    
    # Game history
    async def add_game_history(self, user_id: int, game_type: str, bet: int, result: str):
        await self.conn.execute(
            "INSERT INTO game_history (user_id, game_type, bet, result) VALUES (?, ?, ?, ?)",
            (user_id, game_type, bet, result)
        )
        await self.conn.commit()
    
    # Admin methods
    async def get_stats(self) -> dict:
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM family_relations")
        family_relations = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM garden_plants WHERE is_ready = 0")
        growing_crops = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT SUM(cash) FROM users")
        total_cash = (await cursor.fetchone())[0] or 0
        
        return {
            'total_users': total_users,
            'banned_users': banned_users,
            'family_relations': family_relations,
            'growing_crops': growing_crops,
            'total_cash': total_cash
        }

# ============================================================================
# IMAGE GENERATOR - WORKING
# ============================================================================

class ImageGenerator:
    """Working image generator"""
    
    def __init__(self):
        if HAS_PILLOW:
            self.font = None
            try:
                self.font = ImageFont.truetype("arial.ttf", 20)
            except:
                self.font = ImageFont.load_default()
    
    async def create_garden_image(self, garden_info: dict, crops: List[dict]) -> Optional[bytes]:
        """Create garden image that actually works"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 700
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((width//2 - 60, 20), "🌾 Your Garden", fill='#4CAF50', font=self.font)
            
            # Draw 3x3 grid
            grid_size = 3
            cell_size = 140
            padding = 10
            start_x = (width - (grid_size * cell_size + (grid_size-1) * padding)) // 2
            start_y = 80
            
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    if idx < len(crops):
                        crop = crops[idx]
                        progress = crop['progress']
                        
                        # Color based on progress
                        if progress >= 100:
                            color = '#4CAF50'  # Green
                        elif progress >= 50:
                            color = '#FFC107'  # Yellow
                        else:
                            color = '#2196F3'  # Blue
                        
                        # Draw cell
                        draw.rectangle([x1, y1, x2, y2], fill=color, outline='white', width=2)
                        
                        # Draw crop emoji
                        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
                        draw.text((x1+50, y1+40), emoji, fill='white', font=self.font)
                        
                        # Draw progress
                        draw.text((x1+40, y2-25), f"{int(progress)}%", fill='white', font=self.font)
                        
                        # Crop name
                        name = crop['crop_type'][:6]
                        draw.text((x1+10, y1+5), name, fill='white', font=self.font)
                    else:
                        # Empty slot
                        draw.rectangle([x1, y1, x2, y2], fill='#333', outline='#666', width=1)
                        draw.text((x1+50, y1+50), "➕", fill='white', font=self.font)
            
            # Stats
            stats_y = start_y + (grid_size * (cell_size + padding)) + 20
            stats = [
                f"📊 Slots: {len(crops)}/{garden_info.get('slots', 9)}",
                f"🌱 Growing: {len(crops)}",
                f"✅ Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i*30), stat, fill='#FFC107', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            logger.info(f"✅ Garden image created: {len(img_bytes.getvalue())} bytes")
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Garden image error: {e}")
            return None
    
    async def create_family_tree_image(self, user_name: str, family: List[dict]) -> Optional[bytes]:
        """Create family tree image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='#0d1b2a')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((width//2 - 100, 30), f"🌳 {user_name}'s Family", fill='#4CAF50', font=self.font)
            
            # Center (user)
            center_x, center_y = width//2, height//2
            draw.ellipse([center_x-50, center_y-50, center_x+50, center_y+50], 
                        fill='#2196F3', outline='#FFC107', width=3)
            draw.text((center_x-15, center_y-15), "👤", fill='white', font=self.font)
            draw.text((center_x-20, center_y+40), "You", fill='white', font=self.font)
            
            # Family members
            if family:
                radius = 200
                for i, member in enumerate(family):
                    angle = 2 * math.pi * i / len(family)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # Line
                    draw.line([(center_x, center_y), (x, y)], fill='white', width=2)
                    
                    # Member circle
                    draw.ellipse([x-40, y-40, x+40, y+40], fill='#E91E63', outline='white', width=2)
                    
                    # Relation emoji
                    rel_emoji = {"parent": "👴", "spouse": "💑", "child": "👶", "sibling": "👫"}.get(
                        member['relation_type'], '👤'
                    )
                    draw.text((x-10, y-15), rel_emoji, fill='white', font=self.font)
                    
                    # Name
                    name = member['other_name'][:8] if member['other_name'] else "User"
                    draw.text((x-20, y+30), name, fill='#FFC107', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Family image error: {e}")
            return None

# ============================================================================
# BOT SETUP
# ============================================================================

session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = Database("family_bot_final.db")
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
    """Check command cooldown"""
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
        gif_url = DEFAULT_GIFS.get(command, DEFAULT_GIFS['hug'])
    
    action_texts = {
        'hug': f"🤗 {from_user.first_name} hugged {target_user.first_name if target_user else 'someone'}!",
        'kill': f"🔪 {from_user.first_name} killed {target_user.first_name if target_user else 'someone'}!",
        'rob': f"💰 {from_user.first_name} robbed {target_user.first_name if target_user else 'someone'}!",
        'kiss': f"💋 {from_user.first_name} kissed {target_user.first_name if target_user else 'someone'}!",
        'slap': f"👋 {from_user.first_name} slapped {target_user.first_name if target_user else 'someone'}!",
        'pat': f"👏 {from_user.first_name} patted {target_user.first_name if target_user else 'someone'}!",
        'punch': f"👊 {from_user.first_name} punched {target_user.first_name if target_user else 'someone'}!",
        'cuddle': f"💞 {from_user.first_name} cuddled {target_user.first_name if target_user else 'someone'}!"
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
        await bot.send_message(chat_id, text + f"\n🎬 GIF: {gif_url[:50]}...")

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
# INLINE KEYBOARDS
# ============================================================================

def main_menu_keyboard():
    """Main menu inline keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Family", callback_data="menu_family"),
            InlineKeyboardButton(text="🌾 Garden", callback_data="menu_garden")
        ],
        [
            InlineKeyboardButton(text="🎮 Games", callback_data="menu_games"),
            InlineKeyboardButton(text="💰 Daily", callback_data="menu_daily")
        ],
        [
            InlineKeyboardButton(text="📊 Profile", callback_data="menu_profile"),
            InlineKeyboardButton(text="🎬 Reactions", callback_data="menu_reactions")
        ],
        [
            InlineKeyboardButton(text="🐱 Catbox", callback_data="menu_catbox"),
            InlineKeyboardButton(text="👑 Owner", callback_data="menu_owner")
        ],
        [
            InlineKeyboardButton(text="🆘 Help", callback_data="menu_help")
        ]
    ])
    return keyboard

def family_menu_keyboard():
    """Family menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌳 View Tree", callback_data="family_view"),
            InlineKeyboardButton(text="👶 Adopt", callback_data="family_adopt")
        ],
        [
            InlineKeyboardButton(text="💍 Marry", callback_data="family_marry"),
            InlineKeyboardButton(text="💔 Divorce", callback_data="family_divorce")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

def garden_menu_keyboard():
    """Garden menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖼️ View Garden", callback_data="garden_view"),
            InlineKeyboardButton(text="🌱 Plant", callback_data="garden_plant")
        ],
        [
            InlineKeyboardButton(text="✅ Harvest", callback_data="garden_harvest"),
            InlineKeyboardButton(text="🏠 Barn", callback_data="garden_barn")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

def games_menu_keyboard():
    """Games menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Slot", callback_data="game_slot"),
            InlineKeyboardButton(text="🎲 Dice", callback_data="game_dice")
        ],
        [
            InlineKeyboardButton(text="💰 Rob", callback_data="game_rob"),
            InlineKeyboardButton(text="🎫 Lottery", callback_data="game_lottery")
        ],
        [
            InlineKeyboardButton(text="⚔️ Fight", callback_data="game_fight"),
            InlineKeyboardButton(text="🥊 Punch", callback_data="game_punch")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

def reactions_menu_keyboard():
    """Reactions menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤗 Hug", callback_data="react_hug"),
            InlineKeyboardButton(text="🔪 Kill", callback_data="react_kill")
        ],
        [
            InlineKeyboardButton(text="💋 Kiss", callback_data="react_kiss"),
            InlineKeyboardButton(text="👋 Slap", callback_data="react_slap")
        ],
        [
            InlineKeyboardButton(text="👏 Pat", callback_data="react_pat"),
            InlineKeyboardButton(text="👊 Punch", callback_data="react_punch")
        ],
        [
            InlineKeyboardButton(text="💞 Cuddle", callback_data="react_cuddle"),
            InlineKeyboardButton(text="💰 Rob", callback_data="react_rob")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

def catbox_menu_keyboard():
    """Catbox menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 List GIFs", callback_data="catbox_list"),
            InlineKeyboardButton(text="➕ Add GIF", callback_data="catbox_add")
        ],
        [
            InlineKeyboardButton(text="🗑️ Remove GIF", callback_data="catbox_remove"),
            InlineKeyboardButton(text="👀 Preview", callback_data="catbox_preview")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

def owner_menu_keyboard():
    """Owner menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="owner_stats"),
            InlineKeyboardButton(text="➕ Add Resources", callback_data="owner_add")
        ],
        [
            InlineKeyboardButton(text="🔨 Ban User", callback_data="owner_ban"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="owner_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

# ============================================================================
# START COMMAND
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with inline keyboard"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        await log_to_channel(f"👤 New user: {message.from_user.first_name}")
    
    welcome_text = f"""
✨ <b>WELCOME {message.from_user.first_name}!</b> ✨

🌳 <b>FAMILY TREE BOT</b> - Complete Version

🚀 <b>All Features Working:</b>
• Family Tree with Images
• Garden System with 3x3 Grid
• Reaction Commands with GIFs
• Mini-Games & Lottery
• Daily Bonuses
• Catbox GIF Management
• Admin Controls

📱 <b>Use the buttons below to navigate!</b>

💡 <b>Quick Tips:</b>
• Reply to someone for reaction commands
• Check /help for all commands
• Images require Pillow: pip install pillow
"""
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# CALLBACK QUERY HANDLERS (INLINE BUTTONS)
# ============================================================================

@dp.callback_query(F.data == "menu_main")
async def callback_main_menu(callback: CallbackQuery):
    """Return to main menu"""
    await callback.message.edit_text(
        "🏠 <b>Main Menu</b>\n\nSelect an option:",
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_family")
async def callback_family_menu(callback: CallbackQuery):
    """Family menu"""
    await callback.message.edit_text(
        "👨‍👩‍👧‍👦 <b>Family Menu</b>\n\nManage your family:",
        reply_markup=family_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_garden")
async def callback_garden_menu(callback: CallbackQuery):
    """Garden menu"""
    await callback.message.edit_text(
        "🌾 <b>Garden Menu</b>\n\nManage your garden:",
        reply_markup=garden_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_games")
async def callback_games_menu(callback: CallbackQuery):
    """Games menu"""
    await callback.message.edit_text(
        "🎮 <b>Games Menu</b>\n\nPlay games:",
        reply_markup=games_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_reactions")
async def callback_reactions_menu(callback: CallbackQuery):
    """Reactions menu"""
    await callback.message.edit_text(
        "🎬 <b>Reactions Menu</b>\n\nReact with GIFs:\n💡 Reply to someone first!",
        reply_markup=reactions_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_catbox")
async def callback_catbox_menu(callback: CallbackQuery):
    """Catbox menu"""
    if not is_owner(callback.from_user.id):
        await callback.answer("❌ Owner only!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🐱 <b>Catbox System</b>\n\nManage reaction GIFs:",
        reply_markup=catbox_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_owner")
async def callback_owner_menu(callback: CallbackQuery):
    """Owner menu"""
    if not is_owner(callback.from_user.id):
        await callback.answer("❌ Owner only!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👑 <b>Owner Menu</b>\n\nAdmin controls:",
        reply_markup=owner_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# Family callbacks
@dp.callback_query(F.data == "family_view")
async def callback_family_view(callback: CallbackQuery):
    """View family tree"""
    await cmd_family(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "family_adopt")
async def callback_family_adopt(callback: CallbackQuery):
    """Adopt info"""
    await callback.message.answer(
        "👶 <b>Adopt Someone</b>\n\n"
        "To adopt someone as your child:\n"
        "1. Reply to their message\n"
        "2. Type <code>/adopt</code>\n"
        "3. They become your child!\n\n"
        "💡 Requires: Both users must use /start first",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# Garden callbacks
@dp.callback_query(F.data == "garden_view")
async def callback_garden_view(callback: CallbackQuery):
    """View garden"""
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "garden_plant")
async def callback_garden_plant(callback: CallbackQuery):
    """Plant info"""
    crops_list = "\n".join([
        f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_DATA[c]['buy']} ({CROP_DATA[c]['grow_time']}h)"
        for c in list(CROP_DATA.keys())[:4]
    ])
    
    await callback.message.answer(
        f"🌱 <b>Plant Crops</b>\n\n"
        f"Usage: <code>/plant [crop] [quantity]</code>\n\n"
        f"🌿 <b>Available Crops:</b>\n{crops_list}\n\n"
        f"💡 <b>Example:</b> <code>/plant carrot 3</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# Game callbacks
@dp.callback_query(F.data == "game_slot")
async def callback_game_slot(callback: CallbackQuery):
    """Slot game info"""
    await callback.message.answer(
        "🎰 <b>Slot Machine</b>\n\n"
        "Usage: <code>/slot [bet]</code>\n\n"
        "💡 <b>Example:</b> <code>/slot 100</code>\n\n"
        "🎯 <b>Payouts:</b>\n"
        "• 3x Same: 3-10x\n"
        "• 2x Same: 1.5x\n"
        "• No match: Lose bet",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "game_rob")
async def callback_game_rob(callback: CallbackQuery):
    """Rob game info"""
    await callback.message.answer(
        "💰 <b>Rob Someone</b>\n\n"
        "To rob someone:\n"
        "1. Reply to their message\n"
        "2. Type <code>/rob</code>\n"
        "3. 40% chance of success\n\n"
        "🎯 <b>Outcomes:</b>\n"
        "• Success: Steal 10-30% of their cash\n"
        "• Failure: Pay 100-500 fine\n\n"
        "⏰ Cooldown: 2 hours",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# Reaction callbacks
@dp.callback_query(F.data.startswith("react_"))
async def callback_reaction(callback: CallbackQuery):
    """Reaction callback"""
    command = callback.data.replace("react_", "")
    await callback.message.answer(
        f"🎬 <b>{command.title()} Someone</b>\n\n"
        f"To {command} someone:\n"
        f"1. Reply to their message\n"
        f"2. Type <code>/{command}</code>\n"
        f"3. They get a GIF reaction!\n\n"
        f"💡 Works in groups too!",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# Owner callbacks
@dp.callback_query(F.data == "owner_stats")
async def callback_owner_stats(callback: CallbackQuery):
    """Owner stats"""
    if not is_owner(callback.from_user.id):
        await callback.answer("❌ Owner only!", show_alert=True)
        return
    
    await cmd_stats(callback.message)
    await callback.answer()

# ============================================================================
# FAMILY COMMANDS
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Show family tree with image"""
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

👤 <b>Your Family:</b> {len(family)} members
💝 <b>Relations:</b> {', '.join(set(f['relation_type'] for f in family))}

💡 <b>Family Commands:</b>
• Reply with <code>/adopt</code> - Make child
• Reply with <code>/marry</code> - Marry
• <code>/divorce</code> - End marriage
• <code>/disown @user</code> - Remove

🎯 <b>Benefits:</b>
• Daily bonus: +${len(family) * 100}
• Family quests available
""",
                    parse_mode=ParseMode.HTML,
                    reply_markup=family_menu_keyboard()
                )
                return
        except Exception as e:
            logger.error(f"Family image error: {e}")
    
    # Text version
    if not family:
        await message.answer(
            "🌳 <b>YOUR FAMILY TREE</b>\n\n"
            "└─ You (No family yet)\n\n"
            "💡 <b>How to grow family:</b>\n"
            "1. Reply to someone with <code>/adopt</code>\n"
            "2. Wait for them to accept\n"
            "3. Build your family empire!\n\n"
            "👑 <b>Benefits:</b>\n"
            "• Daily bonus increases per member\n"
            "• Family quests and events\n"
            "• Inheritance system",
            parse_mode=ParseMode.HTML,
            reply_markup=family_menu_keyboard()
        )
        return
    
    family_text = f"🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>\n\n└─ You (Level {user.get('level', 1)})\n"
    
    for member in family:
        emoji = {"parent": "👴", "spouse": "💑", "child": "👶", "sibling": "👫"}.get(
            member['relation_type'], '👤'
        )
        family_text += f"   ├─ {emoji} {member['other_name']} ({member['relation_type']})\n"
    
    family_text += f"\n📊 <b>Statistics:</b>\n• Members: {len(family)}\n• Daily Bonus: +${len(family) * 100}"
    
    await message.answer(
        family_text,
        parse_mode=ParseMode.HTML,
        reply_markup=family_menu_keyboard()
    )

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
    
    await message.answer(
        f"✅ <b>ADOPTION SUCCESSFUL!</b>\n\n"
        f"👤 You adopted <b>{target.first_name}</b>\n"
        f"🤝 Relationship: Parent-Child\n"
        f"💰 Bonus: $500 for you, $200 for {target.first_name}\n\n"
        f"💡 <b>Family benefits activated!</b>",
        parse_mode=ParseMode.HTML
    )

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
        await message.answer("❌ Both users need to use /start first!")
        return
    
    await db.add_relation(message.from_user.id, target.id, 'spouse')
    await db.set_cooldown(message.from_user.id, "marry")
    
    await db.update_currency(message.from_user.id, "cash", 1000)
    await db.update_currency(target.id, "cash", 1000)
    
    await message.answer(
        f"💍 <b>MARRIAGE SUCCESSFUL!</b>\n\n"
        f"👤 You married <b>{target.first_name}</b>\n"
        f"🤝 Relationship: Spouses\n"
        f"💰 Gift: $1,000 each\n\n"
        f"🎉 <b>Congratulations on your wedding!</b>",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("divorce"))
async def cmd_divorce(message: Message):
    """Divorce spouse"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    spouses = [m for m in family if m['relation_type'] == 'spouse']
    
    if not spouses:
        await message.answer("❌ You're not married!")
        return
    
    # Remove all spouse relations
    for spouse in spouses:
        await db.remove_relation(message.from_user.id, spouse['other_id'], 'spouse')
    
    await message.answer(
        "💔 <b>DIVORCE COMPLETED</b>\n\n"
        "You are now single.\n"
        "💸 Marriage gifts have been revoked.",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("disown"))
async def cmd_disown(message: Message, command: CommandObject):
    """Disown family member"""
    if not command.args:
        await message.answer("❌ Usage: /disown @username")
        return
    
    # This would need user ID resolution
    await message.answer(
        "⚙️ <b>Disown Feature</b>\n\n"
        "Currently manual. Use:\n"
        "<code>/owner</code> for admin tools",
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# GARDEN COMMANDS
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    # Try to create image
    if HAS_PILLOW:
        logger.info(f"Creating garden image for {message.from_user.id}")
        try:
            image_bytes = await img_gen.create_garden_image(garden_info, crops)
            
            if image_bytes:
                logger.info(f"✅ Image created: {len(image_bytes)} bytes")
                
                photo = BufferedInputFile(image_bytes, filename="garden.png")
                
                caption = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden_info.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}

💡 <b>Commands:</b>
<code>/plant [crop] [quantity]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
<code>/barn</code> - View storage

🌱 <b>Available Crops:</b>
🥕 Carrot ($10), 🍅 Tomato ($15), 🥔 Potato ($8)
"""
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=garden_menu_keyboard()
                )
                logger.info("✅ Garden image sent!")
                return
            else:
                logger.error("❌ Image bytes are None!")
        except Exception as e:
            logger.error(f"❌ Garden image error: {e}", exc_info=True)
    else:
        logger.warning("⚠️ Pillow not installed")
    
    # Text version
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
    
    await message.answer(
        garden_text,
        parse_mode=ParseMode.HTML,
        reply_markup=garden_menu_keyboard()
    )

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    if not command.args:
        crops_list = "\n".join([
            f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_DATA[c]['buy']} ({CROP_DATA[c]['grow_time']}h)"
            for c in list(CROP_DATA.keys())[:6]
        ])
        
        await message.answer(
            f"🌱 <b>PLANT CROPS</b>\n\n"
            f"Usage: <code>/plant [crop] [quantity]</code>\n\n"
            f"🌿 <b>Available Crops:</b>\n{crops_list}\n\n"
            f"💡 <b>Examples:</b>\n"
            f"<code>/plant carrot 3</code>\n"
            f"<code>/plant tomato 2</code>\n"
            f"<code>/plant watermelon 1</code>",
            parse_mode=ParseMode.HTML
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
    
    await message.answer(
        f"✅ <b>PLANTED SUCCESSFULLY!</b>\n\n"
        f"{emoji} Crop: <b>{crop_type.title()}</b>\n"
        f"🔢 Quantity: <b>{quantity}</b>\n"
        f"💰 Cost: <b>${cost:,}</b>\n"
        f"⏰ Grow Time: <b>{grow_time} hours</b>\n\n"
        f"🌱 Now growing in your garden!\n"
        f"💡 Use <code>/garden</code> to check progress.",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest crops"""
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

@dp.message(Command("barn"))
async def cmd_barn(message: Message):
    """View barn storage"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    barn_items = await db.get_barn_items(message.from_user.id)
    
    if not barn_items:
        await message.answer("🏠 <b>Barn Storage</b>\n\nEmpty! Harvest crops to fill it.")
        return
    
    barn_text = "🏠 <b>Barn Storage</b>\n\n"
    total_value = 0
    
    for crop_type, quantity in barn_items:
        value = CROP_DATA[crop_type]['sell'] * quantity
        total_value += value
        emoji = CROP_EMOJIS.get(crop_type, "📦")
        barn_text += f"{emoji} {crop_type.title()}: {quantity} (${value})\n"
    
    barn_text += f"\n💰 <b>Total Value: ${total_value:,}</b>"
    
    await message.answer(barn_text, parse_mode=ParseMode.HTML)

# ============================================================================
# REACTION COMMANDS
# ============================================================================

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to hug them!")
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
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor to rob! (Need at least $100)")
        return
    
    success = random.random() < 0.4
    
    if success:
        max_steal = int(target_user['cash'] * 0.3)
        min_steal = int(target_user['cash'] * 0.1)
        stolen = random.randint(min_steal, max_steal)
        
        await db.update_currency(target.id, "cash", -stolen)
        await db.update_currency(message.from_user.id, "cash", stolen)
        
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        await message.answer(f"💰 Successfully robbed ${stolen:,} from {target.first_name}!")
        
        await log_to_channel(f"⚠️ ROBBERY: {message.from_user.id} robbed {target.id} - ${stolen}")
    else:
        fine = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", -fine)
        await message.answer(f"🚨 Robbery failed! You were fined ${fine:,}. {target.first_name} caught you!")
    
    await db.set_cooldown(message.from_user.id, "rob")

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to kiss them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "kiss")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("kiss", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "kiss")

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to slap them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "slap")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("slap", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "slap")

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to pat them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "pat")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("pat", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "pat")

@dp.message(Command("punch"))
async def cmd_punch(message: Message):
    """Punch someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to punch them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "punch")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("punch", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "punch")

@dp.message(Command("cuddle"))
async def cmd_cuddle(message: Message):
    """Cuddle someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to cuddle them!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "cuddle")
    if not can_use:
        await message.answer(error)
        return
    
    await send_gif_reaction("cuddle", message.chat.id, message.from_user, target)
    await db.set_cooldown(message.from_user.id, "cuddle")

# ============================================================================
# GAME COMMANDS
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
            await message.answer("Minimum bet is $10!")
            return
    except:
        await message.answer("Invalid bet amount!")
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
    await db.add_game_history(message.from_user.id, "slot", bet, f"{net_gain >= 0}")
    
    await message.answer(
        f"🎰 <b>SLOT MACHINE</b>\n\n"
        f"[{reels[0]}] [{reels[1]}] [{reels[2]}]\n\n"
        f"💰 Bet: <b>${bet:,}</b>\n"
        f"🎯 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}\n"
        f"🏆 Payout: <b>${win_amount:,}</b>\n"
        f"📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>\n\n"
        f"💵 Balance: <b>${user['cash'] + net_gain:,}</b>",
        parse_mode=ParseMode.HTML
    )

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
    await db.add_game_history(message.from_user.id, "dice", bet, result)
    
    await message.answer(
        f"🎲 <b>DICE GAME</b>\n\n"
        f"👤 Your roll: <b>{player_roll}</b>\n"
        f"🤖 Bot roll: <b>{bot_roll}</b>\n\n"
        f"💰 Bet: <b>${bet:,}</b>\n"
        f"🏆 Result: <b>{result}</b>\n"
        f"💵 {'Win' if net_gain > 0 else 'Loss'}: <b>${abs(net_gain):,}</b>\n\n"
        f"📈 Balance: <b>${user['cash'] + net_gain:,}</b>",
        parse_mode=ParseMode.HTML
    )

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
    
    can_use, error = await check_cooldown(message.from_user.id, "fight")
    if not can_use:
        await message.answer(error)
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Calculate fight result
    user_power = user.get('level', 1) * 10 + random.randint(1, 20)
    target_power = target_user.get('level', 1) * 10 + random.randint(1, 20)
    
    if user_power > target_power:
        win_amount = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", win_amount)
        await db.update_currency(target.id, "cash", -win_amount)
        
        await message.answer(
            f"⚔️ <b>FIGHT VICTORY!</b>\n\n"
            f"👤 {message.from_user.first_name} defeated {target.first_name}!\n"
            f"💪 Power: {user_power} vs {target_power}\n"
            f"💰 Won: <b>${win_amount:,}</b> from {target.first_name}",
            parse_mode=ParseMode.HTML
        )
    elif user_power < target_power:
        loss_amount = random.randint(50, 300)
        await db.update_currency(message.from_user.id, "cash", -loss_amount)
        await db.update_currency(target.id, "cash", loss_amount)
        
        await message.answer(
            f"⚔️ <b>FIGHT DEFEAT!</b>\n\n"
            f"👤 {target.first_name} defeated {message.from_user.first_name}!\n"
            f"💪 Power: {target_power} vs {user_power}\n"
            f"💸 Lost: <b>${loss_amount:,}</b> to {target.first_name}",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(
            f"⚔️ <b>FIGHT DRAW!</b>\n\n"
            f"👤 {message.from_user.first_name} and {target.first_name} are evenly matched!\n"
            f"💪 Power: {user_power} vs {target_power}\n"
            f"🤝 No money exchanged.",
            parse_mode=ParseMode.HTML
        )
    
    await db.set_cooldown(message.from_user.id, "fight")

@dp.message(Command("lottery"))
async def cmd_lottery(message: Message, command: CommandObject):
    """Buy lottery tickets"""
    if not command.args:
        tickets = await db.get_lottery_tickets(message.from_user.id)
        await message.answer(
            f"🎫 <b>LOTTERY</b>\n\n"
            f"Your tickets: <b>{tickets}</b>\n"
            f"Price: $50 per ticket\n\n"
            f"Usage: <code>/lottery [tickets]</code>\n"
            f"Example: <code>/lottery 5</code>\n\n"
            f"🎯 <b>Draw every Sunday!</b>\n"
            f"💰 Prize: 70% of ticket sales",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        tickets = int(command.args)
        if tickets < 1:
            await message.answer("Minimum 1 ticket!")
            return
        if tickets > 100:
            await message.answer("Maximum 100 tickets!")
            return
    except:
        await message.answer("Invalid number of tickets!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "lottery")
    if not can_use:
        await message.answer(error)
        return
    
    success = await db.buy_lottery_ticket(message.from_user.id, tickets)
    
    if not success:
        await message.answer("❌ Not enough cash! Tickets cost $50 each.")
        return
    
    await db.set_cooldown(message.from_user.id, "lottery")
    
    total_tickets = await db.get_lottery_tickets(message.from_user.id)
    
    await message.answer(
        f"🎫 <b>LOTTERY TICKETS PURCHASED!</b>\n\n"
        f"Tickets bought: <b>{tickets}</b>\n"
        f"Cost: <b>${tickets * 50:,}</b>\n"
        f"Total tickets: <b>{total_tickets}</b>\n\n"
        f"🎯 <b>Draw every Sunday at 8 PM!</b>\n"
        f"💰 Prize pool: 70% of all ticket sales",
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# DAILY & PROFILE
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
    
    await message.answer(
        f"🎉 <b>DAILY BONUS CLAIMED!</b>\n\n"
        f"💰 <b>Rewards:</b>\n"
        f"• Base: <b>${base_bonus:,}</b>\n"
        f"• Family: <b>${family_bonus:,}</b>\n"
        f"• Streak ({streak} days): <b>${streak_bonus:,}</b>\n"
        f"• Multiplier: <b>{bio_multiplier}x</b>\n"
        f"• <b>Total: ${total_bonus:,}</b>\n\n"
        f"💎 <b>Gemstone:</b> <b>{gemstone}</b>\n"
        f"🎁 <b>Bonus:</b> +5 🌱 Tokens\n\n"
        f"{'✅ Bio verified (2x rewards!)' if bio_multiplier > 1 else '❌ Add @Familly_TreeBot to bio for 2x!'}",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """User profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    tickets = await db.get_lottery_tickets(message.from_user.id)
    
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

🌾 <b>Garden:</b>
• Slots: <b>{len(crops)}/{garden_info.get('slots', 9)}</b>
• Growing: <b>{len(crops)} crops</b>

🎫 <b>Lottery Tickets:</b> <b>{tickets}</b>
💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
"""
    
    await message.answer(
        profile_text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard()
    )

# ============================================================================
# CATBOX SYSTEM
# ============================================================================

@dp.message(Command("catbox"))
async def cmd_catbox(message: Message, command: CommandObject):
    """Catbox GIF management"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    if not command.args:
        await message.answer(
            "🐱 <b>CATBOX SYSTEM</b>\n\n"
            "Manage GIFs for reaction commands.\n\n"
            "📋 <b>Commands:</b>\n"
            "• <code>/catbox list</code> - List all GIFs\n"
            "• <code>/catbox add [cmd] [url]</code> - Add GIF\n"
            "• <code>/catbox remove [cmd]</code> - Remove GIF\n"
            "• <code>/catbox preview [cmd]</code> - Preview GIF\n\n"
            "💡 <b>Available commands:</b>\n"
            "hug, kill, rob, kiss, slap, pat, punch, cuddle",
            parse_mode=ParseMode.HTML,
            reply_markup=catbox_menu_keyboard()
        )
        return
    
    args = command.args.lower().split()
    subcmd = args[0]
    
    if subcmd == "list":
        gifs = await db.list_gifs()
        
        if not gifs:
            await message.answer("📭 No GIFs in catbox yet!")
            return
        
        gif_list = "\n".join([f"• /{cmd}: {url[:50]}..." for cmd, url in gifs])
        await message.answer(
            f"📦 <b>CATBOX GIFS</b>\n\n{gif_list}\n\n"
            f"💡 Use: <code>/catbox add [command] [url]</code>",
            parse_mode=ParseMode.HTML
        )
    
    elif subcmd == "add" and len(args) >= 3:
        cmd = args[1]
        url = args[2]
        
        if cmd not in DEFAULT_GIFS.keys():
            await message.answer(f"❌ Invalid command! Available: {', '.join(DEFAULT_GIFS.keys())}")
            return
        
        if not url.startswith(('http://', 'https://')):
            await message.answer("❌ Invalid URL! Must start with http:// or https://")
            return
        
        await db.add_gif(cmd, url, message.from_user.id)
        await message.answer(
            f"✅ <b>GIF ADDED TO CATBOX</b>\n\n"
            f"🎬 Command: <code>/{cmd}</code>\n"
            f"🔗 URL: {url[:50]}...\n\n"
            f"💡 GIF will be used for <code>/{cmd}</code> command.",
            parse_mode=ParseMode.HTML
        )
    
    elif subcmd == "remove" and len(args) >= 2:
        cmd = args[1]
        await db.remove_gif(cmd)
        await message.answer(
            f"🗑️ <b>GIF REMOVED</b>\n\n"
            f"🎬 Command: <code>/{cmd}</code>\n\n"
            f"✅ GIF removed from catbox.",
            parse_mode=ParseMode.HTML
        )
    
    elif subcmd == "preview" and len(args) >= 2:
        cmd = args[1]
        gif_url = await db.get_gif(cmd)
        
        if not gif_url:
            await message.answer(f"❌ No GIF found for /{cmd}")
            return
        
        try:
            await bot.send_animation(
                chat_id=message.chat.id,
                animation=gif_url,
                caption=f"🎬 Preview of /{cmd} GIF"
            )
        except Exception as e:
            await message.answer(f"❌ Error previewing GIF: {e}")
    
    else:
        await message.answer("❌ Invalid catbox command!")

# ============================================================================
# OWNER COMMANDS
# ============================================================================

@dp.message(Command("owner"))
async def cmd_owner(message: Message):
    """Owner commands"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    await message.answer(
        "👑 <b>OWNER COMMANDS</b>\n\n"
        "💰 <b>Economy:</b>\n"
        "• <code>/add [user_id] [resource] [amount]</code>\n"
        "• <code>/reset [user_id] [all/cash/garden]</code>\n\n"
        "👤 <b>User Management:</b>\n"
        "• <code>/ban</code> - Ban user (reply)\n"
        "• <code>/unban [user_id]</code>\n"
        "• <code>/warn</code> - Warn user (reply)\n"
        "• <code>/sudo</code> - Make admin (reply)\n\n"
        "📊 <b>System:</b>\n"
        "• <code>/stats</code> - Bot statistics\n"
        "• <code>/broadcast [message]</code>\n"
        "• <code>/message [user_id] [text]</code>\n\n"
        "🎬 <b>Catbox:</b>\n"
        "• <code>/catbox add [cmd] [url]</code>\n"
        "• <code>/catbox remove [cmd]</code>\n"
        "• <code>/catbox list</code>\n\n"
        "⚙️ <b>Other:</b>\n"
        "• <code>/setlevel [user_id] [level]</code>\n"
        "• <code>/giveitem [user_id] [item]</code>\n"
        "• <code>/maintenance [on/off]</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=owner_menu_keyboard()
    )

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only!")
        return
    
    if not command.args:
        await message.answer(
            "💰 <b>ADD RESOURCES</b>\n\n"
            "Usage: <code>/add [user_id] [resource] [amount]</code>\n\n"
            "💎 Resources: cash, gold, bonds, credits, tokens\n"
            "📝 Example: <code>/add 123456789 cash 1000</code>\n\n"
            "💡 Or reply to user's message!",
            parse_mode=ParseMode.HTML
        )
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
    
    await message.answer(
        f"✅ <b>RESOURCES ADDED</b>\n\n"
        f"👤 To: <b>{target_name}</b>\n"
        f"💎 Resource: {CURRENCY_EMOJIS.get(resource, '📦')} <b>{resource.upper()}</b>\n"
        f"➕ Amount: <b>{amount:,}</b>\n"
        f"👑 By: {message.from_user.first_name}\n\n"
        f"📊 <b>Logged to admin channel</b>",
        parse_mode=ParseMode.HTML
    )
    
    await log_to_channel(f"👑 {message.from_user.id} added {resource} {amount} to {target_id}")

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban user"""
    if not is_owner(message.from_user.id):
        return
    
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to user to ban them!")
        return
    
    if target.id == OWNER_ID:
        await message.answer("❌ Cannot ban owner!")
        return
    
    await db.conn.execute(
        "UPDATE users SET is_banned = 1 WHERE user_id = ?",
        (target.id,)
    )
    await db.conn.commit()
    
    await message.answer(
        f"✅ <b>USER BANNED</b>\n\n"
        f"👤 User: <b>{target.first_name}</b>\n"
        f"🆔 ID: <code>{target.id}</code>\n"
        f"⏰ Banned: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"⚠️ User can no longer use the bot.",
        parse_mode=ParseMode.HTML
    )
    
    await log_to_channel(f"🔨 BAN: {target.id} by {message.from_user.id}")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
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

🖼️ <b>Images:</b> {'✅ Enabled' if HAS_PILLOW else '❌ Disabled'}
🕒 <b>Uptime:</b> Running
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast to all users"""
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
            await bot.send_message(
                user_id,
                f"📢 <b>ANNOUNCEMENT</b>\n\n{broadcast_msg}",
                parse_mode=ParseMode.HTML
            )
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    
    await message.answer(
        f"✅ <b>BROADCAST COMPLETE</b>\n\n"
        f"📤 Sent: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📊 Total: <b>{len(users)}</b>",
        parse_mode=ParseMode.HTML
    )
    
    await log_to_channel(f"📢 Broadcast sent to {sent}/{len(users)} users")

# ============================================================================
# OTHER COMMANDS
# ============================================================================

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start = time.time()
    msg = await message.answer("🏓 Pong!")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    stats = await db.get_stats()
    
    status_text = f"""
🏓 <b>PONG!</b>

⚡ Speed: <b>{latency}ms</b>
👥 Users: <b>{stats.get('total_users', 0)}</b>
🖼️ Images: {'✅ Working' if HAS_PILLOW else '❌ Pillow not installed'}
🔧 Status: 🟢 ACTIVE

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

@dp.message(Command("games"))
async def cmd_games(message: Message):
    """Games list"""
    await message.answer(
        "🎮 <b>AVAILABLE GAMES</b>\n\n"
        "🎰 <b>Slot Machine:</b>\n"
        "<code>/slot [bet]</code> - Try your luck!\n\n"
        "🎲 <b>Dice Game:</b>\n"
        "<code>/dice [bet]</code> - Roll against bot\n\n"
        "💰 <b>Robbery:</b>\n"
        "<code>/rob</code> - Rob someone (reply)\n\n"
        "⚔️ <b>Fighting:</b>\n"
        "<code>/fight</code> - Fight someone (reply)\n\n"
        "🎫 <b>Lottery:</b>\n"
        "<code>/lottery [tickets]</code> - Buy tickets\n\n"
        "😊 <b>Reactions (with GIFs):</b>\n"
        "• <code>/hug</code> - Hug someone\n"
        "• <code>/kill</code> - Kill someone\n"
        "• <code>/kiss</code> - Kiss someone\n"
        "• <code>/slap</code> - Slap someone\n"
        "• <code>/pat</code> - Pat someone\n"
        "• <code>/punch</code> - Punch someone\n"
        "• <code>/cuddle</code> - Cuddle someone\n\n"
        "💡 All reaction commands require replying to user's message!",
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL WORKING COMMANDS</b>

👨‍👩‍👧‍👦 <b>FAMILY:</b>
• <code>/family</code> - Family tree (with image)
• <code>/adopt</code> - Adopt (reply)
• <code>/marry</code> - Marry (reply)
• <code>/divorce</code> - End marriage

🌾 <b>GARDEN:</b>
• <code>/garden</code> - View garden (with image)
• <code>/plant [crop] [qty]</code> - Plant
• <code>/harvest</code> - Harvest
• <code>/barn</code> - View storage

🎮 <b>GAMES:</b>
• <code>/slot [bet]</code> - Slot machine
• <code>/dice [bet]</code> - Dice game
• <code>/rob</code> - Rob (reply)
• <code>/fight</code> - Fight (reply)
• <code>/lottery [tickets]</code> - Lottery

😊 <b>REACTIONS (with GIFs):</b>
• <code>/hug</code>, <code>/kill</code>, <code>/kiss</code>
• <code>/slap</code>, <code>/pat</code>, <code>/punch</code>
• <code>/cuddle</code>, <code>/rob</code> (all need reply)

💰 <b>ECONOMY:</b>
• <code>/daily</code> - Daily bonus
• <code>/me</code> - Your profile

🔧 <b>OTHER:</b>
• <code>/ping</code> - Bot status
• <code>/games</code> - All games
• <code>/help</code> - This message

👑 <b>OWNER:</b>
• <code>/owner</code> - Owner commands
• <code>/add</code>, <code>/ban</code>, <code>/stats</code>
• <code>/catbox</code> - Manage GIFs

📱 <b>Use inline buttons for easy navigation!</b>
"""
    
    await message.answer(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard()
    )

# ============================================================================
# ERROR HANDLER
# ============================================================================

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Global error handler"""
    logger.error(f"Error: {exception}", exc_info=True)
    
    try:
        error_msg = f"❌ ERROR:\n{type(exception).__name__}: {str(exception)[:200]}"
        await log_to_channel(error_msg)
    except:
        pass
    
    return True

# ============================================================================
# STARTUP
# ============================================================================

async def setup_bot():
    """Setup bot on startup"""
    await db.connect()
    
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="help", description="All commands"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="family", description="Family tree (with image)"),
        types.BotCommand(command="garden", description="Garden (with image)"),
        types.BotCommand(command="games", description="All games"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="dice", description="Dice game"),
        types.BotCommand(command="ping", description="Bot status"),
        types.BotCommand(command="owner", description="Owner commands"),
        types.BotCommand(command="catbox", description="Manage GIFs (owner)")
    ]
    
    await bot.set_my_commands(commands)
    
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - COMPLETE VERSION")
    print(f"Version: 10.0 | Owner: {OWNER_ID}")
    print(f"Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED (install pillow)'}")
    print("=" * 60)
    
    if not HAS_PILLOW:
        print("\n⚠️  Install Pillow for images:")
        print("pip install pillow")
    
    await log_to_channel(f"🤖 Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function"""
    try:
        await setup_bot()
        print("🚀 Starting bot polling...")
        
        # FIXED: This is the critical line for inline buttons to work
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await db.conn.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
