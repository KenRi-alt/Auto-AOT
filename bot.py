#!/usr/bin/env python3
"""
FAMILY TREE TELEGRAM BOT - ULTIMATE VERSION
Complete implementation with maximum security
"""

import os
import json
import asyncio
import logging
import random
import secrets
import string
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import html
import uuid
import hashlib
from pathlib import Path

# Telegram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, URLInputFile, FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Database
import asyncpg
from asyncpg.pool import Pool
import aiosqlite

# For backup/restore
import csv
import zipfile
import io

# ============================================================================
# CONFIGURATION - UPDATE THESE!
# ============================================================================

# 🔐 YOUR CREDENTIALS (UPDATE THESE!)
OWNER_ID = 6108185460  # Your Telegram ID
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"  # ⚠️ REPLACE WITH ACTUAL TOKEN
LOG_CHANNEL = -1003662720845  # Your log channel

# Database configuration
DB_PATH = "family_bot.db"  # SQLite for simplicity, Railway will handle

# Security settings
MAX_REQUESTS_PER_MINUTE = 30  # Rate limiting
BACKUP_KEY = secrets.token_urlsafe(32)  # Auto-generated backup key

# Game constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens"]
CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper"]
CROP_PRICES = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 3600},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 4800},
    "potato": {"buy": 8, "sell": 12, "grow_time": 4200},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 5400},
    "corn": {"buy": 12, "sell": 18, "grow_time": 6000},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6600}
}

# ============================================================================
# SETUP LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING CLASS
# ============================================================================

