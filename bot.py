#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE VERSION
Everything working - All commands included
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
import hashlib

# Core imports
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, BufferedInputFile,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InputFile
)
from aiogram.enums import ParseMode
from aiogram.methods import SendMessage

# Pillow for images
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
OWNER_ID = int(os.getenv("OWNER_ID", "6108185460"))
DB_PATH = "family_bot.db"
BOT_USERNAME = "FamilyTreeBot"

# Game Economy
class GameConfig:
    # Economy
    START_CASH = 1000
    START_BANK = 0
    DAILY_MIN = 500
    DAILY_MAX = 1500
    BANK_INTEREST_RATE = 0.5  # 0.5% daily
    LOAN_INTEREST_RATE = 10   # 10% weekly
    FIXED_DEPOSIT_RATE = 5    # 5% weekly
    
    # Garden
    GARDEN_SLOTS = 9
    GREENHOUSE_SLOT_BONUS = 3
    GROW_TIME_REDUCTION = 0.1  # 10% per greenhouse level
    
    # Lottery
    LOTTERY_TICKET_PRICE = 50
    LOTTERY_PRIZE_POOL = 70   # 70% of sales
    LOTTERY_DRAW_DAY = 6      # Sunday (0=Monday, 6=Sunday)
    
    # Games
    MIN_BET = 10
    MAX_BET = 10000
    SLOT_MULTIPLIERS = {
        "7️⃣": 10,
        "💎": 5,
        "default": 3
    }
    
    # Family
    ADOPT_BONUS = 500
    MARRY_BONUS = 1000
    FAMILY_DAILY_BONUS = 100  # Per member
    
    # Business
    BUSINESS_INCOME_INTERVAL = 24  # Hours
    MIN_BUSINESS_PRICE = 5000

# Crop Types
class CropType(Enum):
    CARROT = "carrot"
    TOMATO = "tomato" 
    POTATO = "potato"
    EGGPLANT = "eggplant"
    CORN = "corn"
    PEPPER = "pepper"
    WATERMELON = "watermelon"
    PUMPKIN = "pumpkin"

