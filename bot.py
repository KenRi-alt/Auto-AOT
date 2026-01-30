#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - COMPLETE PRODUCTION VERSION
Version: 8.2 - FIXED NO MATPLOTLIB ERRORS
Owner ID: 6108185460
Log Channel: -1003662720845
Bot: @Familly_TreeBot
"""
import os
import sys
import json
import asyncio
import logging
import random
import secrets
import re
import math
import html
import time
import uuid
import aiofiles
import io
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict
import traceback
import textwrap

# ============================================================================
# CORRECT IMPORTS - NO ERRORS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F, Router
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto, ChatMemberUpdated, ChatJoinRequest,
        InputMediaAnimation
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode, ChatMemberStatus
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    # Image libraries - ONLY PILLOW (no matplotlib)
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        PILLOW_AVAILABLE = True
        print("✅ Pillow available - Images will work")
    except ImportError:
        PILLOW_AVAILABLE = False
        print("⚠️ Pillow not installed - Text mode only")
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram==3.0.0b7 aiohttp pillow aiosqlite python-dotenv")
    sys.exit(1)

import aiosqlite
import aiohttp
from dataclasses import dataclass

# ============================================================================
# CONFIGURATION
# ============================================================================
OWNER_ID = 6108185460
BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
BOT_USERNAME = "@Familly_TreeBot"
LOG_CHANNEL = -1003662720845
ADMIN_IDS = [OWNER_ID]
SUPPORT_CHAT = "https://t.me/+T7JxyxVOYcxmMzJl"

# Database
DB_PATH = os.getenv("DB_PATH", "family_bot_v8.db")

# Colors for UI
COLORS = {
    "primary": (0, 173, 181),      # #00adb5
    "secondary": (57, 62, 70),     # #393e46
    "accent": (255, 46, 99),       # #ff2e63
    "success": (8, 217, 214),      # #08d9d6
    "warning": (243, 129, 129),    # #f38181
    "danger": (255, 87, 34),       # #ff5722
    "background": (26, 26, 46),    # #1a1a2e
    "card": (22, 33, 62),          # #16213e
    "text": (238, 238, 238),       # #eeeeee
    "border": (48, 71, 94)         # #30475e
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
# DATABASE CLASS - COMPLETE
# ============================================================================
class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.path)
        await self.init_tables()
    
    async def init_tables(self):
        """Initialize ALL database tables"""
        tables = []
        
        # Users table
        tables.append("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            cash INTEGER DEFAULT 1000,
            gold INTEGER DEFAULT 0,
            bonds INTEGER DEFAULT 0,
            credits INTEGER DEFAULT 100,
            tokens INTEGER DEFAULT 50,
            event_coins INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 100,
            is_banned BOOLEAN DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            last_daily TIMESTAMP,
            daily_count INTEGER DEFAULT 0,
            gemstone TEXT,
            bio_verified BOOLEAN DEFAULT 0,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profile_pic_hash TEXT,
            bank_balance INTEGER DEFAULT 0,
            rob_cooldown TIMESTAMP,
            kill_cooldown TIMESTAMP,
            hug_cooldown TIMESTAMP
        )
        """)
        
        # Family relations
        tables.append("""
        CREATE TABLE IF NOT EXISTS family_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL CHECK(relation_type IN ('parent', 'spouse', 'child', 'sibling')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1_id, user2_id, relation_type)
        )
        """)
        
        # Garden
        tables.append("""
        CREATE TABLE IF NOT EXISTS gardens (
            user_id INTEGER PRIMARY KEY,
            slots INTEGER DEFAULT 9,
            barn_capacity INTEGER DEFAULT 50,
            last_watered TIMESTAMP
        )
        """)
        
        # Garden plants
        tables.append("""
        CREATE TABLE IF NOT EXISTS garden_plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            crop_type TEXT NOT NULL CHECK(crop_type IN ('carrot', 'tomato', 'potato', 'eggplant', 'corn', 'pepper', 'watermelon', 'pumpkin')),
            planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            grow_time REAL NOT NULL,
            progress REAL DEFAULT 0,
            is_ready BOOLEAN DEFAULT 0,
            water_count INTEGER DEFAULT 0
        )
        """)
        
        # Barn
        tables.append("""
        CREATE TABLE IF NOT EXISTS barn (
            user_id INTEGER NOT NULL,
            crop_type TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, crop_type)
        )
        """)
        
        # Stands
        tables.append("""
        CREATE TABLE IF NOT EXISTS stands (
            user_id INTEGER PRIMARY KEY,
            stand_name TEXT NOT NULL,
            power INTEGER DEFAULT 1,
            speed INTEGER DEFAULT 1,
            range INTEGER DEFAULT 1,
            durability INTEGER DEFAULT 1,
            precision INTEGER DEFAULT 1,
            potential INTEGER DEFAULT 1,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Friends
        tables.append("""
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            friendship_level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1_id, user2_id)
        )
        """)
        
        # Inventory
        tables.append("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            metadata TEXT
        )
        """)
        
        # CatBox GIFs
        tables.append("""
        CREATE TABLE IF NOT EXISTS catbox_gifs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            url TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Transactions
        tables.append("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER,
            to_id INTEGER,
            amount INTEGER,
            currency TEXT,
            type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Warnings
        tables.append("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Admin logs
        tables.append("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Game stats
        tables.append("""
        CREATE TABLE IF NOT EXISTS game_stats (
            user_id INTEGER PRIMARY KEY,
            slots_played INTEGER DEFAULT 0,
            slots_won INTEGER DEFAULT 0,
            duels_played INTEGER DEFAULT 0,
            duels_won INTEGER DEFAULT 0,
            robs_attempted INTEGER DEFAULT 0,
            robs_successful INTEGER DEFAULT 0,
            hugs_sent INTEGER DEFAULT 0,
            kills_sent INTEGER DEFAULT 0
        )
        """)
        
        # Achievements
        tables.append("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Quests
        tables.append("""
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quest_id TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Market
        tables.append("""
        CREATE TABLE IF NOT EXISTS market (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Execute all tables
        async with self.lock:
            for table_sql in tables:
                try:
                    await self.conn.execute(table_sql)
                except Exception as e:
                    logger.error(f"Table creation error: {e}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_family_user1 ON family_relations(user1_id)",
                "CREATE INDEX IF NOT EXISTS idx_family_user2 ON family_relations(user2_id)",
                "CREATE INDEX IF NOT EXISTS idx_garden_plants_user ON garden_plants(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_garden_plants_ready ON garden_plants(is_ready)",
                "CREATE INDEX IF NOT EXISTS idx_barn_user ON barn(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_friends_user1 ON friends(user1_id)",
                "CREATE INDEX IF NOT EXISTS idx_friends_user2 ON friends(user2_id)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_transactions_from ON transactions(from_id)",
                "CREATE INDEX IF NOT EXISTS idx_transactions_to ON transactions(to_id)",
                "CREATE INDEX IF NOT EXISTS idx_market_seller ON market(seller_id)"
            ]
            
            for index_sql in indexes:
                try:
                    await self.conn.execute(index_sql)
                except Exception as e:
                    logger.error(f"Index creation error: {e}")
            
            await self.conn.commit()
    
    # USER METHODS
    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    async def create_user(self, user: types.User) -> Dict:
        async with self.lock:
            # Insert user
            await self.conn.execute(
                """INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name) 
                VALUES (?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, user.last_name)
            )
            
            # Create garden
            await self.conn.execute(
                "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                (user.id,)
            )
            
            # Create game stats
            await self.conn.execute(
                "INSERT OR IGNORE INTO game_stats (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.commit()
        
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int) -> bool:
        valid_currencies = ['cash', 'gold', 'bonds', 'credits', 'tokens', 'event_coins']
        if currency not in valid_currencies:
            return False
        
        async with self.lock:
            try:
                await self.conn.execute(
                    f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?",
                    (amount, user_id)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Update currency error: {e}")
                return False
    
    async def update_last_active(self, user_id: int):
        async with self.lock:
            await self.conn.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await self.conn.commit()
    
    # FAMILY METHODS
    async def get_family(self, user_id: int) -> List[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT 
                    fr.relation_type,
                    CASE 
                        WHEN fr.user1_id = ? THEN u2.user_id
                        ELSE u1.user_id
                    END as other_id,
                    CASE 
                        WHEN fr.user1_id = ? THEN u2.first_name
                        ELSE u1.first_name
                    END as other_name,
                    fr.created_at
                FROM family_relations fr
                LEFT JOIN users u1 ON u1.user_id = fr.user1_id
                LEFT JOIN users u2 ON u2.user_id = fr.user2_id
                WHERE ? IN (fr.user1_id, fr.user2_id)
                ORDER BY fr.created_at""",
                (user_id, user_id, user_id)
            )
            rows = await cursor.fetchall()
            
            family = []
            for row in rows:
                family.append({
                    'relation_type': row[0],
                    'other_id': row[1],
                    'other_name': row[2],
                    'since': row[3]
                })
            return family
    
    async def add_family_relation(self, user1_id: int, user2_id: int, relation_type: str) -> bool:
        if user1_id == user2_id:
            return False
        
        valid_relations = ['parent', 'spouse', 'child', 'sibling']
        if relation_type not in valid_relations:
            return False
        
        async with self.lock:
            try:
                await self.conn.execute(
                    """INSERT INTO family_relations (user1_id, user2_id, relation_type)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user1_id, user2_id, relation_type) DO NOTHING""",
                    (min(user1_id, user2_id), max(user1_id, user2_id), relation_type)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Add family error: {e}")
                return False
    
    async def remove_family_relation(self, user1_id: int, user2_id: int, relation_type: str) -> bool:
        async with self.lock:
            try:
                await self.conn.execute(
                    """DELETE FROM family_relations 
                    WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
                    AND relation_type = ?""",
                    (user1_id, user2_id, user2_id, user1_id, relation_type)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Remove family error: {e}")
                return False
    
    # GARDEN METHODS
    async def get_garden_info(self, user_id: int) -> Dict:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT slots, barn_capacity FROM gardens WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return {
                'slots': row[0] if row else 9,
                'barn_capacity': row[1] if row else 50
            }
    
    async def get_growing_plants(self, user_id: int) -> List[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT 
                    id, crop_type, 
                    ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours_passed,
                    grow_time, progress, water_count
                FROM garden_plants 
                WHERE user_id = ? AND is_ready = 0
                ORDER BY planted_at""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            plants = []
            for row in rows:
                progress = min(100, (row[2] / row[3]) * 100) if row[3] > 0 else 0
                plants.append({
                    'id': row[0],
                    'crop_type': row[1],
                    'hours_passed': row[2],
                    'grow_time': row[3],
                    'progress': progress,
                    'water_count': row[5]
                })
            return plants
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int) -> bool:
        valid_crops = ['carrot', 'tomato', 'potato', 'eggplant', 'corn', 'pepper', 'watermelon', 'pumpkin']
        if crop_type not in valid_crops:
            return False
        
        grow_times = {
            'carrot': 2, 'tomato': 3, 'potato': 2.5, 'eggplant': 4,
            'corn': 5, 'pepper': 6, 'watermelon': 7, 'pumpkin': 8
        }
        
        async with self.lock:
            try:
                # Check available slots
                garden = await self.get_garden_info(user_id)
                cursor = await self.conn.execute(
                    "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
                    (user_id,)
                )
                current_count = (await cursor.fetchone())[0]
                
                if current_count + quantity > garden['slots']:
                    return False
                
                # Plant crops
                for _ in range(quantity):
                    await self.conn.execute(
                        """INSERT INTO garden_plants 
                        (user_id, crop_type, grow_time, progress)
                        VALUES (?, ?, ?, 0)""",
                        (user_id, crop_type, grow_times[crop_type])
                    )
                
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Plant crop error: {e}")
                return False
    
    async def harvest_plants(self, user_id: int) -> Tuple[int, List[Dict]]:
        """Harvest all ready plants"""
        async with self.lock:
            try:
                # Get ready plants
                cursor = await self.conn.execute(
                    """SELECT id, crop_type FROM garden_plants 
                    WHERE user_id = ? AND progress >= 100""",
                    (user_id,)
                )
                ready_plants = await cursor.fetchall()
                
                if not ready_plants:
                    return 0, []
                
                harvested = []
                total_yield = 0
                
                for plant in ready_plants:
                    plant_id, crop_type = plant
                    
                    # Yield per plant (1-3 with chance)
                    yield_amount = random.randint(1, 3)
                    total_yield += yield_amount
                    
                    # Add to barn
                    await self.conn.execute(
                        """INSERT INTO barn (user_id, crop_type, quantity)
                        VALUES (?, ?, ?)
                        ON CONFLICT(user_id, crop_type) 
                        DO UPDATE SET quantity = quantity + ?""",
                        (user_id, crop_type, yield_amount, yield_amount)
                    )
                    
                    # Mark as harvested
                    await self.conn.execute(
                        "DELETE FROM garden_plants WHERE id = ?",
                        (plant_id,)
                    )
                    
                    harvested.append({
                        'crop_type': crop_type,
                        'yield': yield_amount
                    })
                
                await self.conn.commit()
                return total_yield, harvested
            except Exception as e:
                logger.error(f"Harvest error: {e}")
                return 0, []
    
    async def get_barn_items(self, user_id: int) -> List[Tuple[str, int]]:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT crop_type, quantity FROM barn WHERE user_id = ? ORDER BY quantity DESC",
                (user_id,)
            )
            return await cursor.fetchall()
    
    # STAND METHODS
    async def get_stand(self, user_id: int) -> Optional[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM stands WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    async def create_stand(self, user_id: int) -> Dict:
        stand_names = [
            "Star Platinum", "The World", "Crazy Diamond", "Gold Experience",
            "Killer Queen", "King Crimson", "Stone Free", "Tusk"
        ]
        
        stand_name = random.choice(stand_names)
        
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO stands 
                (user_id, stand_name, power, speed, range, durability, precision, potential)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, stand_name, 1, 1, 1, 1, 1, 1)
            )
            await self.conn.commit()
        
        return await self.get_stand(user_id)
    
    async def upgrade_stand(self, user_id: int, stat: str) -> bool:
        valid_stats = ['power', 'speed', 'range', 'durability', 'precision', 'potential']
        if stat not in valid_stats:
            return False
        
        async with self.lock:
            try:
                await self.conn.execute(
                    f"UPDATE stands SET {stat} = {stat} + 1 WHERE user_id = ?",
                    (user_id,)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Upgrade stand error: {e}")
                return False
    
    # FRIEND METHODS
    async def add_friend(self, user1_id: int, user2_id: int) -> bool:
        if user1_id == user2_id:
            return False
        
        async with self.lock:
            try:
                await self.conn.execute(
                    """INSERT INTO friends (user1_id, user2_id)
                    VALUES (?, ?)
                    ON CONFLICT(user1_id, user2_id) DO NOTHING""",
                    (min(user1_id, user2_id), max(user1_id, user2_id))
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Add friend error: {e}")
                return False
    
    async def remove_friend(self, user1_id: int, user2_id: int) -> bool:
        async with self.lock:
            try:
                await self.conn.execute(
                    """DELETE FROM friends 
                    WHERE (user1_id = ? AND user2_id = ?) 
                    OR (user1_id = ? AND user2_id = ?)""",
                    (user1_id, user2_id, user2_id, user1_id)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Remove friend error: {e}")
                return False
    
    async def get_friends(self, user_id: int) -> List[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT 
                    CASE 
                        WHEN f.user1_id = ? THEN u2.user_id
                        ELSE u1.user_id
                    END as friend_id,
                    CASE 
                        WHEN f.user1_id = ? THEN u2.first_name
                        ELSE u1.first_name
                    END as friend_name,
                    f.friendship_level
                FROM friends f
                LEFT JOIN users u1 ON u1.user_id = f.user1_id
                LEFT JOIN users u2 ON u2.user_id = f.user2_id
                WHERE ? IN (f.user1_id, f.user2_id)""",
                (user_id, user_id, user_id)
            )
            rows = await cursor.fetchall()
            
            friends = []
            for row in rows:
                friends.append({
                    'friend_id': row[0],
                    'friend_name': row[1],
                    'friendship_level': row[2]
                })
            return friends
    
    # INVENTORY METHODS
    async def add_item(self, user_id: int, item_type: str, item_name: str, quantity: int = 1) -> bool:
        async with self.lock:
            try:
                # Check if item exists
                cursor = await self.conn.execute(
                    "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_type = ? AND item_name = ?",
                    (user_id, item_type, item_name)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    # Update quantity
                    await self.conn.execute(
                        "UPDATE inventory SET quantity = quantity + ? WHERE id = ?",
                        (quantity, existing[0])
                    )
                else:
                    # Insert new item
                    await self.conn.execute(
                        """INSERT INTO inventory 
                        (user_id, item_type, item_name, quantity)
                        VALUES (?, ?, ?, ?)""",
                        (user_id, item_type, item_name, quantity)
                    )
                
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Add item error: {e}")
                return False
    
    async def get_inventory(self, user_id: int) -> List[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT item_type, item_name, quantity FROM inventory WHERE user_id = ?",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            inventory = []
            for row in rows:
                inventory.append({
                    'type': row[0],
                    'name': row[1],
                    'quantity': row[2]
                })
            return inventory
    
    # CATBOX GIF METHODS
    async def add_catbox_gif(self, command: str, url: str, added_by: int) -> bool:
        async with self.lock:
            try:
                await self.conn.execute(
                    """INSERT INTO catbox_gifs (command, url, added_by)
                    VALUES (?, ?, ?)""",
                    (command.lower(), url, added_by)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Add CatBox GIF error: {e}")
                return False
    
    async def get_random_gif(self, command: str) -> Optional[str]:
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT url FROM catbox_gifs WHERE command = ? ORDER BY RANDOM() LIMIT 1",
                (command.lower(),)
            )
            row = await cursor.fetchone()
            return row[0] if row else None
    
    # GAME STATS METHODS
    async def update_game_stats(self, user_id: int, game_type: str, won: bool = False) -> bool:
        async with self.lock:
            try:
                if game_type == 'slots':
                    if won:
                        await self.conn.execute(
                            "UPDATE game_stats SET slots_played = slots_played + 1, slots_won = slots_won + 1 WHERE user_id = ?",
                            (user_id,)
                        )
                    else:
                        await self.conn.execute(
                            "UPDATE game_stats SET slots_played = slots_played + 1 WHERE user_id = ?",
                            (user_id,)
                        )
                elif game_type == 'rob':
                    await self.conn.execute(
                        "UPDATE game_stats SET robs_attempted = robs_attempted + 1 WHERE user_id = ?",
                        (user_id,)
                    )
                    if won:
                        await self.conn.execute(
                            "UPDATE game_stats SET robs_successful = robs_successful + 1 WHERE user_id = ?",
                            (user_id,)
                        )
                elif game_type == 'hug':
                    await self.conn.execute(
                        "UPDATE game_stats SET hugs_sent = hugs_sent + 1 WHERE user_id = ?",
                        (user_id,)
                    )
                elif game_type == 'kill':
                    await self.conn.execute(
                        "UPDATE game_stats SET kills_sent = kills_sent + 1 WHERE user_id = ?",
                        (user_id,)
                    )
                
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Update game stats error: {e}")
                return False
    
    # ACHIEVEMENT METHODS
    async def add_achievement(self, user_id: int, achievement_id: str) -> bool:
        async with self.lock:
            try:
                await self.conn.execute(
                    "INSERT INTO achievements (user_id, achievement_id) VALUES (?, ?)",
                    (user_id, achievement_id)
                )
                await self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Add achievement error: {e}")
                return False
    
    # ADMIN METHODS
    async def log_admin_action(self, admin_id: int, action: str, target_id: int = None, details: str = None):
        async with self.lock:
            try:
                await self.conn.execute(
                    "INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)",
                    (admin_id, action, target_id, details)
                )
                await self.conn.commit()
            except Exception as e:
                logger.error(f"Admin log error: {e}")
    
    async def add_warning(self, user_id: int, admin_id: int, reason: str = None):
        async with self.lock:
            try:
                await self.conn.execute(
                    "INSERT INTO warnings (user_id, admin_id, reason) VALUES (?, ?, ?)",
                    (user_id, admin_id, reason)
                )
                await self.conn.execute(
                    "UPDATE users SET warnings = warnings + 1 WHERE user_id = ?",
                    (user_id,)
                )
                await self.conn.commit()
            except Exception as e:
                logger.error(f"Add warning error: {e}")
    
    async def get_warnings(self, user_id: int) -> List[Dict]:
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT reason, created_at FROM warnings 
                WHERE user_id = ? ORDER BY created_at DESC""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            warnings = []
            for row in rows:
                warnings.append({
                    'reason': row[0],
                    'date': row[1]
                })
            return warnings
    
    # STATISTICS METHODS
    async def get_bot_stats(self) -> Dict:
        async with self.lock:
            stats = {}
            
            # Total users
            cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            # Active today
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM users WHERE last_active >= datetime('now', '-1 day')"
            )
            stats['active_today'] = (await cursor.fetchone())[0]
            
            # Total families
            cursor = await self.conn.execute("SELECT COUNT(*) FROM family_relations")
            stats['total_families'] = (await cursor.fetchone())[0]
            
            # Total gardens
            cursor = await self.conn.execute("SELECT COUNT(*) FROM gardens")
            stats['total_gardens'] = (await cursor.fetchone())[0]
            
            # Total cash
            cursor = await self.conn.execute("SELECT SUM(cash) FROM users")
            stats['total_cash'] = (await cursor.fetchone())[0] or 0
            
            return stats
    
    # TRANSACTION LOGGING
    async def log_transaction(self, from_id: int = None, to_id: int = None, amount: int = 0, 
                            currency: str = 'cash', type: str = 'transfer', description: str = None):
        async with self.lock:
            try:
                await self.conn.execute(
                    """INSERT INTO transactions 
                    (from_id, to_id, amount, currency, type, description)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (from_id, to_id, amount, currency, type, description)
                )
                await self.conn.commit()
            except Exception as e:
                logger.error(f"Log transaction error: {e}")

# Initialize database
db = Database(DB_PATH)

# ============================================================================
# IMAGE GENERATOR - PILLOW ONLY (NO MATPLOTLIB)
# ============================================================================
class ImageGenerator:
    """Generate images with Pillow only - NO matplotlib errors"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.profile_pic_cache = {}
        
        # Default GIFs if CatBox has none
        self.default_gifs = {
            'rob': [
                "https://media.tenor.com/5C8aK3q1hZsAAAAd/robbery-steal.gif",
                "https://media.tenor.com/7Sf6E3v5JjAAAAAd/rob-robbery.gif"
            ],
            'kill': [
                "https://media.tenor.com/SGakA_cql6QAAAAC/anime-kill.gif",
                "https://media.tenor.com/9pNq9GjVfCgAAAAC/kill-dead.gif"
            ],
            'hug': [
                "https://media.tenor.com/2dnfSJ5VBCwAAAAC/hug-anime.gif",
                "https://media.tenor.com/xIuJvqdMFwgAAAAC/hugs-and-love.gif"
            ],
            'kiss': [
                "https://media.tenor.com/6PJqgX2S2c0AAAAC/kiss-anime.gif",
                "https://media.tenor.com/1Lh3RwzSGFUAAAAC/kiss-love.gif"
            ],
            'slap': [
                "https://media.tenor.com/-tPxVcJqTJUAAAAC/slap-anime.gif",
                "https://media.tenor.com/3bCzWwQ2q6oAAAAC/slap-hit.gif"
            ],
            'pat': [
                "https://media.tenor.com/2j7_f7n5ZPsAAAAC/pat-anime.gif",
                "https://media.tenor.com/XIvKbAoN0FsAAAAC/pat-head.gif"
            ]
        }
    
    async def generate_family_tree(self, user_id: int, user_name: str, family_members: List[Dict]) -> Optional[bytes]:
        """Generate family tree image"""
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            # Run in thread to avoid blocking
            return await asyncio.to_thread(
                self._generate_family_tree_sync,
                user_id, user_name, family_members
            )
        except Exception as e:
            logger.error(f"Family tree image error: {e}")
            return None
    
    def _generate_family_tree_sync(self, user_id: int, user_name: str, family_members: List[Dict]) -> Optional[bytes]:
        """Synchronous family tree generation"""
        try:
            # Create image
            width, height = 800, 800
            img = Image.new('RGB', (width, height), tuple(COLORS["background"]))
            draw = ImageDraw.Draw(img)
            
            # Try to load font
            try:
                font_large = ImageFont.truetype("arial.ttf", 32)
                font_medium = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Title
            title = f"🌳 {user_name}'s Family"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 40), title, fill=tuple(COLORS["primary"]), font=font_large)
            
            # Center point
            center_x, center_y = width // 2, height // 2
            
            # Draw center user circle
            draw.ellipse(
                [center_x - 60, center_y - 60, center_x + 60, center_y + 60],
                fill=tuple(COLORS["primary"]), outline=tuple(COLORS["text"]), width=3
            )
            
            # Draw center user name
            name_bbox = draw.textbbox((0, 0), user_name[:12], font=font_medium)
            name_x = center_x - (name_bbox[2] - name_bbox[0]) // 2
            draw.text((name_x, center_y + 70), user_name[:12], fill=tuple(COLORS["text"]), font=font_medium)
            
            # Draw family members in circle
            member_count = len(family_members)
            radius = 250
            
            for i, member in enumerate(family_members):
                # Calculate position
                angle = 2 * math.pi * i / max(member_count, 1)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # Line color based on relationship
                relation_colors = {
                    'parent': COLORS["accent"],
                    'spouse': COLORS["success"],
                    'child': COLORS["warning"],
                    'sibling': COLORS["primary"]
                }
                line_color = relation_colors.get(member['relation_type'], tuple(COLORS["secondary"]))
                
                # Draw line
                draw.line([(center_x, center_y), (x, y)], fill=line_color, width=2)
                
                # Draw member circle
                draw.ellipse(
                    [x - 40, y - 40, x + 40, y + 40],
                    fill=tuple(COLORS["secondary"]), outline=line_color, width=2
                )
                
                # Draw member name
                name = member['other_name'][:10]
                name_bbox = draw.textbbox((0, 0), name, font=font_small)
                name_x_pos = x - (name_bbox[2] - name_bbox[0]) // 2
                draw.text((name_x_pos, y + 45), name, fill=tuple(COLORS["text"]), font=font_small)
                
                # Draw relation
                rel = member['relation_type'][:8]
                rel_bbox = draw.textbbox((0, 0), rel, font=font_small)
                rel_x = x - (rel_bbox[2] - rel_bbox[0]) // 2
                draw.text((rel_x, y - 55), rel, fill=line_color, font=font_small)
            
            # Stats at bottom
            stats_text = f"Members: {member_count}"
            stats_bbox = draw.textbbox((0, 0), stats_text, font=font_medium)
            stats_x = (width - (stats_bbox[2] - stats_bbox[0])) // 2
            draw.text((stats_x, height - 60), stats_text, fill=tuple(COLORS["primary"]), font=font_medium)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Family tree sync error: {e}")
            return None
    
    async def generate_garden_image(self, user_id: int, garden_info: Dict, plants: List[Dict]) -> Optional[bytes]:
        """Generate garden grid image"""
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            return await asyncio.to_thread(
                self._generate_garden_image_sync,
                user_id, garden_info, plants
            )
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None
    
    def _generate_garden_image_sync(self, user_id: int, garden_info: Dict, plants: List[Dict]) -> Optional[bytes]:
        """Synchronous garden image generation"""
        try:
            width, height = 600, 700
            img = Image.new('RGB', (width, height), tuple(COLORS["background"]))
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                font_large = ImageFont.truetype("arial.ttf", 28)
                font_medium = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Title
            title = "🌾 Your Garden"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 30), title, fill=tuple(COLORS["primary"]), font=font_large)
            
            # Grid settings
            grid_size = 3
            cell_size = 120
            padding = 20
            start_x = (width - (grid_size * cell_size + (grid_size - 1) * padding)) // 2
            start_y = 100
            
            # Crop emojis
            crop_emojis = {
                'carrot': '🥕', 'tomato': '🍅', 'potato': '🥔',
                'eggplant': '🍆', 'corn': '🌽', 'pepper': '🫑',
                'watermelon': '🍉', 'pumpkin': '🎃'
            }
            
            # Crop colors
            crop_colors = {
                'carrot': (225, 112, 85),
                'tomato': (232, 67, 147),
                'potato': (108, 92, 231),
                'eggplant': (162, 155, 254),
                'corn': (253, 203, 110),
                'pepper': (0, 184, 148),
                'watermelon': (214, 48, 49),
                'pumpkin': (230, 126, 34)
            }
            
            # Draw grid
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x = start_x + col * (cell_size + padding)
                    y = start_y + row * (cell_size + padding)
                    
                    if idx < garden_info['slots']:
                        if idx < len(plants):
                            plant = plants[idx]
                            crop_type = plant['crop_type']
                            progress = plant['progress']
                            
                            # Soil color
                            soil_color = crop_colors.get(crop_type, (121, 85, 72))
                            draw.rounded_rectangle(
                                [x, y, x + cell_size, y + cell_size],
                                radius=15, fill=soil_color
                            )
                            
                            # Progress bar
                            progress_width = int(cell_size * (progress / 100))
                            draw.rectangle(
                                [x, y + cell_size - 10, x + progress_width, y + cell_size],
                                fill=tuple(COLORS["primary"])
                            )
                            
                            # Crop emoji
                            emoji = crop_emojis.get(crop_type, '🌱')
                            emoji_bbox = draw.textbbox((0, 0), emoji, font=font_medium)
                            emoji_x = x + (cell_size - (emoji_bbox[2] - emoji_bbox[0])) // 2
                            emoji_y = y + (cell_size - (emoji_bbox[3] - emoji_bbox[1])) // 2 - 10
                            draw.text((emoji_x, emoji_y), emoji, fill=(255, 255, 255), font=font_medium)
                            
                            # Progress text
                            progress_text = f"{int(progress)}%"
                            text_bbox = draw.textbbox((0, 0), progress_text, font=font_small)
                            text_x = x + (cell_size - (text_bbox[2] - text_bbox[0])) // 2
                            draw.text((text_x, y + 5), progress_text, fill=(255, 255, 255), font=font_small)
                            
                            # Crop name
                            name = crop_type[:8].title()
                            name_bbox = draw.textbbox((0, 0), name, font=font_small)
                            name_x = x + (cell_size - (name_bbox[2] - name_bbox[0])) // 2
                            draw.text((name_x, y + cell_size - 25), name, fill=(255, 255, 255), font=font_small)
                            
                            # Water drops
                            if plant['water_count'] > 0:
                                water_text = "💧" * min(plant['water_count'], 3)
                                water_bbox = draw.textbbox((0, 0), water_text, font=font_small)
                                water_x = x + 5
                                draw.text((water_x, y + 5), water_text, fill=tuple(COLORS["primary"]), font=font_small)
                        
                        else:
                            # Empty slot
                            draw.rounded_rectangle(
                                [x, y, x + cell_size, y + cell_size],
                                radius=15, fill=tuple(COLORS["secondary"]), outline=(99, 110, 114), width=2
                            )
                            draw.text(
                                (x + cell_size//2 - 10, y + cell_size//2 - 10),
                                "🟫", fill=(178, 190, 195), font=font_medium
                            )
                    
                    else:
                        # Locked slot
                        draw.rounded_rectangle(
                            [x, y, x + cell_size, y + cell_size],
                            radius=15, fill=(45, 52, 54), outline=tuple(COLORS["danger"]), width=2
                        )
                        draw.text(
                            (x + cell_size//2 - 10, y + cell_size//2 - 10),
                            "🔒", fill=tuple(COLORS["danger"]), font=font_medium
                        )
            
            # Stats at bottom
            stats_y = start_y + (grid_size * (cell_size + padding)) + 20
            
            stats = [
                f"Slots: {len(plants)}/{garden_info['slots']}",
                f"Ready: {sum(1 for p in plants if p['progress'] >= 100)}",
                f"Growing: {len(plants)}"
            ]
            
            for i, stat in enumerate(stats):
                draw.text((50, stats_y + i * 30), stat, fill=tuple(COLORS["primary"]), font=font_medium)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Garden sync error: {e}")
            return None
    
    async def generate_profile_card(self, user_data: Dict, family_count: int, 
                                  garden_info: Dict, stand_info: Optional[Dict]) -> Optional[bytes]:
        """Generate profile card image"""
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            return await asyncio.to_thread(
                self._generate_profile_card_sync,
                user_data, family_count, garden_info, stand_info
            )
        except Exception as e:
            logger.error(f"Profile card error: {e}")
            return None
    
    def _generate_profile_card_sync(self, user_data: Dict, family_count: int,
                                  garden_info: Dict, stand_info: Optional[Dict]) -> Optional[bytes]:
        """Synchronous profile card generation"""
        try:
            width, height = 600, 800
            img = Image.new('RGB', (width, height), tuple(COLORS["background"]))
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                font_large = ImageFont.truetype("arial.ttf", 32)
                font_medium = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Header
            header_height = 200
            draw.rectangle([0, 0, width, header_height], fill=tuple(COLORS["primary"]))
            
            # Profile picture area (circle)
            profile_x, profile_y = width // 2, header_height // 2
            draw.ellipse(
                [profile_x - 60, profile_y - 60, profile_x + 60, profile_y + 60],
                fill=(255, 255, 255), outline=tuple(COLORS["background"]), width=4
            )
            
            # User name
            name = user_data['first_name'][:20]
            name_bbox = draw.textbbox((0, 0), name, font=font_large)
            name_x = width // 2 - (name_bbox[2] - name_bbox[0]) // 2
            draw.text((name_x, header_height + 20), name, fill=(255, 255, 255), font=font_large)
            
            # Level
            level_text = f"Level {user_data.get('level', 1)}"
            level_bbox = draw.textbbox((0, 0), level_text, font=font_medium)
            level_x = width // 2 - (level_bbox[2] - level_bbox[0]) // 2
            draw.text((level_x, header_height + 60), level_text, fill=tuple(COLORS["success"]), font=font_medium)
            
            # Stats cards
            card_width = width - 100
            card_height = 80
            card_y = header_height + 100
            card_spacing = 20
            
            # Wealth card
            draw.rounded_rectangle(
                [50, card_y, 50 + card_width, card_y + card_height],
                radius=10, fill=tuple(COLORS["secondary"])
            )
            draw.text((70, card_y + 20), "💰 Wealth", fill=(253, 203, 110), font=font_medium)
            wealth = f"${user_data.get('cash', 0):,}"
            wealth_bbox = draw.textbbox((0, 0), wealth, font=font_medium)
            wealth_x = 50 + card_width - (wealth_bbox[2] - wealth_bbox[0]) - 30
            draw.text((wealth_x, card_y + 20), wealth, fill=(255, 255, 255), font=font_medium)
            
            # Family card
            card_y += card_height + card_spacing
            draw.rounded_rectangle(
                [50, card_y, 50 + card_width, card_y + card_height],
                radius=10, fill=tuple(COLORS["secondary"])
            )
            draw.text((70, card_y + 20), "👨‍👩‍👧‍👦 Family", fill=(255, 118, 117), font=font_medium)
            family_text = f"{family_count} members"
            family_bbox = draw.textbbox((0, 0), family_text, font=font_medium)
            family_x = 50 + card_width - (family_bbox[2] - family_bbox[0]) - 30
            draw.text((family_x, card_y + 20), family_text, fill=(255, 255, 255), font=font_medium)
            
            # Garden card
            card_y += card_height + card_spacing
            draw.rounded_rectangle(
                [50, card_y, 50 + card_width, card_y + card_height],
                radius=10, fill=tuple(COLORS["secondary"])
            )
            draw.text((70, card_y + 20), "🌾 Garden", fill=(0, 184, 148), font=font_medium)
            garden_text = f"{garden_info.get('slots', 0)} slots"
            garden_bbox = draw.textbbox((0, 0), garden_text, font=font_medium)
            garden_x = 50 + card_width - (garden_bbox[2] - garden_bbox[0]) - 30
            draw.text((garden_x, card_y + 20), garden_text, fill=(255, 255, 255), font=font_medium)
            
            # Stand card (if exists)
            if stand_info:
                card_y += card_height + card_spacing
                draw.rounded_rectangle(
                    [50, card_y, 50 + card_width, card_y + card_height],
                    radius=10, fill=tuple(COLORS["secondary"])
                )
                draw.text((70, card_y + 20), "⭐ Stand", fill=(162, 155, 254), font=font_medium)
                stand_text = stand_info.get('stand_name', 'None')
                stand_bbox = draw.textbbox((0, 0), stand_text, font=font_medium)
                stand_x = 50 + card_width - (stand_bbox[2] - stand_bbox[0]) - 30
                draw.text((stand_x, card_y + 20), stand_text, fill=(255, 255, 255), font=font_medium)
            
            # Footer
            footer_y = height - 50
            draw.text((50, footer_y), f"ID: {user_data['user_id']}", fill=(99, 110, 114), font=font_small)
            
            # Bio verification badge
            if user_data.get('bio_verified'):
                draw.text((width - 100, footer_y), "✅ Verified", fill=(0, 184, 148), font=font_small)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Profile card sync error: {e}")
            return None
    
    async def generate_stand_card(self, stand_data: Dict) -> Optional[bytes]:
        """Generate stand stats card using Pillow (no matplotlib)"""
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            return await asyncio.to_thread(
                self._generate_stand_card_sync,
                stand_data
            )
        except Exception as e:
            logger.error(f"Stand card error: {e}")
            return None
    
    def _generate_stand_card_sync(self, stand_data: Dict) -> Optional[bytes]:
        """Synchronous stand card generation with Pillow"""
        try:
            width, height = 600, 600
            img = Image.new('RGB', (width, height), tuple(COLORS["background"]))
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                font_large = ImageFont.truetype("arial.ttf", 32)
                font_medium = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Title
            stand_name = stand_data.get('stand_name', 'Unknown Stand')
            title = f"⭐ {stand_name}"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 30), title, fill=tuple(COLORS["primary"]), font=font_large)
            
            # Level
            level = stand_data.get('level', 1)
            level_text = f"Level {level}"
            level_bbox = draw.textbbox((0, 0), level_text, font=font_medium)
            level_x = (width - (level_bbox[2] - level_bbox[0])) // 2
            draw.text((level_x, 80), level_text, fill=tuple(COLORS["success"]), font=font_medium)
            
            # Stats hexagon visualization
            center_x, center_y = width // 2, height // 2 + 50
            radius = 150
            
            # Draw hexagon for stats visualization
            stats = {
                'Power': stand_data.get('power', 1),
                'Speed': stand_data.get('speed', 1),
                'Range': stand_data.get('range', 1),
                'Durability': stand_data.get('durability', 1),
                'Precision': stand_data.get('precision', 1),
                'Potential': stand_data.get('potential', 1)
            }
            
            # Draw stats as bars
            stat_y = 150
            stat_height = 20
            stat_spacing = 35
            
            for i, (stat_name, stat_value) in enumerate(stats.items()):
                y = stat_y + i * stat_spacing
                
                # Stat name
                draw.text((50, y), f"{stat_name}:", fill=tuple(COLORS["text"]), font=font_small)
                
                # Stat value
                value_text = f"{stat_value}/10"
                value_bbox = draw.textbbox((0, 0), value_text, font=font_small)
                value_x = width - value_bbox[2] - 50
                draw.text((value_x, y), value_text, fill=tuple(COLORS["text"]), font=font_small)
                
                # Progress bar
                bar_width = 300
                bar_x = 150
                fill_width = int(bar_width * (stat_value / 10))
                
                # Background
                draw.rectangle([bar_x, y, bar_x + bar_width, y + stat_height], 
                             fill=tuple(COLORS["secondary"]), outline=tuple(COLORS["border"]))
                
                # Fill
                draw.rectangle([bar_x, y, bar_x + fill_width, y + stat_height], 
                             fill=tuple(COLORS["primary"]))
            
            # Experience
            exp = stand_data.get('experience', 0)
            exp_text = f"Experience: {exp}/100"
            exp_bbox = draw.textbbox((0, 0), exp_text, font=font_medium)
            exp_x = (width - (exp_bbox[2] - exp_bbox[0])) // 2
            draw.text((exp_x, height - 80), exp_text, fill=tuple(COLORS["warning"]), font=font_medium)
            
            # Progress bar for experience
            exp_bar_width = 400
            exp_bar_x = (width - exp_bar_width) // 2
            exp_fill_width = int(exp_bar_width * (exp / 100))
            
            draw.rectangle([exp_bar_x, height - 50, exp_bar_x + exp_bar_width, height - 30], 
                         fill=tuple(COLORS["secondary"]), outline=tuple(COLORS["border"]))
            draw.rectangle([exp_bar_x, height - 50, exp_bar_x + exp_fill_width, height - 30], 
                         fill=tuple(COLORS["success"]))
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Stand card sync error: {e}")
            return None
    
    async def get_random_catbox_gif(self, command: str) -> str:
        """Get random GIF for command, fallback to defaults"""
        # Try database first
        gif_url = await db.get_random_gif(command)
        
        if gif_url:
            return gif_url
        
        # Fallback to defaults
        default_gifs = self.default_gifs.get(command, [])
        if default_gifs:
            return random.choice(default_gifs)
        
        # Ultimate fallback
        return "https://media.tenor.com/5C8aK3q1hZsAAAAd/robbery-steal.gif"