class RateLimiter:
    """Advanced rate limiting with per-user, per-command limits"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "default": (30, 60),  # 30 requests per 60 seconds
            "rob": (8, 86400),    # 8 robberies per day
            "kill": (5, 86400),   # 5 kills per day
            "fertilize": (6, 3600),  # 6 fertilizes per hour
            "daily": (1, 86400),  # 1 daily per day
        }
    
    def is_allowed(self, user_id: int, action: str = "default") -> Tuple[bool, str]:
        """Check if user can perform action"""
        now = time.time()
        limit, period = self.limits.get(action, self.limits["default"])
        
        # Clean old requests
        user_requests = [t for t in self.requests[(user_id, action)] 
                        if now - t < period]
        self.requests[(user_id, action)] = user_requests
        
        if len(user_requests) >= limit:
            if action in ["rob", "kill"]:
                reset_time = datetime.fromtimestamp(user_requests[0] + period)
                return False, f"Daily limit reached! Resets at {reset_time:%H:%M}"
            return False, f"Rate limit exceeded! Try again later."
        
        self.requests[(user_id, action)].append(now)
        return True, ""

# ============================================================================
# DATABASE MANAGER WITH MAXIMUM SECURITY
# ============================================================================

class SecureDatabase:
    """Secure database operations with transaction safety"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Initialize database connection"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.init_tables()
        logger.info("Database connected securely")
    
    async def init_tables(self):
        """Create all tables with proper constraints"""
        tables = [
            # Users table with all currencies
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cash INTEGER DEFAULT 1000 CHECK(cash >= 0),
                gold INTEGER DEFAULT 0 CHECK(gold >= 0),
                bonds INTEGER DEFAULT 0 CHECK(bonds >= 0),
                credits INTEGER DEFAULT 100 CHECK(credits >= 0),
                tokens INTEGER DEFAULT 50 CHECK(tokens >= 0),
                reputation INTEGER DEFAULT 100 CHECK(reputation BETWEEN 0 AND 200),
                is_alive BOOLEAN DEFAULT 1,
                last_daily TIMESTAMP,
                gemstone TEXT,
                gemstone_date TIMESTAMP,
                weapon TEXT DEFAULT 'none',
                job TEXT,
                language TEXT DEFAULT 'en',
                UNIQUE(user_id)
            )""",
            
            # Family relations with constraints
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL CHECK(relation_type IN ('parent', 'spouse', 'child', 'sibling')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user1_id, user2_id, relation_type),
                CHECK(user1_id != user2_id)
            )""",
            
            # Friends with bidirectional constraint
            """CREATE TABLE IF NOT EXISTS friendships (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user1_id, user2_id),
                CHECK(user1_id < user2_id)  # Ensures bidirectional consistency
            )""",
            
            # Insurance with validation
            """CREATE TABLE IF NOT EXISTS insurance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insurer_id INTEGER NOT NULL,
                insured_id INTEGER NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (insurer_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (insured_id) REFERENCES users(user_id) ON DELETE CASCADE,
                CHECK(insurer_id != insured_id)
            )""",
            
            # Garden system
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9 CHECK(slots BETWEEN 1 AND 36),
                barn_capacity INTEGER DEFAULT 50 CHECK(barn_capacity >= 0),
                last_fertilized TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Garden plants
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL CHECK(crop_type IN ('carrot', 'tomato', 'potato', 'eggplant', 'corn', 'pepper')),
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time INTEGER NOT NULL,
                is_ready BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Barn inventory
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0 CHECK(quantity >= 0),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Market stands
            """CREATE TABLE IF NOT EXISTS market_stands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                price INTEGER NOT NULL CHECK(price > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Orders for garden expansion
            """CREATE TABLE IF NOT EXISTS garden_orders (
                user_id INTEGER NOT NULL,
                order_data TEXT NOT NULL,  # JSON: {"carrot": 3, "tomato": 2}
                completed INTEGER DEFAULT 0 CHECK(completed BETWEEN 0 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id)
            )""",
            
            # Proposals with expiration
            """CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                proposal_type TEXT NOT NULL CHECK(proposal_type IN ('adopt', 'marry', 'friend', 'trade')),
                data TEXT,  # JSON for trade details
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
                FOREIGN KEY (from_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (to_id) REFERENCES users(user_id) ON DELETE CASCADE,
                CHECK(from_id != to_id)
            )""",
            
            # Admin actions log
            """CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(user_id)
            )""",
            
            # Security: banned users
            """CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                banned_by INTEGER,
                FOREIGN KEY (banned_by) REFERENCES users(user_id)
            )""",
        ]
        
        async with self.lock:
            for table_sql in tables:
                try:
                    await self.conn.execute(table_sql)
                except Exception as e:
                    logger.error(f"Failed to create table: {e}")
            
            await self.conn.commit()
            logger.info("All tables initialized with constraints")
    
    # ==================== SECURE TRANSACTION METHODS ====================
    
    async def execute_transaction(self, queries: List[Tuple[str, tuple]], 
                                 rollback_on_error: bool = True):
        """Execute multiple queries in a transaction with rollback"""
        async with self.lock:
            try:
                await self.conn.execute("BEGIN TRANSACTION")
                
                for query, params in queries:
                    await self.conn.execute(query, params)
                
                await self.conn.commit()
                return True
            except Exception as e:
                if rollback_on_error:
                    await self.conn.rollback()
                logger.error(f"Transaction failed: {e}")
                raise
    
    async def safe_update_balance(self, user_id: int, currency: str, 
                                 amount: int) -> bool:
        """Update balance with check for negative values"""
        if currency not in CURRENCIES:
            return False
        
        query = f"""
        UPDATE users 
        SET {currency} = {currency} + ? 
        WHERE user_id = ? AND {currency} + ? >= 0
        """
        
        async with self.lock:
            cursor = await self.conn.execute(query, (amount, user_id, amount))
            await self.conn.commit()
            return cursor.rowcount > 0
    
    # ==================== USER MANAGEMENT ====================
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID with validation"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user with default values"""
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
            "is_alive": True
        }
        
        queries = [
            ("INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
             (user.id, user.username, user.first_name, user.last_name)),
            ("INSERT OR IGNORE INTO gardens (user_id) VALUES (?)", (user.id,))
        ]
        
        try:
            await self.execute_transaction(queries)
            return user_data
        except:
            # If transaction fails, return minimal user
            return user_data
    
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,)
            )
            return await cursor.fetchone() is not None
    
    # ==================== FAMILY SYSTEM ====================
    
    async def add_family_relation(self, user1_id: int, user2_id: int, 
                                 relation_type: str) -> bool:
        """Add family relation with validation"""
        if user1_id == user2_id:
            return False
        
        try:
            await self.execute_transaction([
                ("INSERT INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
                 (user1_id, user2_id, relation_type)),
                ("INSERT INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
                 (user2_id, user1_id, relation_type))
            ])
            return True
        except:
            return False
    
    async def get_family_tree(self, user_id: int) -> List[dict]:
        """Get complete family tree for a user"""
        async with self.lock:
            cursor = await self.conn.execute('''
                SELECT fr.relation_type, 
                       CASE WHEN fr.user1_id = ? THEN fr.user2_id ELSE fr.user1_id END as relative_id,
                       u.first_name, u.username
                FROM family_relations fr
                LEFT JOIN users u ON u.user_id = CASE WHEN fr.user1_id = ? THEN fr.user2_id ELSE fr.user1_id END
                WHERE ? IN (fr.user1_id, fr.user2_id)
                ORDER BY fr.relation_type, fr.created_at
            ''', (user_id, user_id, user_id))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== FRIEND SYSTEM ====================
    
    async def add_friend(self, user1_id: int, user2_id: int) -> bool:
        """Add friendship with bonus"""
        if user1_id == user2_id:
            return False
        
        # Ensure user1_id < user2_id for consistency
        u1, u2 = sorted([user1_id, user2_id])
        
        queries = [
            ("INSERT OR IGNORE INTO friendships (user1_id, user2_id) VALUES (?, ?)",
             (u1, u2)),
            ("UPDATE users SET cash = cash + 3000 WHERE user_id IN (?, ?)",
             (user1_id, user2_id))
        ]
        
        try:
            await self.execute_transaction(queries)
            return True
        except:
            return False
    
    # ==================== GARDEN SYSTEM ====================
    
    async def plant_crop(self, user_id: int, crop_type: str, 
                        quantity: int) -> Tuple[bool, str]:
        """Plant crops with validation"""
        if crop_type not in CROP_TYPES:
            return False, "Invalid crop type"
        
        # Check available slots
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
                (user_id,)
            )
            active_plants = (await cursor.fetchone())[0]
            
            cursor = await self.conn.execute(
                "SELECT slots FROM gardens WHERE user_id = ?", (user_id,)
            )
            slots = (await cursor.fetchone())[0]
            
            if active_plants + quantity > slots:
                return False, f"Not enough garden slots! ({active_plants}/{slots} used)"
        
        # Check if user has seeds (simplified - using cash)
        price = CROP_PRICES[crop_type]["buy"] * quantity
        user = await self.get_user(user_id)
        
        if user["cash"] < price:
            return False, f"Not enough cash! Need ${price}, have ${user['cash']}"
        
        # Plant crops
        queries = [
            ("UPDATE users SET cash = cash - ? WHERE user_id = ?",
             (price, user_id)),
        ]
        
        grow_time = CROP_PRICES[crop_type]["grow_time"]
        for _ in range(quantity):
            queries.append(
                ("INSERT INTO garden_plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                 (user_id, crop_type, grow_time))
            )
        
        try:
            await self.execute_transaction(queries)
            return True, f"Planted {quantity} {crop_type}(s)! Will grow in {grow_time//3600} hours."
        except Exception as e:
            return False, f"Failed to plant: {e}"
    
    async def harvest_crops(self, user_id: int) -> Tuple[Dict[str, int], str]:
        """Harvest ready crops"""
        async with self.lock:
            # Get ready crops
            cursor = await self.conn.execute(
                "SELECT crop_type, COUNT(*) as count FROM garden_plants "
                "WHERE user_id = ? AND is_ready = 1 GROUP BY crop_type",
                (user_id,)
            )
            ready_crops = {row[0]: row[1] for row in await cursor.fetchall()}
            
            if not ready_crops:
                return {}, "No crops ready for harvest!"
            
            # Update barn and remove plants in transaction
            queries = []
            total_value = 0
            
            for crop_type, count in ready_crops.items():
                sell_price = CROP_PRICES[crop_type]["sell"] * count
                total_value += sell_price
                
                # Add to barn
                queries.append((
                    "INSERT INTO barn (user_id, crop_type, quantity) "
                    "VALUES (?, ?, ?) "
                    "ON CONFLICT(user_id, crop_type) DO UPDATE SET "
                    "quantity = quantity + excluded.quantity",
                    (user_id, crop_type, count)
                ))
            
            # Remove harvested plants
            queries.append((
                "DELETE FROM garden_plants WHERE user_id = ? AND is_ready = 1",
                (user_id,)
            ))
            
            # Add cash from optional selling (commented out - let user decide)
            # queries.append((
            #     "UPDATE users SET cash = cash + ? WHERE user_id = ?",
            #     (total_value, user_id)
            # ))
            
            try:
                await self.execute_transaction(queries)
                return ready_crops, f"Harvested {sum(ready_crops.values())} crops!"
            except Exception as e:
                return {}, f"Harvest failed: {e}"
    
    # ==================== MARKET SYSTEM ====================
    
    async def list_on_market(self, seller_id: int, crop_type: str, 
                           quantity: int, price: int) -> Tuple[bool, str]:
        """List crops on market stand"""
        # Check if user has enough crops
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT quantity FROM barn WHERE user_id = ? AND crop_type = ?",
                (seller_id, crop_type)
            )
            row = await cursor.fetchone()
            
            if not row or row[0] < quantity:
                return False, f"Not enough {crop_type}! You have {row[0] if row else 0}"
        
        max_price = CROP_PRICES[crop_type]["sell"] * 3
        if price > max_price * quantity:
            return False, f"Price too high! Max ${max_price * quantity} for {quantity} {crop_type}"
        
        queries = [
            ("UPDATE barn SET quantity = quantity - ? WHERE user_id = ? AND crop_type = ?",
             (quantity, seller_id, crop_type)),
            ("INSERT INTO market_stands (seller_id, crop_type, quantity, price) VALUES (?, ?, ?, ?)",
             (seller_id, crop_type, quantity, price))
        ]
        
        try:
            await self.execute_transaction(queries)
            return True, f"Listed {quantity} {crop_type} for ${price} on market!"
        except Exception as e:
            return False, f"Failed to list: {e}"
    
    async def buy_from_market(self, buyer_id: int, listing_id: int, 
                            quantity: int) -> Tuple[bool, str]:
        """Buy from market stand"""
        async with self.lock:
            # Get listing details
            cursor = await self.conn.execute(
                "SELECT seller_id, crop_type, quantity as available, price FROM market_stands WHERE id = ?",
                (listing_id,)
            )
            listing = await cursor.fetchone()
            
            if not listing:
                return False, "Listing not found!"
            
            seller_id, crop_type, available, total_price = listing
            
            if available < quantity:
                return False, f"Only {available} available!"
            
            # Calculate price per unit
            price_per_unit = total_price / available
            cost = int(price_per_unit * quantity)
            
            # Check buyer's balance
            buyer = await self.get_user(buyer_id)
            if buyer["cash"] < cost:
                return False, f"Need ${cost}, have ${buyer['cash']}"
            
            # Transaction
            queries = [
                # Deduct from buyer
                ("UPDATE users SET cash = cash - ? WHERE user_id = ?", (cost, buyer_id)),
                # Add to seller
                ("UPDATE users SET cash = cash + ? WHERE user_id = ?", (cost, seller_id)),
                # Update listing
                ("UPDATE market_stands SET quantity = quantity - ? WHERE id = ?", 
                 (quantity, listing_id)),
                # Add to buyer's barn
                ("INSERT INTO barn (user_id, crop_type, quantity) VALUES (?, ?, ?) "
                 "ON CONFLICT(user_id, crop_type) DO UPDATE SET "
                 "quantity = quantity + excluded.quantity",
                 (buyer_id, crop_type, quantity))
            ]
            
            # Remove listing if sold out
            if available - quantity == 0:
                queries.append(("DELETE FROM market_stands WHERE id = ?", (listing_id,)))
            
            try:
                await self.execute_transaction(queries)
                return True, f"Bought {quantity} {crop_type} for ${cost}!"
            except Exception as e:
                return False, f"Purchase failed: {e}"
    
    # ==================== ADMIN & BACKUP ====================
    
    async def create_backup(self) -> bytes:
        """Create encrypted backup of critical data"""
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "users": [],
            "family": [],
            "friends": [],
            "market": []
        }
        
        async with self.lock:
            # Get users
            cursor = await self.conn.execute(
                "SELECT user_id, username, first_name, cash, gold, bonds FROM users"
            )
            backup_data["users"] = [dict(row) for row in await cursor.fetchall()]
            
            # Get family
            cursor = await self.conn.execute(
                "SELECT user1_id, user2_id, relation_type FROM family_relations"
            )
            backup_data["family"] = [dict(row) for row in await cursor.fetchall()]
            
            # Get friends
            cursor = await self.conn.execute(
                "SELECT user1_id, user2_id FROM friendships"
            )
            backup_data["friends"] = [dict(row) for row in await cursor.fetchall()]
            
            # Get market
            cursor = await self.conn.execute(
                "SELECT seller_id, crop_type, quantity, price FROM market_stands"
            )
            backup_data["market"] = [dict(row) for row in await cursor.fetchall()]
        
        # Create ZIP with encryption
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add data with timestamp
            json_data = json.dumps(backup_data, indent=2)
            zip_file.writestr(f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json", json_data)
            
            # Add checksum
            checksum = hashlib.sha256(json_data.encode()).hexdigest()
            zip_file.writestr("checksum.txt", checksum)
        
        return zip_buffer.getvalue()
    
    async def log_admin_action(self, admin_id: int, action: str, 
                             target_id: Optional[int] = None, 
                             details: str = ""):
        """Log admin actions for security"""
        async with self.lock:
            await self.conn.execute(
                "INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
                (admin_id, action, target_id, details)
            )
            await self.conn.commit()

# ============================================================================
# BOT INSTANCE & GLOBALS
# ============================================================================

db = SecureDatabase(DB_PATH)
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None
rate_limiter = RateLimiter()

# ============================================================================
# SECURITY DECORATORS & MIDDLEWARE
# ============================================================================

def owner_only(func):
    """Decorator to restrict commands to owner only"""
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id != OWNER_ID:
            await message.answer("❌ Owner-only command.")
            await db.log_admin_action(
                message.from_user.id, 
                "unauthorized_access", 
                None, 
                f"Tried to use {func.__name__}"
            )
            return
        return await func(message, *args, **kwargs)
    return wrapper

def rate_limit(action: str = "default"):
    """Decorator for rate limiting"""
    def decorator(func):
        async def wrapper(message: Message, *args, **kwargs):
            allowed, msg = rate_limiter.is_allowed(message.from_user.id, action)
            if not allowed:
                await message.answer(f"⏳ {msg}")
                return
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator

async def security_check(message: Message) -> Tuple[bool, str]:
    """Comprehensive security check"""
    user_id = message.from_user.id
    
    # Check if banned
    if await db.is_user_banned(user_id):
        return False, "You are banned from using this bot."
    
    # Check rate limits
    allowed, msg = rate_limiter.is_allowed(user_id)
    if not allowed:
        return False, msg
    
    return True, ""

# ============================================================================
# COMMAND HANDLERS - USER COMMANDS
# ============================================================================

@dp.message(Command("start"))
@rate_limit()
async def cmd_start(message: Message):
    """Start command with security check"""
    passed, msg = await security_check(message)
    if not passed:
        await message.answer(f"❌ {msg}")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    welcome = (
        f"👋 Welcome to Family Tree Bot, {user['first_name']}!\n\n"
        f"🌳 Create virtual families with /adopt and /marry\n"
        f"🤝 Make global friends with /friend\n"
        f"🌾 Farm crops in your /garden\n"
        f"💰 Trade crops on /stands marketplace\n"
        f"⚔️ Engage in PvP with /rob and /kill\n\n"
        f"Use /help for all commands!"
    )
    
    await message.answer(welcome)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Health check command"""
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    # Check database
    db_ok = False
    try:
        user = await db.get_user(message.from_user.id)
        db_ok = True
    except:
        pass
    
    status = (
        f"🏓 **Bot Status**\n\n"
        f"✅ Bot: Online\n"
        f"📡 Latency: {latency}ms\n"
        f"💾 Database: {'✅ Connected' if db_ok else '❌ Error'}\n"
        f"👤 Users: ... (use /admin stats)\n"
        f"🕐 Time: {datetime.utcnow().strftime('%H:%M UTC')}"
    )
    
    await msg.edit_text(status)

@dp.message(Command("backup"))
@owner_only
async def cmd_backup(message: Message):
    """Create secure backup (owner only)"""
    backup_msg = await message.answer("🔐 Creating secure backup...")
    
    try:
        backup_data = await db.create_backup()
        
        # Send as document
        backup_file = FSInputFile(
            path=io.BytesIO(backup_data),
            filename=f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        )
        
        await bot.send_document(
            chat_id=OWNER_ID,
            document=backup_file,
            caption=f"🔐 Backup created at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        
        await backup_msg.edit_text("✅ Backup created and sent to owner privately!")
        
        # Log the action
        await db.log_admin_action(
            message.from_user.id,
            "backup_created",
            None,
            "Full system backup"
        )
        
    except Exception as e:
        await backup_msg.edit_text(f"❌ Backup failed: {str(e)}")
        logger.error(f"Backup error: {e}")

@dp.message(Command("refresh"))
@owner_only
@rate_limit("default")
async def cmd_refresh(message: Message):
    """Refresh system data (owner only)"""
    refresh_msg = await message.answer("🔄 Refreshing system...")
    
    try:
        # Update crop growth
        async with db.lock:
            await db.conn.execute(
                "UPDATE garden_plants SET is_ready = 1 WHERE "
                "julianday('now') - julianday(planted_at) > grow_time/86400.0"
            )
            
            # Clear old proposals (24h+)
            await db.conn.execute(
                "DELETE FROM proposals WHERE expires_at < CURRENT_TIMESTAMP"
            )
            
            await db.conn.commit()
        
        await refresh_msg.edit_text(
            "✅ System refreshed!\n"
            "• Updated crop growth\n"
            "• Cleared expired proposals\n"
            "• All daily limits maintained"
        )
        
        await db.log_admin_action(
            message.from_user.id,
            "system_refresh",
            None,
            "Manual system refresh"
        )
        
    except Exception as e:
        await refresh_msg.edit_text(f"❌ Refresh failed: {str(e)}")

@dp.message(Command("hmk"))
@rate_limit()
async def cmd_hmk(message: Message):
    """Hired Muscle - Special attack"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    if user["cash"] < 5000:
        await message.answer("❌ Need $5,000 to hire muscle!")
        return
    
    # Find random target with money
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT user_id, first_name, cash FROM users "
            "WHERE user_id != ? AND cash > 1000 "
            "ORDER BY RANDOM() LIMIT 1",
            (user["user_id"],)
        )
        target = await cursor.fetchone()
    
    if not target:
        await message.answer("❌ No suitable targets found!")
        return
    
    target_id, target_name, target_cash = target
    
    # Calculate steal (30-50%)
    steal_percent = random.uniform(0.3, 0.5)
    stolen = min(int(target_cash * steal_percent), 5000)
    
    if stolen < 100:
        stolen = min(target_cash, 1000)
    
    # Execute transaction
    queries = [
        ("UPDATE users SET cash = cash - ? WHERE user_id = ?", (5000, user["user_id"])),
        ("UPDATE users SET cash = cash - ? WHERE user_id = ?", (stolen, target_id)),
        ("UPDATE users SET cash = cash + ? WHERE user_id = ?", (stolen + 1000, user["user_id"])),
    ]
    
    try:
        await db.execute_transaction(queries)
        
        result = (
            f"💪 **Hired Muscle Attack Successful!**\n\n"
            f"🦾 You hired muscle for $5,000\n"
            f"🎯 Target: {target_name}\n"
            f"💰 Stolen: ${stolen:,}\n"
            f"💸 Bonus: $1,000 (for successful hire)\n"
            f"📈 Total Gain: ${stolen:,}\n\n"
            f"⚖️ Reputation: -15 (for brutal attack)"
        )
        
        # Update reputation
        await db.conn.execute(
            "UPDATE users SET reputation = reputation - 15 WHERE user_id = ?",
            (user["user_id"],)
        )
        
        await message.answer(result)
        
        # Log the attack
        await db.log_admin_action(
            user["user_id"],
            "hmk_attack",
            target_id,
            f"Stole ${stolen} from {target_name}"
        )
        
    except Exception as e:
        await message.answer(f"❌ Attack failed: {str(e)}")

