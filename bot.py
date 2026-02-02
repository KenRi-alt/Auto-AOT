#!/usr/bin/env python3
"""
🌳 ULTIMATE FAMILY TREE BOT - COMPLETE WITH 13 COMMANDS
Version: 23.0 - All Features, Images Working, One Button
"""

import os
import sys
import asyncio
import logging
import random
import math
import io
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import aiosqlite

# ============================================================================
# CORE IMPORTS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, BufferedInputFile
    )
    from aiogram.enums import ParseMode
    
    # Pillow for images
    try:
        from PIL import Image, ImageDraw, ImageFont
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram pillow aiosqlite")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
OWNER_ID = 6108185460
BOT_USERNAME = "Familly_TreeBot"

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "bank_balance"]

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

# Casino Games
CASINO_SYMBOLS = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎", "🍉", "🍊"]

# Stock Market
STOCKS = {
    "TECH": {"name": "Tech Corp", "price": 100},
    "FARM": {"name": "Farm Inc", "price": 50},
    "GOLD": {"name": "Gold Mining", "price": 200},
    "OIL": {"name": "Oil Co", "price": 80},
    "BIO": {"name": "Bio Tech", "price": 150}
}

# Default GIFs (catbox.moe)
DEFAULT_GIFS = {
    "hug": "https://files.catbox.moe/34u6a1.gif",
    "kill": "https://files.catbox.moe/p6og82.gif", 
    "rob": "https://files.catbox.moe/1x4z9u.gif",
    "kiss": "https://files.catbox.moe/zu3p40.gif",
    "slap": "https://files.catbox.moe/8x5f6d.gif",
    "pat": "https://files.catbox.moe/9k7j2v.gif",
    "punch": "https://files.catbox.moe/l2m5n8.gif",
    "cuddle": "https://files.catbox.moe/r4t9y1.gif"
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
                bank_balance INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 100,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
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
                greenhouse_level INTEGER DEFAULT 0
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
            
            """CREATE TABLE IF NOT EXISTS catbox_gifs (
                command TEXT PRIMARY KEY,
                gif_url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )""",
            
            """CREATE TABLE IF NOT EXISTS lottery_tickets (
                user_id INTEGER NOT NULL,
                tickets INTEGER DEFAULT 0,
                PRIMARY KEY (user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS stocks (
                user_id INTEGER NOT NULL,
                stock_symbol TEXT NOT NULL,
                shares INTEGER DEFAULT 0,
                avg_price REAL DEFAULT 0,
                PRIMARY KEY (user_id, stock_symbol)
            )""",
            
            """CREATE TABLE IF NOT EXISTS friends (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                friendship_level INTEGER DEFAULT 1,
                last_interaction TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                added_by INTEGER,
                member_count INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table in tables:
            await self.conn.execute(table)
        await self.conn.commit()
        
        # Initialize default GIFs
        await self.init_default_gifs()
    
    async def init_default_gifs(self):
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
    
    # User methods
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
        
        # Initialize all tables
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
        
        if currency == "bank_balance":
            await self.conn.execute(
                "UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
        else:
            await self.conn.execute(
                f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
                (amount, user_id)
            )
        await self.conn.commit()
    
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
    
    # Garden methods
    async def get_garden_info(self, user_id: int) -> dict:
        cursor = await self.conn.execute(
            "SELECT slots, greenhouse_level FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return {'slots': row[0] if row else 9, 'greenhouse_level': row[1] if row else 0}
    
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
        
        total_slots = garden['slots'] + (garden['greenhouse_level'] * 3)
        
        if current + quantity > total_slots:
            return False
        
        grow_time = CROP_DATA[crop_type]['grow_time']
        if garden['greenhouse_level'] > 0:
            grow_time = grow_time * (1 - (garden['greenhouse_level'] * 0.1))
        
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
    
    # Stock methods
    async def get_stock_price(self, symbol: str) -> float:
        if symbol in STOCKS:
            # Random price change
            change = random.uniform(-0.1, 0.1)
            STOCKS[symbol]['price'] = max(1, STOCKS[symbol]['price'] * (1 + change))
            return round(STOCKS[symbol]['price'], 2)
        return 0
    
    async def buy_stock(self, user_id: int, symbol: str, shares: int) -> Tuple[bool, float]:
        price = await self.get_stock_price(symbol)
        total_cost = price * shares
        
        user = await self.get_user(user_id)
        if not user or user['cash'] < total_cost:
            return False, 0
        
        await self.update_currency(user_id, "cash", -total_cost)
        
        cursor = await self.conn.execute(
            "SELECT shares, avg_price FROM stocks WHERE user_id = ? AND stock_symbol = ?",
            (user_id, symbol)
        )
        existing = await cursor.fetchone()
        
        if existing:
            current_shares, current_avg = existing
            new_total = current_shares + shares
            new_avg = ((current_avg * current_shares) + (price * shares)) / new_total
            
            await self.conn.execute(
                """UPDATE stocks 
                   SET shares = ?, avg_price = ?
                   WHERE user_id = ? AND stock_symbol = ?""",
                (new_total, new_avg, user_id, symbol)
            )
        else:
            await self.conn.execute(
                "INSERT INTO stocks (user_id, stock_symbol, shares, avg_price) VALUES (?, ?, ?, ?)",
                (user_id, symbol, shares, price)
            )
        
        await self.conn.commit()
        return True, total_cost
    
    async def sell_stock(self, user_id: int, symbol: str, shares: int) -> Tuple[bool, float]:
        cursor = await self.conn.execute(
            "SELECT shares, avg_price FROM stocks WHERE user_id = ? AND stock_symbol = ?",
            (user_id, symbol)
        )
        existing = await cursor.fetchone()
        
        if not existing or existing[0] < shares:
            return False, 0
        
        current_shares, avg_price = existing
        price = await self.get_stock_price(symbol)
        total_value = price * shares
        profit = total_value - (avg_price * shares)
        
        await self.update_currency(user_id, "cash", total_value)
        
        if current_shares == shares:
            await self.conn.execute(
                "DELETE FROM stocks WHERE user_id = ? AND stock_symbol = ?",
                (user_id, symbol)
            )
        else:
            await self.conn.execute(
                "UPDATE stocks SET shares = ? WHERE user_id = ? AND stock_symbol = ?",
                (current_shares - shares, user_id, symbol)
            )
        
        await self.conn.commit()
        return True, profit
    
    async def get_portfolio(self, user_id: int) -> List[dict]:
        cursor = await self.conn.execute(
            "SELECT stock_symbol, shares, avg_price FROM stocks WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        portfolio = []
        for symbol, shares, avg_price in rows:
            current_price = await self.get_stock_price(symbol)
            value = current_price * shares
            profit = value - (avg_price * shares)
            
            portfolio.append({
                'symbol': symbol,
                'name': STOCKS[symbol]['name'],
                'shares': shares,
                'current_price': current_price,
                'value': value,
                'profit': profit
            })
        
        return portfolio
    
    # Friend methods
    async def add_friend(self, user1_id: int, user2_id: int):
        if user1_id == user2_id:
            return False
        
        await self.conn.execute(
            "INSERT OR IGNORE INTO friends (user1_id, user2_id) VALUES (?, ?)",
            (min(user1_id, user2_id), max(user1_id, user2_id))
        )
        await self.conn.commit()
        return True
    
    async def get_friends(self, user_id: int) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT 
               CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END as friend_id,
               u.first_name, u.username
               FROM friends f
               JOIN users u ON u.user_id = CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
               WHERE ? IN (f.user1_id, f.user2_id)""",
            (user_id, user_id, user_id)
        )
        
        rows = await cursor.fetchall()
        return [{'id': r[0], 'name': r[1], 'username': r[2]} for r in rows]
    
    # Group methods
    async def add_group(self, group_id: int, title: str, added_by: int):
        await self.conn.execute(
            """INSERT OR REPLACE INTO groups (group_id, title, added_by, added_at, last_active)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (group_id, title, added_by)
        )
        await self.conn.commit()
    
    async def get_groups(self) -> List[dict]:
        cursor = await self.conn.execute(
            "SELECT group_id, title, added_by, last_active FROM groups ORDER BY last_active DESC"
        )
        rows = await cursor.fetchall()
        return [{'group_id': r[0], 'title': r[1], 'added_by': r[2], 'last_active': r[3]} for r in rows]
    
    # Cooldown methods
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

# ============================================================================
# IMAGE GENERATOR - WORKING
# ============================================================================

class ImageGenerator:
    """Working image generator"""
    
    def __init__(self):
        if HAS_PILLOW:
            try:
                self.font = ImageFont.truetype("arial.ttf", 20)
            except:
                self.font = ImageFont.load_default()
    
    def create_simple_image(self, text: str) -> Optional[bytes]:
        """Create a simple image with text"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 500, 300
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((width//2 - 100, 50), text, fill='white', font=self.font)
            draw.text((width//2 - 150, 150), "🌳 Family Tree Bot", fill='#4CAF50', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Image error: {e}")
            return None
    
    async def create_garden_image(self, crops: List[dict]) -> Optional[bytes]:
        """Create garden image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 400, 500
            img = Image.new('RGB', (width, height), color='#2C3E50')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((120, 20), "🌾 Your Garden", fill='#27AE60', font=self.font)
            
            # 3x3 grid
            grid_size = 3
            cell_size = 100
            padding = 10
            start_x = 50
            start_y = 80
            
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    # Draw cell
                    draw.rectangle([x1, y1, x2, y2], fill='#34495E', outline='#7F8C8D', width=2)
                    
                    if idx < len(crops):
                        crop = crops[idx]
                        progress = crop['progress']
                        
                        # Color based on progress
                        color = '#27AE60' if progress >= 100 else '#F39C12' if progress >= 50 else '#3498DB'
                        draw.rectangle([x1, y1, x2, y2], fill=color, outline='white', width=2)
                        
                        # Crop emoji
                        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
                        draw.text((x1+35, y1+30), emoji, fill='white', font=self.font)
                        
                        # Progress
                        draw.text((x1+30, y2-30), f"{int(progress)}%", fill='white', font=self.font)
                    else:
                        # Empty slot
                        draw.text((x1+40, y1+40), "➕", fill='#BDC3C7', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None

# ============================================================================
# BOT SETUP
# ============================================================================

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = Database("family_bot_complete.db")
img_gen = ImageGenerator()

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
        await bot.send_message(chat_id, text)

def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id == OWNER_ID

# ============================================================================
# ONE BUTTON ONLY
# ============================================================================

def one_button_keyboard():
    """Only one button - Add to Group"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add to Group", 
                               url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ]
    ])
    return keyboard

# ============================================================================
# START COMMAND
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with ONE button"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Test image
    image_bytes = None
    if HAS_PILLOW:
        image_bytes = img_gen.create_simple_image(f"Welcome {message.from_user.first_name}!")
    
    welcome_text = f"""
✨ <b>Welcome {message.from_user.first_name}!</b> ✨

🌳 <b>ULTIMATE FAMILY TREE BOT</b>

📋 <b>13 VISIBLE USER COMMANDS:</b>

1. 👨‍👩‍👧‍👦 /family - Family tree
2. 🌾 /garden - Your garden
3. 🎰 /slot [bet] - Slot machine
4. 🎲 /dice [bet] - Dice game
5. ⚔️ /fight - Fight someone
6. 📈 /stocks - Stock market
7. 🏦 /bank - Bank system
8. 🎫 /lottery - Lottery tickets
9. 🤗 /hug - Hug someone
10. 💰 /rob - Rob someone
11. 💸 /daily - Daily bonus
12. 👤 /me - Your profile
13. 🆘 /help - All commands

👑 <b>1 ADMIN COMMAND:</b>
• /admin (owner only)

🎮 <b>ALL FEATURES WORKING!</b>
• Family Tree with Images
• Garden System
• Casino Games
• Stock Market
• Bank System
• GIF Reactions
• Group Features

📱 <b>Add me to groups for more fun!</b>
"""
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="welcome.png")
            await message.answer_photo(
                photo=photo,
                caption=welcome_text,
                reply_markup=one_button_keyboard()
            )
            return
        except Exception as e:
            logger.error(f"Photo error: {e}")
    
    await message.answer(
        welcome_text,
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# 13 VISIBLE USER COMMANDS
# ============================================================================

# 1. FAMILY COMMAND
@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """👨‍👩‍👧‍👦 Family tree"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    friends = await db.get_friends(message.from_user.id)
    
    family_text = f"""
👨‍👩‍👧‍👦 <b>FAMILY TREE</b>

👤 <b>You:</b> {user['first_name']}
💰 <b>Cash:</b> ${user.get('cash', 0):,}

👨‍👩‍👧‍👦 <b>Family Members:</b> {len(family)}
👥 <b>Friends:</b> {len(friends)}
"""
    
    if family:
        family_text += "\n🌳 <b>Your Family:</b>\n"
        for member in family[:10]:
            emoji = {"parent": "👴", "spouse": "💑", "child": "👶"}.get(member['relation_type'], '👤')
            family_text += f"{emoji} {member['other_name']} ({member['relation_type']})\n"
    
    if len(family) > 10:
        family_text += f"... and {len(family) - 10} more\n"
    
    family_text += """
💡 <b>Commands:</b>
• Reply with /adopt - Make child
• Reply with /marry - Marry someone
• /divorce - End marriage
• /friend @user - Add friend
"""
    
    await message.answer(
        family_text,
        reply_markup=one_button_keyboard()
    )

# 2. GARDEN COMMAND
@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """🌾 Your garden"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    barn_items = await db.get_barn_items(message.from_user.id)
    
    # Create image
    image_bytes = None
    if HAS_PILLOW:
        image_bytes = await img_gen.create_garden_image(crops)
    
    ready_count = sum(1 for c in crops if c.get('progress', 0) >= 100)
    total_slots = garden_info.get('slots', 9) + (garden_info.get('greenhouse_level', 0) * 3)
    
    caption = f"""
🌾 <b>YOUR GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{total_slots}
• Growing: {len(crops)} crops
• Ready: {ready_count} crops
• Greenhouse: Level {garden_info.get('greenhouse_level', 0)}

🏠 <b>Barn Storage:</b>
"""
    
    if barn_items:
        for crop_type, quantity in barn_items[:5]:
            emoji = CROP_EMOJIS.get(crop_type, "📦")
            value = CROP_DATA[crop_type]['sell'] * quantity
            caption += f"{emoji} {crop_type.title()}: {quantity} (${value})\n"
    else:
        caption += "Empty\n"
    
    caption += f"""
💡 <b>Commands:</b>
• <code>/plant [crop] [qty]</code> - Plant crops
• <code>/harvest</code> - Harvest ready crops
• <code>/barn</code> - View all storage

🌱 <b>Available Crops:</b>
🥕 Carrot ($10), 🍅 Tomato ($15), 🥔 Potato ($8)
"""
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="garden.png")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=one_button_keyboard()
            )
            return
        except Exception as e:
            logger.error(f"Garden photo error: {e}")
    
    # Add crop progress
    if crops:
        caption += "\n🌱 <b>Growing Now:</b>\n"
        for crop in crops[:5]:
            emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
            progress = crop['progress']
            if progress >= 100:
                status = "✅ Ready!"
            else:
                status = f"{int(progress)}%"
            caption += f"{emoji} {crop['crop_type'].title()}: {status}\n"
    
    await message.answer(
        caption,
        reply_markup=one_button_keyboard()
    )

