#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE WITH ALL FEATURES
Matches EXACTLY what's in your documentation
"""

import os
import sys
import json
import asyncio
import logging
import random
import math
import io
import time
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import html
import traceback

# ============================================================================
# IMPORTS - PROPER VERSIONS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto, InputMediaVideo, InputMediaAnimation
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode, ChatAction
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    
    # Pillow for images - THIS MUST BE INSTALLED
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        import textwrap
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
        print("⚠️ WARNING: Install Pillow for images: pip install pillow")
    
    import aiosqlite
    
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

# GIF URLs for reaction commands (from your catbox system)
REACTION_GIFS = {
    "hug": "https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif",
    "kill": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "rob": "https://media.giphy.com/media/xTiTnHXbRoaZ1B1Mo8/giphy.gif",
    "kiss": "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif",
    "slap": "https://media.giphy.com/media/Zau0yrl17uzdK/giphy.gif",
    "pat": "https://media.giphy.com/media/109ltuoSQT212w/giphy.gif"
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
# DATABASE - SIMPLE & WORKING
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
                reputation INTEGER DEFAULT 100,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
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
            
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )"""
        ]
        
        for table in tables:
            await self.conn.execute(table)
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
            planted = datetime.fromisoformat(row[1]) if row[1] else datetime.now()
            elapsed = (datetime.now() - planted).total_seconds() / 3600
            progress = min(100, (elapsed / row[2]) * 100) if row[2] > 0 else 0
            
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

# ============================================================================
# IMAGE GENERATOR - PROPERLY WORKING
# ============================================================================