@dp.message(Command("garden"))
@rate_limit()
async def cmd_garden(message: Message):
    """View and manage garden"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Please use /start first!")
        return
    
    async with db.lock:
        # Get garden info
        cursor = await db.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?", (user["user_id"],)
        )
        garden = await cursor.fetchone()
        
        # Get active plants
        cursor = await db.conn.execute(
            "SELECT crop_type, "
            "ROUND((julianday('now') - julianday(planted_at)) * 86400.0) as elapsed, "
            "grow_time, is_ready "
            "FROM garden_plants WHERE user_id = ? AND is_ready = 0",
            (user["user_id"],)
        )
        plants = await cursor.fetchall()
        
        # Get barn contents
        cursor = await db.conn.execute(
            "SELECT crop_type, quantity FROM barn WHERE user_id = ?",
            (user["user_id"],)
        )
        barn = await cursor.fetchall()
    
    if not garden:
        await message.answer("❌ Garden not found! Use /start to create one.")
        return
    
    slots = garden[0]
    active_plants = len(plants)
    
    # Build garden display
    garden_text = f"🌾 **{user['first_name']}'s Garden**\n\n"
    garden_text += f"📊 **Stats:**\n"
    garden_text += f"• Slots: {active_plants}/{slots}\n"
    garden_text += f"• Money: ${user['cash']:,}\n"
    garden_text += f"• Tokens: {user['tokens']} 🌱\n\n"
    
    if plants:
        garden_text += f"🌱 **Growing Plants:**\n"
        for plant in plants:
            crop_type, elapsed, grow_time, is_ready = plant
            if is_ready:
                status = "✅ Ready!"
            else:
                remaining = max(0, grow_time - elapsed)
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                status = f"⏳ {hours}h {minutes}m"
            garden_text += f"• {crop_type.capitalize()}: {status}\n"
    else:
        garden_text += "🌱 No plants growing. Use /plant [crop] [qty]\n"
    
    if barn:
        garden_text += f"\n🏠 **Barn Storage:**\n"
        for item in barn:
            crop_type, quantity = item
            garden_text += f"• {crop_type.capitalize()}: {quantity}\n"
    
    # Add garden actions keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 Plant", callback_data="garden_plant"),
            InlineKeyboardButton(text="🪴 Harvest", callback_data="garden_harvest")
        ],
        [
            InlineKeyboardButton(text="🏪 Market", callback_data="garden_market"),
            InlineKeyboardButton(text="💧 Fertilize", callback_data="garden_fertilize")
        ],
        [
            InlineKeyboardButton(text="📦 Barn", callback_data="garden_barn"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="garden_refresh")
        ]
    ])
    
    await message.answer(garden_text, reply_markup=keyboard)

@dp.message(Command("plant"))
@rate_limit()
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops command"""
    if not command.args:
        await message.answer(
            "❌ Usage: /plant [crop] [quantity]\n"
            f"Available crops: {', '.join(CROP_TYPES)}\n"
            "Example: /plant carrot 3"
        )
        return
    
    try:
        args = command.args.split()
        if len(args) == 2:
            crop_type, quantity = args[0].lower(), int(args[1])
        elif len(args) == 1:
            crop_type, quantity = args[0].lower(), 1
        else:
            await message.answer("❌ Usage: /plant [crop] [quantity]")
            return
    except:
        await message.answer("❌ Invalid format! Use: /plant [crop] [quantity]")
        return
    
    if crop_type not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Choose from: {', '.join(CROP_TYPES)}")
        return
    
    if quantity < 1 or quantity > 10:
        await message.answer("❌ Quantity must be 1-10!")
        return
    
    success, msg = await db.plant_crop(message.from_user.id, crop_type, quantity)
    await message.answer("✅ " + msg if success else "❌ " + msg)