# ============================================================================
# BOT INITIALIZATION
# ============================================================================
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize image generator
img_gen = ImageGenerator(bot)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
async def check_cooldown(user_id: int, action: str) -> Tuple[bool, int]:
    """Check if user has cooldown for action"""
    user = await db.get_user(user_id)
    if not user:
        return True, 0
    
    cooldown_times = {
        'rob': 300,    # 5 minutes
        'kill': 60,    # 1 minute
        'hug': 30,     # 30 seconds
        'daily': 86400 # 24 hours
    }
    
    cooldown_field = f"{action}_cooldown"
    last_time = user.get(cooldown_field)
    
    if not last_time:
        return False, 0
    
    try:
        last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        elapsed = (datetime.now() - last_dt).total_seconds()
        cooldown = cooldown_times.get(action, 60)
        
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            return True, remaining
    except:
        pass
    
    return False, 0

async def update_cooldown(user_id: int, action: str):
    """Update cooldown timestamp"""
    async with db.lock:
        try:
            await db.conn.execute(
                f"UPDATE users SET {action}_cooldown = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await db.conn.commit()
        except Exception as e:
            logger.error(f"Update cooldown error: {e}")

async def transfer_currency(from_id: int, to_id: int, amount: int, currency: str = 'cash') -> bool:
    """Transfer currency between users"""
    if amount <= 0:
        return False
    
    # Check sender balance
    from_user = await db.get_user(from_id)
    if not from_user:
        return False
    
    current_balance = from_user.get(currency, 0)
    if current_balance < amount:
        return False
    
    # Update balances
    success1 = await db.update_currency(from_id, currency, -amount)
    success2 = await db.update_currency(to_id, currency, amount)
    
    if success1 and success2:
        # Log transaction
        await db.log_transaction(
            from_id=from_id, to_id=to_id,
            amount=amount, currency=currency,
            type='transfer', description=f"Transfer"
        )
        return True
    
    return False

async def check_bio_verification(user_id: int) -> bool:
    """Check if user has bot in bio"""
    try:
        chat = await bot.get_chat(user_id)
        bio = getattr(chat, 'bio', '') or ''
        return BOT_USERNAME.lower() in bio.lower() or "Familly_TreeBot" in bio
    except Exception as e:
        logger.error(f"Bio check error: {e}")
        return False

async def update_bio_verification(user_id: int):
    """Update bio verification status in database"""
    has_bio = await check_bio_verification(user_id)
    async with db.lock:
        try:
            await db.conn.execute(
                "UPDATE users SET bio_verified = ? WHERE user_id = ?",
                (1 if has_bio else 0, user_id)
            )
            await db.conn.commit()
        except Exception as e:
            logger.error(f"Update bio verification error: {e}")
    return has_bio

async def send_to_log_channel(text: str, photo: bytes = None):
    """Send message to log channel"""
    try:
        if photo:
            await bot.send_photo(
                chat_id=LOG_CHANNEL,
                photo=BufferedInputFile(photo, filename="log.png"),
                caption=text[:1000],
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                chat_id=LOG_CHANNEL,
                text=text[:4000],
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Log channel error: {e}")

# ============================================================================
# START COMMAND
# ============================================================================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Update last active
    await db.update_last_active(message.from_user.id)
    
    welcome_text = f"""
✨ <b>WELCOME TO FAMILY TREE BOT!</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🌳 <b>Build your virtual family</b>
🌾 <b>Grow and harvest crops</b>
💰 <b>Trade in the marketplace</b>
🎮 <b>Play exciting mini-games</b>
⚔️ <b>Engage in PvP battles</b>
⭐ <b>Awaken your Stand</b>

🚀 <b>Get started:</b>
<code>/daily</code> - Claim daily bonus
<code>/me</code> - View your profile
<code>/garden</code> - Start farming
<code>/family</code> - View family tree

📸 <b>Now with IMAGE visualizations!</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Quick Start", callback_data="quick_start")],
        [InlineKeyboardButton(text="📋 All Commands", callback_data="all_commands")],
        [InlineKeyboardButton(text="👥 Add to Group", url=f"https://t.me/{BOT_USERNAME[1:]}?startgroup=true")],
        [InlineKeyboardButton(text="❓ Help", url=SUPPORT_CHAT)]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    # Log new user
    await send_to_log_channel(
        f"👤 <b>New User</b>\n"
        f"• Name: {message.from_user.first_name}\n"
        f"• ID: <code>{message.from_user.id}</code>\n"
        f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# ============================================================================
# FAMILY COMMANDS
# ============================================================================
@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Show family tree"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    # Try to generate image
    if PILLOW_AVAILABLE and family:
        loading_msg = await message.answer("🖼️ Generating family tree...")
        
        image_bytes = await img_gen.generate_family_tree(
            message.from_user.id,
            user['first_name'],
            family
        )
        
        if image_bytes:
            await message.answer_photo(
                BufferedInputFile(image_bytes, filename="family_tree.png"),
                caption=f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

👨‍👩‍👧‍👦 <b>Family Members:</b> {len(family)}

💝 <b>Relationships:</b>
{', '.join(set(m['relation_type'] for m in family))}

💡 <b>Family commands:</b>
• <code>/adopt</code> - Adopt someone (reply)
• <code>/marry</code> - Marry someone (reply)
• <code>/divorce</code> - End marriage
• <code>/disown</code> - Remove family member
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

💡 <b>How to grow your family:</b>
1. Reply to someone with <code>/adopt</code>
2. Wait for them to accept
3. Build your family empire!

👑 <b>Benefits:</b>
• Daily bonus increases
• Family quests
• Inheritance system
""", parse_mode=ParseMode.HTML)
        return
    
    tree_text = f"""
🌳 <b>FAMILY TREE OF {user['first_name'].upper()}</b>

└─ You
"""
    
    for member in family:
        emoji = {
            'parent': '👴',
            'spouse': '💑', 
            'child': '👶',
            'sibling': '👫'
        }.get(member['relation_type'], '👤')
        
        tree_text += f"   ├─ {emoji} {member['other_name']} ({member['relation_type']})\n"
    
    tree_text += f"""

📊 <b>Statistics:</b>
• Members: {len(family)}
• Daily Bonus: +${len(family) * 100}
"""
    
    await message.answer(tree_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone"""
    if not message.reply_to_message:
        await message.answer("""
👶 <b>ADOPT SOMEONE</b>

To adopt someone as your child:

1. <b>Reply to their message</b> with <code>/adopt</code>
2. Wait for them to accept

💡 <b>Requirements:</b>
• Both must be bot users
• Cannot adopt yourself
• Target must accept
""", parse_mode=ParseMode.HTML)
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    # Check if target exists
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Check if already family
    family = await db.get_family(message.from_user.id)
    for member in family:
        if member['other_id'] == target.id:
            await message.answer(f"❌ {target.first_name} is already in your family!")
            return
    
    # Add relation
    success = await db.add_family_relation(message.from_user.id, target.id, 'parent')
    
    if not success:
        await message.answer("❌ Failed to adopt!")
        return
    
    await message.answer(f"""
✅ <b>ADOPTION COMPLETE!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
📅 {datetime.now().strftime('%Y-%m-%d')}

💡 <b>Benefits activated:</b>
• Daily bonus increased
• Family quests available
• Inheritance rights
""", parse_mode=ParseMode.HTML)
    
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
    
    # Log adoption
    await send_to_log_channel(
        f"👶 <b>Adoption</b>\n"
        f"• Parent: {message.from_user.first_name}\n"
        f"• Child: {target.first_name}\n"
        f"• Time: {datetime.now().strftime('%H:%M:%S')}"
    )

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
• Both must be single
• Cannot marry yourself
• Target must accept
""", parse_mode=ParseMode.HTML)
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Check if already married
    family = await db.get_family(message.from_user.id)
    for member in family:
        if member['other_id'] == target.id and member['relation_type'] == 'spouse':
            await message.answer(f"❌ You're already married to {target.first_name}!")
            return
    
    # Add relation
    success = await db.add_family_relation(message.from_user.id, target.id, 'spouse')
    
    if not success:
        await message.answer("❌ Failed to marry!")
        return
    
    # Cost for wedding
    wedding_cost = 500
    user = await db.get_user(message.from_user.id)
    if user['cash'] < wedding_cost:
        await message.answer(f"❌ Need ${wedding_cost:,} for wedding ceremony!")
        await db.remove_family_relation(message.from_user.id, target.id, 'spouse')
        return
    
    await db.update_currency(message.from_user.id, 'cash', -wedding_cost)
    
    # Wedding gifts
    await db.update_currency(message.from_user.id, 'gold', 50)
    await db.update_currency(target.id, 'gold', 50)
    
    await message.answer(f"""
💍 <b>MARRIAGE COMPLETE!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Cost: <b>${wedding_cost:,}</b>
🎁 Gift: <b>50 🪙 Gold each</b>
📅 {datetime.now().strftime('%Y-%m-%d')}

🎉 <b>Congratulations!</b>
• Couple bonuses activated
• Shared daily rewards
• Family features unlocked
""", parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
💍 <b>MARRIAGE PROPOSAL ACCEPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 Relationship: Spouses
🎁 Gift: <b>50 🪙 Gold</b>

🎉 You are now married!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
    
    # Log marriage
    await send_to_log_channel(
        f"💍 <b>Marriage</b>\n"
        f"• Spouse 1: {message.from_user.first_name}\n"
        f"• Spouse 2: {target.first_name}\n"
        f"• Time: {datetime.now().strftime('%H:%M:%S')}"
    )

@dp.message(Command("divorce"))
async def cmd_divorce(message: Message):
    """Divorce your spouse"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    # Find spouse
    family = await db.get_family(message.from_user.id)
    spouse = None
    
    for member in family:
        if member['relation_type'] == 'spouse':
            spouse = member
            break
    
    if not spouse:
        await message.answer("❌ You're not married!")
        return
    
    # Divorce cost
    divorce_cost = 1000
    if user['cash'] < divorce_cost:
        await message.answer(f"❌ Need ${divorce_cost:,} for divorce papers!")
        return
    
    # Confirm
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, Divorce", callback_data=f"divorce_yes_{spouse['other_id']}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="divorce_no")
        ]
    ])
    
    await message.answer(
        f"💔 <b>DIVORCE CONFIRMATION</b>\n\n"
        f"Are you sure you want to divorce <b>{spouse['other_name']}</b>?\n"
        f"Cost: <b>${divorce_cost:,}</b>\n\n"
        f"⚠️ This action cannot be undone!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data.startswith("divorce_yes_"))
async def callback_divorce_yes(callback: CallbackQuery):
    """Handle divorce confirmation"""
    try:
        spouse_id = int(callback.data.split("_")[2])
        
        # Remove marriage
        success = await db.remove_family_relation(callback.from_user.id, spouse_id, 'spouse')
        
        if not success:
            await callback.answer("❌ Divorce failed!")
            return
        
        # Charge divorce fee
        await db.update_currency(callback.from_user.id, 'cash', -1000)
        
        # Get spouse name
        spouse_user = await db.get_user(spouse_id)
        spouse_name = spouse_user['first_name'] if spouse_user else "Unknown"
        
        await callback.message.edit_text(
            f"💔 <b>DIVORCE COMPLETED</b>\n\n"
            f"You have divorced <b>{spouse_name}</b>.\n"
            f"Cost: <b>$1,000</b>\n\n"
            f"Relationship terminated.",
            parse_mode=ParseMode.HTML
        )
        
        # Notify spouse
        try:
            await bot.send_message(
                spouse_id,
                f"💔 <b>DIVORCE NOTICE</b>\n\n"
                f"<b>{callback.from_user.first_name}</b> has divorced you.\n"
                f"Your marriage has been terminated.",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
    except Exception as e:
        logger.error(f"Divorce error: {e}")
        await callback.answer("❌ Error!")

@dp.callback_query(F.data == "divorce_no")
async def callback_divorce_no(callback: CallbackQuery):
    """Cancel divorce"""
    await callback.message.edit_text(
        "❌ Divorce cancelled.",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("disown"))
async def cmd_disown(message: Message):
    """Disown a family member"""
    if not message.reply_to_message:
        await message.answer("""
👨‍👩‍👧‍👦 <b>DISOWN FAMILY MEMBER</b>

To disown someone:

1. <b>Reply to their message</b> with <code>/disown</code>
2. Confirm the action

⚠️ <b>Warning:</b> This removes them from your family permanently!
""", parse_mode=ParseMode.HTML)
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot disown yourself!")
        return
    
    # Check if they're family
    family = await db.get_family(message.from_user.id)
    target_relation = None
    
    for member in family:
        if member['other_id'] == target.id:
            target_relation = member
            break
    
    if not target_relation:
        await message.answer(f"❌ {target.first_name} is not in your family!")
        return
    
    # Confirm
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Remove", callback_data=f"disown_yes_{target.id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="disown_no")
        ]
    ])
    
    await message.answer(
        f"⚠️ <b>DISOWN CONFIRMATION</b>\n\n"
        f"Remove <b>{target.first_name}</b> from your family?\n"
        f"Relationship: <b>{target_relation['relation_type']}</b>\n\n"
        f"⚠️ This action cannot be undone!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data.startswith("disown_yes_"))
async def callback_disown_yes(callback: CallbackQuery):
    """Handle disown confirmation"""
    try:
        target_id = int(callback.data.split("_")[2])
        
        # Remove all relations
        family = await db.get_family(callback.from_user.id)
        for member in family:
            if member['other_id'] == target_id:
                await db.remove_family_relation(callback.from_user.id, target_id, member['relation_type'])
        
        # Get target name
        target_user = await db.get_user(target_id)
        target_name = target_user['first_name'] if target_user else "Unknown"
        
        await callback.message.edit_text(
            f"👨‍👩‍👧‍👦 <b>DISOWNED</b>\n\n"
            f"You have disowned <b>{target_name}</b>.\n"
            f"They are no longer part of your family.",
            parse_mode=ParseMode.HTML
        )
        
        # Notify target
        try:
            await bot.send_message(
                target_id,
                f"👨‍👩‍👧‍👦 <b>FAMILY UPDATE</b>\n\n"
                f"<b>{callback.from_user.first_name}</b> has disowned you.\n"
                f"You are no longer part of their family.",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
    except Exception as e:
        logger.error(f"Disown error: {e}")
        await callback.answer("❌ Error!")

@dp.callback_query(F.data == "disown_no")
async def callback_disown_no(callback: CallbackQuery):
    """Cancel disown"""
    await callback.message.edit_text(
        "❌ Disown cancelled.",
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# GARDEN COMMANDS
# ============================================================================
@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Show garden"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    garden_info = await db.get_garden_info(message.from_user.id)
    plants = await db.get_growing_plants(message.from_user.id)
    
    # Try to generate image
    if PILLOW_AVAILABLE:
        loading_msg = await message.answer("🖼️ Generating garden...")
        
        image_bytes = await img_gen.generate_garden_image(
            message.from_user.id,
            garden_info,
            plants
        )
        
        if image_bytes:
            # Get barn items
            barn_items = await db.get_barn_items(message.from_user.id)
            barn_text = ""
            if barn_items:
                barn_text = "\n🏠 <b>Barn Storage:</b>\n"
                for crop_type, quantity in barn_items[:5]:
                    emoji = {
                        'carrot': '🥕', 'tomato': '🍅', 'potato': '🥔',
                        'eggplant': '🍆', 'corn': '🌽', 'pepper': '🫑',
                        'watermelon': '🍉', 'pumpkin': '🎃'
                    }.get(crop_type, '📦')
                    barn_text += f"• {emoji} {crop_type.title()}: {quantity}\n"
            
            await message.answer_photo(
                BufferedInputFile(image_bytes, filename="garden.png"),
                caption=f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(plants)}/{garden_info['slots']}
• Growing: {len(plants)} crops
• Ready: {sum(1 for p in plants if p['progress'] >= 100)} crops
{barn_text}

💡 <b>Commands:</b>
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
<code>/barn</code> - View storage
""",
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
    
    # Text version
    garden_text = f"""
🌾 <b>{user['first_name']}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(plants)}/{garden_info['slots']}
• Growing: {len(plants)} crops
• Ready: {sum(1 for p in plants if p['progress'] >= 100)} crops

🌱 <b>Growing Now:</b>
"""
    
    crop_emojis = {
        'carrot': '🥕', 'tomato': '🍅', 'potato': '🥔',
        'eggplant': '🍆', 'corn': '🌽', 'pepper': '🫑',
        'watermelon': '🍉', 'pumpkin': '🎃'
    }
    
    for plant in plants[:5]:
        emoji = crop_emojis.get(plant['crop_type'], '🌱')
        progress = plant['progress']
        
        if progress >= 100:
            status = "✅ Ready!"
        else:
            remaining = max(0, plant['grow_time'] - plant['hours_passed'])
            status = f"⏰ {progress:.0f}% ({remaining:.1f}h left)"
        
        garden_text += f"• {emoji} {plant['crop_type'].title()}: {status}\n"
    
    garden_text += f"""

💡 <b>Crops Available:</b>
• 🥕 Carrot - 2h growth
• 🍅 Tomato - 3h growth  
• 🥔 Potato - 2.5h growth
• 🍆 Eggplant - 4h growth
• 🌽 Corn - 5h growth

<code>/plant carrot 3</code> - Plant 3 carrots
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
🥕 Carrot - $10 (2h)
🍅 Tomato - $15 (3h)  
🥔 Potato - $8 (2.5h)
🍆 Eggplant - $20 (4h)
🌽 Corn - $12 (5h)
🫑 Pepper - $25 (6h)
🍉 Watermelon - $30 (7h)
🎃 Pumpkin - $40 (8h)

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
    
    # Valid crops
    valid_crops = ['carrot', 'tomato', 'potato', 'eggplant', 'corn', 'pepper', 'watermelon', 'pumpkin']
    if crop_type not in valid_crops:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(valid_crops[:5])}")
        return
    
    if quantity < 1 or quantity > 9:
        await message.answer("❌ Quantity must be 1-9!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    # Crop prices
    crop_prices = {
        'carrot': 10, 'tomato': 15, 'potato': 8, 'eggplant': 20,
        'corn': 12, 'pepper': 25, 'watermelon': 30, 'pumpkin': 40
    }
    
    # Check cost
    cost = crop_prices[crop_type] * quantity
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
    
    # Crop emojis
    crop_emojis = {
        'carrot': '🥕', 'tomato': '🍅', 'potato': '🥔',
        'eggplant': '🍆', 'corn': '🌽', 'pepper': '🫑',
        'watermelon': '🍉', 'pumpkin': '🎃'
    }
    
    # Grow times
    grow_times = {
        'carrot': 2, 'tomato': 3, 'potato': 2.5, 'eggplant': 4,
        'corn': 5, 'pepper': 6, 'watermelon': 7, 'pumpkin': 8
    }
    
    emoji = crop_emojis.get(crop_type, "🌱")
    grow_time = grow_times[crop_type]
    
    await message.answer(f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{emoji} Crop: <b>{crop_type.title()}</b>
🔢 Quantity: <b>{quantity}</b>
💰 Cost: <b>${cost:,}</b>
⏰ Grow Time: <b>{grow_time} hours</b>

🌱 Now growing in your garden!
💡 Use <code>/garden</code> to check progress.
""", parse_mode=ParseMode.HTML)
    
    # Log planting
    await db.log_transaction(
        from_id=message.from_user.id, to_id=None,
        amount=cost, currency='cash',
        type='garden_plant', description=f"Plant {quantity} {crop_type}"
    )

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest ready crops"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    # Harvest plants
    total_yield, harvested = await db.harvest_plants(message.from_user.id)
    
    if total_yield == 0:
        await message.answer("❌ No crops ready for harvest!")
        return
    
    # Build harvest message
    crop_emojis = {
        'carrot': '🥕', 'tomato': '🍅', 'potato': '🥔',
        'eggplant': '🍆', 'corn': '🌽', 'pepper': '🫑',
        'watermelon': '🍉', 'pumpkin': '🎃'
    }
    
    harvest_text = f"""
✅ <b>HARVEST COMPLETE!</b>

📦 Total Yield: <b>{total_yield} items</b>

🌾 <b>Harvested:</b>
"""
    
    for item in harvested:
        emoji = crop_emojis.get(item['crop_type'], '📦')
        harvest_text += f"• {emoji} {item['crop_type'].title()}: {item['yield']}\n"
    
    harvest_text += f"""

💡 Crops stored in barn.
💡 Sell with <code>/sell [crop] [quantity]</code>
"""
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)
    
    # Log harvest
    await db.log_transaction(
        from_id=None, to_id=message.from_user.id,
        amount=total_yield, currency='crops',
        type='garden_harvest', description=f"Harvest {len(harvested)} types"
    )