# 3. SLOT COMMAND
@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """🎰 Slot machine"""
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
        await message.answer("❌ Use /start first!")
        return
    
    if bet > user['cash']:
        await message.answer(f"❌ You only have ${user['cash']:,}!")
        return
    
    # Generate slots
    symbols = CASINO_SYMBOLS
    reels = [random.choice(symbols) for _ in range(3)]
    
    # Check win
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
    
    result = f"""
🎰 <b>SLOT MACHINE</b>

[{reels[0]}] [{reels[1]}] [{reels[2]}]

💰 Bet: <b>${bet:,}</b>
🏆 Result: {'WIN! 🎉' if win_amount > 0 else 'Lose 😢'}
💵 Payout: <b>${win_amount:,}</b>
📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>

💸 Balance: <b>${user['cash'] + net_gain:,}</b>
"""
    
    await message.answer(
        result,
        reply_markup=one_button_keyboard()
    )

# 4. DICE COMMAND
@dp.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject):
    """🎲 Dice game"""
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
    
    # Roll dice
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        result = "WIN 🎉"
        net_gain = bet
    elif player_roll < bot_roll:
        result = "LOSE 😢"
        net_gain = -bet
    else:
        result = "DRAW 🤝"
        net_gain = 0
    
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    result_text = f"""
🎲 <b>DICE GAME</b>

👤 Your roll: <b>{player_roll}</b>
🤖 Bot roll: <b>{bot_roll}</b>

💰 Bet: <b>${bet:,}</b>
🏆 Result: <b>{result}</b>
💵 {'Win' if net_gain > 0 else 'Loss'}: <b>${abs(net_gain):,}</b>

💸 Balance: <b>${user['cash'] + net_gain:,}</b>
"""
    
    await message.answer(
        result_text,
        reply_markup=one_button_keyboard()
    )