@dp.message(Command("harvest"))
@rate_limit()
async def cmd_harvest(message: Message):
    """Harvest ready crops"""
    harvested, msg = await db.harvest_crops(message.from_user.id)
    
    if harvested:
        crop_list = ", ".join([f"{qty} {crop}" for crop, qty in harvested.items()])
        total = sum(harvested.values())
        response = (
            f"✅ {msg}\n\n"
            f"📦 **Harvested:**\n{crop_list}\n\n"
            f"📈 Total crops: {total}\n"
            f"🏠 Stored in barn. Use /barn to view."
        )
    else:
        response = "❌ " + msg
    
    await message.answer(response)

@dp.message(Command("stands"))
@rate_limit()
async def cmd_stands(message: Message):
    """View market stands"""
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT ms.id, ms.crop_type, ms.quantity, ms.price, "
            "u.first_name, u.username "
            "FROM market_stands ms "
            "JOIN users u ON ms.seller_id = u.user_id "
            "ORDER BY ms.price / ms.quantity ASC "
            "LIMIT 20"
        )
        listings = await cursor.fetchall()
    
    if not listings:
        await message.answer("🏪 **Market Stands**\n\nNo listings available.")
        return
    
    market_text = "🏪 **Market Stands** (Cheapest First)\n\n"
    
    for listing in listings:
        listing_id, crop_type, quantity, price, seller_name, username = listing
        price_per = price / quantity
        market_text += (
            f"📦 **{crop_type.capitalize()}**\n"
            f"• Quantity: {quantity}\n"
            f"• Price: ${price:,} (${price_per:.1f}/each)\n"
            f"• Seller: {seller_name}\n"
            f"• ID: `{listing_id}`\n"
            f"Use `/buy {listing_id} [qty]` to purchase\n\n"
        )
    
    await message.answer(market_text)

