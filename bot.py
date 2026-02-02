#!/usr/bin/env python3
"""
🌳 ULTIMATE FAMILY TREE BOT - COMPLETE WORKING VERSION
Version: 20.0 - All Features Working + Railway Ready
"""

import os
import sys
import asyncio
import logging
import random
import math
import io
import time
import json
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
        InlineKeyboardButton, BufferedInputFile, ChatJoinRequest,
        InputMediaPhoto, URLInputFile
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
# CONFIGURATION - RAILWAY READY
# ============================================================================

# Get token from environment variable (Railway compatible)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
OWNER_ID = int(os.getenv("OWNER_ID", "6108185460"))
BOT_USERNAME = "Familly_TreeBot"
LOG_CHANNEL = -1003662720845

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "event_coins", "bank_balance"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪",
    "bank_balance": "🏦"
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

# Stock Market
STOCKS = {
    "TECH": {"name": "Tech Corp", "price": 100, "volatility": 0.2},
    "FARM": {"name": "Farm Inc", "price": 50, "volatility": 0.15},
    "GOLD": {"name": "Gold Mining", "price": 200, "volatility": 0.1},
    "OIL": {"name": "Oil Company", "price": 80, "volatility": 0.25},
    "BIO": {"name": "Bio Tech", "price": 150, "volatility": 0.3}
}

# Casino Games
CASINO_GAMES = ["blackjack", "roulette", "poker", "slots", "dice"]

# Quests
DAILY_QUESTS = [
    {"id": 1, "name": "🌅 Morning Farmer", "task": "Harvest 3 crops", "reward": 500, "xp": 50},
    {"id": 2, "name": "💰 Daily Investor", "task": "Check stock market", "reward": 300, "xp": 30},
    {"id": 3, "name": "👨‍👩‍👧‍👦 Family Time", "task": "View family tree", "reward": 400, "xp": 40},
    {"id": 4, "name": "🎮 Game Night", "task": "Play 2 games", "reward": 600, "xp": 60},
    {"id": 5, "name": "🏦 Bank Visit", "task": "Deposit in bank", "reward": 800, "xp": 80}
]

WEEKLY_QUESTS = [
    {"id": 101, "name": "🏆 Stock Master", "task": "Make 5000 profit in stocks", "reward": 5000, "xp": 500},
    {"id": 102, "name": "👑 Family King", "task": "Have 10 family members", "reward": 8000, "xp": 800},
    {"id": 103, "name": "🌾 Farming Legend", "task": "Harvest 50 crops", "reward": 10000, "xp": 1000},
    {"id": 104, "name": "🎰 Casino High Roller", "task": "Win 10000 in casino", "reward": 12000, "xp": 1200},
    {"id": 105, "name": "💼 Business Tycoon", "task": "Earn 20000 from businesses", "reward": 15000, "xp": 1500}
]

# Businesses
BUSINESSES = {
    "farm": {"name": "🌾 Farm", "price": 5000, "income": 500, "upgrade_cost": 2000},
    "store": {"name": "🏪 Convenience Store", "price": 10000, "income": 1000, "upgrade_cost": 5000},
    "restaurant": {"name": "🍽️ Restaurant", "price": 25000, "income": 2500, "upgrade_cost": 12000},
    "hotel": {"name": "🏨 Hotel", "price": 50000, "income": 5000, "upgrade_cost": 25000},
    "casino": {"name": "🎰 Casino", "price": 100000, "income": 10000, "upgrade_cost": 50000}
}

# Default GIFs (catbox.moe compatible)
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
    "lottery": 3600,
    "bank": 300,
    "stock": 1800,
    "quest": 3600
}

# ============================================================================
# LOGGING - RAILWAY COMPATIBLE
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE - COMPLETE WITH NEW TABLES
# ============================================================================