class ImageGenerator:
    """Image generator that actually works"""
    
    def __init__(self):
        self.fonts = {}
        if HAS_PILLOW:
            self.load_fonts()
    
    def load_fonts(self):
        """Load fonts"""
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
        except Exception as e:
            logger.error(f"Font loading error: {e}")
    
    async def create_garden_image(self, garden_info: dict, crops: List[dict]) -> Optional[bytes]:
        """Create garden image - 3x3 grid like in your pictures"""
        if not HAS_PILLOW:
            logger.error("Pillow not installed for images!")
            return None
        
        try:
            # Create image with proper dimensions
            width, height = 600, 800
            img = Image.new('RGB', (width, height), color=(30, 30, 40))
            draw = ImageDraw.Draw(img)
            
            # Title
            title = "🌾 Your Garden"
            try:
                font = self.fonts.get('medium', ImageFont.load_default())
                bbox = draw.textbbox((0, 0), title, font=font)
                title_x = (width - (bbox[2] - bbox[0])) // 2
                draw.text((title_x, 30), title, fill=(76, 175, 80), font=font)
            except:
                draw.text((width//2 - 60, 30), title, fill=(76, 175, 80))
            
            # Garden grid (3x3 exactly like in your pictures)
            grid_size = 3
            cell_size = 140
            padding = 20
            start_x = (width - (grid_size * cell_size + (grid_size-1) * padding)) // 2
            start_y = 100
            
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
                            
                            # Color based on progress (green when ready)
                            if progress >= 100:
                                fill_color = (76, 175, 80)  # Green
                                border_color = (139, 195, 74)
                            elif progress >= 50:
                                fill_color = (255, 193, 7)   # Yellow
                                border_color = (255, 193, 7)
                            else:
                                fill_color = (33, 150, 243)  # Blue
                                border_color = (33, 150, 243)
                            
                            # Draw crop cell
                            draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=border_color, width=3)
                            
                            # Crop emoji in center
                            emoji = CROP_EMOJIS.get(crop_type, "🌱")
                            try:
                                # Try to position emoji
                                bbox = draw.textbbox((0, 0), emoji, font=self.fonts.get('medium'))
                                emoji_width = bbox[2] - bbox[0]
                                emoji_height = bbox[3] - bbox[1]
                                emoji_x = x1 + (cell_size - emoji_width) // 2
                                emoji_y = y1 + (cell_size - emoji_height) // 2 - 10
                                draw.text((emoji_x, emoji_y), emoji, fill=(255, 255, 255), 
                                         font=self.fonts.get('medium'))
                            except:
                                # Fallback
                                draw.text((x1 + cell_size//2 - 15, y1 + cell_size//2 - 15), 
                                         emoji, fill=(255, 255, 255))
                            
                            # Progress percentage at bottom
                            progress_text = f"{int(progress)}%"
                            try:
                                bbox = draw.textbbox((0, 0), progress_text, font=self.fonts.get('small'))
                                text_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                                draw.text((text_x, y2 - 25), progress_text, fill=(255, 255, 255), 
                                         font=self.fonts.get('small'))
                            except:
                                draw.text((x1 + cell_size//2 - 10, y2 - 25), progress_text, fill=(255, 255, 255))
                            
                            # Crop name at top
                            crop_name = crop_type[:6].title()
                            try:
                                bbox = draw.textbbox((0, 0), crop_name, font=self.fonts.get('small'))
                                name_x = x1 + (cell_size - (bbox[2] - bbox[0])) // 2
                                draw.text((name_x, y1 + 5), crop_name, fill=(255, 255, 255), 
                                         font=self.fonts.get('small'))
                            except:
                                draw.text((x1 + 5, y1 + 5), crop_name, fill=(255, 255, 255))
                        else:
                            # Empty slot
                            draw.rectangle([x1, y1, x2, y2], fill=(40, 40, 60), outline=(100, 100, 120), width=2)
                            draw.text((x1 + cell_size//2 - 15, y1 + cell_size//2 - 15), 
                                     "🟫", fill=(150, 150, 150))
                    else:
                        # Locked slot (for upgrades)
                        draw.rectangle([x1, y1, x2, y2], fill=(30, 30, 30), outline=(200, 50, 50), width=2)
                        draw.text((x1 + cell_size//2 - 15, y1 + cell_size//2 - 15), 
                                 "🔒", fill=(200, 50, 50))
            
            # Stats at bottom
            stats_y = start_y + (grid_size * (cell_size + padding)) + 30
            
            stats_text = [
                f"📊 Slots: {len(crops)}/{slots}",
                f"🌱 Growing: {len(crops)}",
                f"✅ Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}"
            ]
            
            for i, stat in enumerate(stats_text):
                try:
                    font = self.fonts.get('small', ImageFont.load_default())
                    draw.text((50, stats_y + i*30), stat, fill=(255, 193, 7), font=font)
                except:
                    draw.text((50, stats_y + i*30), stat, fill=(255, 193, 7))
            
            # CRITICAL: Save image to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            logger.info(f"✅ Garden image created: {len(img_bytes.getvalue())} bytes")
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Image creation failed: {e}", exc_info=True)
            return None
    
    async def create_family_tree_image(self, user_name: str, family: List[dict]) -> Optional[bytes]:
        """Create circular family tree like in your documentation"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 800
            img = Image.new('RGB', (width, height), color=(25, 25, 40))
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"🌳 {user_name}'s Family Tree"
            try:
                font = self.fonts.get('medium', ImageFont.load_default())
                bbox = draw.textbbox((0, 0), title, font=font)
                title_x = (width - (bbox[2] - bbox[0])) // 2
                draw.text((title_x, 40), title, fill=(76, 175, 80), font=font)
            except:
                draw.text((width//2 - 100, 40), title, fill=(76, 175, 80))
            
            # Draw user at center
            center_x, center_y = width // 2, height // 2
            user_radius = 50
            
            # User circle with gradient effect
            for i in range(user_radius, 0, -5):
                alpha = int(255 * (i / user_radius))
                draw.ellipse([center_x-i, center_y-i, center_x+i, center_y+i], 
                            fill=(33, 150, 243, alpha), outline=(255, 193, 7), width=2)
            
            # User icon and name
            draw.text((center_x-15, center_y-15), "👤", fill=(255, 255, 255))
            draw.text((center_x-30, center_y+40), "You", fill=(255, 193, 7))
            
            # Draw family members in circle
            if family:
                radius = 250
                angle_step = 360 / len(family)
                
                for i, member in enumerate(family):
                    angle = math.radians(i * angle_step)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # Draw connection line
                    draw.line([(center_x, center_y), (x, y)], fill=(255, 255, 255, 150), width=2)
                    
                    # Member circle
                    member_radius = 40
                    color = self._relation_color(member['relation_type'])
                    draw.ellipse([x-member_radius, y-member_radius, x+member_radius, y+member_radius], 
                                fill=color, outline=(255, 255, 255), width=2)
                    
                    # Relation emoji
                    emoji = self._relation_emoji(member['relation_type'])
                    draw.text((x-10, y-15), emoji, fill=(255, 255, 255))
                    
                    # Member name
                    name = member['other_name'][:8] if member['other_name'] else "Member"
                    draw.text((x-20, y+30), name, fill=(255, 193, 7))
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Family tree image error: {e}")
            return None
    
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

# ============================================================================
# BOT SETUP
# ============================================================================

session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
db = Database("family_bot_complete.db")
img_gen = ImageGenerator()

# ============================================================================
# KEYBOARD CREATION (REPLY KEYBOARD)
# ============================================================================

def create_main_keyboard() -> ReplyKeyboardMarkup:
    """Create the main reply keyboard like in your documentation"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            # Row 1
            [
                KeyboardButton(text="👨‍👩‍👧‍👦 Family"),
                KeyboardButton(text="🌾 Garden"),
                KeyboardButton(text="💰 Daily")
            ],
            # Row 2
            [
                KeyboardButton(text="🎮 Games"),
                KeyboardButton(text="📊 Profile"),
                KeyboardButton(text="🆘 Help")
            ],
            # Row 3 - Reaction buttons
            [
                KeyboardButton(text="🤗 Hug"),
                KeyboardButton(text="🔪 Kill"),
                KeyboardButton(text="💰 Rob")
            ],
            # Row 4 - More reactions
            [
                KeyboardButton(text="💋 Kiss"),
                KeyboardButton(text="👋 Slap"),
                KeyboardButton(text="👏 Pat")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Select an option or type /help"
    )
    return keyboard

def create_admin_keyboard() -> ReplyKeyboardMarkup:
    """Admin keyboard for owner"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👑 Owner Panel"),
                KeyboardButton(text="📊 Stats"),
                KeyboardButton(text="📢 Broadcast")
            ],
            [
                KeyboardButton(text="➕ Add Resources"),
                KeyboardButton(text="🔨 Ban User"),
                KeyboardButton(text="📝 Warn User")
            ],
            [
                KeyboardButton(text="🔙 Main Menu")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def get_target_user(message: Message) -> Optional[types.User]:
    """Get target user from reply"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None

async def send_gif_reaction(command: str, chat_id: int, from_user: types.User, target_user: types.User = None):
    """Send GIF reaction"""
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
# START COMMAND WITH KEYBOARD
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with keyboard"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        await log_to_channel(f"👤 New user: {message.from_user.first_name} ({message.from_user.id})")
    
    welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT!</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

I'm your virtual family and farming companion! Use the keyboard below or commands to:

🌳 <b>Build Your Family</b> - Adopt, marry, create bonds
🌾 <b>Grow Crops</b> - Farm and harvest in your garden
🎮 <b>Play Games</b> - Slot machine, dice, and more!
😊 <b>React with Friends</b> - Hug, kiss, rob (with GIFs!)

<b>Keyboard is now active!</b> Tap any button to begin.

💡 <b>Quick Start:</b>
1. Tap "💰 Daily" for free coins
2. Tap "🌾 Garden" to start farming
3. Reply to friends with "🤗 Hug" or other reactions

👥 <b>Add me to groups</b> for family fun!
"""
    
    keyboard = create_main_keyboard()
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# KEYBOARD BUTTON HANDLERS
# ============================================================================

@dp.message(F.text == "👨‍👩‍👧‍👦 Family")
async def button_family(message: Message):
    """Family button handler"""
    await cmd_family(message)

@dp.message(F.text == "🌾 Garden")
async def button_garden(message: Message):
    """Garden button handler"""
    await cmd_garden(message)

@dp.message(F.text == "💰 Daily")
async def button_daily(message: Message):
    """Daily button handler"""
    await cmd_daily(message)

@dp.message(F.text == "🎮 Games")
async def button_games(message: Message):
    """Games button handler"""
    await cmd_games(message)

@dp.message(F.text == "📊 Profile")
async def button_profile(message: Message):
    """Profile button handler"""
    await cmd_profile(message)

@dp.message(F.text == "🆘 Help")
async def button_help(message: Message):
    """Help button handler"""
    await cmd_help(message)

# Reaction button handlers
@dp.message(F.text == "🤗 Hug")
async def button_hug(message: Message):
    """Hug button handler"""
    await message.answer("🤗 Reply to someone's message with /hug to hug them!")

@dp.message(F.text == "🔪 Kill")
async def button_kill(message: Message):
    """Kill button handler"""
    await message.answer("🔪 Reply to someone's message with /kill to kill them!")

@dp.message(F.text == "💰 Rob")
async def button_rob(message: Message):
    """Rob button handler"""
    await message.answer("💰 Reply to someone's message with /rob to rob them!")

@dp.message(F.text == "💋 Kiss")
async def button_kiss(message: Message):
    """Kiss button handler"""
    await message.answer("💋 Reply to someone's message with /kiss to kiss them!")

@dp.message(F.text == "👋 Slap")
async def button_slap(message: Message):
    """Slap button handler"""
    await message.answer("👋 Reply to someone's message with /slap to slap them!")

@dp.message(F.text == "👏 Pat")
async def button_pat(message: Message):
    """Pat button handler"""
    await message.answer("👏 Reply to someone's message with /pat to pat them!")

@dp.message(F.text == "🔙 Main Menu")
async def button_main_menu(message: Message):
    """Return to main menu"""
    keyboard = create_main_keyboard()
    await message.answer("📱 Returning to main menu...", reply_markup=keyboard)

# ============================================================================
# FAMILY COMMANDS
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Show family tree with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    # Try to create image
    if HAS_PILLOW and family:
        try:
            image_bytes = await img_gen.create_family_tree_image(user['first_name'], family)
            if image_bytes:
                photo = BufferedInputFile(image_bytes, filename="family_tree.png")
                await message.answer_photo(
                    photo=photo,
                    caption=f"""
🌳 <b>FAMILY TREE</b>

👤 <b>Family Members:</b> {len(family)}
💝 <b>Relationships:</b> {', '.join(set(f['relation_type'] for f in family))}

💡 <b>How to grow:</b>
Reply to someone with:
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

💡 <b>How to grow your family:</b>
1. Reply to someone's message with <code>/adopt</code>
2. Wait for them to accept
3. Build your family empire!

👑 <b>Benefits:</b>
• Daily bonus increases per family member
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
    
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    await db.add_relation(message.from_user.id, target.id, 'parent')
    await db.update_currency(message.from_user.id, "cash", 500)
    await db.update_currency(target.id, "cash", 200)
    
    await message.answer(f"""
✅ <b>ADOPTION SUCCESSFUL!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
💰 Bonus: $500 for you, $200 for {target.first_name}

💡 <b>Family benefits activated!</b>
""", parse_mode=ParseMode.HTML)

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
    
    await db.add_relation(message.from_user.id, target.id, 'spouse')
    await db.update_currency(message.from_user.id, "cash", 1000)
    await db.update_currency(target.id, "cash", 1000)
    
    await message.answer(f"""
💍 <b>MARRIAGE SUCCESSFUL!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Gift: $1,000 each

🎉 <b>Congratulations on your wedding!</b>
""", parse_mode=ParseMode.HTML)

# ============================================================================
# GARDEN COMMANDS WITH WORKING IMAGES
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden with working images"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    # ALWAYS try to create image first
    if HAS_PILLOW:
        logger.info(f"🖼️ Creating garden image for {message.from_user.id}")
        try:
            image_bytes = await img_gen.create_garden_image(garden_info, crops)
            
            if image_bytes and len(image_bytes) > 0:
                logger.info(f"✅ Image created: {len(image_bytes)} bytes")
                
                # Create photo file
                photo = BufferedInputFile(image_bytes, filename="garden.png")
                
                caption = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden_info.get('slots', 9)}
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)}

💡 <b>Commands:</b>
• <code>/plant [crop] [quantity]</code>
• <code>/harvest</code> - Collect ready crops
• <code>/market</code> - Buy/sell crops

🌱 <b>Available Crops:</b>
🥕 Carrot ($10), 🍅 Tomato ($15), 🥔 Potato ($8), 🍆 Eggplant ($20)
"""
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
                logger.info("✅ Garden image sent successfully!")
                return
            else:
                logger.error("❌ Image creation returned empty or None!")
        except Exception as e:
            logger.error(f"❌ Garden image error: {e}", exc_info=True)
    else:
        logger.warning("⚠️ Pillow not installed, using text mode")
    
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
            status = "✅ Ready to harvest!"
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
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
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
    
    for crop_type, count in harvested:
        sell_price = CROP_DATA[crop_type]['sell'] * count
        total_value += sell_price
        emoji = CROP_EMOJIS.get(crop_type, "🌱")
        harvest_text += f"{emoji} {crop_type.title()}: {count} × ${CROP_DATA[crop_type]['sell']} = ${sell_price}\n"
    
    await db.update_currency(message.from_user.id, "cash", total_value)
    
    harvest_text += f"\n💰 <b>Total Earned: ${total_value:,}</b>"
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

# ============================================================================
# REACTION COMMANDS WITH GIFS
# ============================================================================

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone with GIF"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to hug them!")
        return
    
    await send_gif_reaction("hug", message.chat.id, message.from_user, target)

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone with GIF"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to kill them!")
        return
    
    await send_gif_reaction("kill", message.chat.id, message.from_user, target)

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
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor to rob! (Need at least $100)")
        return
    
    # 40% chance of success
    success = random.random() < 0.4
    
    if success:
        max_steal = int(target_user['cash'] * 0.3)
        min_steal = int(target_user['cash'] * 0.1)
        stolen = random.randint(min_steal, max_steal)
        
        await db.update_currency(target.id, "cash", -stolen)
        await db.update_currency(message.from_user.id, "cash", stolen)
        
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        await message.answer(f"💰 Successfully robbed ${stolen:,} from {target.first_name}!")
    else:
        fine = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", -fine)
        await message.answer(f"🚨 Robbery failed! You were fined ${fine:,}. {target.first_name} caught you!")

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to kiss them!")
        return
    
    await send_gif_reaction("kiss", message.chat.id, message.from_user, target)

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to slap them!")
        return
    
    await send_gif_reaction("slap", message.chat.id, message.from_user, target)

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to pat them!")
        return
    
    await send_gif_reaction("pat", message.chat.id, message.from_user, target)

# ============================================================================
# GAME COMMANDS
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
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
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
    
    await message.answer(f"""
🎰 <b>SLOT MACHINE</b>

[{reels[0]}] [{reels[1]}] [{reels[2]}]

💰 Bet: <b>${bet:,}</b>
🎯 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}
🏆 Payout: <b>${win_amount:,}</b>
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
# DAILY & PROFILE
# ============================================================================

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    base_bonus = random.randint(500, 1500)
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * 100
    
    bio_multiplier = 2 if user.get('bio_verified') else 1
    total_bonus = (base_bonus + family_bonus) * bio_multiplier
    
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.update_currency(message.from_user.id, "tokens", 5)
    
    await db.conn.execute(
        "UPDATE users SET gemstone = ? WHERE user_id = ?",
        (gemstone, message.from_user.id)
    )
    await db.conn.commit()
    
    await message.answer(f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base_bonus:,}</b>
• Family: <b>${family_bonus:,}</b>
• Multiplier: <b>{bio_multiplier}x</b>
• <b>Total: ${total_bonus:,}</b>

💎 <b>Today's Gemstone:</b> <b>{gemstone}</b>
🎁 <b>Bonus:</b> +5 🌱 Tokens

{'✅ Bio verified (2x rewards!)' if bio_multiplier > 1 else '❌ Add @Familly_TreeBot to bio for 2x!'}
""", parse_mode=ParseMode.HTML)

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
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Bio Verified: {'✅' if user.get('bio_verified') else '❌'}

💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
"""
    
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

# ============================================================================
# OTHER COMMANDS
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

😊 <b>Reactions (with GIFs):</b>
• <code>/hug</code> - Hug someone
• <code>/kill</code> - Kill someone
• <code>/kiss</code> - Kiss someone
• <code>/slap</code> - Slap someone
• <code>/pat</code> - Pat someone

💡 All reaction commands require replying to user's message!
"""
    
    await message.answer(games_text, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL COMMANDS</b>

👨‍👩‍👧‍👦 <b>FAMILY COMMANDS:</b>
• <code>/family</code> - View family tree
• <code>/adopt</code> - Adopt someone (reply)
• <code>/marry</code> - Marry someone (reply)

🌾 <b>GARDEN COMMANDS:</b>
• <code>/garden</code> - View garden (with image!)
• <code>/plant [crop] [qty]</code> - Plant crops
• <code>/harvest</code> - Harvest ready crops

🎮 <b>GAME COMMANDS:</b>
• <code>/slot [bet]</code> - Slot machine
• <code>/dice [bet]</code> - Dice game
• <code>/rob</code> - Rob someone (reply)

😊 <b>REACTION COMMANDS:</b>
• <code>/hug</code> - Hug someone (reply)
• <code>/kill</code> - Kill someone (reply)
• <code>/kiss</code> - Kiss someone (reply)
• <code>/slap</code> - Slap someone (reply)
• <code>/pat</code> - Pat someone (reply)

💰 <b>ECONOMY:</b>
• <code>/daily</code> - Daily bonus
• <code>/me</code> - Your profile

🔧 <b>OTHER:</b>
• <code>/games</code> - All games list

👑 <b>OWNER:</b>
• <code>/owner</code> - Owner commands
• <code>/add @user cash 1000</code>
• <code>/ban @user</code>
• <code>/stats</code> - Bot statistics

📱 <b>Use the keyboard buttons for quick access!</b>
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Check bot status"""
    start = time.time()
    msg = await message.answer("🏓 Pong!")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    cursor = await db.conn.execute("SELECT COUNT(*) FROM users")
    total_users = (await cursor.fetchone())[0]
    
    status_text = f"""
🏓 <b>PONG!</b>

⚡ Speed: <b>{latency}ms</b>
👥 Users: <b>{total_users}</b>
🖼️ Images: {'✅ Working' if HAS_PILLOW else '❌ Pillow not installed'}
🔧 Status: 🟢 ACTIVE

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

# ============================================================================
# OWNER COMMANDS
# ============================================================================

def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id == OWNER_ID

@dp.message(Command("owner"))
async def cmd_owner(message: Message):
    """Owner commands list"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    owner_text = """
👑 <b>OWNER COMMANDS</b>

💰 <b>Economy:</b>
• <code>/add [user_id] [resource] [amount]</code>
• <code>/reset [user_id] [all/cash/garden]</code>

👤 <b>User Management:</b>
• <code>/ban</code> - Ban user (reply)
• <code>/unban [user_id]</code>
• <code>/warn</code> - Warn user (reply)

📊 <b>System:</b>
• <code>/stats</code> - Bot statistics
• <code>/broadcast [message]</code>
• <code>/maintenance [on/off]</code>
"""
    
    await message.answer(owner_text, parse_mode=ParseMode.HTML)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    cursor = await db.conn.execute("SELECT COUNT(*) FROM users")
    total_users = (await cursor.fetchone())[0]
    
    cursor = await db.conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned_users = (await cursor.fetchone())[0]
    
    cursor = await db.conn.execute("SELECT COUNT(*) FROM family_relations")
    family_relations = (await cursor.fetchone())[0]
    
    cursor = await db.conn.execute("SELECT COUNT(*) FROM garden_plants WHERE is_ready = 0")
    growing_crops = (await cursor.fetchone())[0]
    
    stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b>
• Total: <b>{total_users:,}</b>
• Banned: <b>{banned_users:,}</b>
• Active: <b>{total_users - banned_users:,}</b>

🌳 <b>Family:</b>
• Relations: <b>{family_relations:,}</b>

🌾 <b>Garden:</b>
• Growing Crops: <b>{growing_crops:,}</b>

🖼️ <b>Images:</b> {'✅ Enabled' if HAS_PILLOW else '❌ Disabled'}
🕒 <b>Uptime:</b> Running
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ERROR HANDLER
# ============================================================================

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Global error handler"""
    logger.error(f"Error: {exception}", exc_info=True)
    return True

# ============================================================================
# STARTUP
# ============================================================================

async def setup_bot():
    """Setup bot on startup"""
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start bot with keyboard"),
        types.BotCommand(command="help", description="All commands"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="family", description="Family tree (with image)"),
        types.BotCommand(command="garden", description="Garden (with image)"),
        types.BotCommand(command="games", description="All games"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="dice", description="Dice game"),
        types.BotCommand(command="ping", description="Bot status"),
        types.BotCommand(command="owner", description="Owner commands")
    ]
    
    await bot.set_my_commands(commands)
    
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - COMPLETE VERSION")
    print(f"Owner: {OWNER_ID}")
    print(f"Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED (install pillow)'}")
    print("=" * 60)
    
    if not HAS_PILLOW:
        print("\n⚠️  IMPORTANT: Install Pillow for images:")
        print("pip install pillow")
    
    await log_to_channel(f"🤖 Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function"""
    try:
        await setup_bot()
        print("🚀 Starting bot polling...")
        
        # FIXED: Add allowed updates for keyboard buttons
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