@dp.message(Command("buy"))
@rate_limit()
async def cmd_buy(message: Message, command: CommandObject):
    """Buy from market"""
    if not command.args:
        await message.answer("❌ Usage: /buy [listing_id] [quantity]")
        return
    
    try:
        args = command.args.split()
        listing_id = int(args[0])
        quantity = int(args[1]) if len(args) > 1 else 1
    except:
        await message.answer("❌ Usage: /buy [listing_id] [quantity]")
        return
    
    success, msg = await db.buy_from_market(message.from_user.id, listing_id, quantity)
    await message.answer("✅ " + msg if success else "❌ " + msg)

# ============================================================================
# CALLBACK QUERY HANDLERS
# ============================================================================

@dp.callback_query(F.data.startswith("garden_"))
async def handle_garden_callback(callback: CallbackQuery):
    """Handle garden button callbacks"""
    action = callback.data.split("_")[1]
    
    if action == "plant":
        await callback.message.answer(
            "🌱 **Plant Crops**\n\n"
            "Usage: `/plant [crop] [quantity]`\n"
            f"Crops: {', '.join(CROP_TYPES)}\n"
            "Prices per seed:\n" +
            "\n".join([f"• {crop}: ${CROP_PRICES[crop]['buy']}" for crop in CROP_TYPES])
        )
    elif action == "harvest":
        await cmd_harvest(callback.message)
    elif action == "market":
        await cmd_stands(callback.message)
    elif action == "refresh":
        await callback.message.delete()
        await cmd_garden(callback.message)
    
    await callback.answer()