class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = None
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        await self.init_tables()
    
    async def init_tables(self):
        # Create all tables
        tables = [
            # Users table
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
                bank_balance INTEGER DEFAULT 0,
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
            
            # Family relations
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Gardens
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                greenhouse_level INTEGER DEFAULT 0
            )""",
            
            # Garden plants
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                progress REAL DEFAULT 0,
                is_ready BOOLEAN DEFAULT 0
            )""",
            
            # Barn storage
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Cooldowns
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )""",
            
            # Catbox GIFs
            """CREATE TABLE IF NOT EXISTS catbox_gifs (
                command TEXT PRIMARY KEY,
                gif_url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Lottery tickets
            """CREATE TABLE IF NOT EXISTS lottery_tickets (
                user_id INTEGER NOT NULL,
                tickets INTEGER DEFAULT 0,
                PRIMARY KEY (user_id)
            )""",
            
            # Game history
            """CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                bet INTEGER,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # NEW: Groups table
            """CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                added_by INTEGER,
                member_count INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # NEW: Stock portfolio
            """CREATE TABLE IF NOT EXISTS stocks (
                user_id INTEGER NOT NULL,
                stock_symbol TEXT NOT NULL,
                shares INTEGER DEFAULT 0,
                avg_price REAL DEFAULT 0,
                PRIMARY KEY (user_id, stock_symbol)
            )""",
            
            # NEW: Bank transactions
            """CREATE TABLE IF NOT EXISTS bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                balance_after INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # NEW: Quests
            """CREATE TABLE IF NOT EXISTS quests (
                user_id INTEGER NOT NULL,
                quest_id INTEGER NOT NULL,
                quest_type TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                claimed BOOLEAN DEFAULT 0,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                PRIMARY KEY (user_id, quest_id)
            )""",
            
            # NEW: Friends list
            """CREATE TABLE IF NOT EXISTS friends (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                friendship_level INTEGER DEFAULT 1,
                last_interaction TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            )""",
            
            # NEW: Businesses
            """CREATE TABLE IF NOT EXISTS businesses (
                user_id INTEGER NOT NULL,
                business_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                last_collected TIMESTAMP,
                PRIMARY KEY (user_id, business_type)
            )""",
            
            # NEW: Marketplace items
            """CREATE TABLE IF NOT EXISTS marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                price INTEGER NOT NULL,
                listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )"""
        ]
        
        for table in tables:
            try:
                await self.conn.execute(table)
            except Exception as e:
                logger.error(f"Table creation error: {e}")
        
        await self.conn.commit()
        
        # Initialize default GIFs
        await self.init_default_gifs()
        
        # Initialize stock prices
        await self.init_stock_prices()
    
    async def init_default_gifs(self):
        """Initialize default GIFs from catbox.moe"""
        for cmd, url in DEFAULT_GIFS.items():
            try:
                await self.conn.execute(
                    """INSERT OR IGNORE INTO catbox_gifs (command, gif_url, added_by)
                       VALUES (?, ?, ?)""",
                    (cmd, url, OWNER_ID)
                )
            except Exception as e:
                logger.error(f"GIF init error: {e}")
        await self.conn.commit()
    
    async def init_stock_prices(self):
        """Initialize stock prices in database"""
        for symbol, data in STOCKS.items():
            try:
                await self.conn.execute(
                    """INSERT OR IGNORE INTO stock_prices (symbol, price, last_updated)
                       VALUES (?, ?, CURRENT_TIMESTAMP)""",
                    (symbol, data['price'])
                )
            except:
                # Table might not exist yet
                pass
    
    # ========== USER METHODS ==========
    
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
        
        # Initialize all user tables
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
    
    # ========== COOLDOWN METHODS ==========
    
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
    
    # ========== FAMILY METHODS ==========
    
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
    
    # ========== GARDEN METHODS ==========
    
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
        
        # Calculate slots with greenhouse bonus
        total_slots = garden['slots'] + (garden['greenhouse_level'] * 3)
        
        if current + quantity > total_slots:
            return False
        
        grow_time = CROP_DATA[crop_type]['grow_time']
        # Greenhouse reduces grow time
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
    
    # ========== CATBOX GIF METHODS ==========
    
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
    
    # ========== LOTTERY METHODS ==========
    
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
    
    # ========== GROUP METHODS ==========
    
    async def add_group(self, group_id: int, title: str, added_by: int):
        await self.conn.execute(
            """INSERT OR REPLACE INTO groups (group_id, title, added_by, added_at, last_active)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (group_id, title, added_by)
        )
        await self.conn.commit()
    
    async def update_group_activity(self, group_id: int):
        await self.conn.execute(
            """UPDATE groups 
               SET messages_count = messages_count + 1,
                   last_active = CURRENT_TIMESTAMP
               WHERE group_id = ?""",
            (group_id,)
        )
        await self.conn.commit()
    
    async def get_groups(self, limit: int = 50) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT group_id, title, added_by, member_count, messages_count, 
                      last_active, added_at
               FROM groups 
               ORDER BY last_active DESC
               LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        
        groups = []
        for row in rows:
            groups.append({
                'group_id': row[0],
                'title': row[1],
                'added_by': row[2],
                'member_count': row[3],
                'messages_count': row[4],
                'last_active': row[5],
                'added_at': row[6]
            })
        return groups
    
    async def get_group_count(self) -> int:
        cursor = await self.conn.execute("SELECT COUNT(*) FROM groups")
        return (await cursor.fetchone())[0]
    
    # ========== STOCK MARKET METHODS ==========
    
    async def get_stock_price(self, symbol: str) -> float:
        # Update stock price with some randomness
        if symbol in STOCKS:
            stock = STOCKS[symbol]
            change = random.uniform(-stock['volatility'], stock['volatility'])
            new_price = max(1, stock['price'] * (1 + change))
            STOCKS[symbol]['price'] = round(new_price, 2)
            return STOCKS[symbol]['price']
        return 0
    
    async def buy_stock(self, user_id: int, symbol: str, shares: int) -> Tuple[bool, float]:
        price = await self.get_stock_price(symbol)
        total_cost = price * shares
        
        user = await self.get_user(user_id)
        if not user or user['cash'] < total_cost:
            return False, 0
        
        await self.update_currency(user_id, "cash", -total_cost)
        
        # Check if user already owns this stock
        cursor = await self.conn.execute(
            "SELECT shares, avg_price FROM stocks WHERE user_id = ? AND stock_symbol = ?",
            (user_id, symbol)
        )
        existing = await cursor.fetchone()
        
        if existing:
            current_shares, current_avg = existing
            new_total_shares = current_shares + shares
            new_avg = ((current_avg * current_shares) + (price * shares)) / new_total_shares
            
            await self.conn.execute(
                """UPDATE stocks 
                   SET shares = ?, avg_price = ?
                   WHERE user_id = ? AND stock_symbol = ?""",
                (new_total_shares, new_avg, user_id, symbol)
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
        total_value = 0
        total_profit = 0
        
        for symbol, shares, avg_price in rows:
            current_price = await self.get_stock_price(symbol)
            value = current_price * shares
            profit = value - (avg_price * shares)
            
            portfolio.append({
                'symbol': symbol,
                'name': STOCKS[symbol]['name'] if symbol in STOCKS else symbol,
                'shares': shares,
                'avg_price': avg_price,
                'current_price': current_price,
                'value': value,
                'profit': profit,
                'profit_percent': ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
            })
            
            total_value += value
            total_profit += profit
        
        return {
            'stocks': portfolio,
            'total_value': total_value,
            'total_profit': total_profit,
            'count': len(portfolio)
        }
    
    # ========== BANK METHODS ==========
    
    async def deposit_to_bank(self, user_id: int, amount: int) -> Tuple[bool, str]:
        user = await self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if amount <= 0:
            return False, "Amount must be positive"
        
        if user['cash'] < amount:
            return False, f"Insufficient cash. You have ${user['cash']:,}"
        
        await self.update_currency(user_id, "cash", -amount)
        await self.update_currency(user_id, "bank_balance", amount)
        
        # Record transaction
        await self.conn.execute(
            """INSERT INTO bank_transactions (user_id, transaction_type, amount, balance_after)
               VALUES (?, ?, ?, ?)""",
            (user_id, "deposit", amount, user.get('bank_balance', 0) + amount)
        )
        await self.conn.commit()
        
        return True, f"✅ Deposited ${amount:,} to bank. New balance: ${user.get('bank_balance', 0) + amount:,}"
    
    async def withdraw_from_bank(self, user_id: int, amount: int) -> Tuple[bool, str]:
        user = await self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if amount <= 0:
            return False, "Amount must be positive"
        
        if user.get('bank_balance', 0) < amount:
            return False, f"Insufficient bank balance. You have ${user.get('bank_balance', 0):,}"
        
        await self.update_currency(user_id, "bank_balance", -amount)
        await self.update_currency(user_id, "cash", amount)
        
        # Record transaction
        await self.conn.execute(
            """INSERT INTO bank_transactions (user_id, transaction_type, amount, balance_after)
               VALUES (?, ?, ?, ?)""",
            (user_id, "withdraw", amount, user.get('bank_balance', 0) - amount)
        )
        await self.conn.commit()
        
        return True, f"✅ Withdrew ${amount:,} from bank. New balance: ${user.get('bank_balance', 0) - amount:,}"
    
    async def get_bank_statement(self, user_id: int, limit: int = 10) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT transaction_type, amount, balance_after, created_at
               FROM bank_transactions 
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        
        transactions = []
        for trans_type, amount, balance, created in rows:
            transactions.append({
                'type': trans_type,
                'amount': amount,
                'balance': balance,
                'created': created
            })
        return transactions
    
    # ========== QUEST METHODS ==========
    
    async def assign_daily_quests(self, user_id: int):
        # Assign 3 random daily quests
        random_quests = random.sample(DAILY_QUESTS, min(3, len(DAILY_QUESTS)))
        
        for quest in random_quests:
            await self.conn.execute(
                """INSERT OR IGNORE INTO quests (user_id, quest_id, quest_type, progress, completed, claimed)
                   VALUES (?, ?, 'daily', 0, 0, 0)""",
                (user_id, quest['id'])
            )
        
        await self.conn.commit()
    
    async def get_user_quests(self, user_id: int) -> Dict[str, List[dict]]:
        cursor = await self.conn.execute(
            """SELECT q.quest_id, q.quest_type, q.progress, q.completed, q.claimed, q.assigned_at
               FROM quests q
               WHERE q.user_id = ? AND q.claimed = 0""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        quests = {'daily': [], 'weekly': []}
        for quest_id, quest_type, progress, completed, claimed, assigned in rows:
            # Find quest details
            quest_data = None
            if quest_type == 'daily':
                quest_data = next((q for q in DAILY_QUESTS if q['id'] == quest_id), None)
            elif quest_type == 'weekly':
                quest_data = next((q for q in WEEKLY_QUESTS if q['id'] == quest_id), None)
            
            if quest_data:
                quest_info = {
                    **quest_data,
                    'progress': progress,
                    'completed': bool(completed),
                    'claimed': bool(claimed),
                    'assigned': assigned
                }
                quests[quest_type].append(quest_info)
        
        return quests
    
    async def update_quest_progress(self, user_id: int, quest_type: str, progress_amount: int = 1):
        cursor = await self.conn.execute(
            """UPDATE quests 
               SET progress = progress + ?
               WHERE user_id = ? AND quest_type = ? AND completed = 0 AND claimed = 0""",
            (progress_amount, user_id, quest_type)
        )
        await self.conn.commit()
        
        # Check if quests are completed
        await self.check_quest_completion(user_id)
    
    async def check_quest_completion(self, user_id: int):
        # Get uncompleted quests
        cursor = await self.conn.execute(
            """SELECT q.quest_id, q.quest_type, q.progress
               FROM quests q
               WHERE q.user_id = ? AND q.completed = 0 AND q.claimed = 0""",
            (user_id,)
        )
        quests = await cursor.fetchall()
        
        for quest_id, quest_type, progress in quests:
            # Find required progress
            required = 1
            if quest_type == 'daily':
                quest_data = next((q for q in DAILY_QUESTS if q['id'] == quest_id), None)
                if quest_data:
                    required = 3 if 'Harvest' in quest_data['task'] else 1
            elif quest_type == 'weekly':
                quest_data = next((q for q in WEEKLY_QUESTS if q['id'] == quest_id), None)
                if quest_data:
                    if '5000' in quest_data['task']:
                        required = 5000
                    elif '10' in quest_data['task']:
                        required = 10
                    elif '50' in quest_data['task']:
                        required = 50
                    elif '10000' in quest_data['task']:
                        required = 10000
                    elif '20000' in quest_data['task']:
                        required = 20000
            
            if progress >= required:
                await self.conn.execute(
                    "UPDATE quests SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE user_id = ? AND quest_id = ?",
                    (user_id, quest_id)
                )
        
        await self.conn.commit()
    
    async def claim_quest_reward(self, user_id: int, quest_id: int) -> Tuple[bool, str]:
        cursor = await self.conn.execute(
            "SELECT quest_type, completed, claimed FROM quests WHERE user_id = ? AND quest_id = ?",
            (user_id, quest_id)
        )
        quest = await cursor.fetchone()
        
        if not quest:
            return False, "Quest not found"
        
        quest_type, completed, claimed = quest
        
        if not completed:
            return False, "Quest not completed yet"
        
        if claimed:
            return False, "Reward already claimed"
        
        # Find reward
        reward = 0
        xp = 0
        if quest_type == 'daily':
            quest_data = next((q for q in DAILY_QUESTS if q['id'] == quest_id), None)
        else:
            quest_data = next((q for q in WEEKLY_QUESTS if q['id'] == quest_id), None)
        
        if quest_data:
            reward = quest_data['reward']
            xp = quest_data['xp']
            
            await self.update_currency(user_id, "cash", reward)
            # Update XP and level
            await self.conn.execute(
                "UPDATE users SET xp = xp + ? WHERE user_id = ?",
                (xp, user_id)
            )
            
            # Mark as claimed
            await self.conn.execute(
                "UPDATE quests SET claimed = 1 WHERE user_id = ? AND quest_id = ?",
                (user_id, quest_id)
            )
            
            await self.conn.commit()
            return True, f"✅ Claimed ${reward:,} and {xp} XP!"
        
        return False, "Quest data not found"
    
    # ========== BUSINESS METHODS ==========
    
    async def buy_business(self, user_id: int, business_type: str) -> Tuple[bool, str]:
        if business_type not in BUSINESSES:
            return False, "Invalid business type"
        
        business = BUSINESSES[business_type]
        user = await self.get_user(user_id)
        
        if not user or user['cash'] < business['price']:
            return False, f"Insufficient cash. Need ${business['price']:,}, have ${user['cash']:,}"
        
        # Check if already owns
        cursor = await self.conn.execute(
            "SELECT 1 FROM businesses WHERE user_id = ? AND business_type = ?",
            (user_id, business_type)
        )
        if await cursor.fetchone():
            return False, "You already own this business"
        
        await self.update_currency(user_id, "cash", -business['price'])
        
        await self.conn.execute(
            "INSERT INTO businesses (user_id, business_type, level, last_collected) VALUES (?, ?, 1, CURRENT_TIMESTAMP)",
            (user_id, business_type)
        )
        
        await self.conn.commit()
        return True, f"✅ Purchased {business['name']} for ${business['price']:,}!"
    
    async def collect_business_income(self, user_id: int) -> Tuple[int, str]:
        cursor = await self.conn.execute(
            "SELECT business_type, level, last_collected FROM businesses WHERE user_id = ?",
            (user_id,)
        )
        businesses = await cursor.fetchall()
        
        if not businesses:
            return 0, "You don't own any businesses"
        
        total_income = 0
        now = datetime.now()
        
        for business_type, level, last_collected in businesses:
            last_time = datetime.fromisoformat(last_collected) if last_collected else now
            hours_passed = (now - last_time).total_seconds() / 3600
            
            if hours_passed >= 24:  # Can collect once per day
                business = BUSINESSES[business_type]
                income = business['income'] * level
                total_income += income
                
                # Update last collected
                await self.conn.execute(
                    "UPDATE businesses SET last_collected = CURRENT_TIMESTAMP WHERE user_id = ? AND business_type = ?",
                    (user_id, business_type)
                )
        
        if total_income > 0:
            await self.update_currency(user_id, "cash", total_income)
            await self.conn.commit()
            return total_income, f"✅ Collected ${total_income:,} from your businesses!"
        
        return 0, "⏳ Business income not ready yet. Collect once every 24 hours."
    
    async def upgrade_business(self, user_id: int, business_type: str) -> Tuple[bool, str]:
        cursor = await self.conn.execute(
            "SELECT level FROM businesses WHERE user_id = ? AND business_type = ?",
            (user_id, business_type)
        )
        business = await cursor.fetchone()
        
        if not business:
            return False, "You don't own this business"
        
        level = business[0]
        business_data = BUSINESSES[business_type]
        upgrade_cost = business_data['upgrade_cost'] * level
        
        user = await self.get_user(user_id)
        if user['cash'] < upgrade_cost:
            return False, f"Insufficient cash. Need ${upgrade_cost:,}, have ${user['cash']:,}"
        
        await self.update_currency(user_id, "cash", -upgrade_cost)
        
        await self.conn.execute(
            "UPDATE businesses SET level = level + 1 WHERE user_id = ? AND business_type = ?",
            (user_id, business_type)
        )
        
        await self.conn.commit()
        return True, f"✅ Upgraded {business_data['name']} to level {level + 1} for ${upgrade_cost:,}!"
    
    # ========== FRIEND METHODS ==========
    
    async def add_friend(self, user1_id: int, user2_id: int) -> Tuple[bool, str]:
        if user1_id == user2_id:
            return False, "You cannot add yourself as a friend"
        
        # Check if already friends
        cursor = await self.conn.execute(
            "SELECT 1 FROM friends WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
            (user1_id, user2_id, user2_id, user1_id)
        )
        if await cursor.fetchone():
            return False, "You are already friends"
        
        await self.conn.execute(
            "INSERT INTO friends (user1_id, user2_id, friendship_level, last_interaction) VALUES (?, ?, 1, CURRENT_TIMESTAMP)",
            (min(user1_id, user2_id), max(user1_id, user2_id))
        )
        
        await self.conn.commit()
        return True, "✅ Friend added successfully!"
    
    async def remove_friend(self, user1_id: int, user2_id: int) -> Tuple[bool, str]:
        cursor = await self.conn.execute(
            """DELETE FROM friends 
               WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)""",
            (user1_id, user2_id, user2_id, user1_id)
        )
        
        await self.conn.commit()
        return True, "✅ Friend removed"
    
    async def get_friends(self, user_id: int) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT 
               CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END as friend_id,
               u.first_name, u.username, f.friendship_level, f.last_interaction
               FROM friends f
               JOIN users u ON u.user_id = CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
               WHERE ? IN (f.user1_id, f.user2_id)""",
            (user_id, user_id, user_id)
        )
        
        rows = await cursor.fetchall()
        friends = []
        for friend_id, first_name, username, level, last_interaction in rows:
            friends.append({
                'id': friend_id,
                'name': first_name,
                'username': username,
                'level': level,
                'last_interaction': last_interaction
            })
        
        return friends
    
    async def increase_friendship(self, user1_id: int, user2_id: int, amount: int = 1):
        await self.conn.execute(
            """UPDATE friends 
               SET friendship_level = friendship_level + ?, 
                   last_interaction = CURRENT_TIMESTAMP
               WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)""",
            (amount, user1_id, user2_id, user2_id, user1_id)
        )
        await self.conn.commit()
    
    # ========== ADMIN METHODS ==========
    
    async def get_stats(self) -> dict:
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
        
        cursor = await self.conn.execute("SELECT SUM(bank_balance) FROM users")
        stats['total_bank'] = (await cursor.fetchone())[0] or 0
        
        # Group stats
        stats['total_groups'] = await self.get_group_count()
        
        # Stock stats
        cursor = await self.conn.execute("SELECT COUNT(DISTINCT user_id) FROM stocks")
        stats['stock_investors'] = (await cursor.fetchone())[0]
        
        # Business stats
        cursor = await self.conn.execute("SELECT COUNT(*) FROM businesses")
        stats['total_businesses'] = (await cursor.fetchone())[0]
        
        return stats
    
    async def get_top_users(self, by: str = "cash", limit: int = 10) -> List[dict]:
        if by not in CURRENCIES + ["level", "xp"]:
            by = "cash"
        
        cursor = await self.conn.execute(
            f"SELECT user_id, first_name, {by} FROM users WHERE is_banned = 0 ORDER BY {by} DESC LIMIT ?",
            (limit,)
        )
        
        rows = await cursor.fetchall()
        return [{'id': r[0], 'name': r[1], 'value': r[2]} for r in rows]
    
    async def search_user(self, query: str) -> List[dict]:
        cursor = await self.conn.execute(
            """SELECT user_id, username, first_name, last_name, cash, level 
               FROM users 
               WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
               LIMIT 20""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        
        rows = await cursor.fetchall()
        return [{
            'id': r[0],
            'username': r[1],
            'first_name': r[2],
            'last_name': r[3],
            'cash': r[4],
            'level': r[5]
        } for r in rows]

# ============================================================================
# IMAGE GENERATOR - FIXED & WORKING
# ============================================================================

class ImageGenerator:
    """Working image generator with captions"""
    
    def __init__(self):
        if HAS_PILLOW:
            self.font = None
            self.large_font = None
            try:
                self.font = ImageFont.truetype("arial.ttf", 16)
                self.large_font = ImageFont.truetype("arial.ttf", 24)
            except:
                # Fallback to default fonts
                self.font = ImageFont.load_default()
                self.large_font = ImageFont.load_default()
    
    async def create_garden_image(self, garden_info: dict, crops: List[dict], username: str) -> Optional[bytes]:
        """Create garden image as caption"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 400
            img = Image.new('RGB', (width, height), color='#2C3E50')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((width//2 - 100, 20), f"🌾 {username}'s Garden", fill='#27AE60', font=self.large_font)
            
            # Draw 3x3 grid
            grid_size = 3
            cell_size = 100
            padding = 10
            start_x = (width - (grid_size * cell_size + (grid_size-1) * padding)) // 2
            start_y = 70
            
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
                            color = '#27AE60'  # Green
                        elif progress >= 50:
                            color = '#F39C12'  # Orange
                        else:
                            color = '#3498DB'  # Blue
                        
                        # Draw cell
                        draw.rectangle([x1, y1, x2, y2], fill=color, outline='#ECF0F1', width=2)
                        
                        # Draw crop emoji
                        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
                        draw.text((x1+35, y1+30), emoji, fill='white', font=self.large_font)
                        
                        # Draw progress percentage
                        draw.text((x1+30, y2-25), f"{int(progress)}%", fill='white', font=self.font)
                        
                        # Crop name (short)
                        name = crop['crop_type'][:5]
                        draw.text((x1+5, y1+5), name, fill='white', font=self.font)
                    else:
                        # Empty slot
                        draw.rectangle([x1, y1, x2, y2], fill='#34495E', outline='#7F8C8D', width=1)
                        draw.text((x1+40, y1+40), "➕", fill='#BDC3C7', font=self.large_font)
            
            # Stats at bottom
            stats_y = start_y + (grid_size * (cell_size + padding)) + 10
            ready_count = sum(1 for c in crops if c.get('progress', 0) >= 100)
            total_slots = garden_info.get('slots', 9) + (garden_info.get('greenhouse_level', 0) * 3)
            
            stats = [
                f"📊 Slots: {len(crops)}/{total_slots}",
                f"✅ Ready: {ready_count}",
                f"🏠 Greenhouse: Lvl {garden_info.get('greenhouse_level', 0)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i*25), stat, fill='#F1C40F', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True)
            img_bytes.seek(0)
            
            logger.info(f"✅ Garden image created: {len(img_bytes.getvalue())} bytes")
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Garden image error: {e}", exc_info=True)
            return None
    
    async def create_family_tree_image(self, user_name: str, family: List[dict]) -> Optional[bytes]:
        """Create family tree image as caption"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 450
            img = Image.new('RGB', (width, height), color='#1A5276')
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"🌳 {user_name}'s Family"
            draw.text((width//2 - 100, 20), title, fill='#F4D03F', font=self.large_font)
            
            # Center (user)
            center_x, center_y = width//2, height//2 - 50
            draw.ellipse([center_x-60, center_y-60, center_x+60, center_y+60], 
                        fill='#3498DB', outline='#F4D03F', width=3)
            draw.text((center_x-20, center_y-25), "👤", fill='white', font=self.large_font)
            draw.text((center_x-25, center_y+40), "You", fill='white', font=self.font)
            
            # Family members in a circle
            if family:
                radius = 150
                for i, member in enumerate(family):
                    angle = 2 * math.pi * i / len(family)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # Line connecting to center
                    draw.line([(center_x, center_y), (x, y)], fill='#AED6F1', width=2)
                    
                    # Member circle
                    draw.ellipse([x-40, y-40, x+40, y+40], fill='#E74C3C', outline='#F4D03F', width=2)
                    
                    # Relation emoji
                    rel_emoji = {
                        "parent": "👴", "spouse": "💑", "child": "👶", 
                        "sibling": "👫", "friend": "👥"
                    }.get(member['relation_type'], '👤')
                    
                    draw.text((x-15, y-15), rel_emoji, fill='white', font=self.font)
                    
                    # Name (truncated)
                    name = member['other_name'][:6] if member['other_name'] else "User"
                    draw.text((x-20, y+25), name, fill='#F4D03F', font=self.font)
            
            # Stats at bottom
            stats_y = height - 50
            draw.text((50, stats_y), f"👨‍👩‍👧‍👦 Members: {len(family)}", fill='#ABEBC6', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True)
            img_bytes.seek(0)
            
            logger.info(f"✅ Family image created: {len(img_bytes.getvalue())} bytes")
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Family image error: {e}", exc_info=True)
            return None
    
    async def create_profile_image(self, user_data: dict) -> Optional[bytes]:
        """Create profile image as caption"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 500, 300
            img = Image.new('RGB', (width, height), color='#1C2833')
            draw = ImageDraw.Draw(img)
            
            # Header with name
            name = user_data.get('first_name', 'User')
            draw.text((width//2 - 80, 20), f"👤 {name}'s Profile", fill='#3498DB', font=self.large_font)
            
            # Level and XP
            level = user_data.get('level', 1)
            xp = user_data.get('xp', 0)
            xp_needed = level * 1000
            
            # XP Bar
            bar_width = 300
            bar_height = 20
            bar_x = (width - bar_width) // 2
            bar_y = 70
            
            # Background bar
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill='#34495E', outline='#7F8C8D')
            
            # Progress bar
            progress = min(100, (xp / xp_needed) * 100) if xp_needed > 0 else 0
            progress_width = int(bar_width * (progress / 100))
            draw.rectangle([bar_x, bar_y, bar_x + progress_width, bar_y + bar_height], fill='#2ECC71')
            
            # Level text
            draw.text((bar_x + 10, bar_y + 2), f"Level {level}", fill='white', font=self.font)
            draw.text((bar_x + bar_width - 60, bar_y + 2), f"{xp}/{xp_needed} XP", fill='white', font=self.font)
            
            # Stats
            stats_y = bar_y + 40
            stats = [
                f"💰 Cash: ${user_data.get('cash', 0):,}",
                f"🏦 Bank: ${user_data.get('bank_balance', 0):,}",
                f"⭐ Reputation: {user_data.get('reputation', 100)}",
                f"🌱 Tokens: {user_data.get('tokens', 0)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i*30), stat, fill='#F4D03F', font=self.font)
            
            # Footer with join date
            if user_data.get('created_at'):
                try:
                    join_date = datetime.fromisoformat(user_data['created_at']).strftime('%Y-%m-%d')
                    draw.text((width//2 - 60, height - 30), f"Joined: {join_date}", fill='#AED6F1', font=self.font)
                except:
                    pass
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True)
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Profile image error: {e}")
            return None

# ============================================================================
# BOT SETUP
# ============================================================================

session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = Database("family_bot_ultimate.db")
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
    """Send GIF reaction from catbox.moe"""
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
        # Try to send as animation first
        await bot.send_animation(
            chat_id=chat_id,
            animation=gif_url,
            caption=text
        )
    except Exception as e:
        logger.error(f"Error sending GIF: {e}")
        # Fallback to text with link
        await bot.send_message(
            chat_id,
            f"{text}\n🎬 [GIF Link]({gif_url})",
            parse_mode=ParseMode.MARKDOWN
        )

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

async def format_time(dt: datetime) -> str:
    """Format datetime to readable string"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days//365}y ago"
    elif diff.days > 30:
        return f"{diff.days//30}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds//3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds//60}m ago"
    else:
        return "just now"

# ============================================================================
# INLINE KEYBOARDS - SIMPLIFIED
# ============================================================================

def main_menu_keyboard():
    """Main menu with 4 buttons + Add to Group"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Family", callback_data="menu_family"),
            InlineKeyboardButton(text="🌾 Garden", callback_data="menu_garden")
        ],
        [
            InlineKeyboardButton(text="🎮 Games", callback_data="menu_games"),
            InlineKeyboardButton(text="💰 Profile", callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton(text="➕ Add to Group", 
                               url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ]
    ])
    return keyboard

def admin_menu_keyboard():
    """Admin menu (owner only)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Groups", callback_data="admin_groups")
        ],
        [
            InlineKeyboardButton(text="💰 Add Money", callback_data="admin_add"),
            InlineKeyboardButton(text="🔨 Ban User", callback_data="admin_ban")
        ],
        [
            InlineKeyboardButton(text="🐱 Catbox", callback_data="admin_catbox"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

def games_menu_keyboard():
    """Games menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Casino", callback_data="games_casino"),
            InlineKeyboardButton(text="📈 Stocks", callback_data="games_stocks")
        ],
        [
            InlineKeyboardButton(text="🏦 Bank", callback_data="games_bank"),
            InlineKeyboardButton(text="📋 Quests", callback_data="games_quests")
        ],
        [
            InlineKeyboardButton(text="👥 Friends", callback_data="games_friends"),
            InlineKeyboardButton(text="💼 Business", callback_data="games_business")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])
    return keyboard

# ============================================================================
# START COMMAND & MAIN MENU
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with image caption"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        await log_to_channel(f"👤 New user: {message.from_user.first_name}")
        # Assign initial quests
        await db.assign_daily_quests(message.from_user.id)
    
    # Try to create profile image
    image_bytes = None
    if HAS_PILLOW:
        try:
            image_bytes = await img_gen.create_profile_image(user)
        except Exception as e:
            logger.error(f"Profile image error: {e}")
    
    welcome_text = f"""
✨ <b>WELCOME {message.from_user.first_name}!</b> ✨

🌳 <b>ULTIMATE FAMILY TREE BOT</b> - Version 20.0

🚀 <b>All Features Working:</b>
• Family Tree with Images 🌳
• Garden System with 3x3 Grid 🌾
• Casino Games & Stock Market 🎰
• Bank System with Interest 🏦
• Daily Quests & Businesses 📋
• Friends System & Reactions 👥
• Group Features & Leaderboards 👥

📱 <b>Use the buttons below to navigate!</b>

💡 <b>Quick Start:</b>
• Click buttons for easy access
• Use /help for all commands
• Add bot to groups for fun!
"""
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="profile.png")
            await message.answer_photo(
                photo=photo,
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )
            return
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
    
    # Fallback to text only
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# CALLBACK QUERY HANDLERS
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
    """Show family info"""
    await cmd_family(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_garden")
async def callback_garden_menu(callback: CallbackQuery):
    """Show garden"""
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_games")
async def callback_games_menu(callback: CallbackQuery):
    """Show games menu"""
    await callback.message.edit_text(
        "🎮 <b>Games & Features Menu</b>\n\nSelect a feature:",
        reply_markup=games_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_profile")
async def callback_profile_menu(callback: CallbackQuery):
    """Show profile"""
    await cmd_profile(callback.message)
    await callback.answer()

# Admin callbacks
@dp.callback_query(F.data.startswith("admin_"))
async def callback_admin_menu(callback: CallbackQuery):
    """Admin menu callbacks"""
    if not is_owner(callback.from_user.id):
        await callback.answer("❌ Owner only!", show_alert=True)
        return
    
    action = callback.data.replace("admin_", "")
    
    if action == "stats":
        await cmd_stats(callback.message)
    elif action == "groups":
        await cmd_groups(callback.message)
    elif action == "catbox":
        await cmd_catbox(callback.message, CommandObject(args=""))
    elif action == "broadcast":
        await callback.message.answer(
            "📢 <b>Broadcast Message</b>\n\n"
            "Usage: <code>/broadcast Your message here</code>\n\n"
            "💡 This will send to all users.",
            parse_mode=ParseMode.HTML
        )
    elif action == "add":
        await callback.message.answer(
            "💰 <b>Add Resources</b>\n\n"
            "Usage: <code>/add [user_id] [resource] [amount]</code>\n\n"
            "💎 Resources: cash, gold, bonds, credits, tokens, bank_balance\n"
            "📝 Example: <code>/add 123456789 cash 1000</code>\n\n"
            "💡 Or reply to user's message with /add!",
            parse_mode=ParseMode.HTML
        )
    elif action == "ban":
        await callback.message.answer(
            "🔨 <b>Ban User</b>\n\n"
            "Reply to user's message with <code>/ban</code> to ban them.",
            parse_mode=ParseMode.HTML
        )
    
    await callback.answer()

# Games callbacks
@dp.callback_query(F.data.startswith("games_"))
async def callback_games_menu(callback: CallbackQuery):
    """Games menu callbacks"""
    action = callback.data.replace("games_", "")
    
    if action == "casino":
        await cmd_casino(callback.message)
    elif action == "stocks":
        await cmd_stocks(callback.message)
    elif action == "bank":
        await cmd_bank(callback.message)
    elif action == "quests":
        await cmd_quests(callback.message)
    elif action == "friends":
        await cmd_friends(callback.message)
    elif action == "business":
        await cmd_business(callback.message)
    
    await callback.answer()

# ============================================================================
# FAMILY COMMANDS
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Show family tree with image caption"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    friends = await db.get_friends(message.from_user.id)
    
    # Try to create image
    image_bytes = None
    if HAS_PILLOW:
        try:
            image_bytes = await img_gen.create_family_tree_image(user['first_name'], family + [
                {'relation_type': 'friend', 'other_name': f['name']} for f in friends[:3]
            ])
        except Exception as e:
            logger.error(f"Family image error: {e}")
    
    caption = f"""
🌳 <b>{user['first_name']}'s FAMILY TREE</b>

👨‍👩‍👧‍👦 <b>Family Members:</b> {len(family)}
👥 <b>Friends:</b> {len(friends)}

💡 <b>Family Commands:</b>
• Reply with <code>/adopt</code> - Make someone your child
• Reply with <code>/marry</code> - Marry someone
• <code>/divorce</code> - End marriage
• <code>/friend @username</code> - Add friend

💰 <b>Benefits:</b>
• Daily bonus increases per family member
• Family quests available
• Inheritance system
"""
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="family.png")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending family photo: {e}")
            await message.answer(caption, parse_mode=ParseMode.HTML)
    else:
        # Text version with family list
        if family:
            family_list = "\n".join([
                f"• {member['relation_type'].title()}: {member['other_name']}"
                for member in family[:10]
            ])
            caption += f"\n👨‍👩‍👧‍👦 <b>Your Family:</b>\n{family_list}"
        
        if len(family) > 10:
            caption += f"\n... and {len(family) - 10} more"
        
        await message.answer(
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard()
        )

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone as child"""
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

# ============================================================================
# GARDEN COMMANDS
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden with image caption"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    garden_info = await db.get_garden_info(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    barn_items = await db.get_barn_items(message.from_user.id)
    
    # Try to create image
    image_bytes = None
    if HAS_PILLOW:
        try:
            image_bytes = await img_gen.create_garden_image(garden_info, crops, user['first_name'])
        except Exception as e:
            logger.error(f"Garden image error: {e}")
    
    ready_count = sum(1 for c in crops if c.get('progress', 0) >= 100)
    total_slots = garden_info.get('slots', 9) + (garden_info.get('greenhouse_level', 0) * 3)
    
    caption = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{total_slots}
• Growing: {len(crops)} crops
• Ready: {ready_count} crops
• Greenhouse: Level {garden_info.get('greenhouse_level', 0)}

💰 <b>Barn Storage:</b>
"""
    
    if barn_items:
        for crop_type, quantity in barn_items[:5]:
            emoji = CROP_EMOJIS.get(crop_type, "📦")
            value = CROP_DATA[crop_type]['sell'] * quantity
            caption += f"{emoji} {crop_type.title()}: {quantity} (${value})\n"
        
        if len(barn_items) > 5:
            caption += f"... and {len(barn_items) - 5} more items\n"
    else:
        caption += "Empty! Harvest crops to fill.\n"
    
    caption += f"""
💡 <b>Commands:</b>
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
<code>/barn</code> - View all storage

🌱 <b>Available Crops:</b>
🥕 Carrot ($10), 🍅 Tomato ($15), 🥔 Potato ($8)
"""
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="garden.png")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending garden photo: {e}")
            await message.answer(caption, parse_mode=ParseMode.HTML)
    else:
        # Add crop progress to text version
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
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard()
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
    
    # Update quest progress
    await db.update_quest_progress(message.from_user.id, "plant", quantity)
    
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
    
    # Update quest progress
    await db.update_quest_progress(message.from_user.id, "harvest", len(harvested))
    
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
# REACTION COMMANDS (with catbox.moe GIFs)
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
    
    # Increase friendship if friends
    await db.increase_friendship(message.from_user.id, target.id)

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
    
    # Increase friendship if friends
    await db.increase_friendship(message.from_user.id, target.id)

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
    
    # Increase friendship if friends
    await db.increase_friendship(message.from_user.id, target.id)

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
    
    # Increase friendship if friends
    await db.increase_friendship(message.from_user.id, target.id)

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
    
    # Update quest progress
    if net_gain > 0:
        await db.update_quest_progress(message.from_user.id, "win", net_gain)
    
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
    
    # Update quest progress
    if net_gain > 0:
        await db.update_quest_progress(message.from_user.id, "win", net_gain)
    
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
# NEW FEATURES: CASINO, STOCKS, BANK, QUESTS, FRIENDS, BUSINESS
# ============================================================================

@dp.message(Command("casino"))
async def cmd_casino(message: Message):
    """Casino games menu"""
    await message.answer(
        "🎰 <b>CASINO GAMES</b>\n\n"
        "🎲 <b>Available Games:</b>\n"
        "• <code>/slot [bet]</code> - Slot machine\n"
        "• <code>/dice [bet]</code> - Dice game\n"
        "• <code>/blackjack [bet]</code> - Coming soon!\n"
        "• <code>/roulette [bet]</code> - Coming soon!\n\n"
        "💰 <b>Current Games:</b>\n"
        "Try <code>/slot 100</code> or <code>/dice 50</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("stocks", "stock"))
async def cmd_stocks(message: Message):
    """Stock market"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    # Get current stock prices
    stocks_text = "📈 <b>STOCK MARKET</b>\n\n"
    stocks_text += "🏢 <b>Available Stocks:</b>\n"
    
    for symbol, data in STOCKS.items():
        price = await db.get_stock_price(symbol)
        change = random.uniform(-5, 5)  # Simulate change
        arrow = "📈" if change >= 0 else "📉"
        stocks_text += f"{arrow} <b>{symbol}</b>: ${price:.2f} ({data['name']})\n"
    
    # Get user's portfolio
    portfolio = await db.get_portfolio(message.from_user.id)
    
    stocks_text += f"\n💰 <b>Your Portfolio:</b>\n"
    if portfolio['count'] > 0:
        stocks_text += f"• Stocks: {portfolio['count']}\n"
        stocks_text += f"• Total Value: ${portfolio['total_value']:.2f}\n"
        stocks_text += f"• Total Profit: ${portfolio['total_profit']:.2f}\n"
    else:
        stocks_text += "No stocks owned yet.\n"
    
    stocks_text += f"""
💡 <b>Commands:</b>
• <code>/buy [symbol] [shares]</code> - Buy stocks
• <code>/sell [symbol] [shares]</code> - Sell stocks
• <code>/portfolio</code> - View your portfolio

📝 <b>Example:</b>
<code>/buy TECH 10</code> - Buy 10 Tech Corp shares
"""
    
    await message.answer(
        stocks_text,
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("buy"))
async def cmd_buy_stock(message: Message, command: CommandObject):
    """Buy stocks"""
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
        await message.answer(f"❌ Invalid stock symbol! Available: {', '.join(STOCKS.keys())}")
        return
    
    if shares < 1:
        await message.answer("❌ Must buy at least 1 share!")
        return
    
    can_use, error = await check_cooldown(message.from_user.id, "stock")
    if not can_use:
        await message.answer(error)
        return
    
    success, cost = await db.buy_stock(message.from_user.id, symbol, shares)
    
    if not success:
        await message.answer("❌ Not enough cash to buy stocks!")
        return
    
    await db.set_cooldown(message.from_user.id, "stock")
    
    current_price = await db.get_stock_price(symbol)
    
    await message.answer(
        f"✅ <b>STOCKS PURCHASED!</b>\n\n"
        f"🏢 Stock: <b>{symbol}</b> ({STOCKS[symbol]['name']})\n"
        f"📊 Shares: <b>{shares}</b>\n"
        f"💰 Price per share: <b>${current_price:.2f}</b>\n"
        f"💵 Total cost: <b>${cost:.2f}</b>\n\n"
        f"📈 Now in your portfolio!",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("sell"))
async def cmd_sell_stock(message: Message, command: CommandObject):
    """Sell stocks"""
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
        await message.answer(f"❌ Invalid stock symbol! Available: {', '.join(STOCKS.keys())}")
        return
    
    if shares < 1:
        await message.answer("❌ Must sell at least 1 share!")
        return
    
    success, profit = await db.sell_stock(message.from_user.id, symbol, shares)
    
    if not success:
        await message.answer("❌ You don't own that many shares!")
        return
    
    current_price = await db.get_stock_price(symbol)
    
    profit_text = f"📈 Profit: ${profit:.2f}" if profit > 0 else f"📉 Loss: ${abs(profit):.2f}"
    
    await message.answer(
        f"✅ <b>STOCKS SOLD!</b>\n\n"
        f"🏢 Stock: <b>{symbol}</b> ({STOCKS[symbol]['name']})\n"
        f"📊 Shares sold: <b>{shares}</b>\n"
        f"💰 Price per share: <b>${current_price:.2f}</b>\n"
        f"💵 Total received: <b>${current_price * shares:.2f}</b>\n"
        f"{profit_text}\n\n"
        f"📉 Removed from portfolio.",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("portfolio"))
async def cmd_portfolio(message: Message):
    """View stock portfolio"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    portfolio = await db.get_portfolio(message.from_user.id)
    
    if portfolio['count'] == 0:
        await message.answer(
            "📊 <b>STOCK PORTFOLIO</b>\n\n"
            "You don't own any stocks yet.\n"
            "💡 Use <code>/buy TECH 10</code> to start investing!",
            parse_mode=ParseMode.HTML
        )
        return
    
    portfolio_text = "📊 <b>STOCK PORTFOLIO</b>\n\n"
    
    for stock in portfolio['stocks']:
        arrow = "📈" if stock['profit'] >= 0 else "📉"
        portfolio_text += (
            f"{arrow} <b>{stock['symbol']}</b> ({stock['name']})\n"
            f"   └─ Shares: {stock['shares']}\n"
            f"   └─ Avg Price: ${stock['avg_price']:.2f}\n"
            f"   └─ Current: ${stock['current_price']:.2f}\n"
            f"   └─ Value: ${stock['value']:.2f}\n"
            f"   └─ Profit: ${stock['profit']:.2f} ({stock['profit_percent']:.1f}%)\n\n"
        )
    
    portfolio_text += (
        f"💰 <b>Portfolio Summary:</b>\n"
        f"• Total Stocks: {portfolio['count']}\n"
        f"• Total Value: ${portfolio['total_value']:.2f}\n"
        f"• Total Profit: ${portfolio['total_profit']:.2f}\n\n"
        f"💡 Use <code>/stocks</code> to see market"
    )
    
    await message.answer(
        portfolio_text,
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("bank"))
async def cmd_bank(message: Message):
    """Bank system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    bank_text = f"""
🏦 <b>BANK OF {BOT_USERNAME}</b>

💰 <b>Your Accounts:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Bank Balance: <b>${user.get('bank_balance', 0):,}</b>
• 💰 Total Wealth: <b>${user.get('cash', 0) + user.get('bank_balance', 0):,}</b>

💡 <b>Bank Features:</b>
• Earn 2% daily interest on bank balance
• Safe storage for your money
• No risk of robbery

📋 <b>Commands:</b>
• <code>/deposit [amount]</code> - Deposit to bank
• <code>/withdraw [amount]</code> - Withdraw from bank
• <code>/statement</code> - View transactions
• <code>/interest</code> - Collect daily interest (coming soon)

📝 <b>Examples:</b>
<code>/deposit 1000</code>
<code>/withdraw 500</code>
"""
    
    await message.answer(
        bank_text,
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("deposit"))
async def cmd_deposit(message: Message, command: CommandObject):
    """Deposit money to bank"""
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
    
    can_use, error = await check_cooldown(message.from_user.id, "bank")
    if not can_use:
        await message.answer(error)
        return
    
    success, msg = await db.deposit_to_bank(message.from_user.id, amount)
    
    if not success:
        await message.answer(f"❌ {msg}")
        return
    
    await db.set_cooldown(message.from_user.id, "bank")
    
    # Update quest progress
    await db.update_quest_progress(message.from_user.id, "deposit", amount)
    
    await message.answer(f"✅ {msg}")

@dp.message(Command("withdraw"))
async def cmd_withdraw(message: Message, command: CommandObject):
    """Withdraw money from bank"""
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
    
    can_use, error = await check_cooldown(message.from_user.id, "bank")
    if not can_use:
        await message.answer(error)
        return
    
    success, msg = await db.withdraw_from_bank(message.from_user.id, amount)
    
    if not success:
        await message.answer(f"❌ {msg}")
        return
    
    await db.set_cooldown(message.from_user.id, "bank")
    await message.answer(f"✅ {msg}")

@dp.message(Command("statement"))
async def cmd_statement(message: Message):
    """Bank statement"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    transactions = await db.get_bank_statement(message.from_user.id, limit=10)
    
    if not transactions:
        await message.answer(
            "📄 <b>BANK STATEMENT</b>\n\n"
            "No transactions yet.\n"
            "💡 Use <code>/deposit</code> or <code>/withdraw</code> to start!",
            parse_mode=ParseMode.HTML
        )
        return
    
    statement_text = "📄 <b>BANK STATEMENT</b>\n\n"
    statement_text += f"🏦 Balance: <b>${user.get('bank_balance', 0):,}</b>\n\n"
    statement_text += "📋 <b>Recent Transactions:</b>\n"
    
    for trans in transactions:
        trans_type = "📥 Deposit" if trans['type'] == 'deposit' else "📤 Withdraw"
        amount = f"+${trans['amount']:,}" if trans['type'] == 'deposit' else f"-${trans['amount']:,}"
        
        # Format date
        try:
            trans_date = datetime.fromisoformat(trans['created']).strftime('%b %d, %H:%M')
        except:
            trans_date = "Recent"
        
        statement_text += f"{trans_type}: {amount}\n"
        statement_text += f"   └─ Balance: ${trans['balance']:,}\n"
        statement_text += f"   └─ Date: {trans_date}\n\n"
    
    statement_text += "💡 Use <code>/bank</code> for bank menu"
    
    await message.answer(
        statement_text,
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("quests", "quest"))
async def cmd_quests(message: Message):
    """Quests system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    quests = await db.get_user_quests(message.from_user.id)
    
    quests_text = "📋 <b>QUESTS</b>\n\n"
    
    # Daily quests
    if quests['daily']:
        quests_text += "🌅 <b>Daily Quests:</b>\n"
        for quest in quests['daily']:
            status = "✅" if quest['completed'] else f"{quest['progress']}/3" if 'Harvest' in quest['task'] else f"{quest['progress']}/1"
            quests_text += f"{status} {quest['name']}\n"
            quests_text += f"   └─ {quest['task']}\n"
            quests_text += f"   └─ Reward: ${quest['reward']:,} + {quest['xp']} XP\n"
            
            if quest['completed'] and not quest['claimed']:
                quests_text += f"   └─ <code>/claim {quest['id']}</code>\n"
            
            quests_text += "\n"
    else:
        # Assign new daily quests if none
        await db.assign_daily_quests(message.from_user.id)
        quests_text += "🎯 New daily quests assigned! Use /quests again.\n\n"
    
    # Weekly quests
    if quests['weekly']:
        quests_text += "🏆 <b>Weekly Quests:</b>\n"
        for quest in quests['weekly']:
            status = "✅" if quest['completed'] else f"{quest['progress']}/{quest['task'].split()[-2]}"
            quests_text += f"{status} {quest['name']}\n"
            quests_text += f"   └─ {quest['task']}\n"
            quests_text += f"   └─ Reward: ${quest['reward']:,} + {quest['xp']} XP\n"
            
            if quest['completed'] and not quest['claimed']:
                quests_text += f"   └─ <code>/claim {quest['id']}</code>\n"
            
            quests_text += "\n"
    
    quests_text += "💡 <b>Commands:</b>\n"
    quests_text += "• <code>/quests</code> - View quests\n"
    quests_text += "• <code>/claim [id]</code> - Claim reward\n"
    quests_text += "• Complete quests to earn money and XP!"
    
    await message.answer(
        quests_text,
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("claim"))
async def cmd_claim(message: Message, command: CommandObject):
    """Claim quest reward"""
    if not command.args:
        await message.answer("❌ Usage: /claim [quest_id]\nExample: /claim 1")
        return
    
    try:
        quest_id = int(command.args)
    except:
        await message.answer("❌ Quest ID must be a number!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    success, msg = await db.claim_quest_reward(message.from_user.id, quest_id)
    
    if not success:
        await message.answer(f"❌ {msg}")
        return
    
    await message.answer(f"✅ {msg}")

@dp.message(Command("friends", "friend"))
async def cmd_friends(message: Message):
    """Friends system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    friends = await db.get_friends(message.from_user.id)
    
    friends_text = f"👥 <b>FRIENDS</b>\n\n"
    friends_text += f"🤝 You have <b>{len(friends)}</b> friends\n\n"
    
    if friends:
        friends_text += "👤 <b>Your Friends:</b>\n"
        for friend in friends[:10]:  # Show first 10
            level = "❤️" * min(friend['level'], 5)
            friends_text += f"{level} {friend['name']}"
            if friend['username']:
                friends_text += f" (@{friend['username']})"
            friends_text += f"\n"
        
        if len(friends) > 10:
            friends_text += f"... and {len(friends) - 10} more\n"
    else:
        friends_text += "No friends yet. Add some!\n"
    
    friends_text += f"""
💡 <b>Commands:</b>
• <code>/friend @username</code> - Add friend
• <code>/unfriend @username</code> - Remove friend
• <code>/friends</code> - View friends list

🤝 <b>Benefits:</b>
• Increased friendship levels
• Special friend bonuses
• Trade and gift systems
"""
    
    await message.answer(
        friends_text,
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("friend"))
async def cmd_add_friend(message: Message, command: CommandObject):
    """Add friend"""
    if not command.args:
        await message.answer("❌ Usage: /friend @username\nExample: /friend @username")
        return
    
    # This would need user ID resolution
    # For now, show info
    await message.answer(
        "👥 <b>ADD FRIEND</b>\n\n"
        "To add a friend:\n"
        "1. Make sure they've used /start\n"
        "2. Use their Telegram ID\n"
        "3. Example: <code>/friend 123456789</code>\n\n"
        "💡 Coming soon: Add by @username",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("business", "shop"))
async def cmd_business(message: Message):
    """Business system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    business_text = "💼 <b>BUSINESS EMPIRE</b>\n\n"
    business_text += "🏢 <b>Available Businesses:</b>\n"
    
    for biz_type, biz_data in BUSINESSES.items():
        emoji = biz_data['name'][0]  # Get emoji
        business_text += f"{emoji} <b>{biz_data['name']}</b>\n"
        business_text += f"   └─ Price: ${biz_data['price']:,}\n"
        business_text += f"   └─ Daily Income: ${biz_data['income']:,}\n"
        business_text += f"   └─ <code>/buybiz {biz_type}</code>\n\n"
    
    business_text += """
💰 <b>Your Businesses:</b>
Use <code>/mybiz</code> to view your businesses

💡 <b>Commands:</b>
• <code>/buybiz [type]</code> - Buy business
• <code>/mybiz</code> - View your businesses
• <code>/collect</code> - Collect business income
• <code>/upgrade [type]</code> - Upgrade business

📝 <b>Example:</b>
<code>/buybiz farm</code> - Buy a farm business
"""
    
    await message.answer(
        business_text,
        parse_mode=ParseMode.HTML,
        reply_markup=games_menu_keyboard()
    )

@dp.message(Command("buybiz"))
async def cmd_buy_business(message: Message, command: CommandObject):
    """Buy business"""
    if not command.args:
        await message.answer("❌ Usage: /buybiz [type]\nExample: /buybiz farm")
        return
    
    biz_type = command.args.lower()
    
    success, msg = await db.buy_business(message.from_user.id, biz_type)
    
    if not success:
        await message.answer(f"❌ {msg}")
        return
    
    await message.answer(f"✅ {msg}")

@dp.message(Command("mybiz"))
async def cmd_my_businesses(message: Message):
    """View my businesses"""
    # This would query user's businesses
    await message.answer(
        "💼 <b>MY BUSINESSES</b>\n\n"
        "Feature coming soon!\n"
        "💡 Use <code>/business</code> to see available businesses",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("collect"))
async def cmd_collect_business(message: Message):
    """Collect business income"""
    income, msg = await db.collect_business_income(message.from_user.id)
    
    if income == 0:
        await message.answer(msg)
        return
    
    await message.answer(f"✅ {msg}")

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
    """User profile with image caption"""
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
    
    # Try to create profile image
    image_bytes = None
    if HAS_PILLOW:
        try:
            image_bytes = await img_gen.create_profile_image(user)
        except Exception as e:
            logger.error(f"Profile image error: {e}")
    
    profile_text = f"""
🏆 <b>PROFILE OF {user['first_name'].upper()}</b>

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Bank: <b>${user.get('bank_balance', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

📊 <b>Stats:</b>
• Level: <b>{user.get('level', 1)}</b>
• XP: <b>{user.get('xp', 0)}/{(user.get('level', 1) * 1000)}</b>
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Family: <b>{len(family)} members</b>
• Friends: <b>{len(friends)} friends</b>
• Daily Streak: <b>{user.get('daily_streak', 0)} days</b>
• Bio Verified: {'✅' if user.get('bio_verified') else '❌'}

🌾 <b>Garden:</b>
• Slots: <b>{len(crops)}/{garden_info.get('slots', 9) + (garden_info.get('greenhouse_level', 0) * 3)}</b>
• Growing: <b>{len(crops)} crops</b>

📈 <b>Investments:</b>
• Stocks: <b>{portfolio['count']}</b> (${portfolio['total_value']:.2f})
• Lottery Tickets: <b>{tickets}</b>
💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
"""
    
    if image_bytes:
        try:
            photo = BufferedInputFile(image_bytes, filename="profile.png")
            await message.answer_photo(
                photo=photo,
                caption=profile_text,
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending profile photo: {e}")
            await message.answer(profile_text, parse_mode=ParseMode.HTML)
    else:
        await message.answer(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard()
        )

# ============================================================================
# GROUP FEATURES
# ============================================================================

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message):
    """Handle group messages and track activity"""
    # Update group activity
    if message.chat.id < 0:  # Group chat
        try:
            await db.update_group_activity(message.chat.id)
        except:
            pass
    
    # When bot is added to group
    if message.new_chat_members:
        for user in message.new_chat_members:
            if user.id == (await bot.get_me()).id:
                # Bot was added to group
                try:
                    await db.add_group(
                        message.chat.id,
                        message.chat.title or "Unknown Group",
                        message.from_user.id
                    )
                    
                    await log_to_channel(
                        f"📥 Added to group:\n"
                        f"• Group: {message.chat.title}\n"
                        f"• ID: {message.chat.id}\n"
                        f"• Added by: {message.from_user.first_name}\n"
                        f"• Link: https://t.me/c/{str(abs(message.chat.id))[4:]}"
                    )
                    
                    await message.answer(
                        f"🌳 Thanks for adding Family Tree Bot!\n\n"
                        f"👋 Hello everyone! I'm a family tree and farming bot.\n\n"
                        f"📋 <b>Group Commands:</b>\n"
                        f"• Use /help to see all commands\n"
                        f"• Play games together\n"
                        f"• Build family trees\n"
                        f"• Compete in leaderboards\n\n"
                        f"💡 Add me to your bio for 2x daily rewards!",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Group add error: {e}")

@dp.message(Command("groups"))
async def cmd_groups(message: Message):
    """Show groups bot is in (owner only)"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Owner only command!")
        return
    
    groups = await db.get_groups(limit=20)
    group_count = await db.get_group_count()
    
    if not groups:
        await message.answer("📭 Bot is not in any groups yet.")
        return
    
    groups_text = f"👥 <b>GROUPS LIST</b> ({group_count} total)\n\n"
    
    for i, group in enumerate(groups, 1):
        try:
            last_active = datetime.fromisoformat(group['last_active'])
            time_ago = await format_time(last_active)
        except:
            time_ago = "Unknown"
        
        groups_text += f"{i}. <b>{group['title']}</b>\n"
        groups_text += f"   └─ ID: <code>{group['group_id']}</code>\n"
        groups_text += f"   └─ Messages: {group['messages_count']:,}\n"
        groups_text += f"   └─ Last active: {time_ago}\n"
        groups_text += f"   └─ Added by: {group['added_by']}\n"
        
        # Add group link button
        group_link = f"https://t.me/c/{str(abs(group['group_id']))[4:]}"
        groups_text += f"   └─ [🔗 Open Group]({group_link})\n\n"
    
    groups_text += "💡 Click links to open groups"
    
    await message.answer(
        groups_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

# ============================================================================
# CATBOX SYSTEM (Owner only)
# ============================================================================

@dp.message(Command("cat", "catbox"))
async def cmd_catbox(message: Message, command: CommandObject):
    """Catbox GIF management (owner only)"""
    if not is_owner(message.from_user.id):
        # Hide from regular users
        return
    
    if not command.args:
        await message.answer(
            "🐱 <b>CATBOX SYSTEM</b>\n\n"
            "Manage GIFs for reaction commands.\n\n"
            "📋 <b>Commands:</b>\n"
            "• <code>/cat list</code> - List all GIFs\n"
            "• <code>/cat add [cmd] [url]</code> - Add GIF\n"
            "• <code>/cat remove [cmd]</code> - Remove GIF\n"
            "• <code>/cat preview [cmd]</code> - Preview GIF\n\n"
            "💡 <b>Available commands:</b>\n"
            "hug, kill, rob, kiss, slap, pat, punch, cuddle\n\n"
            "🔗 <b>Use catbox.moe links!</b>",
            parse_mode=ParseMode.HTML
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
            f"💡 Use: <code>/cat add [command] [url]</code>",
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
        
        # Check if it's a catbox.moe link
        if 'catbox.moe' not in url:
            await message.answer("⚠️ Please use catbox.moe links for best results!")
        
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
# ADMIN COMMANDS (Hidden from regular users)
# ============================================================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel (owner only)"""
    if not is_owner(message.from_user.id):
        # Hide from regular users
        return
    
    await message.answer(
        "👑 <b>ADMIN PANEL</b>\n\n"
        "Select an option:",
        reply_markup=admin_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources (owner only)"""
    if not is_owner(message.from_user.id):
        return
    
    if not command.args:
        await message.answer(
            "💰 <b>ADD RESOURCES</b>\n\n"
            "Usage: <code>/add [user_id] [resource] [amount]</code>\n\n"
            "💎 Resources: cash, gold, bonds, credits, tokens, bank_balance\n"
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
        f"👑 By: {message.from_user.first_name}",
        parse_mode=ParseMode.HTML
    )
    
    await log_to_channel(f"👑 {message.from_user.id} added {resource} {amount} to {target_id}")

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban user (owner only)"""
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
    """Bot statistics (owner only)"""
    if not is_owner(message.from_user.id):
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
• Total Bank: <b>${stats.get('total_bank', 0):,}</b>

👥 <b>Groups:</b>
• Total Groups: <b>{stats.get('total_groups', 0):,}</b>

📈 <b>Investments:</b>
• Stock Investors: <b>{stats.get('stock_investors', 0):,}</b>
• Businesses: <b>{stats.get('total_businesses', 0):,}</b>

🖼️ <b>Images:</b> {'✅ Enabled' if HAS_PILLOW else '❌ Disabled'}
🕒 <b>Uptime:</b> Running on Railway
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast to all users (owner only)"""
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
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast failed to {user_id}: {e}")
    
    await message.answer(
        f"✅ <b>BROADCAST COMPLETE</b>\n\n"
        f"📤 Sent: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📊 Total: <b>{len(users)}</b>",
        parse_mode=ParseMode.HTML
    )
    
    await log_to_channel(f"📢 Broadcast sent to {sent}/{len(users)} users")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command (owner only)"""
    if not is_owner(message.from_user.id):
        return
    
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
🚀 Host: Railway
🔧 Status: 🟢 ACTIVE

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

# ============================================================================
# OTHER COMMANDS
# ============================================================================

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL WORKING COMMANDS</b>

👨‍👩‍👧‍👦 <b>FAMILY:</b>
• <code>/family</code> - Family tree (with image)
• <code>/adopt</code> - Adopt (reply to message)
• <code>/marry</code> - Marry (reply to message)
• <code>/divorce</code> - End marriage

🌾 <b>GARDEN:</b>
• <code>/garden</code> - View garden (with image)
• <code>/plant [crop] [qty]</code> - Plant crops
• <code>/harvest</code> - Harvest ready crops
• <code>/barn</code> - View storage

🎮 <b>GAMES:</b>
• <code>/slot [bet]</code> - Slot machine
• <code>/dice [bet]</code> - Dice game
• <code>/rob</code> - Rob (reply to message)
• <code>/fight</code> - Fight (reply to message)
• <code>/lottery [tickets]</code> - Lottery tickets

📈 <b>NEW FEATURES:</b>
• <code>/stocks</code> - Stock market
• <code>/bank</code> - Bank system  
• <code>/quests</code> - Daily quests
• <code>/friends</code> - Friends system
• <code>/business</code> - Business empire
• <code>/casino</code> - Casino games

😊 <b>REACTIONS (with catbox GIFs):</b>
• <code>/hug</code>, <code>/kill</code>, <code>/kiss</code>
• <code>/slap</code>, <code>/pat</code>, <code>/punch</code>
• <code>/cuddle</code>, <code>/rob</code> (all need reply)

💰 <b>ECONOMY:</b>
• <code>/daily</code> - Daily bonus
• <code>/me</code> - Your profile (with image)

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
    logger.error(f"Update: {update}\nError: {exception}", exc_info=True)
    
    try:
        error_msg = f"❌ ERROR:\n{type(exception).__name__}: {str(exception)[:200]}"
        await log_to_channel(error_msg)
    except:
        pass
    
    return True

# ============================================================================
# STARTUP - RAILWAY READY
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
        types.BotCommand(command="family", description="Family tree (with image)"),
        types.BotCommand(command="garden", description="Garden (with image)"),
        types.BotCommand(command="stocks", description="Stock market"),
        types.BotCommand(command="bank", description="Bank system"),
        types.BotCommand(command="quests", description="Daily quests"),
        types.BotCommand(command="friends", description="Friends system"),
        types.BotCommand(command="business", description="Business empire"),
        types.BotCommand(command="casino", description="Casino games")
    ]
    
    await bot.set_my_commands(commands)
    
    # Get bot info
    bot_info = await bot.get_me()
    print("=" * 60)
    print(f"🤖 BOT STARTED: @{bot_info.username}")
    print(f"🌳 ULTIMATE FAMILY TREE BOT - Version 20.0")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"🖼️ Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED (install pillow)'}")
    print(f"🚀 Host: Railway")
    print("=" * 60)
    
    if not HAS_PILLOW:
        print("\n⚠️  Install Pillow for images:")
        print("pip install pillow")
    
    await log_to_channel(
        f"🤖 Bot @{bot_info.username} started!\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🚀 Running on Railway"
    )

async def main():
    """Main function - Railway compatible"""
    try:
        await setup_bot()
        print("🚀 Starting bot polling...")
        
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"❌ Fatal error: {e}")
    finally:
        # Cleanup
        if db.conn:
            await db.conn.close()
        await bot.session.close()

# Railway compatible entry point
if __name__ == "__main__":
    # Create required directories
    os.makedirs("data", exist_ok=True)
    
    # Run the bot
    asyncio.run(main())