@dp.message(Command("barn"))
async def cmd_barn(message: Message):
    """View barn storage"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    barn_items = await db.get_barn_items(message.from_user.id)
    
    if not barn_items:
        await message.answer("""
🏠 <b>YOUR BARN</b>

📦 Empty - No crops stored yet!

💡 Harvest crops with <code>/harvest</code>
💡 Sell crops with <code>/sell [crop] [quantity]</code>
""", parse_mode=ParseMode.HTML)
        return
    
    barn_text = """
🏠 <b>YOUR BARN</b>

📦 <b>Stored Crops:</b>
"""
    
    crop_emojis = {
        'carrot': '🥕', 'tomato': '🍅', 'potato': '🥔',
        'eggplant': '🍆', 'corn': '🌽', 'pepper': '🫑',
        'watermelon': '🍉', 'pumpkin': '🎃'
    }
    
    for crop_type, quantity in barn_items[:10]:
        emoji = crop_emojis.get(crop_type, '📦')
        barn_text += f"• {emoji} {crop_type.title()}: {quantity}\n"
    
    barn_text += f"""

💡 <b>Commands:</b>
<code>/sell [crop] [quantity]</code> - Sell crops
<code>/sellall</code> - Sell everything
"""
    
    if len(barn_items) > 10:
        barn_text += f"\n📋 ... and {len(barn_items) - 10} more items"
    
    await message.answer(barn_text, parse_mode=ParseMode.HTML)

# ============================================================================
# DAILY & PROFILE COMMANDS
# ============================================================================
@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    # Check cooldown
    on_cooldown, remaining = await check_cooldown(message.from_user.id, 'daily')
    if on_cooldown:
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await message.answer(f"❌ Come back in {hours}h {minutes}m!")
        return
    
    # Check bio verification after 5 claims
    daily_count = user.get('daily_count', 0) + 1
    
    if daily_count >= 5 and not user.get('bio_verified'):
        # Check bio
        has_bio = await update_bio_verification(message.from_user.id)
        
        if not has_bio:
            await message.answer(f"""