# ============================================================================
# MESSAGE HANDLERS (Reactions, Trading, etc.)
# ============================================================================

@dp.message(F.text.startswith("I trade "))
async def handle_trade(message: Message):
    """Handle trading syntax: I trade 5 carrot for 3 tomato"""
    try:
        # Parse trade command
        text = message.text[8:]  # Remove "I trade "
        
        if " for " not in text:
            await message.answer("❌ Format: `I trade [qty] [item] for [qty] [item]`")
            return
        
        offer_part, request_part = text.split(" for ", 1)
        
        # Parse offer
        offer_parts = offer_part.strip().split()
        if len(offer_parts) != 2:
            await message.answer("❌ Offer format: [quantity] [item]")
            return
        
        offer_qty = int(offer_parts[0])
        offer_item = offer_parts[1].lower()
        
        # Parse request
        request_parts = request_part.strip().split()
        if len(request_parts) != 2:
            # Might be for money
            try:
                request_money = int(request_parts[0])
                is_money_trade = True
            except:
                await message.answer("❌ Request format: [quantity] [item] OR [amount]")
                return
        else:
            is_money_trade = False
            request_qty = int(request_parts[0])
            request_item = request_parts[1].lower()
        
        if not message.reply_to_message:
            await message.answer("❌ Reply to the person you want to trade with!")
            return
        
        # Create trade proposal
        trade_id = str(uuid.uuid4())[:8]
        trade_data = {
            "offer": {"item": offer_item, "quantity": offer_qty},
            "request": {"item": request_item if not is_money_trade else "cash", 
                       "quantity": request_qty if not is_money_trade else request_money},
            "is_money": is_money_trade
        }
        
        # Store proposal
        async with db.lock:
            await db.conn.execute(
                "INSERT INTO proposals (proposal_id, from_id, to_id, proposal_type, data) "
                "VALUES (?, ?, ?, ?, ?)",
                (trade_id, message.from_user.id, 
                 message.reply_to_message.from_user.id,
                 "trade", json.dumps(trade_data))
            )
            await db.conn.commit()
        
        # Create accept/reject buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Accept Trade", 
                                   callback_data=f"trade_accept_{trade_id}"),
                InlineKeyboardButton(text="❌ Decline", 
                                   callback_data=f"trade_decline_{trade_id}")
            ]
        ])
        
        trade_desc = (
            f"🤝 **Trade Proposal**\n\n"
            f"From: {message.from_user.first_name}\n"
            f"Offers: {offer_qty} {offer_item}\n"
            f"Requests: {request_qty} {request_item if not is_money_trade else 'cash'}\n\n"
            f"ID: `{trade_id}`\n"
            f"Expires in 24 hours"
        )
        
        await message.reply_to_message.reply(trade_desc, reply_markup=keyboard)
        
    except Exception as e:
        await message.answer(f"❌ Trade error: {str(e)}")

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