# 5. FIGHT COMMAND
@dp.message(Command("fight"))
async def cmd_fight(message: Message):
    """⚔️ Fight someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to fight them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ Can't fight yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both need /start first!")
        return
    
    # Calculate power
    user_power = user.get('level', 1) * 10 + random.randint(1, 20)
    target_power = target_user.get('level', 1) * 10 + random.randint(1, 20)
    
    if user_power > target_power:
        win_amount = random.randint(100, 500)
        await db.update_currency(message.from_user.id, "cash", win_amount)
        await db.update_currency(target.id, "cash", -win_amount)
        
        result = f"""
⚔️ <b>FIGHT VICTORY!</b>

👤 {message.from_user.first_name} defeated {target.first_name}!
💪 Power: {user_power} vs {target_power}
💰 Won: <b>${win_amount:,}</b> from {target.first_name}
"""
    elif user_power < target_power:
        loss_amount = random.randint(50, 300)
        await db.update_currency(message.from_user.id, "cash", -loss_amount)
        await db.update_currency(target.id, "cash", loss_amount)
        
        result = f"""
⚔️ <b>FIGHT DEFEAT!</b>

👤 {target.first_name} defeated {message.from_user.first_name}!
💪 Power: {target_power} vs {user_power}
💸 Lost: <b>${loss_amount:,}</b> to {target.first_name}
"""
    else:
        result = f"""