⚠️ <b>BIO VERIFICATION REQUIRED!</b>

You've claimed daily bonuses {daily_count} times!

1. <b>Edit your Telegram Bio</b>
2. <b>Add:</b> <code>@Familly_TreeBot</code>
3. <b>Use</b> <code>/daily</code> again

✅ <b>After verification:</b>
• 2x daily rewards
• Premium features
• Higher limits

🔒 <b>Prevents bot abuse</b>
""", parse_mode=ParseMode.HTML)
            return
    
    # Calculate bonus
    base_bonus = random.randint(500, 1500)
    family_bonus = len(await db.get_family(message.from_user.id)) * 100
    bio_multiplier = 2 if user.get('bio_verified') else 1
    
    total_bonus = (base_bonus + family_bonus) * bio_multiplier
    
    # Gemstone
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    gemstone = random.choice(gemstones)
    
    # Update user
    await db.update_currency(message.from_user.id, "cash", total_bonus)
    await db.update_currency(message.from_user.id, "tokens", 5)
    
    # Update daily info
    async with db.lock:
        await db.conn.execute(
            """UPDATE users 
            SET last_daily = CURRENT_TIMESTAMP, 
                daily_count = ?,
                gemstone = ?
            WHERE user_id = ?""",
            (daily_count, gemstone, message.from_user.id)
        )
        await db.conn.commit()
    
    # Set cooldown
    await update_cooldown(message.from_user.id, 'daily')
    
    daily_text = f"""