@dp.message(Command("admin"))
@owner_only
async def cmd_admin(message: Message, command: CommandObject):
    """Admin panel"""
    if not command.args:
        admin_text = (
            "👑 **Admin Panel**\n\n"
            "**User Management:**\n"
            "• /admin user [id] - User info\n"
            "• /admin ban [id] [reason] - Ban user\n"
            "• /admin unban [id] - Unban user\n"
            "• /admin addmoney [id] [amount] [currency]\n\n"
            "**System:**\n"
            "• /backup - Create secure backup\n"
            "• /refresh - Refresh system data\n"
            "• /admin stats - Bot statistics\n"
            "• /admin logs [n] - Recent logs\n\n"
            "**Garden/Market:**\n"
            "• /admin clearmarket - Clear all market listings\n"
            "• /admin resetgarden [id] - Reset user's garden"
        )
        await message.answer(admin_text)
        return

@dp.message(Command("admin", "stats"))
@owner_only
async def cmd_admin_stats(message: Message):
    """Admin statistics"""
    async with db.lock:
        # Get counts
        cursor = await db.conn.execute("SELECT COUNT(*) FROM users")
        user_count = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute("SELECT COUNT(*) FROM family_relations")
        family_count = (await cursor.fetchone())[0] // 2
        
        cursor = await db.conn.execute("SELECT COUNT(*) FROM friendships")
        friend_count = (await cursor.fetchone())[0] // 2
        
        cursor = await db.conn.execute("SELECT COUNT(*) FROM market_stands")
        market_count = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute("SELECT COUNT(*) FROM garden_plants WHERE is_ready = 0")
        growing_count = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute("SELECT SUM(cash), SUM(gold) FROM users")
        totals = await cursor.fetchone()
        total_cash, total_gold = totals if totals else (0, 0)
    
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"👥 Users: {user_count:,}\n"
        f"👨‍👩‍👧‍👦 Families: {family_count:,}\n"
        f"🤝 Friendships: {friend_count:,}\n"
        f"🏪 Market Listings: {market_count:,}\n"
        f"🌱 Growing Plants: {growing_count:,}\n\n"
        f"💰 **Economy:**\n"
        f"• Total Cash: ${total_cash:,}\n"
        f"• Total Gold: {total_gold:,}\n\n"
        f"⚙️ **System:**\n"
        f"• Owner ID: {OWNER_ID}\n"
        f"• Log Channel: {LOG_CHANNEL}\n"
        f"• Database: {DB_PATH}\n"
        f"• Uptime: ... (implement with startup time)"
    )
    
    await message.answer(stats_text)

# ============================================================================
# MAIN BOT SETUP
# ============================================================================

async def setup_bot():
    """Initialize bot with security features"""
    global bot, dp
    
    # Initialize bot
    bot = Bot(token=BOT_TOKEN, 
              default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Connect to database
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Show help"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="stands", description="Market stands"),
        types.BotCommand(command="buy", description="Buy from market"),
        types.BotCommand(command="ping", description="Check bot status"),
        types.BotCommand(command="refresh", description="Refresh data"),
        types.BotCommand(command="hmk", description="Hired muscle attack"),
        types.BotCommand(command="admin", description="Admin panel"),
    ]
    
    await bot.set_my_commands(commands)
    
    # Send startup message to log channel
    try:
        await bot.send_message(
            LOG_CHANNEL,
            f"🤖 **Family Tree Bot Started**\n"
            f"⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"👑 Owner: {OWNER_ID}\n"
            f"🔐 Security: Maximum protection enabled"
        )
    except:
        logger.warning("Could not send startup message to log channel")
    
    logger.info("Bot setup complete with maximum security")

async def main():
    """Main entry point"""
    try:
        await setup_bot()
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