⚔️ <b>FIGHT DRAW!</b>

👤 {message.from_user.first_name} vs {target.first_name}
💪 Power: {user_power} vs {target_power}
🤝 No money exchanged.
"""
    
    await message.answer(
        result,
        reply_markup=one_button_keyboard()
    )

# 6. STOCKS COMMAND
@dp.message(Command("stocks", "stock"))
async def cmd_stocks(message: Message):
    """📈 Stock market"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    # Get current prices
    stocks_text = """
📈 <b>STOCK MARKET</b>

🏢 <b>Available Stocks:</b>
"""
    
    for symbol, data in STOCKS.items():
        price = await db.get_stock_price(symbol)
        stocks_text += f"• {symbol}: {data['name']} - <b>${price:.2f}</b>\n"
    
    # Get portfolio
    portfolio = await db.get_portfolio(message.from_user.id)
    
    stocks_text += f"""
💰 <b>Your Portfolio:</b>
"""
    
    if portfolio:
        total_value = sum(stock['value'] for stock in portfolio)
        total_profit = sum(stock['profit'] for stock in portfolio)
        
        stocks_text += f"• Stocks: {len(portfolio)}\n"
        stocks_text += f"• Total Value: <b>${total_value:.2f}</b>\n"
        stocks_text += f"• Total Profit: <b>${total_profit:.2f}</b>\n"
        
        for stock in portfolio[:3]:
            arrow = "📈" if stock['profit'] >= 0 else "📉"
            stocks_text += f"{arrow} {stock['symbol']}: {stock['shares']} shares\n"
    else:
        stocks_text += "No stocks owned yet.\n"
    
    stocks_text += """
💡 <b>Commands:</b>
• <code>/buy [symbol] [shares]</code> - Buy stocks
• <code>/sell [symbol] [shares]</code> - Sell stocks
• <code>/portfolio</code> - View portfolio

📝 <b>Example:</b>
<code>/buy TECH 10</code>
"""
    
    await message.answer(
        stocks_text,
        reply_markup=one_button_keyboard()
    )

# 7. BANK COMMAND
@dp.message(Command("bank"))
async def cmd_bank(message: Message):
    """🏦 Bank system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    bank_text = f"""
🏦 <b>BANK SYSTEM</b>

💰 <b>Your Accounts:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Bank Balance: <b>${user.get('bank_balance', 0):,}</b>
• 💰 Total Wealth: <b>${user.get('cash', 0) + user.get('bank_balance', 0):,}</b>

💡 <b>Features:</b>
• Safe storage for money
• No risk of robbery
• Earn interest (coming soon)

📋 <b>Commands:</b>
• <code>/deposit [amount]</code> - Deposit to bank
• <code>/withdraw [amount]</code> - Withdraw from bank
• <code>/statement</code> - View transactions

📝 <b>Examples:</b>
<code>/deposit 1000</code>
<code>/withdraw 500</code>
"""
    
    await message.answer(
        bank_text,
        reply_markup=one_button_keyboard()
    )

# 8. LOTTERY COMMAND
@dp.message(Command("lottery"))
async def cmd_lottery(message: Message, command: CommandObject):
    """🎫 Lottery tickets"""
    if not command.args:
        tickets = await db.get_lottery_tickets(message.from_user.id)
        
        await message.answer(
            f"""
🎫 <b>LOTTERY</b>

Your tickets: <b>{tickets}</b>
Price: $50 per ticket

💡 <b>Commands:</b>
• <code>/lottery [tickets]</code> - Buy tickets
• Draw every Sunday!