🎉 <b>DAILY BONUS CLAIMED!</b>

💰 <b>Rewards:</b>
• Base: <b>${base_bonus:,}</b>
• Family: <b>${family_bonus:,}</b>
• Multiplier: <b>{bio_multiplier}x</b>
• <b>Total: ${total_bonus:,}</b>

💎 <b>Today's Gemstone:</b> <b>{gemstone}</b>
🎁 <b>Bonus:</b> +5 🌱 Tokens

📊 <b>Daily Claims:</b> {daily_count}
{'✅ Bio verified (2x rewards!)' if bio_multiplier > 1 else '❌ Add @Familly_TreeBot to bio for 2x!'}
"""
    
    await message.answer(daily_text, parse_mode=ParseMode.HTML)
    
    # Log daily claim
    await send_to_log_channel(
        f"🎉 <b>Daily Claim</b>\n"
        f"• User: {message.from_user.first_name}\n"
        f"• Amount: ${total_bonus:,}\n"
        f"• Time: {datetime.now().strftime('%H:%M:%S')}"
    )

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """Show profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    # Get user data
    family = await db.get_family(message.from_user.id)
    garden_info = await db.get_garden_info(message.from_user.id)
    stand_info = await db.get_stand(message.from_user.id)
    
    # Try to generate image
    if PILLOW_AVAILABLE:
        loading_msg = await message.answer("🖼️ Generating profile...")
        
        image_bytes = await img_gen.generate_profile_card(
            user, len(family), garden_info, stand_info
        )
        
        if image_bytes:
            # Additional stats text
            stats_text = f"""
📊 <b>Additional Stats:</b>

💵 Cash: <b>${user.get('cash', 0):,}</b>
🪙 Gold: <b>{user.get('gold', 0):,}</b>
👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
⭐ Credits: <b>{user.get('credits', 0):,}</b>
🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

👑 Level: <b>{user.get('level', 1)}</b>
🎯 Reputation: <b>{user.get('reputation', 100)}/200</b>
👨‍👩‍👧‍👦 Family: <b>{len(family)} members</b>
🌾 Garden: <b>{garden_info.get('slots', 9)} slots</b>
{'⭐ Stand: ' + stand_info.get('stand_name', 'None') if stand_info else '❌ No Stand'}

📅 Joined: {user.get('created_at', 'Unknown')[:10]}
"""
            
            await message.answer_photo(
                BufferedInputFile(image_bytes, filename="profile.png"),
                caption=stats_text,
                parse_mode=ParseMode.HTML
            )
            await loading_msg.delete()
            return
    
    # Text version
    profile_text = f"""
🏆 <b>PROFILE OF {user['first_name'].upper()}</b>

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

📊 <b>Stats:</b>
• 👑 Level: <b>{user.get('level', 1)}</b>
• 🎯 Reputation: <b>{user.get('reputation', 100)}/200</b>
• 👨‍👩‍👧‍👦 Family: <b>{len(family)} members</b>
• 🌾 Garden: <b>{garden_info.get('slots', 9)}/{garden_info.get('barn_capacity', 50)}</b>
• ⭐ Stand: <b>{stand_info.get('stand_name', 'None') if stand_info else 'None'}</b>

✅ Bio Verified: {'Yes ✅' if user.get('bio_verified') else 'No ❌'}
💎 Gemstone: {user.get('gemstone', 'None')}
📅 Joined: {user.get('created_at', 'Unknown')[:10]}
"""
    
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