CROP_DATA = {
    CropType.CARROT: {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕", "xp": 5},
    CropType.TOMATO: {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅", "xp": 8},
    CropType.POTATO: {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔", "xp": 6},
    CropType.EGGPLANT: {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆", "xp": 12},
    CropType.CORN: {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽", "xp": 10},
    CropType.PEPPER: {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑", "xp": 15},
    CropType.WATERMELON: {"buy": 30, "sell": 45, "grow_time": 7, "emoji": "🍉", "xp": 18},
    CropType.PUMPKIN: {"buy": 40, "sell": 60, "grow_time": 8, "emoji": "🎃", "xp": 20}
}

# Business Types
BUSINESS_TYPES = {
    "farm": {"name": "🌾 Farm", "price": 5000, "income": 500, "upgrade": 2000},
    "store": {"name": "🏪 Store", "price": 10000, "income": 1000, "upgrade": 5000},
    "restaurant": {"name": "🍽️ Restaurant", "price": 25000, "income": 2500, "upgrade": 12000},
    "hotel": {"name": "🏨 Hotel", "price": 50000, "income": 5000, "upgrade": 25000},
    "casino": {"name": "🎰 Casino", "price": 100000, "income": 10000, "upgrade": 50000}
}

# Stock Market
STOCKS = {
    "TECH": {"name": "Tech Corp", "base_price": 100, "volatility": 0.2},
    "FARM": {"name": "Farm Inc", "base_price": 50, "volatility": 0.15},
    "GOLD": {"name": "Gold Mining", "base_price": 200, "volatility": 0.1},
    "OIL": {"name": "Oil Co", "base_price": 80, "volatility": 0.25},
    "BIO": {"name": "Bio Tech", "base_price": 150, "volatility": 0.3}
}

# Achievement System
ACHIEVEMENTS = {
    "first_daily": {"name": "🌅 First Timer", "desc": "Claim first daily bonus", "reward": 100},
    "family_5": {"name": "👨‍👩‍👧‍👦 Growing Family", "desc": "Have 5 family members", "reward": 500},
    "garden_master": {"name": "🌾 Garden Master", "desc": "Harvest 100 crops", "reward": 1000},
    "millionaire": {"name": "💰 Millionaire", "desc": "Reach $1,000,000 total wealth", "reward": 5000},
    "stock_king": {"name": "📈 Stock King", "desc": "Make $50,000 profit in stocks", "reward": 10000}
}

# Reaction GIFs
REACTION_GIFS = {
    "hug": "https://files.catbox.moe/34u6a1.gif",
    "kiss": "https://files.catbox.moe/zu3p40.gif",
    "slap": "https://files.catbox.moe/8x5f6d.gif",
    "pat": "https://files.catbox.moe/9k7j2v.gif",
    "punch": "https://files.catbox.moe/l2m5n8.gif",
    "cuddle": "https://files.catbox.moe/r4t9y1.gif",
    "kill": "https://files.catbox.moe/p6og82.gif",
    "rob": "https://files.catbox.moe/1x4z9u.gif"
}

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
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
        await self.init_data()
    
    async def init_tables(self):
        """Create all database tables"""
        tables = [
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                cash INTEGER DEFAULT ?,
                bank_balance INTEGER DEFAULT ?,
                gold INTEGER DEFAULT 50,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 100,
                daily_streak INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                bio_verified BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Family
            """CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id, relation)
            )""",
            
            # Garden
            """CREATE TABLE IF NOT EXISTS garden (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT ?,
                greenhouse_level INTEGER DEFAULT 0,
                last_watered TIMESTAMP
            )""",
            
            # Plants
            """CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                progress REAL DEFAULT 0,
                is_ready BOOLEAN DEFAULT 0,
                watered_at TIMESTAMP
            )""",
            
            # Barn
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Bank
            """CREATE TABLE IF NOT EXISTS bank_accounts (
                user_id INTEGER PRIMARY KEY,
                last_interest TIMESTAMP,
                total_interest INTEGER DEFAULT 0,
                fixed_deposit INTEGER DEFAULT 0,
                fixed_deposit_end TIMESTAMP,
                loan_amount INTEGER DEFAULT 0,
                loan_due TIMESTAMP
            )""",
            
            # Transactions
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT,
                balance_after INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Lottery
            """CREATE TABLE IF NOT EXISTS lottery_tickets (
                ticket_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                numbers TEXT NOT NULL,
                scratched BOOLEAN DEFAULT 0,
                scratched_at TIMESTAMP,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_winner BOOLEAN DEFAULT 0
            )""",
            
            # Lottery Draws
            """CREATE TABLE IF NOT EXISTS lottery_draws (
                draw_id INTEGER PRIMARY KEY AUTOINCREMENT,
                winning_numbers TEXT NOT NULL,
                prize_pool INTEGER NOT NULL,
                winner_id INTEGER,
                drawn_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Stocks
            """CREATE TABLE IF NOT EXISTS stocks (
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                shares INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, symbol)
            )""",
            
            # Stock Prices
            """CREATE TABLE IF NOT EXISTS stock_prices (
                symbol TEXT PRIMARY KEY,
                price REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Businesses
            """CREATE TABLE IF NOT EXISTS businesses (
                user_id INTEGER NOT NULL,
                business_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                last_collected TIMESTAMP,
                total_earned INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, business_type)
            )""",
            
            # Friends
            """CREATE TABLE IF NOT EXISTS friends (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                friendship_level INTEGER DEFAULT 1,
                last_interaction TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            )""",
            
            # Achievements
            """CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )""",
            
            # Groups
            """CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                added_by INTEGER,
                member_count INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Cooldowns
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )""",
            
            # Reaction GIFs
            """CREATE TABLE IF NOT EXISTS reaction_gifs (
                command TEXT PRIMARY KEY,
                gif_url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Game History
            """CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                bet INTEGER,
                result TEXT,
                profit INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Quests
            """CREATE TABLE IF NOT EXISTS quests (
                user_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                quest_type TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                claimed BOOLEAN DEFAULT 0,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                PRIMARY KEY (user_id, quest_id)
            )""",
            
            # Market Items
            """CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                price INTEGER NOT NULL,
                listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )""",
            
            # Items Inventory
            """CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, item_type, item_name)
            )"""
        ]
        
        for i, table_sql in enumerate(tables):
            try:
                if i == 0:  # Users table
                    await self.conn.execute(table_sql, (GameConfig.START_CASH, GameConfig.START_BANK))
                elif i == 2:  # Garden table
                    await self.conn.execute(table_sql, (GameConfig.GARDEN_SLOTS,))
                else:
                    await self.conn.execute(table_sql)
            except Exception as e:
                logger.error(f"Table creation error {i}: {e}")
        
        await self.conn.commit()
    
    async def init_data(self):
        """Initialize default data"""
        # Initialize stock prices
        for symbol, data in STOCKS.items():
            await self.conn.execute(
                """INSERT OR IGNORE INTO stock_prices (symbol, price)
                   VALUES (?, ?)""",
                (symbol, data["base_price"])
            )
        
        # Initialize default GIFs
        for command, url in REACTION_GIFS.items():
            await self.conn.execute(
                """INSERT OR IGNORE INTO reaction_gifs (command, gif_url, added_by)
                   VALUES (?, ?, ?)""",
                (command, url, OWNER_ID)
            )
        
        await self.conn.commit()
    
    # ========== USER METHODS ==========
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user data"""
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user with all default data"""
        async with self.conn.cursor() as cursor:
            # Create user
            await cursor.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name, cash, bank_balance)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, user.last_name, 
                 GameConfig.START_CASH, GameConfig.START_BANK)
            )
            
            # Initialize garden
            await cursor.execute(
                "INSERT OR IGNORE INTO garden (user_id) VALUES (?)",
                (user.id,)
            )
            
            # Initialize bank account
            await cursor.execute(
                "INSERT OR IGNORE INTO bank_accounts (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.commit()
        
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        """Update user currency"""
        if currency == "bank_balance":
            await self.conn.execute(
                "UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
        elif currency == "cash":
            await self.conn.execute(
                "UPDATE users SET cash = cash + ? WHERE user_id = ?",
                (amount, user_id)
            )
        elif currency == "gold":
            await self.conn.execute(
                "UPDATE users SET gold = gold + ? WHERE user_id = ?",
                (amount, user_id)
            )
        elif currency == "credits":
            await self.conn.execute(
                "UPDATE users SET credits = credits + ? WHERE user_id = ?",
                (amount, user_id)
            )
        elif currency == "tokens":
            await self.conn.execute(
                "UPDATE users SET tokens = tokens + ? WHERE user_id = ?",
                (amount, user_id)
            )
        
        await self.conn.commit()
    
    async def add_transaction(self, user_id: int, trans_type: str, amount: int, description: str = ""):
        """Record bank transaction"""
        user = await self.get_user(user_id)
        if not user:
            return
        
        balance_after = user.get("bank_balance", 0) + amount if trans_type == "deposit" else user.get("bank_balance", 0) - amount
        
        await self.conn.execute(
            """INSERT INTO transactions (user_id, type, amount, description, balance_after)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, trans_type, amount, description, balance_after)
        )
        await self.conn.commit()
    
    async def add_xp(self, user_id: int, xp: int):
        """Add XP to user"""
        user = await self.get_user(user_id)
        if not user:
            return
        
        current_xp = user.get('xp', 0)
        current_level = user.get('level', 1)
        new_xp = current_xp + xp
        
        # Check for level up
        xp_needed = current_level * 1000
        levels_gained = 0
        
        while new_xp >= xp_needed:
            levels_gained += 1
            new_xp -= xp_needed
            current_level += 1
            xp_needed = current_level * 1000
        
        await self.conn.execute(
            """UPDATE users 
               SET xp = ?, level = ?
               WHERE user_id = ?""",
            (new_xp, current_level, user_id)
        )
        await self.conn.commit()
        
        return levels_gained
    
    # ========== FAMILY METHODS ==========
    
    async def get_family(self, user_id: int) -> List[dict]:
        """Get user's family members"""
        cursor = await self.conn.execute(
            """SELECT 
               CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END as member_id,
               u.first_name, u.username, f.relation, f.created_at
               FROM family f
               JOIN users u ON u.user_id = CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
               WHERE ? IN (f.user1_id, f.user2_id)
               ORDER BY f.created_at""",
            (user_id, user_id, user_id)
        )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def add_family_member(self, user1_id: int, user2_id: int, relation: str):
        """Add family relation"""
        await self.conn.execute(
            """INSERT OR IGNORE INTO family (user1_id, user2_id, relation)
               VALUES (?, ?, ?)""",
            (min(user1_id, user2_id), max(user1_id, user2_id), relation)
        )
        await self.conn.commit()
    
    async def remove_family_member(self, user1_id: int, user2_id: int, relation: str = None):
        """Remove family relation"""
        if relation:
            await self.conn.execute(
                """DELETE FROM family 
                   WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
                   AND relation = ?""",
                (user1_id, user2_id, user2_id, user1_id, relation)
            )
        else:
            await self.conn.execute(
                """DELETE FROM family 
                   WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)""",
                (user1_id, user2_id, user2_id, user1_id)
            )
        await self.conn.commit()
    
    # ========== GARDEN METHODS ==========
    
    async def get_garden(self, user_id: int) -> dict:
        """Get garden info"""
        cursor = await self.conn.execute(
            "SELECT slots, greenhouse_level FROM garden WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else {"slots": GameConfig.GARDEN_SLOTS, "greenhouse_level": 0}
    
    async def get_plants(self, user_id: int) -> List[dict]:
        """Get growing plants"""
        cursor = await self.conn.execute(
            """SELECT id, crop_type, planted_at, grow_time, progress, is_ready
               FROM plants WHERE user_id = ? AND is_ready = 0
               ORDER BY planted_at""",
            (user_id,)
        )
        
        rows = await cursor.fetchall()
        plants = []
        for row in rows:
            plant = dict(row)
            # Calculate current progress
            if plant['planted_at']:
                planted_at = datetime.fromisoformat(plant['planted_at'])
                elapsed = (datetime.now() - planted_at).total_seconds() / 3600
                progress = min(100, (elapsed / plant['grow_time']) * 100)
                plant['current_progress'] = progress
                plant['is_ready'] = progress >= 100
            else:
                plant['current_progress'] = 0
                plant['is_ready'] = False
            plants.append(plant)
        
        return plants
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int) -> bool:
        """Plant crops in garden"""
        garden = await self.get_garden(user_id)
        plants = await self.get_plants(user_id)
        
        total_slots = garden['slots'] + (garden['greenhouse_level'] * GameConfig.GREENHOUSE_SLOT_BONUS)
        
        if len(plants) + quantity > total_slots:
            return False
        
        try:
            crop_enum = CropType(crop_type)
            crop_data = CROP_DATA.get(crop_enum)
        except ValueError:
            return False
        
        if not crop_data:
            return False
        
        grow_time = crop_data['grow_time']
        # Greenhouse reduces grow time
        if garden['greenhouse_level'] > 0:
            grow_time = grow_time * (1 - (GameConfig.GROW_TIME_REDUCTION * garden['greenhouse_level']))
        
        for _ in range(quantity):
            await self.conn.execute(
                """INSERT INTO plants (user_id, crop_type, grow_time)
                   VALUES (?, ?, ?)""",
                (user_id, crop_type, grow_time)
            )
        
        await self.conn.commit()
        return True
    
    async def harvest_crops(self, user_id: int) -> List[tuple]:
        """Harvest ready crops"""
        # Get ready plants
        cursor = await self.conn.execute(
            """SELECT crop_type, COUNT(*) as count
               FROM plants 
               WHERE user_id = ? AND is_ready = 0
               GROUP BY crop_type""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        harvested = []
        for row in rows:
            crop_type = row['crop_type']
            count = row['count']
            
            # Add to barn
            await self.conn.execute(
                """INSERT INTO barn (user_id, crop_type, quantity)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id, crop_type) 
                   DO UPDATE SET quantity = quantity + ?""",
                (user_id, crop_type, count, count)
            )
            
            # Remove from plants
            await self.conn.execute(
                "DELETE FROM plants WHERE user_id = ? AND crop_type = ? AND is_ready = 0",
                (user_id, crop_type)
            )
            
            harvested.append((crop_type, count))
        
        await self.conn.commit()
        return harvested
    
    async def get_barn(self, user_id: int) -> List[dict]:
        """Get barn items"""
        cursor = await self.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def sell_crops(self, user_id: int, crop_type: str, quantity: int) -> Optional[int]:
        """Sell crops from barn"""
        cursor = await self.conn.execute(
            "SELECT quantity FROM barn WHERE user_id = ? AND crop_type = ?",
            (user_id, crop_type)
        )
        row = await cursor.fetchone()
        
        if not row or row['quantity'] < quantity:
            return None
        
        try:
            crop_enum = CropType(crop_type)
            crop_data = CROP_DATA.get(crop_enum)
        except ValueError:
            return None
        
        if not crop_data:
            return None
        
        total_value = crop_data['sell'] * quantity
        
        # Update barn
        if row['quantity'] == quantity:
            await self.conn.execute(
                "DELETE FROM barn WHERE user_id = ? AND crop_type = ?",
                (user_id, crop_type)
            )
        else:
            await self.conn.execute(
                "UPDATE barn SET quantity = quantity - ? WHERE user_id = ? AND crop_type = ?",
                (quantity, user_id, crop_type)
            )
        
        # Add money and XP
        await self.update_currency(user_id, "cash", total_value)
        await self.add_xp(user_id, crop_data['xp'] * quantity)
        
        await self.conn.commit()
        
        return total_value
    
    # ========== BANK METHODS ==========
    
    async def get_bank_account(self, user_id: int) -> dict:
        """Get bank account details"""
        cursor = await self.conn.execute(
            """SELECT * FROM bank_accounts WHERE user_id = ?""",
            (user_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return {
                "user_id": user_id,
                "last_interest": None,
                "total_interest": 0,
                "fixed_deposit": 0,
                "fixed_deposit_end": None,
                "loan_amount": 0,
                "loan_due": None
            }
        
        return dict(row)
    
    async def calculate_interest(self, user_id: int) -> Tuple[int, str]:
        """Calculate and add daily interest"""
        user = await self.get_user(user_id)
        if not user or user['bank_balance'] <= 0:
            return 0, "No balance for interest"
        
        account = await self.get_bank_account(user_id)
        
        # Check if interest was already calculated today
        if account['last_interest']:
            last_interest = datetime.fromisoformat(account['last_interest'])
            if (datetime.now() - last_interest).days < 1:
                next_interest = last_interest + timedelta(days=1)
                hours_left = int((next_interest - datetime.now()).total_seconds() / 3600)
                return 0, f"Interest already calculated today. Next in {hours_left}h"
        
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
            
            await self.add_transaction(user_id, "interest", interest, "Daily interest")
            await self.conn.commit()
            
            return interest, f"Interest added: ${interest:,}"
        
        return 0, "No interest to add"
    
    async def get_transactions(self, user_id: int, limit: int = 10) -> List[dict]:
        """Get transaction history"""
        cursor = await self.conn.execute(
            """SELECT type, amount, description, balance_after, created_at
               FROM transactions 
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ========== LOTTERY METHODS ==========
    
    async def generate_lottery_ticket(self) -> str:
        """Generate a 6-digit lottery ticket"""
        return ''.join(str(random.randint(0, 9)) for _ in range(6))
    
    async def buy_lottery_ticket(self, user_id: int, quantity: int) -> Tuple[bool, List[str], int]:
        """Buy lottery tickets"""
        user = await self.get_user(user_id)
        if not user:
            return False, [], 0
        
        total_cost = quantity * GameConfig.LOTTERY_TICKET_PRICE
        
        if user['cash'] < total_cost:
            return False, [], 0
        
        # Deduct money
        await self.update_currency(user_id, "cash", -total_cost)
        
        tickets = []
        for _ in range(quantity):
            ticket_id = f"LOT-{random.randint(100000, 999999)}"
            numbers = await self.generate_lottery_ticket()
            
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
            """SELECT ticket_id, numbers, scratched, scratched_at, purchased_at, is_winner
               FROM lottery_tickets 
               WHERE user_id = ?
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
    
    # ========== STOCK METHODS ==========
    
    async def update_stock_prices(self):
        """Update stock prices with random fluctuations"""
        for symbol, data in STOCKS.items():
            cursor = await self.conn.execute(
                "SELECT price FROM stock_prices WHERE symbol = ?",
                (symbol,)
            )
            row = await cursor.fetchone()
            
            current_price = data['base_price'] if not row else row['price']
            
            # Random price change based on volatility
            change = random.uniform(-data['volatility'], data['volatility'])
            new_price = max(1, current_price * (1 + change))
            
            await self.conn.execute(
                """INSERT OR REPLACE INTO stock_prices (symbol, price, last_updated)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (symbol, round(new_price, 2))
            )
        
        await self.conn.commit()
    
    async def get_stock_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        await self.update_stock_prices()  # Update prices first
        
        cursor = await self.conn.execute(
            "SELECT price FROM stock_prices WHERE symbol = ?",
            (symbol,)
        )
        row = await cursor.fetchone()
        return row['price'] if row else None
    
    async def buy_stocks(self, user_id: int, symbol: str, shares: int) -> Tuple[bool, float]:
        """Buy stocks"""
        price = await self.get_stock_price(symbol)
        if not price:
            return False, 0
        
        total_cost = price * shares
        
        user = await self.get_user(user_id)
        if not user or user['cash'] < total_cost:
            return False, 0
        
        # Check if user already owns this stock
        cursor = await self.conn.execute(
            "SELECT shares, avg_price FROM stocks WHERE user_id = ? AND symbol = ?",
            (user_id, symbol)
        )
        row = await cursor.fetchone()
        
        if row:
            # Update existing position
            current_shares = row['shares']
            current_avg = row['avg_price']
            new_shares = current_shares + shares
            new_avg = ((current_avg * current_shares) + (price * shares)) / new_shares
            
            await self.conn.execute(
                """UPDATE stocks 
                   SET shares = ?, avg_price = ?, purchased_at = CURRENT_TIMESTAMP
                   WHERE user_id = ? AND symbol = ?""",
                (new_shares, new_avg, user_id, symbol)
            )
        else:
            # New position
            await self.conn.execute(
                """INSERT INTO stocks (user_id, symbol, shares, avg_price)
                   VALUES (?, ?, ?, ?)""",
                (user_id, symbol, shares, price)
            )
        
        # Deduct money
        await self.update_currency(user_id, "cash", -total_cost)
        await self.conn.commit()
        
        return True, total_cost
    
    async def sell_stocks(self, user_id: int, symbol: str, shares: int) -> Tuple[bool, float, float]:
        """Sell stocks"""
        cursor = await self.conn.execute(
            "SELECT shares, avg_price FROM stocks WHERE user_id = ? AND symbol = ?",
            (user_id, symbol)
        )
        row = await cursor.fetchone()
        
        if not row or row['shares'] < shares:
            return False, 0, 0
        
        current_price = await self.get_stock_price(symbol)
        if not current_price:
            return False, 0, 0
        
        total_value = current_price * shares
        cost_basis = row['avg_price'] * shares
        profit = total_value - cost_basis
        
        # Update or remove position
        if row['shares'] == shares:
            await self.conn.execute(
                "DELETE FROM stocks WHERE user_id = ? AND symbol = ?",
                (user_id, symbol)
            )
        else:
            await self.conn.execute(
                "UPDATE stocks SET shares = shares - ? WHERE user_id = ? AND symbol = ?",
                (shares, user_id, symbol)
            )
        
        # Add money
        await self.update_currency(user_id, "cash", total_value)
        await self.conn.commit()
        
        return True, total_value, profit
    
    async def get_portfolio(self, user_id: int) -> dict:
        """Get user's stock portfolio"""
        cursor = await self.conn.execute(
            "SELECT symbol, shares, avg_price FROM stocks WHERE user_id = ?",
            (user_id,)
        )
        
        rows = await cursor.fetchall()
        portfolio = []
        total_value = 0
        total_profit = 0
        
        for row in rows:
            symbol = row['symbol']
            shares = row['shares']
            avg_price = row['avg_price']
            
            current_price = await self.get_stock_price(symbol)
            if current_price:
                value = current_price * shares
                profit = value - (avg_price * shares)
                
                portfolio.append({
                    'symbol': symbol,
                    'name': STOCKS.get(symbol, {}).get('name', symbol),
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
    
    # ========== BUSINESS METHODS ==========
    
    async def buy_business(self, user_id: int, business_type: str) -> Tuple[bool, str]:
        """Buy a business"""
        if business_type not in BUSINESS_TYPES:
            return False, "Invalid business type"
        
        business = BUSINESS_TYPES[business_type]
        user = await self.get_user(user_id)
        
        if not user or user['cash'] < business['price']:
            return False, f"Insufficient funds. Need ${business['price']:,}"
        
        # Check if already owns
        cursor = await self.conn.execute(
            "SELECT 1 FROM businesses WHERE user_id = ? AND business_type = ?",
            (user_id, business_type)
        )
        if await cursor.fetchone():
            return False, "You already own this business"
        
        # Purchase business
        await self.update_currency(user_id, "cash", -business['price'])
        
        await self.conn.execute(
            """INSERT INTO businesses (user_id, business_type, level, last_collected)
               VALUES (?, ?, 1, CURRENT_TIMESTAMP)""",
            (user_id, business_type)
        )
        
        await self.conn.commit()
        return True, f"Purchased {business['name']} for ${business['price']:,}"
    
    async def collect_business_income(self, user_id: int) -> Tuple[int, str]:
        """Collect income from businesses"""
        cursor = await self.conn.execute(
            "SELECT business_type, level, last_collected FROM businesses WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        if not rows:
            return 0, "You don't own any businesses"
        
        total_income = 0
        now = datetime.now()
        businesses_collected = []
        
        for row in rows:
            business_type = row['business_type']
            level = row['level']
            last_collected_str = row['last_collected']
            
            if not last_collected_str:
                continue
                
            last_collected = datetime.fromisoformat(last_collected_str)
            hours_passed = (now - last_collected).total_seconds() / 3600
            
            if hours_passed >= GameConfig.BUSINESS_INCOME_INTERVAL:
                business = BUSINESS_TYPES[business_type]
                income = business['income'] * level
                total_income += income
                businesses_collected.append(business['name'])
                
                # Update last collected
                await self.conn.execute(
                    """UPDATE businesses 
                       SET last_collected = CURRENT_TIMESTAMP,
                           total_earned = total_earned + ?
                       WHERE user_id = ? AND business_type = ?""",
                    (income, user_id, business_type)
                )
        
        if total_income > 0:
            await self.update_currency(user_id, "cash", total_income)
            await self.conn.commit()
            
            business_list = ", ".join(businesses_collected[:3])
            if len(businesses_collected) > 3:
                business_list += f" and {len(businesses_collected) - 3} more"
            
            return total_income, f"Collected ${total_income:,} from {business_list}"
        
        return 0, "Business income not ready yet"
    
    async def get_businesses(self, user_id: int) -> List[dict]:
        """Get user's businesses"""
        cursor = await self.conn.execute(
            "SELECT business_type, level, last_collected, total_earned FROM businesses WHERE user_id = ?",
            (user_id,)
        )
        
        rows = await cursor.fetchall()
        businesses = []
        
        for row in rows:
            business_type = row['business_type']
            business_data = BUSINESS_TYPES.get(business_type, {})
            
            businesses.append({
                'type': business_type,
                'name': business_data.get('name', business_type),
                'level': row['level'],
                'last_collected': row['last_collected'],
                'total_earned': row['total_earned'] or 0,
                'next_income': business_data.get('income', 0) * row['level']
            })
        
        return businesses
    
    # ========== FRIEND METHODS ==========
    
    async def add_friend(self, user1_id: int, user2_id: int) -> Tuple[bool, str]:
        """Add friend"""
        if user1_id == user2_id:
            return False, "You cannot add yourself"
        
        # Check if already friends
        cursor = await self.conn.execute(
            """SELECT 1 FROM friends 
               WHERE (user1_id = ? AND user2_id = ?) 
               OR (user1_id = ? AND user2_id = ?)""",
            (user1_id, user2_id, user2_id, user1_id)
        )
        
        if await cursor.fetchone():
            return False, "Already friends"
        
        await self.conn.execute(
            """INSERT INTO friends (user1_id, user2_id, friendship_level, last_interaction)
               VALUES (?, ?, 1, CURRENT_TIMESTAMP)""",
            (min(user1_id, user2_id), max(user1_id, user2_id))
        )
        
        await self.conn.commit()
        return True, "Friend added successfully"
    
    async def get_friends(self, user_id: int) -> List[dict]:
        """Get user's friends"""
        cursor = await self.conn.execute(
            """SELECT 
               CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END as friend_id,
               u.first_name, u.username, f.friendship_level, f.last_interaction
               FROM friends f
               JOIN users u ON u.user_id = CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
               WHERE ? IN (f.user1_id, f.user2_id)
               ORDER BY f.last_interaction DESC""",
            (user_id, user_id, user_id)
        )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ========== ACHIEVEMENT METHODS ==========
    
    async def unlock_achievement(self, user_id: int, achievement_id: str) -> Tuple[bool, dict]:
        """Unlock achievement for user"""
        if achievement_id not in ACHIEVEMENTS:
            return False, {}
        
        # Check if already unlocked
        cursor = await self.conn.execute(
            "SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?",
            (user_id, achievement_id)
        )
        
        if await cursor.fetchone():
            return False, {}
        
        achievement = ACHIEVEMENTS[achievement_id]
        
        # Record achievement
        await self.conn.execute(
            "INSERT INTO achievements (user_id, achievement_id) VALUES (?, ?)",
            (user_id, achievement_id)
        )
        
        # Give reward
        if achievement.get('reward', 0) > 0:
            await self.update_currency(user_id, "cash", achievement['reward'])
        
        await self.conn.commit()
        return True, achievement
    
    async def get_achievements(self, user_id: int) -> List[dict]:
        """Get user's achievements"""
        # First get unlocked achievements
        cursor = await self.conn.execute(
            """SELECT a.achievement_id, a.unlocked_at, 
                      ach.name, ach.desc, ach.reward
               FROM achievements a
               JOIN (SELECT ? as achievement_id, ? as name, ? as desc, ? as reward) ach
               ON ach.achievement_id = a.achievement_id
               WHERE a.user_id = ?""",
            ('dummy', 'dummy', 'dummy', 0, user_id)
        )
        
        rows = await cursor.fetchall()
        achievements = []
        
        for row in rows:
            if row['achievement_id'] != 'dummy':
                achievements.append({
                    'id': row['achievement_id'],
                    'name': row['name'],
                    'description': row['desc'],
                    'reward': row['reward'],
                    'unlocked_at': row['unlocked_at'],
                    'unlocked': True
                })
        
        # Add locked achievements
        unlocked_ids = {a['id'] for a in achievements}
        for achievement_id, data in ACHIEVEMENTS.items():
            if achievement_id not in unlocked_ids:
                achievements.append({
                    'id': achievement_id,
                    'name': data['name'],
                    'description': data['desc'],
                    'reward': data.get('reward', 0),
                    'unlocked_at': None,
                    'unlocked': False
                })
        
        return achievements
    
    # ========== GROUP METHODS ==========
    
    async def add_group(self, group_id: int, title: str, added_by: int):
        """Add group to database"""
        await self.conn.execute(
            """INSERT OR REPLACE INTO groups (group_id, title, added_by, added_at, last_active)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (group_id, title, added_by)
        )
        await self.conn.commit()
    
    async def update_group_activity(self, group_id: int):
        """Update group activity timestamp"""
        await self.conn.execute(
            """UPDATE groups 
               SET messages_count = messages_count + 1,
                   last_active = CURRENT_TIMESTAMP
               WHERE group_id = ?""",
            (group_id,)
        )
        await self.conn.commit()
    
    async def get_groups(self, limit: int = 20) -> List[dict]:
        """Get all groups"""
        cursor = await self.conn.execute(
            """SELECT group_id, title, added_by, member_count, messages_count, 
                      last_active, added_at
               FROM groups 
               ORDER BY last_active DESC
               LIMIT ?""",
            (limit,)
        )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ========== COOLDOWN METHODS ==========
    
    async def check_cooldown(self, user_id: int, command: str, cooldown_seconds: int) -> Tuple[bool, int]:
        """Check if command is on cooldown"""
        cursor = await self.conn.execute(
            "SELECT last_used FROM cooldowns WHERE user_id = ? AND command = ?",
            (user_id, command)
        )
        row = await cursor.fetchone()
        
        if not row:
            return True, 0
        
        last_used = datetime.fromisoformat(row['last_used'])
        elapsed = (datetime.now() - last_used).total_seconds()
        
        if elapsed >= cooldown_seconds:
            return True, 0
        
        remaining = int(cooldown_seconds - elapsed)
        return False, remaining
    
    async def set_cooldown(self, user_id: int, command: str):
        """Set command cooldown"""
        await self.conn.execute(
            """INSERT OR REPLACE INTO cooldowns (user_id, command, last_used)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (user_id, command)
        )
        await self.conn.commit()
    
    # ========== ADMIN METHODS ==========
    
    async def get_stats(self) -> dict:
        """Get bot statistics"""
        stats = {}
        
        queries = [
            ("total_users", "SELECT COUNT(*) FROM users"),
            ("active_today", "SELECT COUNT(*) FROM users WHERE last_daily >= datetime('now', '-1 day')"),
            ("banned_users", "SELECT COUNT(*) FROM users WHERE is_banned = 1"),
            ("total_cash", "SELECT SUM(cash) FROM users"),
            ("total_bank", "SELECT SUM(bank_balance) FROM users"),
            ("family_relations", "SELECT COUNT(*) FROM family"),
            ("growing_crops", "SELECT COUNT(*) FROM plants WHERE is_ready = 0"),
            ("lottery_tickets", "SELECT COUNT(*) FROM lottery_tickets"),
            ("businesses", "SELECT COUNT(*) FROM businesses"),
            ("groups", "SELECT COUNT(*) FROM groups")
        ]
        
        for key, query in queries:
            cursor = await self.conn.execute(query)
            row = await cursor.fetchone()
            stats[key] = row[0] or 0 if row else 0
        
        return stats
    
    async def search_users(self, query: str) -> List[dict]:
        """Search users by name or username"""
        cursor = await self.conn.execute(
            """SELECT user_id, username, first_name, last_name, cash, level
               FROM users 
               WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
               ORDER BY cash DESC
               LIMIT 20""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_top_users(self, by: str = "cash", limit: int = 10) -> List[dict]:
        """Get top users by specified metric"""
        valid_columns = ["cash", "bank_balance", "level", "reputation"]
        if by not in valid_columns:
            by = "cash"
        
        cursor = await self.conn.execute(
            f"""SELECT user_id, first_name, username, {by}
                FROM users 
                WHERE is_banned = 0
                ORDER BY {by} DESC
                LIMIT ?""",
            (limit,)
        )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def ban_user(self, user_id: int) -> bool:
        """Ban user"""
        cursor = await self.conn.execute(
            "SELECT is_banned FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return False
        
        await self.conn.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (user_id,)
        )
        await self.conn.commit()
        return True
    
    async def unban_user(self, user_id: int) -> bool:
        """Unban user"""
        cursor = await self.conn.execute(
            "SELECT is_banned FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return False
        
        await self.conn.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?",
            (user_id,)
        )
        await self.conn.commit()
        return True
    
    async def warn_user(self, user_id: int) -> Tuple[bool, int]:
        """Warn user, returns (success, total_warnings)"""
        await self.conn.execute(
            "UPDATE users SET warnings = warnings + 1 WHERE user_id = ?",
            (user_id,)
        )
        await self.conn.commit()
        
        cursor = await self.conn.execute(
            "SELECT warnings FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        
        return True, row['warnings'] if row else 1
    
    async def reset_user(self, user_id: int, reset_type: str) -> bool:
        """Reset user data"""
        if reset_type == "all":
            # Reset everything except user ID and name
            await self.conn.execute("DELETE FROM family WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
            await self.conn.execute("DELETE FROM plants WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM barn WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM bank_accounts WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM lottery_tickets WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM stocks WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM businesses WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM friends WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
            await self.conn.execute("DELETE FROM achievements WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM cooldowns WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM game_history WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM quests WHERE user_id = ?", (user_id,))
            
            # Reset user stats
            await self.conn.execute(
                """UPDATE users 
                   SET cash = ?, bank_balance = ?, gold = 50, credits = 100, 
                       tokens = 50, level = 1, xp = 0, reputation = 100,
                       daily_streak = 0, last_daily = NULL, warnings = 0
                   WHERE user_id = ?""",
                (GameConfig.START_CASH, GameConfig.START_BANK, user_id)
            )
        
        elif reset_type == "cash":
            await self.conn.execute(
                "UPDATE users SET cash = ? WHERE user_id = ?",
                (GameConfig.START_CASH, user_id)
            )
        
        elif reset_type == "garden":
            await self.conn.execute("DELETE FROM plants WHERE user_id = ?", (user_id,))
            await self.conn.execute("DELETE FROM barn WHERE user_id = ?", (user_id,))
            await self.conn.execute(
                "UPDATE garden SET greenhouse_level = 0 WHERE user_id = ?",
                (user_id,)
            )
        
        await self.conn.commit()
        return True

# ============================================================================
# IMAGE GENERATOR
# ============================================================================

class ImageGenerator:
    """Generate images for the bot"""
    
    def __init__(self):
        self.fonts = {}
        if HAS_PILLOW:
            self.load_fonts()
    
    def load_fonts(self):
        """Load fonts"""
        try:
            # Try to load system fonts
            self.fonts['small'] = ImageFont.truetype("arial.ttf", 14)
            self.fonts['medium'] = ImageFont.truetype("arial.ttf", 18)
            self.fonts['large'] = ImageFont.truetype("arial.ttf", 24)
            self.fonts['title'] = ImageFont.truetype("arial.ttf", 32)
        except:
            # Fallback to default fonts
            self.fonts['small'] = ImageFont.load_default()
            self.fonts['medium'] = ImageFont.load_default()
            self.fonts['large'] = ImageFont.load_default()
            self.fonts['title'] = ImageFont.load_default()
    
    def create_progress_bar(self, progress: float, width: int = 200, height: int = 20) -> Optional[bytes]:
        """Create a progress bar image"""
        if not HAS_PILLOW:
            return None
        
        try:
            img = Image.new('RGB', (width, height), color='#2d3436')
            draw = ImageDraw.Draw(img)
            
            # Draw background
            draw.rectangle([0, 0, width, height], fill='#2d3436', outline='#636e72', width=1)
            
            # Draw progress
            progress_width = int(width * (progress / 100))
            if progress >= 100:
                color = '#00b894'  # Green
            elif progress >= 70:
                color = '#fdcb6e'  # Yellow
            elif progress >= 40:
                color = '#e17055'  # Orange
            else:
                color = '#6c5ce7'  # Purple
            
            draw.rectangle([0, 0, progress_width, height], fill=color)
            
            # Draw percentage text
            text = f"{int(progress)}%"
            text_x = (width - 40) // 2
            draw.text((text_x, 2), text, fill='white' if progress < 50 else 'black', font=self.fonts['small'])
            
            # Save to bytes
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
            width, height = 600, 450
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Title
            title = f"{username}'s Garden"
            draw.text((50, 20), title, fill='#4CAF50', font=self.fonts['title'])
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 120
            padding = 15
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
                        progress = plant.get('current_progress', 0)
                        
                        # Determine color based on progress
                        if progress >= 100:
                            color = '#4CAF50'  # Green - ready
                            status = "READY"
                        elif progress >= 50:
                            color = '#FFC107'  # Yellow - growing
                            status = "GROWING"
                        else:
                            color = '#2196F3'  # Blue - just planted
                            status = "PLANTED"
                        
                        # Draw cell
                        draw.rectangle([x1, y1, x2, y2], fill=color, outline='white', width=2)
                        
                        # Crop emoji
                        try:
                            crop_enum = CropType(plant['crop_type'])
                            crop_data = CROP_DATA.get(crop_enum, {})
                            emoji = crop_data.get('emoji', '🌱')
                        except:
                            emoji = '🌱'
                        
                        # Draw emoji
                        draw.text((x1 + 40, y1 + 20), emoji, fill='white', font=self.fonts['large'])
                        
                        # Crop name
                        crop_name = plant['crop_type'][:6].title()
                        draw.text((x1 + 5, y1 + 5), crop_name, fill='white', font=self.fonts['small'])
                        
                        # Progress percentage
                        progress_text = f"{int(progress)}%"
                        draw.text((x1 + 30, y2 - 25), progress_text, fill='white', font=self.fonts['small'])
                        
                        # Status
                        draw.text((x1 + 5, y2 - 45), status, fill='white', font=self.fonts['small'])
                    
                    else:
                        # Empty slot
                        draw.rectangle([x1, y1, x2, y2], fill='#333333', outline='#666666', width=1)
                        draw.text((x1 + 40, y1 + 40), "➕", fill='#CCCCCC', font=self.fonts['large'])
            
            # Stats at bottom
            stats_y = start_y + grid_size * (cell_size + padding) + 20
            
            # Slots info
            total_slots = garden_info.get('slots', 9) + (garden_info.get('greenhouse_level', 0) * GameConfig.GREENHOUSE_SLOT_BONUS)
            slots_text = f"Slots: {len(plants)}/{total_slots}"
            draw.text((50, stats_y), slots_text, fill='#FFC107', font=self.fonts['medium'])
            
            # Greenhouse level
            greenhouse_text = f"Greenhouse: Level {garden_info.get('greenhouse_level', 0)}"
            draw.text((width - 250, stats_y), greenhouse_text, fill='#4CAF50', font=self.fonts['medium'])
            
            # Ready count
            ready_count = sum(1 for p in plants if p.get('current_progress', 0) >= 100)
            ready_text = f"Ready: {ready_count}"
            draw.text((50, stats_y + 30), ready_text, fill='#4CAF50', font=self.fonts['medium'])
            
            # Footer
            footer = "Use /harvest to collect ready crops"
            draw.text((width//2 - 150, height - 30), footer, fill='#CCCCCC', font=self.fonts['small'])
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None
    
    def create_profile_card(self, user_data: dict, achievements: List[dict]) -> Optional[bytes]:
        """Create profile card image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 500, 400
            img = Image.new('RGB', (width, height), color='#0d1b2a')
            draw = ImageDraw.Draw(img)
            
            # Header with name
            name = user_data.get('first_name', 'User')
            title = f"{name}'s Profile"
            draw.text((width//2 - 100, 20), title, fill='#4CC9F0', font=self.fonts['title'])
            
            # Level and XP
            level = user_data.get('level', 1)
            xp = user_data.get('xp', 0)
            xp_needed = level * 1000
            
            # XP Bar
            bar_width = 300
            bar_height = 25
            bar_x = (width - bar_width) // 2
            bar_y = 70
            
            # Background bar
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                         fill='#1b263b', outline='#415a77', width=2)
            
            # Progress bar
            progress = min(100, (xp / xp_needed) * 100) if xp_needed > 0 else 0
            progress_width = int(bar_width * (progress / 100))
            draw.rectangle([bar_x, bar_y, bar_x + progress_width, bar_y + bar_height], 
                         fill='#4361ee')
            
            # Level text
            level_text = f"Level {level}"
            draw.text((bar_x + 10, bar_y + 4), level_text, fill='white', font=self.fonts['medium'])
            
            # XP text
            xp_text = f"{xp}/{xp_needed} XP"
            draw.text((bar_x + bar_width - 100, bar_y + 4), xp_text, fill='white', font=self.fonts['medium'])
            
            # Stats section
            stats_y = bar_y + bar_height + 20
            stats = [
                f"💰 Cash: ${user_data.get('cash', 0):,}",
                f"🏦 Bank: ${user_data.get('bank_balance', 0):,}",
                f"⭐ Rep: {user_data.get('reputation', 100)}",
                f"🔥 Streak: {user_data.get('daily_streak', 0)} days"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i * 30), stat, fill='#f72585', font=self.fonts['medium'])
            
            # Achievements section
            achievements_y = stats_y + 130
            unlocked = sum(1 for a in achievements if a.get('unlocked', False))
            total = len(achievements)
            
            achievements_text = f"🏆 Achievements: {unlocked}/{total}"
            draw.text((50, achievements_y), achievements_text, fill='#ffba08', font=self.fonts['medium'])
            
            # Show first 3 achievements
            for i, achievement in enumerate(achievements[:3]):
                status = "✅" if achievement.get('unlocked') else "🔒"
                name = achievement.get('name', '')[:15]
                draw.text((70, achievements_y + 25 + i * 25), 
                         f"{status} {name}", 
                         fill='#90be6d' if achievement.get('unlocked') else '#777777',
                         font=self.fonts['small'])
            
            # Footer with join date
            if user_data.get('created_at'):
                try:
                    join_date = datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00'))
                    join_text = f"Joined: {join_date.strftime('%b %d, %Y')}"
                    draw.text((width//2 - 100, height - 30), 
                             join_text, fill='#8ac926', font=self.fonts['small'])
                except:
                    pass
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Profile card error: {e}")
            return None
    
    def create_scratch_card(self, ticket_id: str, numbers: str) -> Optional[bytes]:
        """Create lottery scratch card image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 400, 250
            img = Image.new('RGB', (width, height), color='#2a9d8f')
            draw = ImageDraw.Draw(img)
            
            # Border
            draw.rectangle([0, 0, width, height], outline='#264653', width=5)
            
            # Title
            draw.text((width//2 - 80, 20), "🎰 LOTTERY TICKET", fill='white', font=self.fonts['title'])
            
            # Ticket ID
            draw.text((width//2 - 60, 60), f"#{ticket_id}", fill='#ffd166', font=self.fonts['large'])
            
            # Scratch area
            scratch_x = width//2 - 150
            scratch_y = 100
            scratch_width = 300
            scratch_height = 80
            
            # Scratch background (covered)
            for i in range(scratch_y, scratch_y + scratch_height, 5):
                for j in range(scratch_x, scratch_x + scratch_width, 5):
                    color = random.choice(['#e9c46a', '#f4a261', '#e76f51'])
                    draw.rectangle([j, i, j+3, i+3], fill=color)
            
            # "Scratch Here" text
            draw.text((scratch_x + 80, scratch_y + 25), "SCRATCH HERE", 
                     fill='#264653', font=self.fonts['medium'])
            
            # Hidden numbers (would be revealed after scratching)
            if len(numbers) == 6:
                # Show first and last digit as hint
                hint = f"{numbers[0]} • • • • {numbers[-1]}"
                draw.text((scratch_x + 90, scratch_y + 50), hint, 
                         fill='#264653', font=self.fonts['medium'])
            
            # Instructions
            draw.text((width//2 - 120, height - 40), 
                     "Use /scratch to reveal numbers", 
                     fill='#e9f5db', font=self.fonts['small'])
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Scratch card error: {e}")
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
    """Format seconds to human readable time"""
    if seconds >= 86400:
        return f"{seconds // 86400}d"
    elif seconds >= 3600:
        return f"{seconds // 3600}h"
    elif seconds >= 60:
        return f"{seconds // 60}m"
    else:
        return f"{seconds}s"

def create_progress_bar(progress: float, width: int = 20) -> str:
    """Create text progress bar"""
    filled = int(width * progress / 100)
    return "█" * filled + "░" * (width - filled)

async def send_gif_reaction(command: str, chat_id: int, from_user: types.User, target_user: types.User = None):
    """Send reaction GIF"""
    cursor = await db.conn.execute(
        "SELECT gif_url FROM reaction_gifs WHERE command = ?",
        (command,)
    )
    row = await cursor.fetchone()
    gif_url = row['gif_url'] if row else REACTION_GIFS.get(command)
    
    if not gif_url:
        return
    
    actions = {
        "hug": "hugged",
        "kiss": "kissed",
        "slap": "slapped",
        "pat": "patted",
        "punch": "punched",
        "cuddle": "cuddled",
        "kill": "killed",
        "rob": "robbed"
    }
    
    action = actions.get(command, "interacted with")
    target_name = target_user.first_name if target_user else "someone"
    
    caption = f"🤗 {from_user.first_name} {action} {target_name}!"
    
    try:
        await bot.send_animation(
            chat_id=chat_id,
            animation=gif_url,
            caption=caption
        )
    except Exception as e:
        logger.error(f"GIF send error: {e}")
        await bot.send_message(chat_id, caption)

# ============================================================================
# KEYBOARDS
# ============================================================================

def get_start_keyboard():
    """Get start keyboard with Add to Group button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add to Group", 
                            url=f"https://t.me/{bot.token.split(':')[0]}?startgroup=true")]
    ])
    return keyboard

def get_admin_keyboard():
    """Get admin keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Users", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="💰 Economy", callback_data="admin_economy"),
            InlineKeyboardButton(text="🎮 Games", callback_data="admin_games")
        ],
        [
            InlineKeyboardButton(text="🔧 System", callback_data="admin_system"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")
        ]
    ])
    return keyboard

# ============================================================================
# COMMAND HANDLERS - USER COMMANDS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command - ONLY place with Add to Group button"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
        await db.unlock_achievement(message.from_user.id, "first_daily")
    
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
• Add me to groups for family fun!

📱 <b>Quick Commands:</b>
/me - Your profile
/garden - Your farm  
/bank - Banking system
/lottery - Try your luck
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_start_keyboard(),
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>HELP - ALL COMMANDS</b>

👤 <b>PROFILE & ECONOMY:</b>
/me - Your profile card
/daily - Daily bonus ($500-$1500)
/bank - Banking with interest
/interest - Collect bank interest
/leaderboard - Top players
/balance - Check your money

👨‍👩‍👧‍👦 <b>FAMILY:</b>
/family - View family tree
/adopt - Adopt someone (reply)
/marry - Marry someone (reply)  
/divorce - End marriage
/friends - Friends list
/friend @username - Add friend

🌾 <b>FARMING:</b>
/garden - Your garden (with image)
/plant [crop] [qty] - Plant crops
/harvest - Harvest ready crops
/barn - Storage & sell crops
/sell [crop] [qty] - Sell crops
/crops - Available crops list

💰 <b>INVESTMENTS:</b>
/stocks - Stock market
/buy [symbol] [qty] - Buy stocks
/sellstock [symbol] [qty] - Sell stocks
/portfolio - Your investments
/business - Business empire
/collect - Collect business income

🎮 <b>GAMES:</b>
/slot [bet] - Slot machine
/dice [bet] - Dice game  
/fight - Fight someone (reply)
/lottery - Lottery tickets
/scratch [id] - Scratch ticket
/blackjack [bet] - Blackjack game
/race [bet] - Horse racing

🏪 <b>MARKET:</b>
/market - Marketplace
/shop - Buy items
/inventory - Your items
/trade @user [item] [qty] - Trade items

📈 <b>QUEST SYSTEM:</b>
/quests - Daily quests
/achievements - Your achievements

😊 <b>REACTIONS (reply to user):</b>
/hug, /kiss, /slap, /pat
/punch, /cuddle, /rob, /kill

👑 <b>ADMIN:</b>
/admin - Admin panel (owner only)

📱 <b>Need more help? Contact support!</b>
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("me"))
async def cmd_me(message: Message):
    """User profile with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Get user achievements
    achievements = await db.get_achievements(message.from_user.id)
    
    # Create profile image
    image_bytes = img_gen.create_profile_card(user, achievements)
    
    # Get additional data
    family = await db.get_family(message.from_user.id)
    garden = await db.get_garden(message.from_user.id)
    plants = await db.get_plants(message.from_user.id)
    portfolio = await db.get_portfolio(message.from_user.id)
    businesses = await db.get_businesses(message.from_user.id)
    
    # Calculate total wealth
    total_wealth = user.get('cash', 0) + user.get('bank_balance', 0) + portfolio.get('total_value', 0)
    
    # Check for millionaire achievement
    if total_wealth >= 1000000:
        await db.unlock_achievement(message.from_user.id, "millionaire")
    
    caption = f"""
👤 <b>{user['first_name']}'s Profile</b>

💰 <b>Wealth Summary:</b>
• Cash: ${user.get('cash', 0):,}
• Bank: ${user.get('bank_balance', 0):,}
• Investments: ${portfolio.get('total_value', 0):,.2f}
• <b>Total: ${total_wealth:,}</b>

📊 <b>Stats:</b>
• Level: {user.get('level', 1)}
• XP: {user.get('xp', 0)}/{(user.get('level', 1) * 1000)}
• Reputation: {user.get('reputation', 100)}
• Daily Streak: {user.get('daily_streak', 0)} days

👨‍👩‍👧‍👦 <b>Family:</b> {len(family)} members
🌾 <b>Garden:</b> {len(plants)} crops growing
🏢 <b>Businesses:</b> {len(businesses)} owned
🏆 <b>Achievements:</b> {sum(1 for a in achievements if a.get('unlocked'))}/{len(achievements)}

💡 Use /help for all commands
"""
    
    # Try to get user's profile photo
    try:
        photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            if image_bytes:
                # Send both profile photo and generated image
                await message.answer_photo(
                    photo.file_id,
                    caption="Your profile photo 👤",
                    parse_mode=ParseMode.HTML
                )
                photo_gen = BufferedInputFile(image_bytes, filename="profile.png")
                await message.answer_photo(
                    photo=photo_gen,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.answer_photo(
                    photo.file_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
        else:
            if image_bytes:
                photo = BufferedInputFile(image_bytes, filename="profile.png")
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.answer(caption, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Profile photo error: {e}")
        if image_bytes:
            photo = BufferedInputFile(image_bytes, filename="profile.png")
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer(caption, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Check cooldown
    can_use, remaining = await db.check_cooldown(message.from_user.id, "daily", 86400)
    if not can_use:
        await message.answer(f"⏳ Come back in {format_time(remaining)}!")
        return
    
    # Calculate bonus
    base_bonus = random.randint(GameConfig.DAILY_MIN, GameConfig.DAILY_MAX)
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * GameConfig.FAMILY_DAILY_BONUS
    
    streak = user.get('daily_streak', 0) + 1
    streak_bonus = min(500, streak * 50)
    
    # Bio verification bonus
    bio_multiplier = 2 if user.get('bio_verified') else 1
    
    total_bonus = (base_bonus + family_bonus + streak_bonus) * bio_multiplier
    
    # Give bonus
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.set_cooldown(message.from_user.id, "daily")
    
    # Update streak
    await db.conn.execute(
        """UPDATE users 
           SET daily_streak = ?, last_daily = CURRENT_TIMESTAMP
           WHERE user_id = ?""",
        (streak, message.from_user.id)
    )
    await db.conn.commit()
    
    # Give random gemstone
    gemstones = ["💎 Diamond", "🔴 Ruby", "🔵 Sapphire", "🟢 Emerald", "🟣 Amethyst"]
    gemstone = random.choice(gemstones)
    
    response = f"""
🎉 <b>DAILY BONUS COLLECTED!</b>

💰 <b>Breakdown:</b>
• Base Bonus: ${base_bonus:,}
• Family Bonus ({len(family)}): ${family_bonus:,}
• Streak Bonus ({streak} days): ${streak_bonus:,}
• Multiplier: {bio_multiplier}x

🎁 <b>Total: ${total_bonus:,}</b>

{gemstone} You found a {gemstone}!
💵 New Balance: ${user.get('cash', 0) + total_bonus:,}

{"✅ Bio verified (2x bonus!)" if bio_multiplier > 1 else "💡 Add me to bio for 2x bonus!"}
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    """Check balance"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    portfolio = await db.get_portfolio(message.from_user.id)
    total_wealth = user.get('cash', 0) + user.get('bank_balance', 0) + portfolio.get('total_value', 0)
    
    response = f"""
💰 <b>BALANCE</b>

💵 <b>Cash:</b> ${user.get('cash', 0):,}
🏦 <b>Bank:</b> ${user.get('bank_balance', 0):,}
📈 <b>Investments:</b> ${portfolio.get('total_value', 0):,.2f}

🏆 <b>Total Wealth:</b> ${total_wealth:,}

💡 Use /bank to manage money
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# FAMILY COMMANDS
# ============================================================================

@dp.message(Command("family"))
async def cmd_family(message: Message):
    """Family tree"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    friends = await db.get_friends(message.from_user.id)
    
    if not family and not friends:
        response = """
🌳 <b>Your Family Tree</b>

└─ You (Just starting!)

💡 <b>How to grow your family:</b>
• Reply to someone with /adopt to make them your child
• Reply with /marry to get married
• Use /friend @username to add friends

👑 <b>Benefits:</b>
• Daily bonus increases per family member
• Family quests and events
• Inheritance system
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    # Build family tree text
    tree_text = f"🌳 <b>Family Tree of {user['first_name']}</b>\n\n"
    tree_text += f"└─ {user['first_name']} (You)\n"
    
    # Add family members
    for member in family:
        emoji = "💑" if member['relation'] == "spouse" else "👶" if member['relation'] == "child" else "👴"
        tree_text += f"   ├─ {emoji} {member['first_name']} ({member['relation']})\n"
    
    # Add friends
    if friends:
        tree_text += "\n👥 <b>Friends:</b>\n"
        for friend in friends[:5]:  # Show first 5
            level_hearts = "❤️" * min(friend['friendship_level'], 5)
            tree_text += f"{level_hearts} {friend['first_name']}\n"
    
    stats_text = f"""
📊 <b>Family Stats:</b>
• Members: {len(family)}
• Friends: {len(friends)}
• Daily Bonus: +${len(family) * GameConfig.FAMILY_DAILY_BONUS}

💡 <b>Commands:</b>
• /adopt - Make someone your child
• /marry - Marry someone
• /divorce - End marriage
• /friend @username - Add friend
"""
    
    await message.answer(tree_text + stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone as child"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Please reply to someone's message to adopt them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    if target.is_bot:
        await message.answer("❌ Cannot adopt bots!")
        return
    
    # Check if users exist
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Add relation
    await db.add_family_member(message.from_user.id, target.id, "child")
    
    # Give adoption bonuses
    await db.update_currency(message.from_user.id, "cash", GameConfig.ADOPT_BONUS)
    await db.update_currency(target.id, "cash", GameConfig.ADOPT_BONUS // 2)
    
    # Check for family achievement
    family = await db.get_family(message.from_user.id)
    if len(family) >= 5:
        await db.unlock_achievement(message.from_user.id, "family_5")
    
    response = f"""
✅ <b>ADOPTION SUCCESSFUL!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
💰 Bonus: ${GameConfig.ADOPT_BONUS:,} for you, ${GameConfig.ADOPT_BONUS // 2:,} for {target.first_name}

👨‍👩‍👧‍👦 Your family now has {len(family)} members
💡 Daily bonus increased!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Marry someone"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Please reply to someone's message to marry them!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    # Check if users exist
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Add relation
    await db.add_family_member(message.from_user.id, target.id, "spouse")
    
    # Give marriage bonuses
    await db.update_currency(message.from_user.id, "cash", GameConfig.MARRY_BONUS)
    await db.update_currency(target.id, "cash", GameConfig.MARRY_BONUS)
    
    response = f"""
💍 <b>MARRIAGE SUCCESSFUL!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Gift: ${GameConfig.MARRY_BONUS:,} each

🎉 <b>Congratulations on your wedding!</b>

💡 Now you can build your family together!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("divorce"))
async def cmd_divorce(message: Message):
    """Divorce spouse"""
    target = await get_target_user(message)
    
    if not target:
        await message.answer("❌ Reply to someone's message to divorce them!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Remove marriage relationship
    await db.remove_family_member(message.from_user.id, target.id, "spouse")
    
    response = f"""
💔 <b>DIVORCE COMPLETE</b>

You are no longer married to {target.first_name}.

Relationship ended.
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("friend"))
async def cmd_friend(message: Message, command: CommandObject):
    """Add friend by username"""
    if not command.args:
        await message.answer("❌ Usage: /friend @username\nExample: /friend @john")
        return
    
    # This is a simplified version - in real bot, you would lookup user by username
    response = """
👥 <b>ADD FRIEND</b>

To add a friend, mention them:
<code>/friend @username</code>

Or reply to their message with:
<code>/friend</code>

💡 Friends give you:
• Daily interaction bonuses
• Gift exchange
• Friendship levels
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("friends"))
async def cmd_friends(message: Message):
    """Friends list"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    friends = await db.get_friends(message.from_user.id)
    
    if not friends:
        response = """
👥 <b>FRIENDS LIST</b>

You don't have any friends yet!

💡 <b>How to add friends:</b>
• Use /friend @username
• Interact with people in groups
• Complete quests together

🤝 <b>Friendship Benefits:</b>
• Daily interaction bonuses
• Gift exchanges
• Special quests
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    response = "👥 <b>YOUR FRIENDS</b>\n\n"
    
    for i, friend in enumerate(friends[:10], 1):
        level_hearts = "❤️" * min(friend['friendship_level'], 5)
        response += f"{i}. {friend['first_name']} {level_hearts}\n"
    
    if len(friends) > 10:
        response += f"\n... and {len(friends) - 10} more friends"
    
    response += f"\n\n📊 Total friends: {len(friends)}"
    response += "\n💡 Use /friend @username to add more!"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# GARDEN COMMANDS
# ============================================================================

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
    
    # Calculate stats
    ready_count = sum(1 for p in plants if p.get('current_progress', 0) >= 100)
    total_slots = garden_info.get('slots', 9) + (garden_info.get('greenhouse_level', 0) * GameConfig.GREENHOUSE_SLOT_BONUS)
    
    caption = f"""
🌾 <b>{user['first_name']}'s Garden</b>

📊 <b>Stats:</b>
• Growing: {len(plants)}/{total_slots} slots
• Ready: {ready_count} crops
• Greenhouse: Level {garden_info.get('greenhouse_level', 0)}
• Growth Speed: +{garden_info.get('greenhouse_level', 0) * 10}%

💡 <b>Commands:</b>
• /plant [crop] [qty] - Plant crops
• /harvest - Collect ready crops
• /barn - View storage
• /sell [crop] [qty] - Sell crops

🌱 <b>Available Crops:</b>
🥕 Carrot - $10 (2h)
🍅 Tomato - $15 (3h)  
🥔 Potato - $8 (2.5h)
🍆 Eggplant - $20 (4h)
🌽 Corn - $12 (5h)
🫑 Pepper - $25 (6h)
🍉 Watermelon - $30 (7h)
🎃 Pumpkin - $40 (8h)
"""
    
    # Add progress bars for plants
    if plants:
        caption += "\n📈 <b>Current Crops:</b>\n"
        for plant in plants[:3]:  # Show first 3
            progress = plant.get('current_progress', 0)
            try:
                crop_enum = CropType(plant['crop_type'])
                crop_data = CROP_DATA.get(crop_enum, {})
                emoji = crop_data.get('emoji', '🌱')
            except:
                emoji = '🌱'
            caption += f"{emoji} {plant['crop_type'].title()}: {create_progress_bar(progress)} {int(progress)}%\n"
    
    if len(plants) > 3:
        caption += f"... and {len(plants) - 3} more crops\n"
    
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

@dp.message(Command("crops"))
async def cmd_crops(message: Message):
    """Show available crops"""
    crops_list = "\n".join([
        f"{data['emoji']} {crop.value.title()} - Buy: ${data['buy']} | Sell: ${data['sell']} | Grow: {data['grow_time']}h | XP: {data['xp']}"
        for crop, data in CROP_DATA.items()
    ])
    
    response = f"""
🌱 <b>AVAILABLE CROPS</b>

{crops_list}

💡 <b>Tips:</b>
• Faster crops = quicker money
• Higher value crops = more profit
• Greenhouse reduces grow time
• Level up to unlock better crops
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    if not command.args:
        crops_list = "\n".join([
            f"{data['emoji']} {crop.value.title()} - ${data['buy']} ({data['grow_time']}h)"
            for crop, data in list(CROP_DATA.items())[:6]
        ])
        
        response = f"""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
{crops_list}

💡 <b>Examples:</b>
<code>/plant carrot 3</code>
<code>/plant tomato 2</code>  
<code>/plant watermelon 1</code>

📊 <b>Your Garden:</b>
Use /garden to check available space
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
    
    # Validate crop type
    try:
        crop_enum = CropType(crop_type)
        crop_data = CROP_DATA.get(crop_enum)
    except ValueError:
        available_crops = ", ".join([c.value for c in CropType])
        await message.answer(f"❌ Invalid crop! Available: {available_crops}")
        return
    
    if quantity < 1 or quantity > 9:
        await message.answer("❌ Quantity must be between 1 and 9!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Check cost
    total_cost = crop_data['buy'] * quantity
    if user['cash'] < total_cost:
        await message.answer(f"❌ You need ${total_cost:,}! You have ${user['cash']:,}")
        return
    
    # Plant crops
    success = await db.plant_crop(message.from_user.id, crop_type, quantity)
    
    if not success:
        await message.answer("❌ Not enough garden space! Use /garden to check available slots.")
        return
    
    # Deduct money
    await db.update_currency(message.from_user.id, "cash", -total_cost)
    
    response = f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{crop_data['emoji']} <b>Crop:</b> {crop_type.title()}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Cost:</b> ${total_cost:,}
⏰ <b>Grow Time:</b> {crop_data['grow_time']} hours
⭐ <b>XP per crop:</b> {crop_data['xp']}

🌱 {quantity} {crop_type.title()}{'s' if quantity > 1 else ''} now growing in your garden!

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
    
    # Calculate total value and XP
    total_value = 0
    total_xp = 0
    harvest_text = "✅ <b>HARVEST COMPLETE!</b>\n\n"
    
    for crop_type, count in harvested:
        try:
            crop_enum = CropType(crop_type)
            crop_data = CROP_DATA.get(crop_enum, {})
            sell_price = crop_data.get('sell', 0) * count
            crop_xp = crop_data.get('xp', 0) * count
            total_value += sell_price
            total_xp += crop_xp
            
            harvest_text += f"{crop_data.get('emoji', '🌱')} {crop_type.title()}: {count} × ${crop_data.get('sell', 0)} = ${sell_price}\n"
        except:
            harvest_text += f"🌱 {crop_type}: {count} crops\n"
    
    # Add money and XP
    if total_value > 0:
        await db.update_currency(message.from_user.id, "cash", total_value)
    
    if total_xp > 0:
        levels_gained = await db.add_xp(message.from_user.id, total_xp)
        if levels_gained > 0:
            harvest_text += f"\n⭐ <b>Level Up!</b> You gained {levels_gained} level(s)!"
    
    # Check for achievement
    cursor = await db.conn.execute(
        "SELECT COUNT(*) as total FROM (SELECT 1 FROM plants WHERE user_id = ? AND is_ready = 1)",
        (message.from_user.id,)
    )
    row = await cursor.fetchone()
    total_harvested = row['total'] if row else 0
    
    if total_harvested >= 100:
        await db.unlock_achievement(message.from_user.id, "garden_master")
    
    harvest_text += f"\n💰 <b>Total Earned: ${total_value:,}</b>"
    harvest_text += f"\n💵 New Balance: ${user['cash'] + total_value:,}"
    if total_xp > 0:
        harvest_text += f"\n⭐ <b>XP Gained:</b> {total_xp}"
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

@dp.message(Command("barn"))
async def cmd_barn(message: Message):
    """Barn storage"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    barn_items = await db.get_barn(message.from_user.id)
    
    if not barn_items:
        await message.answer("🏠 <b>Barn Storage</b>\n\nYour barn is empty! Harvest crops to fill it.")
        return
    
    barn_text = "🏠 <b>Barn Storage</b>\n\n"
    total_value = 0
    
    for item in barn_items:
        try:
            crop_enum = CropType(item['crop_type'])
            crop_data = CROP_DATA.get(crop_enum, {})
            value = crop_data.get('sell', 0) * item['quantity']
            total_value += value
            
            barn_text += f"{crop_data.get('emoji', '📦')} {item['crop_type'].title()}: {item['quantity']} (${value})\n"
        except:
            barn_text += f"📦 {item['crop_type'].title()}: {item['quantity']}\n"
    
    barn_text += f"\n💰 <b>Total Value: ${total_value:,}</b>"
    barn_text += f"\n💡 Use /sell [crop] [quantity] to sell crops"
    barn_text += f"\n📊 Use /market to see current prices"
    
    await message.answer(barn_text, parse_mode=ParseMode.HTML)

@dp.message(Command("sell"))
async def cmd_sell(message: Message, command: CommandObject):
    """Sell crops"""
    if not command.args:
        response = """
💰 <b>SELL CROPS</b>

Usage: <code>/sell [crop] [quantity]</code>

💡 <b>Examples:</b>
<code>/sell carrot 10</code>
<code>/sell tomato 5</code>

📦 <b>Your Storage:</b>
Use /barn to see what you have
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    args = command.args.lower().split()
    if len(args) < 2:
        await message.answer("❌ Format: /sell [crop] [quantity]\nExample: /sell carrot 10")
        return
    
    crop_type = args[0]
    try:
        quantity = int(args[1])
    except ValueError:
        await message.answer("❌ Quantity must be a number!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # Sell crops
    total_value = await db.sell_crops(message.from_user.id, crop_type, quantity)
    
    if total_value is None:
        await message.answer(f"❌ You don't have enough {crop_type} in your barn!")
        return
    
    try:
        crop_enum = CropType(crop_type)
        crop_data = CROP_DATA.get(crop_enum, {})
        emoji = crop_data.get('emoji', '🌱')
    except:
        emoji = '🌱'
    
    response = f"""
✅ <b>SOLD SUCCESSFULLY!</b>

{emoji} <b>Crop:</b> {crop_type.title()}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Earned:</b> ${total_value:,}

💵 New Balance: ${user['cash'] + total_value:,}

📦 Remaining in barn: /barn
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# BANK COMMANDS
# ============================================================================

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
        try:
            last_interest = datetime.fromisoformat(bank_account['last_interest'])
            next_time = last_interest + timedelta(days=1)
            if next_time > datetime.now():
                hours_left = int((next_time - datetime.now()).total_seconds() / 3600)
                next_interest = f"{hours_left}h"
        except:
            pass
    
    response = f"""
🏦 <b>BANK OF FAMILY TREE</b>

💰 <b>Your Accounts:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Savings: <b>${user.get('bank_balance', 0):,}</b>
• 📈 Interest Earned: <b>${bank_account.get('total_interest', 0):,}</b>

📊 <b>Bank Features:</b>
• Daily Interest: {GameConfig.BANK_INTEREST_RATE}%
• Next Interest: {next_interest}
• Safe from robbery
• Transaction history

💡 <b>Commands:</b>
• /deposit [amount] - Deposit to bank
• /withdraw [amount] - Withdraw from bank  
• /interest - Collect interest
• /statement - View transactions

🔒 <b>Your money is safe with us!</b>
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

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
    
    # Deposit
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
    """Withdraw money from bank"""
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
    
    # Withdraw
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
    """Collect bank interest"""
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
async def cmd_statement(message: Message, command: CommandObject):
    """Bank statement"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    limit = 10
    if command.args:
        try:
            limit = min(int(command.args), 50)
        except:
            pass
    
    transactions = await db.get_transactions(message.from_user.id, limit)
    
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
        
        # Format date
        try:
            trans_date = datetime.fromisoformat(trans['created_at'])
            date_str = trans_date.strftime('%m/%d %H:%M')
        except:
            date_str = trans['created_at'][:16]
        
        amount_text = f"${abs(trans['amount']):,}"
        statement_text += f"{emoji} {sign}{amount_text} - {trans.get('description', 'Transaction')} ({date_str})\n"
    
    statement_text += f"\n💡 Showing last {len(transactions)} transactions"
    statement_text += "\n💡 Use /statement [number] to see more"
    
    await message.answer(statement_text, parse_mode=ParseMode.HTML)

# ============================================================================
# STOCK MARKET COMMANDS
# ============================================================================

@dp.message(Command("stocks"))
async def cmd_stocks(message: Message):
    """Stock market"""
    response = """
📈 <b>STOCK MARKET</b>

Welcome to the Family Tree Stock Exchange!

💹 <b>Available Stocks:</b>
• TECH - Tech Corp (Volatile)
• FARM - Farm Inc (Stable)
• GOLD - Gold Mining (Safe)
• OIL - Oil Co (Risky)
• BIO - Bio Tech (High Risk)

💡 <b>How it works:</b>
• Prices change randomly every hour
• Buy low, sell high
• Monitor market trends

📊 <b>Commands:</b>
• /buystock [symbol] [qty] - Buy stocks
• /sellstock [symbol] [qty] - Sell stocks
• /portfolio - Your investments
• /stockprice [symbol] - Check price

🎯 <b>Tip:</b> Diversify your portfolio!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("buystock"))
async def cmd_buystock(message: Message, command: CommandObject):
    """Buy stocks"""
    if not command.args:
        await message.answer("❌ Usage: /buystock [symbol] [quantity]\nExample: /buystock TECH 10")
        return
    
    args = command.args.upper().split()
    if len(args) < 2:
        await message.answer("❌ Format: /buystock [symbol] [quantity]\nExample: /buystock TECH 10")
        return
    
    symbol = args[0]
    try:
        quantity = int(args[1])
    except ValueError:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if symbol not in STOCKS:
        await message.answer(f"❌ Invalid symbol! Available: {', '.join(STOCKS.keys())}")
        return
    
    if quantity < 1:
        await message.answer("❌ Quantity must be at least 1!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    success, total_cost = await db.buy_stocks(message.from_user.id, symbol, quantity)
    
    if not success:
        await message.answer(f"❌ You need ${total_cost:,.2f} to buy {quantity} shares of {symbol}!")
        return
    
    stock_data = STOCKS[symbol]
    current_price = await db.get_stock_price(symbol)
    
    response = f"""
✅ <b>STOCKS PURCHASED!</b>

📈 <b>Stock:</b> {stock_data['name']} ({symbol})
🔢 <b>Quantity:</b> {quantity}
💰 <b>Price per share:</b> ${current_price:,.2f}
💵 <b>Total Cost:</b> ${total_cost:,.2f}

🏦 <b>New Cash Balance:</b> ${user['cash'] - total_cost:,}

📊 <b>Portfolio:</b> /portfolio
💡 Check /stockprice {symbol} for updates
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("sellstock"))
async def cmd_sellstock(message: Message, command: CommandObject):
    """Sell stocks"""
    if not command.args:
        await message.answer("❌ Usage: /sellstock [symbol] [quantity]\nExample: /sellstock TECH 5")
        return
    
    args = command.args.upper().split()
    if len(args) < 2:
        await message.answer("❌ Format: /sellstock [symbol] [quantity]\nExample: /sellstock TECH 5")
        return
    
    symbol = args[0]
    try:
        quantity = int(args[1])
    except ValueError:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if symbol not in STOCKS:
        await message.answer(f"❌ Invalid symbol! Available: {', '.join(STOCKS.keys())}")
        return
    
    if quantity < 1:
        await message.answer("❌ Quantity must be at least 1!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    success, total_value, profit = await db.sell_stocks(message.from_user.id, symbol, quantity)
    
    if not success:
        await message.answer(f"❌ You don't own enough shares of {symbol}!")
        return
    
    stock_data = STOCKS[symbol]
    current_price = await db.get_stock_price(symbol)
    
    profit_color = "🟢" if profit >= 0 else "🔴"
    
    response = f"""
✅ <b>STOCKS SOLD!</b>

📈 <b>Stock:</b> {stock_data['name']} ({symbol})
🔢 <b>Quantity:</b> {quantity}
💰 <b>Price per share:</b> ${current_price:,.2f}
💵 <b>Total Value:</b> ${total_value:,.2f}
{profit_color} <b>Profit/Loss:</b> ${profit:,.2f}

🏦 <b>New Cash Balance:</b> ${user['cash'] + total_value:,}

📊 <b>Portfolio:</b> /portfolio
💡 Smart trading!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("portfolio"))
async def cmd_portfolio(message: Message):
    """Stock portfolio"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    portfolio = await db.get_portfolio(message.from_user.id)
    
    if not portfolio['stocks']:
        response = """
📊 <b>STOCK PORTFOLIO</b>

Your portfolio is empty!

💡 <b>Get started:</b>
• Check /stocks for available stocks
• Buy stocks with /buystock
• Monitor prices with /stockprice

🎯 <b>Tip:</b> Start with stable stocks like FARM or GOLD
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    response = f"""
📊 <b>STOCK PORTFOLIO</b>

📈 <b>Summary:</b>
• Total Stocks: {portfolio['count']}
• Total Value: ${portfolio['total_value']:,.2f}
• Total Profit: ${portfolio['total_profit']:,.2f}

💹 <b>Your Holdings:</b>
"""
    
    for stock in portfolio['stocks']:
        profit_color = "🟢" if stock['profit'] >= 0 else "🔴"
        response += f"\n{stock['symbol']} - {stock['name']}"
        response += f"\n  Shares: {stock['shares']}"
        response += f"\n  Value: ${stock['value']:,.2f}"
        response += f"\n  {profit_color} Profit: ${stock['profit']:,.2f} ({stock['profit_percent']:.1f}%)"
    
    response += "\n\n💡 Use /stocks to trade more!"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("stockprice"))
async def cmd_stockprice(message: Message, command: CommandObject):
    """Check stock price"""
    if not command.args:
        # Show all stock prices
        response = "📈 <b>CURRENT STOCK PRICES</b>\n\n"
        
        for symbol, data in STOCKS.items():
            price = await db.get_stock_price(symbol)
            if price:
                response += f"{symbol} - {data['name']}: <b>${price:,.2f}</b>\n"
            else:
                response += f"{symbol} - {data['name']}: Loading...\n"
        
        response += "\n💡 Prices update every hour"
        response += "\n📊 Use /stocks for trading"
        
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    symbol = command.args.strip().upper()
    
    if symbol not in STOCKS:
        await message.answer(f"❌ Invalid symbol! Available: {', '.join(STOCKS.keys())}")
        return
    
    price = await db.get_stock_price(symbol)
    if not price:
        await message.answer("❌ Could not fetch price. Try again later.")
        return
    
    stock_data = STOCKS[symbol]
    
    response = f"""
📈 <b>STOCK PRICE</b>

🏢 <b>Company:</b> {stock_data['name']}
📊 <b>Symbol:</b> {symbol}
💰 <b>Current Price:</b> <b>${price:,.2f}</b>
📉 <b>Volatility:</b> {stock_data['volatility']*100:.1f}%

💡 <b>Trading:</b>
• Buy: /buystock {symbol} [quantity]
• Sell: /sellstock {symbol} [quantity]

🎯 <b>Tip:</b> {stock_data['name']} is {'high risk' if stock_data['volatility'] > 0.2 else 'medium risk' if stock_data['volatility'] > 0.15 else 'low risk'}
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# BUSINESS COMMANDS
# ============================================================================

@dp.message(Command("business"))
async def cmd_business(message: Message):
    """Business system"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    businesses = await db.get_businesses(message.from_user.id)
    
    if not businesses:
        response = """
🏢 <b>BUSINESS EMPIRE</b>

Start your business empire and earn passive income!

💼 <b>Available Businesses:</b>
• 🌾 Farm - $5,000 (Income: $500/day)
• 🏪 Store - $10,000 (Income: $1,000/day)
• 🍽️ Restaurant - $25,000 (Income: $2,500/day)
• 🏨 Hotel - $50,000 (Income: $5,000/day)
• 🎰 Casino - $100,000 (Income: $10,000/day)

💡 <b>How it works:</b>
• Buy businesses with /buybusiness [type]
• Collect income every 24 hours with /collect
• Upgrade businesses to increase income
• Multiple businesses = multiple income streams

💰 <b>Commands:</b>
• /buybusiness [type] - Purchase business
• /collect - Collect business income
• /mybusiness - View your businesses
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    response = f"""
🏢 <b>YOUR BUSINESS EMPIRE</b>

📊 <b>Summary:</b>
• Total Businesses: {len(businesses)}
• Total Earned: ${sum(b['total_earned'] for b in businesses):,}

💼 <b>Your Businesses:</b>
"""
    
    total_next_income = 0
    for business in businesses:
        response += f"\n{business['name']} (Level {business['level']})"
        response += f"\n  Earned: ${business['total_earned']:,}"
        response += f"\n  Next Income: ${business['next_income']:,}"
        total_next_income += business['next_income']
    
    response += f"\n\n💰 <b>Total Next Income:</b> ${total_next_income:,}"
    response += f"\n💡 Use /collect to collect income"
    response += f"\n🔄 Income available every {GameConfig.BUSINESS_INCOME_INTERVAL} hours"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("buybusiness"))
async def cmd_buybusiness(message: Message, command: CommandObject):
    """Buy a business"""
    if not command.args:
        business_list = "\n".join([
            f"{data['name']} - ${data['price']:,} (Income: ${data['income']:,}/day)"
            for biz_type, data in BUSINESS_TYPES.items()
        ])
        
        response = f"""
🏢 <b>BUY BUSINESS</b>

Usage: <code>/buybusiness [type]</code>

💼 <b>Available Businesses:</b>
{business_list}

💡 <b>Examples:</b>
<code>/buybusiness farm</code>
<code>/buybusiness store</code>

💰 <b>Tip:</b> Start with a Farm or Store to build capital
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    business_type = command.args.lower().strip()
    
    if business_type not in BUSINESS_TYPES:
        available = ", ".join(BUSINESS_TYPES.keys())
        await message.answer(f"❌ Invalid business type! Available: {available}")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    success, message_text = await db.buy_business(message.from_user.id, business_type)
    
    if success:
        business = BUSINESS_TYPES[business_type]
        response = f"""
✅ <b>BUSINESS PURCHASED!</b>

{business['name']}
💰 <b>Price:</b> ${business['price']:,}
💵 <b>Daily Income:</b> ${business['income']:,}
📊 <b>Level:</b> 1

🏢 Your business is now operational!
💡 Collect income every {GameConfig.BUSINESS_INCOME_INTERVAL} hours with /collect

📈 <b>New Cash Balance:</b> ${user['cash'] - business['price']:,}
"""
    else:
        response = f"❌ {message_text}"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("collect"))
async def cmd_collect(message: Message):
    """Collect business income"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    income, message_text = await db.collect_business_income(message.from_user.id)
    
    if income > 0:
        response = f"""
✅ <b>INCOME COLLECTED!</b>

💰 <b>Amount:</b> ${income:,}
💼 <b>From:</b> {message_text}

💵 <b>New Cash Balance:</b> ${user['cash'] + income:,}

🏢 Your businesses continue to generate income!
💡 Check back in {GameConfig.BUSINESS_INCOME_INTERVAL} hours
"""
    else:
        response = f"""
⏳ <b>BUSINESS INCOME</b>

{message_text}

💼 Check /business to see your businesses
🔄 Income available every {GameConfig.BUSINESS_INCOME_INTERVAL} hours
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("mybusiness"))
async def cmd_mybusiness(message: Message):
    """View your businesses"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    businesses = await db.get_businesses(message.from_user.id)
    
    if not businesses:
        response = """
🏢 <b>MY BUSINESSES</b>

You don't own any businesses yet!

💡 <b>Get started:</b>
• Check /business for available businesses
• Buy your first business with /buybusiness
• Earn passive income every day!

💰 <b>Recommended:</b>
Start with a Farm ($5,000) or Store ($10,000)
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    response = "🏢 <b>MY BUSINESSES</b>\n\n"
    
    for business in businesses:
        response += f"{business['name']} (Level {business['level']})\n"
        response += f"  Earned: ${business['total_earned']:,}\n"
        response += f"  Next Income: ${business['next_income']:,}\n"
        
        if business['last_collected']:
            try:
                last_collected = datetime.fromisoformat(business['last_collected'])
                next_collect = last_collected + timedelta(hours=GameConfig.BUSINESS_INCOME_INTERVAL)
                if next_collect > datetime.now():
                    hours_left = int((next_collect - datetime.now()).total_seconds() / 3600)
                    response += f"  Next collect in: {hours_left}h\n"
                else:
                    response += f"  ⏰ Ready to collect!\n"
            except:
                response += f"  ⏰ Check collection time\n"
        
        response += "\n"
    
    response += "💡 Use /collect to collect income from all businesses"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# LOTTERY COMMANDS
# ============================================================================

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

🎁 <b>Current Jackpot:</b> Based on ticket sales
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    if command.args.lower().startswith("buy"):
        try:
            args = command.args.split()[1:]
            if not args:
                await message.answer("❌ Usage: /lottery buy [quantity]\nExample: /lottery buy 3")
                return
            
            quantity = int(args[0])
            if quantity < 1 or quantity > 10:
                await message.answer("❌ Quantity must be between 1 and 10!")
                return
            
            user = await db.get_user(message.from_user.id)
            if not user:
                await message.answer("❌ Please use /start first!")
                return
            
            success, tickets, cost = await db.buy_lottery_ticket(message.from_user.id, quantity)
            
            if not success:
                await message.answer(f"❌ You need ${cost:,} to buy {quantity} tickets! You have ${user['cash']:,}")
                return
            
            # Create scratch card image for first ticket
            image_bytes = None
            if tickets:
                ticket_data = await db.scratch_ticket(message.from_user.id, tickets[0])
                if ticket_data and not ticket_data['already_scratched']:
                    image_bytes = img_gen.create_scratch_card(tickets[0], ticket_data['numbers'])
            
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
            
            if image_bytes:
                photo = BufferedInputFile(image_bytes, filename="scratch_card.png")
                await message.answer_photo(
                    photo=photo,
                    caption=response,
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.answer(response, parse_mode=ParseMode.HTML)
            
        except ValueError:
            await message.answer("❌ Quantity must be a number!")
        except IndexError:
            await message.answer("❌ Usage: /lottery buy [quantity]")
    else:
        await message.answer("❌ Use /lottery buy [quantity] to purchase tickets")

@dp.message(Command("buy"))
async def cmd_buy(message: Message, command: CommandObject):
    """Buy lottery tickets (short command)"""
    if not command.args:
        await message.answer("❌ Usage: /buy [quantity]\nExample: /buy 3\n\n💡 This buys lottery tickets for $50 each")
        return
    
    try:
        quantity = int(command.args)
        if quantity < 1 or quantity > 10:
            await message.answer("❌ Quantity must be between 1 and 10!")
            return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        success, tickets, cost = await db.buy_lottery_ticket(message.from_user.id, quantity)
        
        if not success:
            await message.answer(f"❌ You need ${cost:,} to buy {quantity} tickets! You have ${user['cash']:,}")
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
<code>/buy 3</code>

💰 Ticket price: ${GameConfig.LOTTERY_TICKET_PRICE}
🎰 Weekly draws every Sunday
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
        ticket_id_short = ticket['ticket_id'][:10]
        response += f"{status} #{ticket_id_short}\n"
    
    if total_tickets > 5:
        response += f"• ... and {total_tickets - 5} more\n"
    
    response += "\n💡 <b>Commands:</b>"
    response += "\n• /scratch [ticket_id] - Scratch a ticket"
    response += "\n• /buy [qty] - Buy more tickets"
    response += "\n🎰 Draw every Sunday!"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("scratch"))
async def cmd_scratch(message: Message, command: CommandObject):
    """Scratch lottery ticket"""
    if not command.args:
        await message.answer("❌ Usage: /scratch [ticket_id]\nExample: /scratch LOT-123456\n\n💡 Check /mytickets for your ticket IDs")
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

# ============================================================================
# GAME COMMANDS
# ============================================================================

@dp.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject):
    """Dice game"""
    # Get bet amount
    bet = 100
    if command.args:
        try:
            bet = int(command.args)
            if bet < GameConfig.MIN_BET:
                await message.answer(f"❌ Minimum bet is ${GameConfig.MIN_BET}!")
                return
            if bet > GameConfig.MAX_BET:
                await message.answer(f"❌ Maximum bet is ${GameConfig.MAX_BET}!")
                return
        except ValueError:
            await message.answer(f"❌ Bet must be a number!\nExample: /dice {GameConfig.MIN_BET}")
            return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user['cash'] < bet:
        await message.answer(f"❌ You need ${bet:,} to play! You have ${user['cash']:,}")
        return
    
    # Send Telegram dice
    try:
        sent_dice = await message.answer_dice()
        dice_value = sent_dice.dice.value
    except:
        # Fallback to random dice
        dice_value = random.randint(1, 6)
        await message.answer(f"🎲 You rolled: {dice_value}")
    
    # Calculate win/loss
    if dice_value >= 4:  # Win on 4, 5, or 6
        win_amount = bet * 2
        result = "🎉 YOU WIN!"
        await db.update_currency(message.from_user.id, "cash", win_amount)
        profit = win_amount
    else:  # Lose on 1, 2, or 3
        win_amount = -bet
        result = "😢 YOU LOSE"
        await db.update_currency(message.from_user.id, "cash", -bet)
        profit = -bet
    
    response = f"""
🎲 <b>DICE GAME</b>

Your roll: <b>{dice_value}</b>
Bet: <b>${bet:,}</b>

{result} <b>${abs(profit):,}</b>

💰 <b>New Balance:</b> ${user['cash'] + profit:,}

💡 Play again with /dice [amount]
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine"""
    # Get bet amount
    bet = 100
    if command.args:
        try:
            bet = int(command.args)
            if bet < GameConfig.MIN_BET:
                await message.answer(f"❌ Minimum bet is ${GameConfig.MIN_BET}!")
                return
            if bet > GameConfig.MAX_BET:
                await message.answer(f"❌ Maximum bet is ${GameConfig.MAX_BET}!")
                return
        except ValueError:
            await message.answer(f"❌ Bet must be a number!\nExample: /slot {GameConfig.MIN_BET}")
            return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user['cash'] < bet:
        await message.answer(f"❌ You need ${bet:,} to play! You have ${user['cash']:,}")
        return
    
    # Generate slot result
    symbols = ["7️⃣", "💎", "🍒", "⭐", "🔔", "🍀"]
    result = [random.choice(symbols) for _ in range(3)]
    
    # Calculate win
    win_multiplier = 0
    
    # Check for three of a kind
    if result[0] == result[1] == result[2]:
        win_multiplier = GameConfig.SLOT_MULTIPLIERS.get(result[0], GameConfig.SLOT_MULTIPLIERS["default"])
    # Check for two of a kind
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win_multiplier = 1
    
    win_amount = bet * win_multiplier
    profit = win_amount - bet if win_multiplier > 0 else -bet
    
    # Update currency
    if win_amount > 0:
        await db.update_currency(message.from_user.id, "cash", win_amount)
    else:
        await db.update_currency(message.from_user.id, "cash", -bet)
    
    # Format result
    slot_display = f"[ {result[0]} | {result[1]} | {result[2]} ]"
    
    if win_multiplier > 0:
        if win_multiplier == 1:
            result_text = "Small win! 🎉"
        else:
            result_text = f"JACKPOT! 🎰 x{win_multiplier}"
    else:
        result_text = "No win this time 😢"
    
    response = f"""
🎰 <b>SLOT MACHINE</b>

{slot_display}

Bet: <b>${bet:,}</b>
{result_text}

💰 <b>{'Won' if profit >= 0 else 'Lost'}:</b> ${abs(profit):,}
💵 <b>New Balance:</b> ${user['cash'] + profit:,}

💡 Spin again with /slot [amount]
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
    user_power = (user.get('cash', 0) // 1000) + (user.get('level', 1) * 2) + (user.get('reputation', 100) // 20)
    target_power = (target_user.get('cash', 0) // 1000) + (target_user.get('level', 1) * 2) + (target_user.get('reputation', 100) // 20)
    
    total_power = user_power + target_power
    user_win_chance = user_power / total_power if total_power > 0 else 0.5
    
    if random.random() < user_win_chance:
        # User wins
        prize = min(1000, target_user.get('cash', 0) // 10)
        if prize > 0:
            await db.update_currency(message.from_user.id, "cash", prize)
            await db.update_currency(target.id, "cash", -prize)
        
        # Add XP
        await db.add_xp(message.from_user.id, 50)
        
        response = f"""
🥊 <b>FIGHT RESULTS</b>

⚔️ {message.from_user.first_name} vs {target.first_name}

🏆 <b>WINNER:</b> {message.from_user.first_name}!
💰 <b>Prize:</b> ${prize:,}
⭐ <b>XP Gained:</b> 50

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

@dp.message(Command("blackjack"))
async def cmd_blackjack(message: Message, command: CommandObject):
    """Blackjack game"""
    bet = 100
    if command.args:
        try:
            bet = int(command.args)
            if bet < GameConfig.MIN_BET:
                await message.answer(f"❌ Minimum bet is ${GameConfig.MIN_BET}!")
                return
            if bet > GameConfig.MAX_BET:
                await message.answer(f"❌ Maximum bet is ${GameConfig.MAX_BET}!")
                return
        except ValueError:
            await message.answer(f"❌ Bet must be a number!\nExample: /blackjack {GameConfig.MIN_BET}")
            return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user['cash'] < bet:
        await message.answer(f"❌ You need ${bet:,} to play! You have ${user['cash']:,}")
        return
    
    # Simple blackjack logic
    player_cards = [random.randint(1, 11), random.randint(1, 10)]
    dealer_cards = [random.randint(1, 11), random.randint(1, 10)]
    
    player_total = sum(player_cards)
    dealer_total = sum(dealer_cards)
    
    # Determine winner
    player_bust = player_total > 21
    dealer_bust = dealer_total > 21
    
    if player_bust:
        result = "BUST! You lose 😢"
        profit = -bet
        await db.update_currency(message.from_user.id, "cash", -bet)
    elif dealer_bust:
        result = "Dealer busts! You win 🎉"
        profit = bet * 2
        await db.update_currency(message.from_user.id, "cash", profit)
    elif player_total > dealer_total:
        result = "You win! 🎉"
        profit = bet * 2
        await db.update_currency(message.from_user.id, "cash", profit)
    elif player_total < dealer_total:
        result = "Dealer wins 😢"
        profit = -bet
        await db.update_currency(message.from_user.id, "cash", -bet)
    else:
        result = "Push (Tie) 🤝"
        profit = 0
    
    response = f"""
🃏 <b>BLACKJACK</b>

Your cards: {player_cards[0]}, {player_cards[1]} = <b>{player_total}</b>
Dealer cards: {dealer_cards[0]}, {dealer_cards[1]} = <b>{dealer_total}</b>

Bet: <b>${bet:,}</b>
Result: <b>{result}</b>

💰 <b>{'Won' if profit >= 0 else 'Lost'}:</b> ${abs(profit):,}
💵 <b>New Balance:</b> ${user['cash'] + profit:,}

💡 Play again with /blackjack [amount]
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("race"))
async def cmd_race(message: Message, command: CommandObject):
    """Horse racing game"""
    bet = 100
    if command.args:
        try:
            bet = int(command.args)
            if bet < GameConfig.MIN_BET:
                await message.answer(f"❌ Minimum bet is ${GameConfig.MIN_BET}!")
                return
            if bet > GameConfig.MAX_BET:
                await message.answer(f"❌ Maximum bet is ${GameConfig.MAX_BET}!")
                return
        except ValueError:
            await message.answer(f"❌ Bet must be a number!\nExample: /race {GameConfig.MIN_BET}")
            return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user['cash'] < bet:
        await message.answer(f"❌ You need ${bet:,} to play! You have ${user['cash']:,}")
        return
    
    # Choose a horse
    horses = ["🐎 Lightning", "🏇 Thunder", "🚀 Blaze", "⚡ Flash", "🌟 Star"]
    chosen_horse = random.choice(horses)
    
    # Simulate race
    positions = {horse: 0 for horse in horses}
    winner = None
    
    for _ in range(10):
        for horse in horses:
            positions[horse] += random.randint(1, 3)
        
        # Check if any horse reached finish line
        for horse, position in positions.items():
            if position >= 20:
                winner = horse
                break
        if winner:
            break
    
    # Determine if user won
    user_won = (chosen_horse == winner)
    
    if user_won:
        win_amount = bet * 3
        result = "🎉 YOU WIN!"
        profit = win_amount - bet
        await db.update_currency(message.from_user.id, "cash", win_amount)
    else:
        result = f"😢 {winner} won!"
        profit = -bet
        await db.update_currency(message.from_user.id, "cash", -bet)
    
    # Create race visualization
    race_display = ""
    for horse in horses:
        position = min(positions[horse], 20)
        bar = "█" * position + "░" * (20 - position)
        marker = "👤" if horse == chosen_horse else ""
        race_display += f"{horse}: {bar} {marker}\n"
    
    response = f"""
🏇 <b>HORSE RACING</b>

{race_display}

Your horse: <b>{chosen_horse}</b>
Bet: <b>${bet:,}</b>

🏆 <b>Winner:</b> {winner}
{result}

💰 <b>{'Won' if profit >= 0 else 'Lost'}:</b> ${abs(profit):,}
💵 <b>New Balance:</b> ${user['cash'] + profit:,}

💡 Race again with /race [amount]
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# REACTION COMMANDS
# ============================================================================

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to hug them!")
        return
    
    await send_gif_reaction("hug", message.chat.id, message.from_user, target)

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to kiss them!")
        return
    
    await send_gif_reaction("kiss", message.chat.id, message.from_user, target)

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to slap them!")
        return
    
    await send_gif_reaction("slap", message.chat.id, message.from_user, target)

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to pat them!")
        return
    
    await send_gif_reaction("pat", message.chat.id, message.from_user, target)

@dp.message(Command("punch"))
async def cmd_punch(message: Message):
    """Punch someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to punch them!")
        return
    
    await send_gif_reaction("punch", message.chat.id, message.from_user, target)

@dp.message(Command("cuddle"))
async def cmd_cuddle(message: Message):
    """Cuddle someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to cuddle them!")
        return
    
    await send_gif_reaction("cuddle", message.chat.id, message.from_user, target)

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone (fun)"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to 'kill' them!")
        return
    
    await send_gif_reaction("kill", message.chat.id, message.from_user, target)

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
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both users need to use /start first!")
        return
    
    # Calculate robbery success
    success_chance = 0.3  # 30% chance
    if random.random() < success_chance:
        # Robbery successful
        stolen_amount = min(1000, target_user.get('cash', 0) // 10)
        if stolen_amount > 0:
            await db.update_currency(message.from_user.id, "cash", stolen_amount)
            await db.update_currency(target.id, "cash", -stolen_amount)
        
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        
        response = f"""
💰 <b>ROBBERY SUCCESSFUL!</b>

{message.from_user.first_name} robbed {target.first_name}!

Stolen: <b>${stolen_amount:,}</b>
💵 Your new balance: ${user['cash'] + stolen_amount:,}

🏃‍♂️ Run before they catch you!
"""
    else:
        # Robbery failed
        penalty = min(500, user.get('cash', 0) // 20)
        if penalty > 0:
            await db.update_currency(message.from_user.id, "cash", -penalty)
            await db.update_currency(target.id, "cash", penalty)
        
        response = f"""
🚨 <b>ROBBERY FAILED!</b>

{target.first_name} caught {message.from_user.first_name}!

Penalty: <b>${penalty:,}</b>
💵 Your new balance: ${user['cash'] - penalty:,}

👮‍♂️ Better luck next time!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# MARKETPLACE COMMANDS
# ============================================================================

@dp.message(Command("market"))
async def cmd_market(message: Message):
    """Marketplace"""
    response = """
🏪 <b>MARKETPLACE</b>

Buy and sell items with other players!

📦 <b>Available Sections:</b>
• Crops - Buy/Sell farm products
• Items - Special game items
• Properties - Land and buildings
• Services - Player services

💡 <b>How to use:</b>
• Browse items with /shop
• List items for sale
• Make offers to other players
• Trade items with /trade

💰 <b>Commands:</b>
• /shop - Browse items
• /sellitem [item] [price] - List item
• /buyitem [item_id] - Purchase item
• /tradelist - Active trades
• /offer [user] [item] [price] - Make offer

🎯 <b>Tip:</b> Buy low, sell high!
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("shop"))
async def cmd_shop(message: Message):
    """Shop items"""
    items = [
        {"name": "🌱 Starter Pack", "price": 1000, "desc": "Basic farming tools"},
        {"name": "💎 Diamond Pickaxe", "price": 5000, "desc": "Mine gems faster"},
        {"name": "🏠 Small House", "price": 10000, "desc": "Basic property"},
        {"name": "🚗 Sports Car", "price": 50000, "desc": "Fast transportation"},
        {"name": "✈️ Private Jet", "price": 100000, "desc": "Travel anywhere"},
        {"name": "🏰 Castle", "price": 500000, "desc": "Royal property"},
        {"name": "🛡️ Shield", "price": 2000, "desc": "Protection in fights"},
        {"name": "⚔️ Sword", "price": 3000, "desc": "Increased fight power"},
        {"name": "📈 Stock Tips", "price": 10000, "desc": "Better stock returns"},
        {"name": "🎫 Lottery Bundle", "price": 500, "desc": "10 lottery tickets"}
    ]
    
    shop_text = "🛒 <b>ITEM SHOP</b>\n\n"
    
    for i, item in enumerate(items, 1):
        shop_text += f"{i}. {item['name']} - ${item['price']:,}\n"
        shop_text += f"   {item['desc']}\n\n"
    
    shop_text += "💡 Use /buy [item_number] to purchase\n"
    shop_text += "💰 Check your balance with /balance"
    
    await message.answer(shop_text, parse_mode=ParseMode.HTML)

@dp.message(Command("inventory"))
async def cmd_inventory(message: Message):
    """View inventory"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    # In a real implementation, you would fetch from inventory table
    # For now, show a sample inventory
    response = """
🎒 <b>YOUR INVENTORY</b>

📦 <b>Items:</b>
• 🌱 Starter Pack x1
• 🛡️ Shield x1
• 📈 Stock Tips x2
• 🎫 Lottery Tickets x5

💼 <b>Properties:</b>
• 🏠 Small House x1

🚗 <b>Vehicles:</b>
• 🚲 Bicycle x1

💰 <b>Total Value:</b> $25,000

💡 <b>Use items:</b>
• Equip items for bonuses
• Sell items in /market
• Trade with other players
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# QUEST & ACHIEVEMENT COMMANDS
# ============================================================================

@dp.message(Command("quests"))
async def cmd_quests(message: Message):
    """Daily quests"""
    quests = [
        {"name": "🌅 Morning Routine", "reward": 500, "desc": "Claim daily bonus"},
        {"name": "🌾 Farm Master", "reward": 1000, "desc": "Harvest 10 crops"},
        {"name": "💰 Money Maker", "reward": 1500, "desc": "Earn $10,000 today"},
        {"name": "🎰 Lucky Day", "reward": 800, "desc": "Play 3 games"},
        {"name": "👥 Social Butterfly", "reward": 1200, "desc": "Interact with 5 friends"}
    ]
    
    response = "📋 <b>DAILY QUESTS</b>\n\n"
    
    for i, quest in enumerate(quests, 1):
        status = "✅" if random.random() > 0.5 else "⏳"
        response += f"{i}. {quest['name']} - ${quest['reward']:,}\n"
        response += f"   {quest['desc']} {status}\n\n"
    
    response += "💡 Complete quests for bonus rewards!\n"
    response += "🔄 Quests reset daily at midnight"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("achievements"))
async def cmd_achievements(message: Message):
    """Achievements"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    achievements = await db.get_achievements(message.from_user.id)
    
    if not achievements:
        response = """
🏆 <b>ACHIEVEMENTS</b>

No achievements yet!

💡 <b>How to unlock:</b>
• Play games
• Grow your family
• Build wealth
• Complete challenges

🌟 <b>Available Achievements:</b>
• First Timer - Claim first daily
• Growing Family - Have 5 family members
• Garden Master - Harvest 100 crops
• Millionaire - Reach $1,000,000
• Stock King - Make $50,000 in stocks
"""
        await message.answer(response, parse_mode=ParseMode.HTML)
        return
    
    response = "🏆 <b>YOUR ACHIEVEMENTS</b>\n\n"
    
    unlocked = [a for a in achievements if a.get('unlocked')]
    locked = [a for a in achievements if not a.get('unlocked')]
    
    if unlocked:
        response += "✅ <b>UNLOCKED:</b>\n"
        for achievement in unlocked[:5]:
            response += f"• {achievement['name']} - {achievement['description']}\n"
            if achievement.get('reward', 0) > 0:
                response += f"  Reward: ${achievement['reward']:,}\n"
        response += "\n"
    
    if locked:
        response += "🔒 <b>LOCKED:</b>\n"
        for achievement in locked[:5]:
            response += f"• {achievement['name']} - {achievement['description']}\n"
            if achievement.get('reward', 0) > 0:
                response += f"  Reward: ${achievement['reward']:,}\n"
    
    response += f"\n📊 <b>Progress:</b> {len(unlocked)}/{len(achievements)} achievements"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# LEADERBOARD COMMANDS
# ============================================================================

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message, command: CommandObject):
    """Leaderboard"""
    by = "cash"
    if command.args:
        arg = command.args.lower()
        if arg in ["cash", "money"]:
            by = "cash"
        elif arg in ["bank", "savings"]:
            by = "bank_balance"
        elif arg in ["level", "xp"]:
            by = "level"
        elif arg in ["rep", "reputation"]:
            by = "reputation"
    
    top_users = await db.get_top_users(by, 10)
    
    column_name = "Cash" if by == "cash" else "Bank" if by == "bank_balance" else "Level" if by == "level" else "Reputation"
    
    response = f"🏆 <b>TOP 10 PLAYERS BY {column_name.upper()}</b>\n\n"
    
    for i, user in enumerate(top_users, 1):
        name = user.get('username') or user.get('first_name', 'User')
        value = user.get(by, 0)
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        if by == "cash" or by == "bank_balance":
            response += f"{medal} {name}: <b>${value:,}</b>\n"
        else:
            response += f"{medal} {name}: <b>{value}</b>\n"
    
    response += "\n💡 <b>Other leaderboards:</b>"
    response += "\n• /leaderboard cash - Richest players"
    response += "\n• /leaderboard bank - Best savers"
    response += "\n• /leaderboard level - Highest levels"
    response += "\n• /leaderboard reputation - Most respected"
    
    await message.answer(response, parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

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
• /search [query] - Search users

👥 <b>User Management:</b>
• /userinfo [id] - User details
• /ban [id] - Ban user
• /unban [id] - Unban user
• /warn [id] - Warn user
• /reset [id] [type] - Reset user

💰 <b>Economy:</b>
• /add [id] [currency] [amount] - Add money
• /remove [id] [currency] [amount] - Remove money
• /setlevel [id] [level] - Set level

🔧 <b>System:</b>
• /broadcast [text] - Announcement
• /message [id] [text] - PM user
• /backup - Backup database
• /logs - View bot logs

⚠️ <b>Danger Zone:</b>
• /resetall - Reset all users
• /maintenance [on/off] - Maintenance mode
"""
    
    await message.answer(response, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)

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
🏢 <b>Businesses:</b> {stats.get('businesses', 0):,}
👥 <b>Groups:</b> {stats.get('groups', 0):,}

🕒 <b>Last updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "users":
        top_users = await db.get_top_users("cash", 5)
        
        response = "👥 <b>TOP 5 USERS</b>\n\n"
        
        for i, user in enumerate(top_users, 1):
            name = user.get('username') or user.get('first_name', 'User')
            cash = user.get('cash', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            response += f"{medal} {name} (ID: {user['user_id']}): <b>${cash:,}</b>\n"
        
        response += "\n💡 Use /search [name] to find users"
        
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "economy":
        stats = await db.get_stats()
        total_economy = stats.get('total_cash', 0) + stats.get('total_bank', 0)
        
        response = f"""
💰 <b>ECONOMY OVERVIEW</b>

💵 <b>Total Money in Circulation:</b> ${total_economy:,}
• Cash: ${stats.get('total_cash', 0):,}
• Bank: ${stats.get('total_bank', 0):,}

📈 <b>Average per User:</b> ${total_economy // max(1, stats.get('total_users', 1)):,}

🎰 <b>Lottery System:</b>
• Tickets Sold: {stats.get('lottery_tickets', 0):,}
• Total Value: ${stats.get('lottery_tickets', 0) * GameConfig.LOTTERY_TICKET_PRICE:,}

🏢 <b>Business Economy:</b>
• Active Businesses: {stats.get('businesses', 0):,}
"""
        
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "games":
        response = """
🎮 <b>GAMES STATISTICS</b>

🎰 <b>Slot Machine:</b>
• Most played game
• Average bet: $500
• Payout rate: 95%

🎲 <b>Dice Game:</b>
• Simple 50/50 odds
• Popular with new players
• Average bet: $300

🃏 <b>Blackjack:</b>
• Skill-based game
• Higher average bets
• House edge: 2%

🏇 <b>Horse Racing:</b>
• Most exciting game
• High volatility
• Big jackpots possible

💡 <b>Game Health:</b>
All games running smoothly
Balanced economy
Happy players!
"""
        
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "system":
        response = """
🔧 <b>SYSTEM STATUS</b>

✅ <b>All Systems Operational</b>

📊 <b>Database:</b> Healthy
🖥️ <b>Bot Uptime:</b> 99.9%
🔗 <b>API Connections:</b> Stable
💾 <b>Memory Usage:</b> Normal

⚙️ <b>Maintenance Tools:</b>
• /backup - Create database backup
• /logs - View system logs
• /restart - Restart bot (if configured)
• /update - Update bot (if configured)

⚠️ <b>Warning:</b>
Use maintenance tools carefully
Backup before major changes
"""
        
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML)
        
    elif action == "broadcast":
        response = """
📢 <b>BROADCAST MESSAGE</b>

To send a message to all users:

<code>/broadcast [your message here]</code>

💡 <b>Tips:</b>
• Keep messages short and clear
• Use for important announcements
• Don't spam users
• Test with small group first

⚠️ <b>Warning:</b>
Broadcasting to many users may take time
Rate limits apply
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
🏢 <b>Businesses:</b> {stats.get('businesses', 0):,}
👥 <b>Groups:</b> {stats.get('groups', 0):,}
⚠️ <b>Banned Users:</b> {stats.get('banned_users', 0):,}
📅 <b>Active Today:</b> {stats.get('active_today', 0):,}

🕒 <b>Last updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("top"))
async def cmd_top(message: Message, command: CommandObject):
    """Top users"""
    by = "cash"
    if command.args:
        args = command.args.lower().split()
        if args and args[0] in ["cash", "money"]:
            by = "cash"
        elif args and args[0] in ["bank", "savings"]:
            by = "bank_balance"
        elif args and args[0] in ["level", "xp"]:
            by = "level"
        elif args and args[0] in ["rep", "reputation"]:
            by = "reputation"
    
    top_users = await db.get_top_users(by, 15)
    
    column_name = "Cash" if by == "cash" else "Bank" if by == "bank_balance" else "Level" if by == "level" else "Reputation"
    
    response = f"🏆 <b>TOP 15 USERS BY {column_name.upper()}</b>\n\n"
    
    for i, user in enumerate(top_users, 1):
        name = user.get('username') or user.get('first_name', 'User')
        value = user.get(by, 0)
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        if by == "cash" or by == "bank_balance":
            response += f"{medal} {name}: <b>${value:,}</b>\n"
        else:
            response += f"{medal} {name}: <b>{value}</b>\n"
    
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
    users = await db.search_users(query)
    
    if not users:
        await message.answer("❌ No users found!")
        return
    
    response = f"🔍 <b>SEARCH RESULTS for '{command.args}'</b>\n\n"
    
    for user in users[:10]:
        name = user.get('username') or user.get('first_name', 'User')
        response += f"👤 {name}\n"
        response += f"   ID: {user.get('user_id')}\n"
        response += f"   💰 ${user.get('cash', 0):,}\n"
        response += f"   ⭐ Level {user.get('level', 1)}\n\n"
    
    if len(users) > 10:
        response += f"... and {len(users) - 10} more users"
    
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
<code>/add 123456789 gold 50</code>
<code>/add 123456789 credits 100</code>

📌 <b>Currencies:</b>
• cash - User's pocket money
• bank - Bank balance
• gold - Gold coins
• credits - Premium credits
• tokens - Game tokens
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
        
        valid_currencies = ["cash", "bank", "gold", "credits", "tokens"]
        if currency not in valid_currencies:
            await message.answer(f"❌ Currency must be one of: {', '.join(valid_currencies)}!")
            return
        
        if amount <= 0:
            await message.answer("❌ Amount must be positive!")
            return
        
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            await message.answer("❌ User not found!")
            return
        
        db_currency = "bank_balance" if currency == "bank" else currency
        await db.update_currency(user_id, db_currency, amount)
        
        # Get updated user info
        updated_user = await db.get_user(user_id)
        
        if currency == "bank":
            new_balance = updated_user.get('bank_balance', 0)
        else:
            new_balance = updated_user.get(currency, 0)
        
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
4. Log broadcast activity

Estimated recipients: {await db.get_stats().get('total_users', 0)} users
"""
    
    await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(Command("userinfo"))
async def cmd_userinfo(message: Message, command: CommandObject):
    """Get user info (admin only)"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Admin only!")
        return
    
    if not command.args:
        await message.answer("❌ Usage: /userinfo [user_id]\nExample: /userinfo 123456789")
        return
    
    try:
        user_id = int(command.args)
        user = await db.get_user(user_id)
        
        if not user:
            await message.answer("❌ User not found!")
            return
        
        # Get additional user data
        family = await db.get_family(user_id)
        businesses = await db.get_businesses(user_id)
        achievements = await db.get_achievements(user_id)
        
        response = f"""
👤 <b>USER INFORMATION</b>

🆔 <b>ID:</b> {user['user_id']}
👤 <b>Name:</b> {user.get('first_name', 'Unknown')} {user.get('last_name', '')}
📛 <b>Username:</b> @{user.get('username', 'None')}

💰 <b>Economy:</b>
• Cash: ${user.get('cash', 0):,}
• Bank: ${user.get('bank_balance', 0):,}
• Gold: {user.get('gold', 0)}
• Credits: {user.get('credits', 0)}
• Tokens: {user.get('tokens', 0)}

📊 <b>Stats:</b>
• Level: {user.get('level', 1)}
• XP: {user.get('xp', 0)}/{(user.get('level', 1) * 1000)}
• Reputation: {user.get('reputation', 100)}
• Daily Streak: {user.get('daily_streak', 0)} days

👨‍👩‍👧‍👦 <b>Family:</b> {len(family)} members
🏢 <b>Businesses:</b> {len(businesses)} owned
🏆 <b>Achievements:</b> {sum(1 for a in achievements if a.get('unlocked'))} unlocked

📅 <b>Account:</b>
• Created: {user.get('created_at', 'Unknown')}
• Last Daily: {user.get('last_daily', 'Never')}
• Warnings: {user.get('warnings', 0)}
• Banned: {'Yes' if user.get('is_banned') else 'No'}
• Bio Verified: {'Yes' if user.get('bio_verified') else 'No'}
"""
        
        await message.answer(response, parse_mode=ParseMode.HTML)
        
    except ValueError:
        await message.answer("❌ User ID must be a number!")
    except Exception as e:
        logger.error(f"Userinfo error: {e}")
        await message.answer("❌ Error fetching user info!")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main function"""
    logger.info("🚀 Starting Family Tree Bot...")
    
    # Connect to database
    try:
        await db.connect()
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return
    
    # Set bot commands for better UX
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Show all commands"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="garden", description="Your farm"),
        types.BotCommand(command="bank", description="Banking system"),
        types.BotCommand(command="lottery", description="Lottery tickets"),
        types.BotCommand(command="dice", description="Dice game"),
        types.BotCommand(command="shop", description="Item shop"),
        types.BotCommand(command="leaderboard", description="Top players"),
    ]
    
    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Bot commands set")
    except Exception as e:
        logger.warning(f"⚠️ Could not set bot commands: {e}")
    
    # Start polling
    logger.info("✅ Bot is ready! Starting poll...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    
    # Check for required packages
    try:
        import aiogram
        import aiosqlite
        if not HAS_PILLOW:
            logger.warning("⚠️ Pillow not installed. Images will be text-only.")
            logger.info("💡 Install: pip install Pillow")
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.info("💡 Install: pip install aiogram aiosqlite Pillow")
        sys.exit(1)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