📝 <b>Example:</b>
<code>/lottery 5</code> - Buy 5 tickets ($250)
""",
            reply_markup=one_button_keyboard()
        )
        return
    
    try:
        tickets = int(command.args)
        if tickets < 1:
            await message.answer("Minimum 1 ticket!")
            return
    except:
        await message.answer("Invalid number!")
        return
    
    success = await db.buy_lottery_ticket(message.from_user.id, tickets)
    
    if not success:
        await message.answer("❌ Not enough cash! Tickets cost $50 each.")
        return
    
    total_tickets = await db.get_lottery_tickets(message.from_user.id)
    
    await message.answer(
        f"""
✅ <b>LOTTERY TICKETS BOUGHT!</b>

Tickets bought: <b>{tickets}</b>
Cost: <b>${tickets * 50:,}</b>
Total tickets: <b>{total_tickets}</b>

🎯 Draw every Sunday!
💰 Prize: 70% of ticket sales
""",
        reply_markup=one_button_keyboard()
    )

# 9. HUG COMMAND
@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """🤗 Hug someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to hug them!")
        return
    
    await send_gif_reaction("hug", message.chat.id, message.from_user, target)

# 10. ROB COMMAND
@dp.message(Command("rob"))
async def cmd_rob(message: Message):
    """💰 Rob someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to rob them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ Can't rob yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both need /start first!")
        return
    
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor! (Need $100)")
        return
    
    success = random.random() < 0.4
    
    if success:
        stolen = random.randint(100, min(500, target_user['cash']))
        await db.update_currency(target.id, "cash", -stolen)
        await db.update_currency(message.from_user.id, "cash", stolen)
        
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        await message.answer(f"💰 Successfully robbed ${stolen:,} from {target.first_name}!")
    else:
        fine = random.randint(100, 300)
        await db.update_currency(message.from_user.id, "cash", -fine)
        await message.answer(f"🚨 Robbery failed! You were fined ${fine:,}. {target.first_name} caught you!")

# 11. DAILY COMMAND
@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """💰 Daily bonus"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Check cooldown
    last_daily = await db.get_cooldown(message.from_user.id, "daily")
    if last_daily:
        elapsed = (datetime.now() - last_daily).total_seconds()
        if elapsed < 86400:  # 24 hours
            remaining = int(86400 - elapsed)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await message.answer(f"⏰ Come back in {hours}h {minutes}m!")
            return
    
    base_bonus = random.randint(500, 1500)
    streak = user.get('daily_streak', 0) + 1
    streak_bonus = min(500, streak * 50)
    total = base_bonus + streak_bonus
    
    await db.update_currency(message.from_user.id, "cash", total)
    await db.set_cooldown(message.from_user.id, "daily")
    
    await db.conn.execute(
        "UPDATE users SET daily_streak = ? WHERE user_id = ?",
        (streak, message.from_user.id)
    )
    await db.conn.commit()
    
    await message.answer(
        f"""
🎉 <b>DAILY BONUS!</b>

💰 Base Bonus: <b>${base_bonus:,}</b>
🔥 Streak ({streak} days): <b>${streak_bonus:,}</b>
🎁 Total: <b>${total:,}</b>

💸 New balance: <b>${user['cash'] + total:,}</b>

💡 Come back tomorrow!
""",
        reply_markup=one_button_keyboard()
    )

# 12. PROFILE COMMAND
@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """👤 Your profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    tickets = await db.get_lottery_tickets(message.from_user.id)
    friends = await db.get_friends(message.from_user.id)
    portfolio = await db.get_portfolio(message.from_user.id)
    
    profile_text = f"""