# ============================================================================
# REACTION COMMANDS WITH CATBOX GIFS
# ============================================================================
@dp.message(Command("rob"))
async def cmd_rob(message: Message):
    """Rob someone"""
    if not message.reply_to_message:
        await message.answer("""
💰 <b>ROB SOMEONE</b>

To rob someone:

1. <b>Reply to their message</b> with <code>/rob</code>
2. Try to steal their money

🎲 <b>Success depends on:</b>
• Your level vs their level
• Random chance (30-70%)
• Cooldown: 5 minutes

💡 Steal 10-50% of their cash on success!
""", parse_mode=ParseMode.HTML)
        return
    
    robber = message.from_user
    target = message.reply_to_message.from_user
    
    if target.id == robber.id:
        await message.answer("❌ You cannot rob yourself!")
        return
    
    # Check cooldown
    on_cooldown, remaining = await check_cooldown(robber.id, 'rob')
    if on_cooldown:
        minutes = remaining // 60
        seconds = remaining % 60
        await message.answer(f"❌ Robbing cooldown! Wait {minutes}m {seconds}s")
        return
    
    # Get users
    robber_user = await db.get_user(robber.id)
    target_user = await db.get_user(target.id)
    
    if not robber_user or not target_user:
        await message.answer("❌ Both users must use /start first!")
        return
    
    # Check if target has money
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor to rob!")
        return
    
    # Calculate success chance
    robber_level = robber_user.get('level', 1)
    target_level = target_user.get('level', 1)
    level_diff = robber_level - target_level
    
    base_chance = 50
    level_bonus = level_diff * 5
    success_chance = min(90, max(10, base_chance + level_bonus))
    
    # Roll for success
    success = random.randint(1, 100) <= success_chance
    
    # Get CatBox GIF
    gif_url = await img_gen.get_random_catbox_gif('rob')
    
    if success:
        # Calculate steal amount (10-50% of target's cash)
        steal_percent = random.randint(10, 50)
        steal_amount = int(target_user['cash'] * steal_percent / 100)
        
        # Minimum and maximum
        steal_amount = max(100, min(steal_amount, 10000))
        
        # Transfer money
        transfer_success = await transfer_currency(target.id, robber.id, steal_amount, 'cash')
        
        if transfer_success:
            # Update game stats
            await db.update_game_stats(robber.id, 'rob', won=True)
            
            await message.answer_animation(
                animation=gif_url,
                caption=f"""
✅ <b>ROB SUCCESSFUL!</b>

👤 Robber: <b>{robber.first_name}</b>
🎯 Target: <b>{target.first_name}</b>
💰 Stole: <b>${steal_amount:,}</b>
📊 Chance: <b>{success_chance}%</b>

🎲 Lucky roll! Better luck next time {target.first_name}!
⏰ Cooldown: 5 minutes
""",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer("❌ Rob failed - transfer error!")
    else:
        # Rob failed - robber pays fine
        fine_amount = min(500, robber_user['cash'] // 10)
        if fine_amount > 0:
            await db.update_currency(robber.id, 'cash', -fine_amount)
            await db.update_currency(target.id, 'cash', fine_amount // 2)
        
        # Update game stats
        await db.update_game_stats(robber.id, 'rob', won=False)
        
        await message.answer_animation(
            animation=gif_url,
            caption=f"""
❌ <b>ROB FAILED!</b>

👤 Robber: <b>{robber.first_name}</b>
🎯 Target: <b>{target.first_name}</b>
📊 Chance: <b>{success_chance}%</b>
💸 Fine: <b>${fine_amount:,}</b>

🚓 Caught by police! {target.first_name} gets ${fine_amount//2:,} reward!
⏰ Cooldown: 5 minutes
""",
            parse_mode=ParseMode.HTML
        )
    
    # Set cooldown
    await update_cooldown(robber.id, 'rob')
    
    # Log rob attempt
    await db.log_transaction(
        from_id=robber.id, to_id=target.id if success else None,
        amount=steal_amount if success else fine_amount,
        currency='cash', type='rob',
        description=f"Rob {'success' if success else 'fail'}"
    )

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone (fun command)"""
    if not message.reply_to_message:
        await message.answer("""
⚔️ <b>KILL SOMEONE</b>

To kill someone:

1. <b>Reply to their message</b> with <code>/kill</code>
2. Send a funny kill GIF

🎮 <b>This is just for fun!</b>
No real damage, just entertainment.

⏰ Cooldown: 1 minute
""", parse_mode=ParseMode.HTML)
        return
    
    killer = message.from_user
    target = message.reply_to_message.from_user
    
    if target.id == killer.id:
        await message.answer("❌ You cannot kill yourself!")
        return
    
    # Check cooldown
    on_cooldown, remaining = await check_cooldown(killer.id, 'kill')
    if on_cooldown:
        await message.answer(f"❌ Killing cooldown! Wait {remaining}s")
        return
    
    # Get CatBox GIF
    gif_url = await img_gen.get_random_catbox_gif('kill')
    
    # Update game stats
    await db.update_game_stats(killer.id, 'kill')
    
    # Set cooldown
    await update_cooldown(killer.id, 'kill')
    
    # Kill messages
    kill_messages = [
        f"{killer.first_name} brutally eliminated {target.first_name}! 💀",
        f"{target.first_name} was no match for {killer.first_name}'s skills! ⚔️",
        f"RIP {target.first_name} ✝️ Killed by {killer.first_name}",
        f"{killer.first_name} sent {target.first_name} to the shadow realm! 👻",
        f"Game over for {target.first_name}! Winner: {killer.first_name} 🏆"
    ]
    
    await message.answer_animation(
        animation=gif_url,
        caption=f"""
⚔️ <b>KILL CONFIRMED!</b>

🗡️ Killer: <b>{killer.first_name}</b>
💀 Victim: <b>{target.first_name}</b>

{random.choice(kill_messages)}

⏰ Cooldown: 1 minute
""",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("hug"))
async def cmd_hug(message: Message):
    """Hug someone"""
    if not message.reply_to_message:
        await message.answer("""
🤗 <b>HUG SOMEONE</b>

To hug someone:

1. <b>Reply to their message</b> with <code>/hug</code>
2. Send a cute hug GIF

💖 <b>Spread love and positivity!</b>
Hugs increase friendship points.

⏰ Cooldown: 30 seconds
""", parse_mode=ParseMode.HTML)
        return
    
    hugger = message.from_user
    target = message.reply_to_message.from_user
    
    if target.id == hugger.id:
        await message.answer("❌ You cannot hug yourself!")
        return
    
    # Check cooldown
    on_cooldown, remaining = await check_cooldown(hugger.id, 'hug')
    if on_cooldown:
        await message.answer(f"❌ Hugging cooldown! Wait {remaining}s")
        return
    
    # Get CatBox GIF
    gif_url = await img_gen.get_random_catbox_gif('hug')
    
    # Update game stats
    await db.update_game_stats(hugger.id, 'hug')
    
    # Small reward for hug
    await db.update_currency(hugger.id, 'credits', 5)
    await db.update_currency(target.id, 'credits', 5)
    
    # Set cooldown
    await update_cooldown(hugger.id, 'hug')
    
    # Hug messages
    hug_messages = [
        f"{hugger.first_name} gives {target.first_name} a warm hug! 💖",
        f"A big bear hug from {hugger.first_name} to {target.first_name}! 🐻",
        f"{target.first_name} feels loved thanks to {hugger.first_name}'s hug! 💕",
        f"Group hug! {hugger.first_name} embraces {target.first_name}! 👫",
        f"Hearts everywhere! {hugger.first_name} hugs {target.first_name}! ❤️"
    ]
    
    await message.answer_animation(
        animation=gif_url,
        caption=f"""
🤗 <b>HUG DELIVERED!</b>

👤 Hugger: <b>{hugger.first_name}</b>
🎯 Target: <b>{target.first_name}</b>

{random.choice(hug_messages)}

🎁 Reward: +5 ⭐ Credits each
⏰ Cooldown: 30 seconds
""",
        parse_mode=ParseMode.HTML
    )
    
    # Log hug
    await db.log_transaction(
        from_id=None, to_id=hugger.id,
        amount=5, currency='credits',
        type='hug', description=f"Hug {target.first_name}"
    )

@dp.message(Command("kiss"))
async def cmd_kiss(message: Message):
    """Kiss someone"""
    if not message.reply_to_message:
        await message.answer("💋 Reply to someone with /kiss")
        return
    
    kisser = message.from_user
    target = message.reply_to_message.from_user
    
    if target.id == kisser.id:
        await message.answer("❌ You cannot kiss yourself!")
        return
    
    # Get CatBox GIF
    gif_url = await img_gen.get_random_catbox_gif('kiss')
    
    await message.answer_animation(
        animation=gif_url,
        caption=f"""
💋 <b>KISS!</b>

😘 {kisser.first_name} kissed {target.first_name}!

💕 Love is in the air!
""",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("slap"))
async def cmd_slap(message: Message):
    """Slap someone"""
    if not message.reply_to_message:
        await message.answer("👋 Reply to someone with /slap")
        return
    
    slapper = message.from_user
    target = message.reply_to_message.from_user
    
    if target.id == slapper.id:
        await message.answer("❌ You cannot slap yourself!")
        return
    
    # Get CatBox GIF
    gif_url = await img_gen.get_random_catbox_gif('slap')
    
    await message.answer_animation(
        animation=gif_url,
        caption=f"""
👋 <b>SLAP!</b>

✋ {slapper.first_name} slapped {target.first_name}!

😵 That's gotta hurt!
""",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("pat"))
async def cmd_pat(message: Message):
    """Pat someone's head"""
    if not message.reply_to_message:
        await message.answer("👋 Reply to someone with /pat")
        return
    
    patter = message.from_user
    target = message.reply_to_message.from_user
    
    if target.id == patter.id:
        await message.answer("❌ You cannot pat yourself!")
        return
    
    # Get CatBox GIF
    gif_url = await img_gen.get_random_catbox_gif('pat')
    
    await message.answer_animation(
        animation=gif_url,
        caption=f"""
🐾 <b>HEAD PAT!</b>

👋 {patter.first_name} pats {target.first_name}'s head!

🥰 Good {target.first_name}!
""",
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# MINI-GAMES
# ============================================================================
@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if not command.args:
        await message.answer("Usage: /slot [bet]\nExample: /slot 100\nMin: $10, Max: $10,000")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet is $10!")
            return
        if bet > 10000:
            await message.answer("Maximum bet is $10,000!")
            return
        if bet > user['cash']:
            await message.answer(f"You only have ${user['cash']:,}!")
            return
    except:
        await message.answer("Invalid bet amount!")
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
        win_amount = bet * multiplier
        win_type = "JACKPOT! 🎰"
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        win_amount = int(bet * 1.5)
        win_type = "Two of a kind!"
    else:
        win_amount = 0
        win_type = "No win 😢"
    
    net_gain = win_amount - bet
    
    # Update balance
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    # Update game stats
    await db.update_game_stats(message.from_user.id, 'slots', won=(win_amount > 0))
    
    slot_text = f"""
🎰 <b>SLOT MACHINE</b>

{reels[0]} | {reels[1]} | {reels[2]}

💰 Bet: <b>${bet:,}</b>
🎯 Result: <b>{win_type}</b>
🏆 Payout: <b>${win_amount:,}</b>
📈 Net: {'+' if net_gain > 0 else ''}<b>${net_gain:,}</b>

💵 New Balance: <b>${user['cash'] + net_gain:,}</b>
"""
    
    await message.answer(slot_text, parse_mode=ParseMode.HTML)
    
    # Log slot play
    await db.log_transaction(
        from_id=message.from_user.id, to_id=None,
        amount=net_gain, currency='cash',
        type='slots', description=f"Slot bet ${bet}"
    )

@dp.message(Command("flip"))
async def cmd_flip(message: Message, command: CommandObject):
    """Coin flip game"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if not command.args:
        await message.answer("Usage: /flip [heads/tails] [bet]\nExample: /flip heads 100")
        return
    
    args = command.args.lower().split()
    if len(args) < 2:
        await message.answer("❌ Format: /flip [heads/tails] [bet]")
        return
    
    choice = args[0]
    if choice not in ['heads', 'tails']:
        await message.answer("❌ Choose 'heads' or 'tails'!")
        return
    
    try:
        bet = int(args[1])
        if bet < 10:
            await message.answer("Minimum bet is $10!")
            return
        if bet > user['cash']:
            await message.answer(f"You only have ${user['cash']:,}!")
            return
    except:
        await message.answer("Invalid bet amount!")
        return
    
    # Flip coin
    result = random.choice(['heads', 'tails'])
    
    if choice == result:
        win_amount = bet * 2
        win_text = f"✅ You won ${win_amount:,}!"
        net_gain = bet
    else:
        win_amount = 0
        win_text = f"❌ You lost ${bet:,}!"
        net_gain = -bet
    
    # Update balance
    await db.update_currency(message.from_user.id, "cash", net_gain)
    
    flip_text = f"""
🪙 <b>COIN FLIP</b>

Your choice: <b>{choice.title()}</b>
Result: <b>{result.title()}</b> 🪙

💰 Bet: <b>${bet:,}</b>
{win_text}

💵 New Balance: <b>${user['cash'] + net_gain:,}</b>
"""
    
    await message.answer(flip_text, parse_mode=ParseMode.HTML)

# ============================================================================
# STAND COMMANDS
# ============================================================================
@dp.message(Command("stand"))
async def cmd_stand(message: Message):
    """Get or view your stand"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    stand = await db.get_stand(message.from_user.id)
    
    if not stand:
        # Create new stand
        stand = await db.create_stand(message.from_user.id)
        
        stand_names_descriptions = {
            "Star Platinum": "💪 Incredible strength and precision!",
            "The World": "⏰ Can stop time for a few seconds!",
            "Crazy Diamond": "🔧 Can heal and restore anything!",
            "Gold Experience": "🌱 Creates life and enhances things!",
            "Killer Queen": "💣 Turns anything into a bomb!",
            "King Crimson": "🌀 Erases time and sees the future!",
            "Stone Free": "🧵 Can unravel into strings!",
            "Tusk": "🌀 Spin-based powers that evolve!"
        }
        
        description = stand_names_descriptions.get(stand['stand_name'], "A powerful stand!")
        
        await message.answer(f"""
⭐ <b>STAND AWAKENED!</b>

🎭 Stand: <b>{stand['stand_name']}</b>
{description}

📊 <b>Initial Stats:</b>
• 💪 Power: {stand['power']}/10
• ⚡ Speed: {stand['speed']}/10
• 🎯 Range: {stand['range']}/10
• 🛡️ Durability: {stand['durability']}/10
• 🎯 Precision: {stand['precision']}/10
• 🌟 Potential: {stand['potential']}/10

💡 Use <code>/stand_info</code> to view your stand
💡 Use <code>/stand_upgrade</code> to improve stats
""", parse_mode=ParseMode.HTML)
    else:
        # Show stand info
        if PILLOW_AVAILABLE:
            loading_msg = await message.answer("🖼️ Generating stand card...")
            
            image_bytes = await img_gen.generate_stand_card(stand)
            
            if image_bytes:
                await message.answer_photo(
                    BufferedInputFile(image_bytes, filename="stand.png"),
                    caption=f"""
⭐ <b>{stand['stand_name']}</b>

📊 <b>Stats:</b>
• 💪 Power: {stand['power']}/10
• ⚡ Speed: {stand['speed']}/10
• 🎯 Range: {stand['range']}/10
• 🛡️ Durability: {stand['durability']}/10
• 🎯 Precision: {stand['precision']}/10
• 🌟 Potential: {stand['potential']}/10

👑 Level: {stand['level']}
📈 Experience: {stand['experience']}/100

💡 Commands:
<code>/stand_upgrade</code> - Improve stats
<code>/stand_battle</code> - Battle other stands
""",
                    parse_mode=ParseMode.HTML
                )
                await loading_msg.delete()
                return
        
        # Text version
        await message.answer(f"""
⭐ <b>YOUR STAND</b>

🎭 Stand: <b>{stand['stand_name']}</b>

📊 <b>Stats:</b>
• 💪 Power: {stand['power']}/10
• ⚡ Speed: {stand['speed']}/10
• 🎯 Range: {stand['range']}/10
• 🛡️ Durability: {stand['durability']}/10
• 🎯 Precision: {stand['precision']}/10
• 🌟 Potential: {stand['potential']}/10

👑 Level: {stand['level']}
📈 Experience: {stand['experience']}/100

💡 Commands:
<code>/stand_upgrade</code> - Improve stats
<code>/stand_battle</code> - Battle other stands
""", parse_mode=ParseMode.HTML)

@dp.message(Command("stand_upgrade"))
async def cmd_stand_upgrade(message: Message, command: CommandObject):
    """Upgrade stand stats"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    stand = await db.get_stand(message.from_user.id)
    if not stand:
        await message.answer("❌ You don't have a stand! Use /stand")
        return
    
    if not command.args:
        await message.answer("""
⭐ <b>UPGRADE STAND</b>

Usage: <code>/stand_upgrade [stat]</code>

📊 <b>Available Stats:</b>
• <code>power</code> - 💪 Increases damage
• <code>speed</code> - ⚡ Increases speed
• <code>range</code> - 🎯 Increases range
• <code>durability</code> - 🛡️ Increases health
• <code>precision</code> - 🎯 Increases accuracy
• <code>potential</code> - 🌟 Increases potential

💰 Cost: 100 🌱 Tokens per upgrade
💡 Max: 10 points per stat
""", parse_mode=ParseMode.HTML)
        return
    
    stat = command.args.lower().strip()
    valid_stats = ['power', 'speed', 'range', 'durability', 'precision', 'potential']
    
    if stat not in valid_stats:
        await message.answer(f"❌ Invalid stat! Available: {', '.join(valid_stats)}")
        return
    
    # Check current value
    current_value = stand.get(stat, 1)
    if current_value >= 10:
        await message.answer(f"❌ {stat.title()} is already at max level (10)!")
        return
    
    # Check tokens
    if user['tokens'] < 100:
        await message.answer("❌ Need 100 🌱 Tokens to upgrade!")
        return
    
    # Upgrade
    success = await db.upgrade_stand(message.from_user.id, stat)
    if not success:
        await message.answer("❌ Upgrade failed!")
        return
    
    # Deduct tokens
    await db.update_currency(message.from_user.id, 'tokens', -100)
    
    await message.answer(f"""
✅ <b>STAND UPGRADED!</b>

📊 Stat: <b>{stat.title()}</b>
📈 From: <b>{current_value}/10</b> → <b>{current_value + 1}/10</b>
💰 Cost: <b>100 🌱 Tokens</b>

⭐ Your stand is getting stronger!
""", parse_mode=ParseMode.HTML)
    
    # Log upgrade
    await db.log_transaction(
        from_id=message.from_user.id, to_id=None,
        amount=100, currency='tokens',
        type='stand_upgrade', description=f"Upgrade {stat}"
    )

# ============================================================================
# FRIEND COMMANDS
# ============================================================================
@dp.message(Command("friend_add"))
async def cmd_friend_add(message: Message):
    """Add a friend"""
    if not message.reply_to_message:
        await message.answer("👥 Reply to someone with /friend_add")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    target = message.reply_to_message.from_user
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot add yourself!")
        return
    
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Add friend
    success = await db.add_friend(message.from_user.id, target.id)
    
    if not success:
        await message.answer("❌ Failed to add friend!")
        return
    
    await message.answer(f"""
✅ <b>FRIEND ADDED!</b>

👤 You added <b>{target.first_name}</b> as a friend!

💖 <b>Friend Benefits:</b>
• See when friends are online
• Send friend gifts
• Complete friend quests together
• Earn friendship points

💡 Use <code>/friends</code> to see your friends
""", parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
👥 <b>NEW FRIEND!</b>

👤 <b>{message.from_user.first_name}</b> added you as a friend!

🤝 You are now friends!
💖 Friendship level: 1
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("friends"))
async def cmd_friends(message: Message):
    """View friends list"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    friends = await db.get_friends(message.from_user.id)
    
    if not friends:
        await message.answer("""
👥 <b>YOUR FRIENDS</b>

📭 No friends yet!

💡 Add friends with <code>/friend_add</code> (reply to someone)
💖 Friends can send gifts and do quests together
""", parse_mode=ParseMode.HTML)
        return
    
    friends_text = """
👥 <b>YOUR FRIENDS</b>

"""
    
    for friend in friends:
        level_emoji = "💖" * min(friend['friendship_level'], 5)
        friends_text += f"• {friend['friend_name']} {level_emoji} (Level {friend['friendship_level']})\n"
    
    friends_text += f"""

📊 Total: {len(friends)} friends
💖 Max friendship level: 10

💡 Commands:
<code>/friend_remove</code> - Remove friend
"""
    
    await message.answer(friends_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS
# ============================================================================
@dp.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    """Add resources (owner only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🔒 Owner only command!")
        return
    
    if not command.args:
        await message.answer("""
💰 <b>ADD RESOURCES</b>

Usage: <code>/add [user] [resource] [amount]</code>

🎯 <b>User:</b> Reply to user or provide ID
💎 <b>Resources:</b> cash, gold, bonds, credits, tokens, event_coins
📝 <b>Example:</b> <code>/add 123456789 cash 1000</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Format: /add [user] [resource] [amount]")
        return
    
    # Parse target
    target_str = args[0]
    resource = args[1].lower()
    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Amount must be a number!")
        return
    
    # Find target
    target_id = None
    
    # Check if reply
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif target_str.isdigit():
        target_id = int(target_str)
    else:
        await message.answer("❌ Target must be user ID or reply!")
        return
    
    if resource not in ['cash', 'gold', 'bonds', 'credits', 'tokens', 'event_coins']:
        await message.answer("❌ Invalid resource!")
        return
    
    # Add resources
    success = await db.update_currency(target_id, resource, amount)
    
    if not success:
        await message.answer("❌ Failed to add resources!")
        return
    
    target_user = await db.get_user(target_id)
    target_name = target_user.get('first_name', 'Unknown') if target_user else 'Unknown'
    
    await message.answer(f"""
✅ <b>RESOURCES ADDED</b>

👤 To: <b>{target_name}</b>
💎 Resource: <b>{resource.upper()}</b>
➕ Amount: <b>{amount:,}</b>
🎯 By: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        'add_resources',
        target_id,
        f"Added {amount} {resource} to {target_name}"
    )
    
    # Notify target
    try:
        await bot.send_message(
            target_id,
            f"""
🎁 <b>ADMIN GIFT</b>

👤 Admin: <b>{message.from_user.first_name}</b>
💎 Resource: <b>{resource.upper()}</b>
🎁 Amount: <b>{amount:,}</b>

Thank you for playing! 🎮
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban user (owner only)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Reply to user to ban them!")
        return
    
    target = message.reply_to_message.from_user
    reason = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else "No reason provided"
    
    if target.id in ADMIN_IDS:
        await message.answer("❌ Cannot ban admin!")
        return
    
    # Ban user
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (target.id,)
        )
        await db.conn.commit()
    
    await message.answer(f"""
✅ <b>USER BANNED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
📝 Reason: {reason}
⏰ Banned: {datetime.now().strftime('%Y-%m-%d %H:%M')}

⚠️ User can no longer use the bot.
""", parse_mode=ParseMode.HTML)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        'ban',
        target.id,
        f"Banned: {reason}"
    )
    
    # Add warning
    await db.add_warning(target.id, message.from_user.id, reason)
    
    # Notify user
    try:
        await bot.send_message(
            target.id,
            f"""
🚫 <b>YOU HAVE BEEN BANNED</b>

📝 Reason: {reason}
⏰ Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👤 Admin: {message.from_user.first_name}

⚠️ You can no longer use the bot.
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    """Unban user (owner only)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if not command.args:
        await message.answer("❌ Provide user ID!")
        return
    
    target_id = int(command.args) if command.args.isdigit() else None
    
    if not target_id:
        await message.answer("❌ Invalid user ID!")
        return
    
    # Unban user
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?",
            (target_id,)
        )
        await db.conn.commit()
    
    target_user = await db.get_user(target_id)
    target_name = target_user.get('first_name', 'Unknown') if target_user else 'Unknown'
    
    await message.answer(f"""
✅ <b>USER UNBANNED</b>

👤 User: <b>{target_name}</b>
🆔 ID: <code>{target_id}</code>
⏰ Unbanned: {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ User can now use the bot again.
""", parse_mode=ParseMode.HTML)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        'unban',
        target_id,
        "User unbanned"
    )
    
    # Notify user
    try:
        await bot.send_message(
            target_id,
            f"""
✅ <b>YOU HAVE BEEN UNBANNED</b>

⏰ Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👤 Admin: {message.from_user.first_name}

✅ You can now use the bot again!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("warn"))
async def cmd_warn(message: Message):
    """Warn user (owner only)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Reply to user to warn them!")
        return
    
    target = message.reply_to_message.from_user
    reason = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else "No reason provided"
    
    # Add warning
    await db.add_warning(target.id, message.from_user.id, reason)
    
    warnings = await db.get_warnings(target.id)
    
    await message.answer(f"""
⚠️ <b>USER WARNED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
📝 Reason: {reason}
📊 Total Warnings: {len(warnings)}

❌ 3 warnings = automatic ban!
""", parse_mode=ParseMode.HTML)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        'warn',
        target.id,
        f"Warning: {reason}"
    )
    
    # Check for auto-ban (3 warnings)
    if len(warnings) >= 3:
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET is_banned = 1 WHERE user_id = ?",
                (target.id,)
            )
            await db.conn.commit()
        
        await message.answer(f"""
🚫 <b>AUTO-BAN TRIGGERED</b>

👤 User: <b>{target.first_name}</b>
🆔 ID: <code>{target.id}</code>
📊 Warnings: {len(warnings)}/3

⚠️ User has been automatically banned!
""", parse_mode=ParseMode.HTML)
    
    # Notify user
    try:
        warning_count = len(warnings)
        await bot.send_message(
            target.id,
            f"""
⚠️ <b>YOU HAVE BEEN WARNED</b>

📝 Reason: {reason}
👤 Admin: {message.from_user.first_name}
📊 Warnings: {warning_count}/3

❌ 3 warnings will result in a ban!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show bot statistics"""
    if message.from_user.id not in ADMIN_IDS:
        # Regular users see simplified stats
        bot_stats = await db.get_bot_stats()
        
        stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 Total Users: <b>{bot_stats['total_users']:,}</b>
🌳 Total Families: <b>{bot_stats['total_families']:,}</b>
🌾 Total Gardens: <b>{bot_stats['total_gardens']:,}</b>
💰 Total Cash: <b>${bot_stats['total_cash']:,}</b>

📈 Active Today: <b>{bot_stats['active_today']:,}</b>
"""
        
        await message.answer(stats_text, parse_mode=ParseMode.HTML)
        return
    
    # Admin sees detailed stats
    bot_stats = await db.get_bot_stats()
    
    # Get more detailed stats
    async with db.lock:
        # Weekly active users
        cursor = await db.conn.execute(
            "SELECT COUNT(*) FROM users WHERE last_active >= datetime('now', '-7 days')"
        )
        weekly_active = (await cursor.fetchone())[0]
        
        # Total plants growing
        cursor = await db.conn.execute("SELECT COUNT(*) FROM garden_plants WHERE progress < 100")
        plants_growing = (await cursor.fetchone())[0]
        
        # Total stands
        cursor = await db.conn.execute("SELECT COUNT(*) FROM stands")
        total_stands = (await cursor.fetchone())[0]
        
        # Total friends
        cursor = await db.conn.execute("SELECT COUNT(*) FROM friends")
        total_friends = (await cursor.fetchone())[0]
        
        # Banned users
        cursor = await db.conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = (await cursor.fetchone())[0]
    
    stats_text = f"""
📊 <b>ADMIN STATISTICS</b>

👥 <b>Users:</b>
• Total: <b>{bot_stats['total_users']:,}</b>
• Active Today: <b>{bot_stats['active_today']:,}</b>
• Active Week: <b>{weekly_active:,}</b>
• Banned: <b>{banned_users:,}</b>

🌳 <b>Family System:</b>
• Total Families: <b>{bot_stats['total_families']:,}</b>

🌾 <b>Garden System:</b>
• Total Gardens: <b>{bot_stats['total_gardens']:,}</b>
• Plants Growing: <b>{plants_growing:,}</b>

💰 <b>Economy:</b>
• Total Cash: <b>${bot_stats['total_cash']:,}</b>
• Total Gold: <b>{(await db.conn.execute("SELECT SUM(gold) FROM users")).fetchone()[0] or 0:,}</b>

⭐ <b>Stands:</b>
• Total Stands: <b>{total_stands:,}</b>
• Average Level: <b>{(await db.conn.execute("SELECT AVG(level) FROM stands")).fetchone()[0] or 1:.1f}</b>

👥 <b>Friends:</b>
• Total Friendships: <b>{total_friends:,}</b>

📈 <b>Growth:</b>
• New Today: <b>{(await db.conn.execute("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-1 day')")).fetchone()[0]:,}</b>
• New Week: <b>{(await db.conn.execute("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')")).fetchone()[0]:,}</b>
"""
    
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start_time = time.time()
    msg = await message.answer("🏓 Pong!")
    end_time = time.time()
    
    latency = round((end_time - start_time) * 1000, 2)
    
    # Get some stats
    bot_stats = await db.get_bot_stats()
    
    ping_text = f"""
🏓 <b>PONG!</b>

⚡ Speed: <b>{latency}ms</b>
👥 Users: <b>{bot_stats['total_users']:,}</b>
🌳 Families: <b>{bot_stats['total_families']:,}</b>
🔧 Status: <b>🟢 ACTIVE</b>

✅ All systems operational!
"""
    
    await msg.edit_text(ping_text, parse_mode=ParseMode.HTML)

@dp.message(Command("catbox_add"))
async def cmd_catbox_add(message: Message, command: CommandObject):
    """Add CatBox GIF (owner only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🔒 Owner only command!")
        return
    
    if not command.args:
        await message.answer("""
🎬 <b>ADD CATBOX GIF</b>

Usage: <code>/catbox_add [command] [url]</code>

💡 <b>Commands:</b> rob, kill, hug, kiss, slap, pat
🔗 <b>URL:</b> CatBox.moe GIF URL

📝 <b>Example:</b>
<code>/catbox_add rob https://catbox.moe/example.gif</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Format: /catbox_add [command] [url]")
        return
    
    cmd = args[0].lower()
    url = args[1]
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await message.answer("❌ Invalid URL!")
        return
    
    # Add GIF
    success = await db.add_catbox_gif(cmd, url, message.from_user.id)
    
    if not success:
        await message.answer("❌ Failed to add GIF!")
        return
    
    await message.answer(f"""
✅ <b>CATBOX GIF ADDED</b>

🎬 Command: <code>{cmd}</code>
🔗 URL: {url[:50]}...
👤 Added by: {message.from_user.first_name}
""", parse_mode=ParseMode.HTML)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        'add_catbox_gif',
        None,
        f"Added GIF for {cmd}"
    )

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast message to all users (owner only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🔒 Owner only command!")
        return
    
    if not command.args:
        await message.answer("❌ Provide message to broadcast!")
        return
    
    broadcast_text = command.args
    
    # Get all users
    async with db.lock:
        cursor = await db.conn.execute("SELECT user_id FROM users WHERE is_banned = 0")
        users = await cursor.fetchall()
    
    total_users = len(users)
    successful = 0
    
    status_msg = await message.answer(f"📢 Broadcasting to {total_users} users...")
    
    for user_row in users:
        user_id = user_row[0]
        try:
            await bot.send_message(
                user_id,
                f"""
📢 <b>BROADCAST MESSAGE</b>

{broadcast_text}

👤 From: {message.from_user.first_name}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
                parse_mode=ParseMode.HTML
            )
            successful += 1
            await asyncio.sleep(0.1)
        except:
            pass
    
    await status_msg.edit_text(f"""
✅ <b>BROADCAST COMPLETE</b>

📊 Statistics:
• Total Users: {total_users}
• ✅ Successful: {successful}
• 📨 Sent: {successful} messages
""", parse_mode=ParseMode.HTML)
    
    # Log admin action
    await db.log_admin_action(
        message.from_user.id,
        'broadcast',
        None,
        f"Sent to {successful}/{total_users} users"
    )

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================
@dp.callback_query(F.data == "quick_start")
async def callback_quick_start(callback: CallbackQuery):
    """Quick start guide"""
    await callback.message.edit_text("""
🚀 <b>QUICK START GUIDE</b>

1. <b>Claim Daily Bonus</b>
   <code>/daily</code> - Get free money every day!

2. <b>Build Your Family</b>
   <code>/adopt</code> - Adopt someone (reply to them)
   <code>/marry</code> - Marry someone (reply to them)

3. <b>Start Gardening</b>
   <code>/garden</code> - View your garden
   <code>/plant carrot 3</code> - Plant 3 carrots

4. <b>Play Games</b>
   <code>/rob</code> - Rob someone (reply)
   <code>/slot 100</code> - Play slots
   <code>/kill</code> - Kill someone (reply)

5. <b>Get Your Stand</b>
   <code>/stand</code> - Awaken your stand
   <code>/stand_upgrade power</code> - Upgrade stand

💡 <b>Tip:</b> Add @Familly_TreeBot to your bio for 2x daily rewards!
""", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "all_commands")
async def callback_all_commands(callback: CallbackQuery):
    """All commands list"""
    commands_text = """
📋 <b>ALL COMMANDS</b>

👑 <b>Account:</b>
<code>/start</code> - Start bot
<code>/daily</code> - Daily bonus
<code>/me</code> - Your profile

🌳 <b>Family:</b>
<code>/family</code> - Family tree
<code>/adopt</code> - Adopt someone (reply)
<code>/marry</code> - Marry someone (reply)
<code>/divorce</code> - End marriage
<code>/disown</code> - Remove family

🌾 <b>Garden:</b>
<code>/garden</code> - Your garden
<code>/plant [crop] [qty]</code> - Plant crops
<code>/harvest</code> - Harvest ready crops
<code>/barn</code> - View storage

🎮 <b>Games:</b>
<code>/rob</code> - Rob someone (reply)
<code>/kill</code> - Kill someone (reply)
<code>/hug</code> - Hug someone (reply)
<code>/kiss</code> - Kiss someone (reply)
<code>/slap</code> - Slap someone (reply)
<code>/pat</code> - Pat someone (reply)
<code>/slot [bet]</code> - Slot machine
<code>/flip [choice] [bet]</code> - Coin flip

⭐ <b>Stands:</b>
<code>/stand</code> - Your stand
<code>/stand_upgrade [stat]</code> - Upgrade stand

👥 <b>Friends:</b>
<code>/friend_add</code> - Add friend (reply)
<code>/friends</code> - Friends list

⚙️ <b>Admin:</b>
<code>/add [user] [resource] [amount]</code>
<code>/ban [user] [reason]</code>
<code>/unban [user]</code>
<code>/warn [user] [reason]</code>
<code>/stats</code> - Bot statistics
<code>/ping</code> - Check bot status
<code>/broadcast</code> - Send message to all
<code>/catbox_add</code> - Add GIFs
"""
    
    await callback.message.edit_text(commands_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ERROR HANDLER
# ============================================================================
@dp.errors.register(Exception)
async def error_handler(event: types.ErrorEvent):
    """Global error handler"""
    logger.error(f"Error: {event.exception}", exc_info=True)
    
    # Send to log channel
    error_text = f"""
🚨 <b>BOT ERROR</b>

❌ Error: <code>{html.escape(str(event.exception))[:500]}</code>
🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        await send_to_log_channel(error_text)
    except:
        pass
    
    return True

# ============================================================================
# STARTUP
# ============================================================================
async def setup_bot():
    """Initialize bot on startup"""
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="adopt", description="Adopt someone"),
        types.BotCommand(command="marry", description="Marry someone"),
        types.BotCommand(command="rob", description="Rob someone"),
        types.BotCommand(command="kill", description="Kill someone (fun)"),
        types.BotCommand(command="hug", description="Hug someone"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="stand", description="Your stand"),
        types.BotCommand(command="friends", description="Friends list"),
        types.BotCommand(command="stats", description="Bot statistics"),
        types.BotCommand(command="ping", description="Check bot status"),
    ]
    
    await bot.set_my_commands(commands)
    
    # Startup message
    print("=" * 60)
    print("🌳 FAMILY TREE BOT - COMPLETE VERSION")
    print(f"Version: 8.2 | Owner: {OWNER_ID}")
    print(f"Bot: {BOT_USERNAME}")
    print(f"Log Channel: {LOG_CHANNEL}")
    print(f"Images: {'✅ ENABLED' if PILLOW_AVAILABLE else '❌ DISABLED'}")
    print("=" * 60)
    print("🚀 Bot started successfully!")
    
    # Send startup message to log channel
    await send_to_log_channel(
        f"🚀 <b>BOT STARTED</b>\n"
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"✅ Version 8.2\n"
        f"📊 All systems operational"
    )

async def main():
    """Main function"""
    if not BOT_TOKEN:
        print("❌ ERROR: Set BOT_TOKEN in environment!")
        sys.exit(1)
    
    try:
        await setup_bot()
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