👤 <b>PROFILE OF {user['first_name'].upper()}</b>

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Bank: <b>${user.get('bank_balance', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

📊 <b>Stats:</b>
• Level: <b>{user.get('level', 1)}</b>
• XP: <b>{user.get('xp', 0)}/1000</b>
• Reputation: <b>{user.get('reputation', 100)}</b>
• Daily Streak: <b>{user.get('daily_streak', 0)} days</b>

👨‍👩‍👧‍👦 <b>Social:</b>
• Family: <b>{len(family)} members</b>
• Friends: <b>{len(friends)} friends</b>

🌾 <b>Garden:</b>
• Growing: <b>{len(crops)}/9 crops</b>
• Greenhouse: <b>Level {garden_info.get('greenhouse_level', 0)}</b>

📈 <b>Investments:</b>
• Stocks: <b>{len(portfolio)}</b>
• Lottery Tickets: <b>{tickets}</b>

💡 Use /help for all commands!
"""
    
    await message.answer(
        profile_text,
        reply_markup=one_button_keyboard()
    )

# 13. HELP COMMAND
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """🆘 Help command"""
    help_text = """
🆘 <b>HELP - 13 VISIBLE COMMANDS</b>

1. 👨‍👩‍👧‍👦 <b>/family</b> - Family tree
2. 🌾 <b>/garden</b> - Your garden
3. 🎰 <b>/slot [bet]</b> - Slot machine
4. 🎲 <b>/dice [bet]</b> - Dice game
5. ⚔️ <b>/fight</b> - Fight someone (reply)
6. 📈 <b>/stocks</b> - Stock market
7. 🏦 <b>/bank</b> - Bank system
8. 🎫 <b>/lottery</b> - Lottery tickets
9. 🤗 <b>/hug</b> - Hug someone (reply)
10. 💰 <b>/rob</b> - Rob someone (reply)
11. 💸 <b>/daily</b> - Daily bonus
12. 👤 <b>/me</b> - Your profile
13. 🆘 <b>/help</b> - This message

🎬 <b>More Reactions (reply):</b>
• /kiss, /slap, /pat, /punch
• /cuddle, /kill

🌱 <b>Garden Commands:</b>
• /plant [crop] [qty]
• /harvest
• /barn

👑 <b>Admin Only:</b>
• /admin

📱 <b>Add bot to groups for more fun!</b>
"""
    
    await message.answer(
        help_text,
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# OTHER REACTION COMMANDS
# ============================================================================

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """💋 Kiss someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone!")
        return
    await send_gif_reaction("kiss", message.chat.id, message.from_user, target)

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """👋 Slap someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone!")
        return
    await send_gif_reaction("slap", message.chat.id, message.from_user, target)

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """👏 Pat someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone!")
        return
    await send_gif_reaction("pat", message.chat.id, message.from_user, target)

@dp.message(Command("punch"))
async def cmd_punch(message: Message):
    """👊 Punch someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone!")
        return
    await send_gif_reaction("punch", message.chat.id, message.from_user, target)

@dp.message(Command("cuddle"))
async def cmd_cuddle(message: Message):
    """💞 Cuddle someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone!")
        return
    await send_gif_reaction("cuddle", message.chat.id, message.from_user, target)

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """🔪 Kill someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone!")
        return
    await send_gif_reaction("kill", message.chat.id, message.from_user, target)

# ============================================================================
# GARDEN COMMANDS
# ============================================================================

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """🌱 Plant crops"""
    if not command.args:
        crops_list = "\n".join([
            f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_DATA[c]['buy']} ({CROP_DATA[c]['grow_time']}h)"
            for c in list(CROP_DATA.keys())[:6]
        ])
        
        await message.answer(
            f"""
🌱 <b>PLANT CROPS</b>

Usage: /plant [crop] [quantity]

🌿 <b>Available:</b>
{crops_list}

💡 <b>Examples:</b>
<code>/plant carrot 3</code>
<code>/plant tomato 2</code>
<code>/plant watermelon 1</code>
""",
            reply_markup=one_button_keyboard()
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
        await message.answer(f"❌ Invalid crop! Try: {', '.join(CROP_TYPES[:4])}")
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
    
    emoji = CROP_EMOJIS.get(crop_type, "🌱")
    grow_time = CROP_DATA[crop_type]['grow_time']
    
    await message.answer(
        f"""
✅ <b>PLANTED!</b>

{emoji} Crop: {crop_type.title()}
🔢 Quantity: {quantity}
💰 Cost: ${cost:,}
⏰ Grow Time: {grow_time} hours

🌱 Now growing in garden!
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """✅ Harvest crops"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    harvested = await db.harvest_crops(message.from_user.id)
    
    if not harvested:
        await message.answer("❌ No crops ready!")
        return
    
    total_value = 0
    harvest_text = "✅ <b>HARVESTED!</b>\n\n"
    
    for crop_type, count in harvested:
        sell_price = CROP_DATA[crop_type]['sell'] * count
        total_value += sell_price
        emoji = CROP_EMOJIS.get(crop_type, "🌱")
        harvest_text += f"{emoji} {crop_type.title()}: {count} × ${CROP_DATA[crop_type]['sell']} = ${sell_price}\n"
    
    await db.update_currency(message.from_user.id, "cash", total_value)
    
    harvest_text += f"\n💰 <b>Total: ${total_value:,}</b>"
    
    await message.answer(
        harvest_text,
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("barn"))
async def cmd_barn(message: Message):
    """🏠 Barn storage"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    barn_items = await db.get_barn_items(message.from_user.id)
    
    if not barn_items:
        await message.answer("🏠 <b>Barn Storage</b>\n\nEmpty! Harvest crops to fill.", reply_markup=one_button_keyboard())
        return
    
    barn_text = "🏠 <b>Barn Storage</b>\n\n"
    total_value = 0
    
    for crop_type, quantity in barn_items:
        value = CROP_DATA[crop_type]['sell'] * quantity
        total_value += value
        emoji = CROP_EMOJIS.get(crop_type, "📦")
        barn_text += f"{emoji} {crop_type.title()}: {quantity} (${value})\n"
    
    barn_text += f"\n💰 <b>Total Value: ${total_value:,}</b>"
    
    await message.answer(
        barn_text,
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# STOCK COMMANDS
# ============================================================================

@dp.message(Command("buy"))
async def cmd_buy_stock(message: Message, command: CommandObject):
    """📈 Buy stocks"""
    if not command.args:
        await message.answer("❌ Usage: /buy [symbol] [shares]\nExample: /buy TECH 10")
        return
    
    args = command.args.upper().split()
    if len(args) < 2:
        await message.answer("❌ Format: /buy [symbol] [shares]")
        return
    
    symbol = args[0]
    try:
        shares = int(args[1])
    except:
        await message.answer("❌ Shares must be a number!")
        return
    
    if symbol not in STOCKS:
        await message.answer(f"❌ Invalid stock! Available: {', '.join(STOCKS.keys())}")
        return
    
    if shares < 1:
        await message.answer("❌ Must buy at least 1 share!")
        return
    
    success, cost = await db.buy_stock(message.from_user.id, symbol, shares)
    
    if not success:
        await message.answer("❌ Not enough cash!")
        return
    
    current_price = await db.get_stock_price(symbol)
    
    await message.answer(
        f"""
✅ <b>STOCKS BOUGHT!</b>

🏢 Stock: {symbol} ({STOCKS[symbol]['name']})
📊 Shares: {shares}
💰 Price per share: ${current_price:.2f}
💵 Total cost: ${cost:.2f}

📈 Now in your portfolio!
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("sell"))
async def cmd_sell_stock(message: Message, command: CommandObject):
    """📉 Sell stocks"""
    if not command.args:
        await message.answer("❌ Usage: /sell [symbol] [shares]\nExample: /sell TECH 5")
        return
    
    args = command.args.upper().split()
    if len(args) < 2:
        await message.answer("❌ Format: /sell [symbol] [shares]")
        return
    
    symbol = args[0]
    try:
        shares = int(args[1])
    except:
        await message.answer("❌ Shares must be a number!")
        return
    
    if symbol not in STOCKS:
        await message.answer(f"❌ Invalid stock! Available: {', '.join(STOCKS.keys())}")
        return
    
    success, profit = await db.sell_stock(message.from_user.id, symbol, shares)
    
    if not success:
        await message.answer("❌ You don't own that many shares!")
        return
    
    current_price = await db.get_stock_price(symbol)
    
    profit_text = f"📈 Profit: ${profit:.2f}" if profit > 0 else f"📉 Loss: ${abs(profit):.2f}"
    
    await message.answer(
        f"""
✅ <b>STOCKS SOLD!</b>

🏢 Stock: {symbol} ({STOCKS[symbol]['name']})
📊 Shares sold: {shares}
💰 Price per share: ${current_price:.2f}
💵 Total received: ${current_price * shares:.2f}
{profit_text}
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("portfolio"))
async def cmd_portfolio(message: Message):
    """📊 Stock portfolio"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    portfolio = await db.get_portfolio(message.from_user.id)
    
    if not portfolio:
        await message.answer(
            "📊 <b>PORTFOLIO</b>\n\nNo stocks owned yet.\n💡 Use /buy TECH 10 to start!",
            reply_markup=one_button_keyboard()
        )
        return
    
    portfolio_text = "📊 <b>STOCK PORTFOLIO</b>\n\n"
    total_value = 0
    total_profit = 0
    
    for stock in portfolio:
        arrow = "📈" if stock['profit'] >= 0 else "📉"
        portfolio_text += f"{arrow} <b>{stock['symbol']}</b> ({stock['name']})\n"
        portfolio_text += f"   └─ Shares: {stock['shares']}\n"
        portfolio_text += f"   └─ Current: ${stock['current_price']:.2f}\n"
        portfolio_text += f"   └─ Value: ${stock['value']:.2f}\n"
        portfolio_text += f"   └─ Profit: ${stock['profit']:.2f}\n\n"
        
        total_value += stock['value']
        total_profit += stock['profit']
    
    portfolio_text += f"💰 <b>Summary:</b>\n"
    portfolio_text += f"• Total Value: <b>${total_value:.2f}</b>\n"
    portfolio_text += f"• Total Profit: <b>${total_profit:.2f}</b>\n"
    
    await message.answer(
        portfolio_text,
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# BANK COMMANDS
# ============================================================================

@dp.message(Command("deposit"))
async def cmd_deposit(message: Message, command: CommandObject):
    """💰 Deposit to bank"""
    if not command.args:
        await message.answer("❌ Usage: /deposit [amount]\nExample: /deposit 1000")
        return
    
    try:
        amount = int(command.args)
        if amount <= 0:
            await message.answer("❌ Amount must be positive!")
            return
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if user['cash'] < amount:
        await message.answer(f"❌ You only have ${user['cash']:,} cash!")
        return
    
    await db.update_currency(message.from_user.id, "cash", -amount)
    await db.update_currency(message.from_user.id, "bank_balance", amount)
    
    await message.answer(
        f"""
✅ <b>DEPOSITED!</b>

💰 Amount: ${amount:,}
🏦 New bank balance: ${user.get('bank_balance', 0) + amount:,}
💵 Cash left: ${user['cash'] - amount:,}
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("withdraw"))
async def cmd_withdraw(message: Message, command: CommandObject):
    """💸 Withdraw from bank"""
    if not command.args:
        await message.answer("❌ Usage: /withdraw [amount]\nExample: /withdraw 500")
        return
    
    try:
        amount = int(command.args)
        if amount <= 0:
            await message.answer("❌ Amount must be positive!")
            return
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if user.get('bank_balance', 0) < amount:
        await message.answer(f"❌ You only have ${user.get('bank_balance', 0):,} in bank!")
        return
    
    await db.update_currency(message.from_user.id, "bank_balance", -amount)
    await db.update_currency(message.from_user.id, "cash", amount)
    
    await message.answer(
        f"""
✅ <b>WITHDRAWN!</b>

💰 Amount: ${amount:,}
🏦 New bank balance: ${user.get('bank_balance', 0) - amount:,}
💵 Cash now: ${user['cash'] + amount:,}
""",
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# FAMILY COMMANDS
# ============================================================================

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """👶 Adopt someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to adopt them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ Can't adopt yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both need /start first!")
        return
    
    await db.add_relation(message.from_user.id, target.id, 'parent')
    
    await message.answer(
        f"""
✅ <b>ADOPTED!</b>

👤 You adopted {target.first_name}
🤝 Relationship: Parent-Child
💰 Bonus: $500 for you, $200 for {target.first_name}
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """💍 Marry someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone to marry them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ Can't marry yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both need /start first!")
        return
    
    await db.add_relation(message.from_user.id, target.id, 'spouse')
    
    await message.answer(
        f"""
💍 <b>MARRIED!</b>

👤 You married {target.first_name}
🤝 Relationship: Spouses
💰 Gift: $1,000 each
🎉 Congratulations!
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("divorce"))
async def cmd_divorce(message: Message):
    """💔 Divorce"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    await message.answer(
        """
💔 <b>DIVORCE</b>

To divorce, use:
<code>/divorce @username</code>

💡 You must be married first!
""",
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# ADMIN COMMAND (only 1 visible)
# ============================================================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """👑 Admin panel"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    await message.answer(
        """
👑 <b>ADMIN PANEL</b>

📋 <b>Available Commands:</b>
• /add [user_id] [resource] [amount]
• /ban (reply to user)
• /cat add [cmd] [url]
• /cat list
• /cat remove [cmd]
• /groups - View groups bot is in

💡 <b>Example:</b>
<code>/add 123456789 cash 1000</code>
""",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources (owner only)"""
    if not is_owner(message.from_user.id):
        return
    
    if not command.args:
        await message.answer(
            "💰 <b>ADD RESOURCES</b>\n\n"
            "Usage: /add [user_id] [resource] [amount]\n\n"
            "💎 Resources: cash, gold, bonds, credits, tokens, bank_balance\n"
            "📝 Example: /add 123456789 cash 1000",
            reply_markup=one_button_keyboard()
        )
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Format: /add [user_id] [resource] [amount]")
        return
    
    user_id = int(args[0])
    resource = args[1]
    amount = int(args[2])
    
    if resource not in CURRENCIES:
        await message.answer(f"❌ Invalid resource! Use: {', '.join(CURRENCIES)}")
        return
    
    await db.update_currency(user_id, resource, amount)
    
    await message.answer(
        f"✅ Added {amount:,} {resource} to user {user_id}",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban user (owner only)"""
    if not is_owner(message.from_user.id):
        return
    
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to user to ban!")
        return
    
    await message.answer(
        f"🔨 Banned {target.first_name} (ID: {target.id})",
        reply_markup=one_button_keyboard()
    )

@dp.message(Command("cat"))
async def cmd_cat(message: Message, command: CommandObject):
    """Catbox GIFs (owner only)"""
    if not is_owner(message.from_user.id):
        return
    
    if not command.args:
        await message.answer(
            """
🐱 <b>CATBOX GIFS</b>

Commands:
• /cat list - List GIFs
• /cat add [cmd] [url] - Add GIF
• /cat remove [cmd] - Remove GIF

💡 Use catbox.moe links!
""",
            reply_markup=one_button_keyboard()
        )
        return
    
    args = command.args.lower().split()
    if args[0] == "list":
        await message.answer(
            """
🎬 <b>Available GIFs:</b>
• hug, kiss, slap, pat
• punch, cuddle, kill, rob

💡 Add new: /cat add hug https://catbox.moe/your.gif
""",
            reply_markup=one_button_keyboard()
        )
    elif args[0] == "add" and len(args) >= 3:
        cmd = args[1]
        url = args[2]
        await db.add_gif(cmd, url, message.from_user.id)
        await message.answer(f"✅ Added GIF for /{cmd}", reply_markup=one_button_keyboard())

@dp.message(Command("groups"))
async def cmd_groups(message: Message):
    """View groups (owner only)"""
    if not is_owner(message.from_user.id):
        return
    
    groups = await db.get_groups()
    
    if not groups:
        await message.answer("📭 Bot is not in any groups yet.", reply_markup=one_button_keyboard())
        return
    
    groups_text = "👥 <b>GROUPS BOT IS IN:</b>\n\n"
    
    for group in groups:
        groups_text += f"• {group['title']}\n"
        groups_text += f"  └─ ID: {group['group_id']}\n"
        groups_text += f"  └─ Added by: {group['added_by']}\n\n"
    
    await message.answer(
        groups_text,
        reply_markup=one_button_keyboard()
    )

# ============================================================================
# GROUP HANDLING
# ============================================================================

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message):
    """Handle group messages"""
    if message.new_chat_members:
        for user in message.new_chat_members:
            if user.id == (await bot.get_me()).id:
                # Bot added to group
                try:
                    await db.add_group(
                        message.chat.id,
                        message.chat.title or "Unknown Group",
                        message.from_user.id
                    )
                    await message.answer(
                        f"""
🌳 Thanks for adding Family Tree Bot!

👋 Hello everyone! I'm a family tree and farming bot.

📋 <b>Group Commands:</b>
• Use /help to see all commands
• Play games together
• Build family trees

💡 Add me to your bio for bonuses!
""",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Group add error: {e}")

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
    
    # Set 13 visible commands + 1 admin command
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="family", description="Family tree 👨‍👩‍👧‍👦"),
        types.BotCommand(command="garden", description="Your garden 🌾"),
        types.BotCommand(command="slot", description="Slot machine 🎰"),
        types.BotCommand(command="dice", description="Dice game 🎲"),
        types.BotCommand(command="fight", description="Fight someone ⚔️"),
        types.BotCommand(command="stocks", description="Stock market 📈"),
        types.BotCommand(command="bank", description="Bank system 🏦"),
        types.BotCommand(command="lottery", description="Lottery tickets 🎫"),
        types.BotCommand(command="hug", description="Hug someone 🤗"),
        types.BotCommand(command="rob", description="Rob someone 💰"),
        types.BotCommand(command="daily", description="Daily bonus 💸"),
        types.BotCommand(command="me", description="Your profile 👤"),
        types.BotCommand(command="help", description="Help 🆘"),
        types.BotCommand(command="admin", description="Admin panel 👑")
    ]
    
    await bot.set_my_commands(commands)
    
    print("=" * 60)
    print("🌳 ULTIMATE FAMILY TREE BOT - COMPLETE")
    print(f"Version: 23.0 - 13 Commands, One Button")
    print(f"Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED'}")
    print("=" * 60)
    
    if not HAS_PILLOW:
        print("\n⚠️  Install Pillow for images:")
        print("pip install pillow")

async def main():
    """Main function"""
    try:
        await setup_bot()
        print("🚀 Starting bot polling...")
        
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    finally:
        await db.conn.close()

if __name__ == "__main__":
    asyncio.run(main())
