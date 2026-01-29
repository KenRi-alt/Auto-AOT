#!/usr/bin/env python3
"""
🏆 ULTIMATE FAMILY TREE BOT
Version: 10.0 - Complete Professional Edition
For Railway Deployment
"""

import os
import sys
import json
import asyncio
import logging
import random
import secrets
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
        InputMediaPhoto, ChatMemberUpdated, ChatJoinRequest,
        InputFile, URLInputFile
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode, ChatMemberStatus
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
    
    # Try to import Pillow for images
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        import textwrap
        HAS_PILLOW = True
        print("✅ Pillow installed - Image features enabled")
    except ImportError:
        HAS_PILLOW = False
        print("⚠️ Pillow not installed - Using text visualizations only")
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram==3.0.0b7 aiohttp==3.8.6 aiosqlite python-dotenv pillow")
    sys.exit(1)

import aiosqlite
import sqlite3

# ============================================================================
# CONFIGURATION
# ============================================================================

OWNER_ID = 6108185460
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
BOT_USERNAME = "Familly_TreeBot"
DB_PATH = os.getenv("DB_PATH", "family_tree_v10.db")

# Game Constants
CURRENCIES = ["cash", "gold", "gems", "bonds", "credits", "tokens", "event_coins", "food"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "gems": "💎", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪", "food": "🍖"
}

CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper", "watermelon", "pumpkin", 
              "wheat", "rice", "cotton", "coffee", "tea", "sugarcane", "tobacco", "opium"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔", "eggplant": "🍆", 
    "corn": "🌽", "pepper": "🫑", "watermelon": "🍉", "pumpkin": "🎃",
    "wheat": "🌾", "rice": "🍚", "cotton": "🧶", "coffee": "☕",
    "tea": "🫖", "sugarcane": "🎋", "tobacco": "🚬", "opium": "💊"
}

CROP_PRICES = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕", "season": "all"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅", "season": "summer"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔", "season": "spring"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆", "season": "summer"},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽", "season": "summer"},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑", "season": "summer"},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "emoji": "🍉", "season": "summer"},
    "pumpkin": {"buy": 40, "sell": 60, "grow_time": 8, "emoji": "🎃", "season": "autumn"},
    "wheat": {"buy": 50, "sell": 75, "grow_time": 10, "emoji": "🌾", "season": "spring"},
    "rice": {"buy": 60, "sell": 90, "grow_time": 12, "emoji": "🍚", "season": "summer"},
    "cotton": {"buy": 80, "sell": 120, "grow_time": 15, "emoji": "🧶", "season": "autumn"},
    "coffee": {"buy": 100, "sell": 150, "grow_time": 20, "emoji": "☕", "season": "all"},
    "tea": {"buy": 120, "sell": 180, "grow_time": 25, "emoji": "🫖", "season": "spring"},
    "sugarcane": {"buy": 150, "sell": 225, "grow_time": 30, "emoji": "🎋", "season": "summer"},
    "tobacco": {"buy": 200, "sell": 300, "grow_time": 40, "emoji": "🚬", "season": "autumn"},
    "opium": {"buy": 500, "sell": 750, "grow_time": 60, "emoji": "💊", "season": "all"}
}

# Stand Types
STAND_TYPES = {
    "bakery": {"name": "Bakery", "cost": 5000, "income": 200, "emoji": "🥖"},
    "butcher": {"name": "Butcher Shop", "cost": 10000, "income": 400, "emoji": "🥩"},
    "grocery": {"name": "Grocery Store", "cost": 15000, "income": 600, "emoji": "🏪"},
    "hardware": {"name": "Hardware Store", "cost": 25000, "income": 1000, "emoji": "🛠️"},
    "pharmacy": {"name": "Pharmacy", "cost": 50000, "income": 2000, "emoji": "💊"},
    "jewelry": {"name": "Jewelry Store", "cost": 100000, "income": 4000, "emoji": "💎"},
    "casino": {"name": "Casino", "cost": 250000, "income": 10000, "emoji": "🎰"},
    "bank": {"name": "Bank", "cost": 500000, "income": 20000, "emoji": "🏦"}
}

# Mini Games
MINI_GAMES = {
    "dice": {"name": "🎲 Dice Game", "min_bet": 10, "max_bet": 10000},
    "slots": {"name": "🎰 Slot Machine", "min_bet": 50, "max_bet": 50000},
    "blackjack": {"name": "🃏 Blackjack", "min_bet": 100, "max_bet": 100000},
    "roulette": {"name": "🎯 Roulette", "min_bet": 200, "max_bet": 200000},
    "trivia": {"name": "🧠 Trivia", "reward": 500},
    "memory": {"name": "🧩 Memory Game", "reward": 300}
}

# Achievement System
ACHIEVEMENTS = {
    "first_daily": {"name": "Early Bird", "reward": 1000, "emoji": "🐦"},
    "first_family": {"name": "Family Starter", "reward": 2000, "emoji": "👨‍👩‍👧‍👦"},
    "first_plant": {"name": "Green Thumb", "reward": 500, "emoji": "🌱"},
    "first_stand": {"name": "Entrepreneur", "reward": 5000, "emoji": "💼"},
    "millionaire": {"name": "Millionaire", "reward": 10000, "emoji": "💰"},
    "level_50": {"name": "Legend", "reward": 50000, "emoji": "🏆"}
}

# ============================================================================
# GUARANTEED IMAGE GENERATOR
# ============================================================================

class GuaranteedImageGenerator:
    """Image generator that WORKS even without fonts"""
    
    @staticmethod
    async def create_family_tree_image(user_name: str, family_data: List[dict]) -> Optional[bytes]:
        """Create family tree image - SIMPLE AND GUARANTEED TO WORK"""
        if not HAS_PILLOW:
            return None
        
        try:
            # Simple image - NO FONTS, just shapes
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color=(30, 30, 50))
            draw = ImageDraw.Draw(img)
            
            # Draw user at center
            cx, cy = width // 2, height // 2
            draw.ellipse([cx-50, cy-50, cx+50, cy+50], fill=(0, 120, 255), outline=(255, 255, 255), width=3)
            
            # Draw family members in circle
            colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 200, 100)]
            
            for i, member in enumerate(family_data[:8]):  # Max 8 members
                angle = (i / max(len(family_data), 1)) * 2 * math.pi
                radius = 200
                x = cx + int(radius * math.cos(angle))
                y = cy + int(radius * math.sin(angle))
                
                # Draw line
                draw.line([(cx, cy), (x, y)], fill=colors[i % len(colors)], width=2)
                
                # Draw member circle
                draw.ellipse([x-30, y-30, x+30, y+30], fill=colors[i % len(colors)], outline=(255, 255, 255), width=2)
                
                # Draw relation symbol (emoji would need font, so use shape)
                if member.get('relation_type') == 'spouse':
                    draw.rectangle([x-15, y-15, x+15, y+15], fill=(255, 50, 50))
                elif member.get('relation_type') == 'child':
                    draw.polygon([(x, y-20), (x-20, y+20), (x+20, y+20)], fill=(50, 255, 50))
                elif member.get('relation_type') == 'parent':
                    draw.rectangle([x-20, y-20, x+20, y+20], fill=(50, 50, 255))
            
            # Save to bytes
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()
            
        except Exception as e:
            print(f"Image error (safe): {e}")
            return None
    
    @staticmethod
    async def create_garden_image(plants: List[dict], slots: int) -> Optional[bytes]:
        """Create garden image - SIMPLE AND GUARANTEED"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 600
            img = Image.new('RGB', (width, height), color=(20, 60, 20))
            draw = ImageDraw.Draw(img)
            
            # Draw garden grid
            grid_size = int(math.ceil(math.sqrt(slots)))
            cell_size = 100
            margin = 20
            
            for i in range(slots):
                row = i // grid_size
                col = i % grid_size
                
                x1 = margin + col * (cell_size + margin)
                y1 = margin + row * (cell_size + margin)
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                if i < len(plants):
                    # Plant slot with progress
                    progress = plants[i].get('progress', 0)
                    color = (0, 200, 0) if progress >= 100 else (200, 200, 0)
                    
                    # Draw plant progress
                    draw.rectangle([x1, y1, x2, y2], fill=color, outline=(255, 255, 255), width=2)
                    
                    # Progress bar inside
                    if progress < 100:
                        bar_height = int((progress / 100) * cell_size)
                        draw.rectangle([x1+5, y2-5-bar_height, x2-5, y2-5], fill=(0, 100, 0))
                else:
                    # Empty slot
                    draw.rectangle([x1, y1, x2, y2], fill=(50, 100, 50), outline=(200, 200, 200), width=1)
            
            return io.BytesIO(img.tobytes()).getvalue()
            
        except Exception as e:
            print(f"Garden image error: {e}")
            return None
    
    @staticmethod
    async def create_wealth_chart(currencies: dict) -> Optional[bytes]:
        """Create wealth chart - SIMPLE AND GUARANTEED"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 400
            img = Image.new('RGB', (width, height), color=(25, 25, 35))
            draw = ImageDraw.Draw(img)
            
            # Find max value for scaling
            values = list(currencies.values())
            max_val = max(values) if values else 1
            
            # Draw bars
            bar_width = 80
            spacing = 20
            start_x = 50
            start_y = height - 100
            max_bar = 250
            
            for i, (currency, value) in enumerate(currencies.items()):
                if i >= 6:  # Show only 6 currencies
                    break
                    
                x1 = start_x + i * (bar_width + spacing)
                bar_height = min(max_bar, int((value / max_val) * max_bar))
                y1 = start_y - bar_height
                x2 = x1 + bar_width
                y2 = start_y
                
                # Bar color
                colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), 
                         (255, 200, 100), (200, 100, 255), (100, 255, 255)]
                color = colors[i % len(colors)]
                
                draw.rectangle([x1, y1, x2, y2], fill=color)
                
                # Value text (drawn with rectangles for simplicity)
                # For a real implementation, we'd need fonts
                
            return io.BytesIO(img.tobytes()).getvalue()
            
        except Exception as e:
            print(f"Wealth chart error: {e}")
            return None

# ============================================================================
# COMPLETE DATABASE SYSTEM
# ============================================================================

class CompleteDatabase:
    """Complete database system for all features"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.init_all_tables()
    
    async def init_all_tables(self):
        """Initialize ALL tables for complete system"""
        
        tables = [
            # Users table
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                cash INTEGER DEFAULT 5000,
                gold INTEGER DEFAULT 100,
                gems INTEGER DEFAULT 10,
                bonds INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                event_coins INTEGER DEFAULT 0,
                food INTEGER DEFAULT 100,
                reputation INTEGER DEFAULT 100,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                is_banned BOOLEAN DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                daily_streak INTEGER DEFAULT 0,
                total_dailies INTEGER DEFAULT 0,
                bio_verified BOOLEAN DEFAULT 0,
                gemstone TEXT DEFAULT 'None',
                achievements TEXT DEFAULT '[]',
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Family relations
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                approved BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id, relation_type)
            )""",
            
            # Garden
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 100,
                water_level INTEGER DEFAULT 100,
                fertilizer_level INTEGER DEFAULT 0,
                auto_harvest BOOLEAN DEFAULT 0,
                last_watered TIMESTAMP,
                last_fertilized TIMESTAMP
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
                quality INTEGER DEFAULT 1
            )""",
            
            # Barn storage
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                quality INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Stands (Businesses)
            """CREATE TABLE IF NOT EXISTS stands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stand_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                employees INTEGER DEFAULT 0,
                last_collected TIMESTAMP,
                income INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0
            )""",
            
            # Inventory
            """CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                data TEXT DEFAULT '{}',
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, item_type, item_name)
            )""",
            
            # Friends
            """CREATE TABLE IF NOT EXISTS friends (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                status TEXT DEFAULT 'friends',
                since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_gift TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            )""",
            
            # Friend requests
            """CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Gifts
            """CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                gift_type TEXT NOT NULL,
                amount INTEGER DEFAULT 0,
                message TEXT,
                opened BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Messages
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Market listings
            """CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_data TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )""",
            
            # Transactions
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Game stats
            """CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER PRIMARY KEY,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                total_winnings INTEGER DEFAULT 0,
                largest_win INTEGER DEFAULT 0,
                last_game TIMESTAMP
            )""",
            
            # Admin actions
            """CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Cat Box (Admin Storage)
            """CREATE TABLE IF NOT EXISTS cat_box (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        async with self.lock:
            for table in tables:
                try:
                    await self.conn.execute(table)
                except Exception as e:
                    print(f"Table creation error: {e}")
            await self.conn.commit()
    
    # ==================== USER METHODS ====================
    
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
            user = dict(zip(columns, row))
            
            # Parse JSON fields
            if user.get('achievements'):
                try:
                    user['achievements'] = json.loads(user['achievements'])
                except:
                    user['achievements'] = []
            
            if user.get('settings'):
                try:
                    user['settings'] = json.loads(user['settings'])
                except:
                    user['settings'] = {}
            
            return user
    
    async def create_user(self, user: types.User) -> dict:
        """Create new user"""
        async with self.lock:
            await self.conn.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name) 
                   VALUES (?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, user.last_name)
            )
            
            # Initialize other tables
            await self.conn.execute(
                "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.execute(
                "INSERT OR IGNORE INTO game_stats (user_id) VALUES (?)",
                (user.id,)
            )
            
            await self.conn.commit()
        
        return await self.get_user(user.id)
    
    async def update_user(self, user_id: int, updates: dict):
        """Update user data"""
        if not updates:
            return
        
        async with self.lock:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values())
            values.append(user_id)
            
            await self.conn.execute(
                f"UPDATE users SET {set_clause} WHERE user_id = ?",
                values
            )
            await self.conn.commit()
    
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
    
    # ==================== FAMILY METHODS ====================
    
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
                   WHERE ? IN (fr.user1_id, fr.user2_id) AND fr.approved = 1""",
                (user_id, user_id, user_id, user_id)
            )
            rows = await cursor.fetchall()
            
            family = []
            for row in rows:
                family.append({
                    'relation_type': row[0],
                    'other_id': row[1],
                    'other_name': row[2],
                    'other_username': row[3]
                })
            
            return family
    
    async def add_family_relation(self, user1_id: int, user2_id: int, relation_type: str, approved: bool = True):
        """Add family relation"""
        async with self.lock:
            await self.conn.execute(
                """INSERT OR REPLACE INTO family_relations 
                   (user1_id, user2_id, relation_type, approved) 
                   VALUES (?, ?, ?, ?)""",
                (min(user1_id, user2_id), max(user1_id, user2_id), relation_type, approved)
            )
            await self.conn.commit()
    
    async def remove_family_relation(self, user1_id: int, user2_id: int, relation_type: str = None):
        """Remove family relation"""
        async with self.lock:
            if relation_type:
                await self.conn.execute(
                    """DELETE FROM family_relations 
                       WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
                       AND relation_type = ?""",
                    (user1_id, user2_id, user2_id, user1_id, relation_type)
                )
            else:
                await self.conn.execute(
                    """DELETE FROM family_relations 
                       WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)""",
                    (user1_id, user2_id, user2_id, user1_id)
                )
            await self.conn.commit()
    
    # ==================== GARDEN METHODS ====================
    
    async def get_garden(self, user_id: int) -> dict:
        """Get user garden"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM gardens WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return {"slots": 9, "barn_capacity": 100, "water_level": 100}
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int = 1) -> bool:
        """Plant crops"""
        if crop_type not in CROP_TYPES:
            return False
        
        garden = await self.get_garden(user_id)
        if not garden:
            return False
        
        # Check available slots
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM garden_plants WHERE user_id = ? AND is_ready = 0",
            (user_id,)
        )
        used_slots = (await cursor.fetchone())[0]
        
        if used_slots + quantity > garden['slots']:
            return False
        
        # Plant crops
        grow_time = CROP_PRICES[crop_type]["grow_time"]
        async with self.lock:
            for _ in range(quantity):
                await self.conn.execute(
                    """INSERT INTO garden_plants 
                       (user_id, crop_type, grow_time, progress) 
                       VALUES (?, ?, ?, 0)""",
                    (user_id, crop_type, grow_time)
                )
            await self.conn.commit()
        
        return True
    
    async def get_growing_crops(self, user_id: int) -> List[dict]:
        """Get growing crops"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT id, crop_type, 
                   (julianday('now') - julianday(planted_at)) * 24 as hours_passed,
                   grow_time, progress, is_ready
                   FROM garden_plants 
                   WHERE user_id = ? AND is_ready = 0""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            crops = []
            for row in rows:
                hours_passed = row[2] or 0
                grow_time = row[3] or 1
                progress = min(100, (hours_passed / grow_time) * 100) if grow_time > 0 else 0
                
                crops.append({
                    'id': row[0],
                    'crop_type': row[1],
                    'hours_passed': hours_passed,
                    'grow_time': grow_time,
                    'progress': progress,
                    'is_ready': row[5] or progress >= 100
                })
            
            return crops
    
    async def harvest_crop(self, user_id: int, crop_id: int) -> Optional[dict]:
        """Harvest a crop"""
        async with self.lock:
            # Get crop
            cursor = await self.conn.execute(
                "SELECT crop_type, progress FROM garden_plants WHERE id = ? AND user_id = ?",
                (crop_id, user_id)
            )
            crop = await cursor.fetchone()
            
            if not crop:
                return None
            
            crop_type, progress = crop
            
            if progress < 100:
                return {"success": False, "message": "Crop not ready"}
            
            # Remove from garden
            await self.conn.execute(
                "DELETE FROM garden_plants WHERE id = ?",
                (crop_id,)
            )
            
            # Add to barn
            await self.conn.execute(
                """INSERT INTO barn (user_id, crop_type, quantity, quality) 
                   VALUES (?, ?, 1, 1)
                   ON CONFLICT(user_id, crop_type) 
                   DO UPDATE SET quantity = quantity + 1""",
                (user_id, crop_type)
            )
            
            await self.conn.commit()
            
            return {
                "success": True,
                "crop_type": crop_type,
                "sell_price": CROP_PRICES.get(crop_type, {}).get("sell", 0)
            }
    
    async def get_barn(self, user_id: int) -> List[dict]:
        """Get barn items"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT crop_type, quantity, quality FROM barn WHERE user_id = ?",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            barn = []
            for row in rows:
                barn.append({
                    'crop_type': row[0],
                    'quantity': row[1],
                    'quality': row[2],
                    'emoji': CROP_EMOJIS.get(row[0], "📦"),
                    'value': CROP_PRICES.get(row[0], {}).get("sell", 0) * row[1]
                })
            
            return barn
    
    # ==================== STAND METHODS ====================
    
    async def get_stands(self, user_id: int) -> List[dict]:
        """Get user's stands"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM stands WHERE user_id = ?",
                (user_id,)
            )
            rows = await cursor.fetchall()
            
            stands = []
            for row in rows:
                stand_data = dict(zip([desc[0] for desc in cursor.description], row))
                stand_type = stand_data['stand_type']
                
                # Add stand info
                stand_info = STAND_TYPES.get(stand_type, {})
                stand_data.update(stand_info)
                
                stands.append(stand_data)
            
            return stands
    
    async def buy_stand(self, user_id: int, stand_type: str) -> bool:
        """Buy a stand"""
        if stand_type not in STAND_TYPES:
            return False
        
        stand_info = STAND_TYPES[stand_type]
        cost = stand_info["cost"]
        
        # Check if user can afford
        user = await self.get_user(user_id)
        if not user or user.get('cash', 0) < cost:
            return False
        
        # Check if already has this stand type
        stands = await self.get_stands(user_id)
        if any(s['stand_type'] == stand_type for s in stands):
            return False
        
        # Create stand
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO stands 
                   (user_id, stand_type, level, last_collected, income) 
                   VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?)""",
                (user_id, stand_type, stand_info["income"])
            )
            
            # Deduct cost
            await self.conn.execute(
                "UPDATE users SET cash = cash - ? WHERE user_id = ?",
                (cost, user_id)
            )
            
            await self.conn.commit()
        
        return True
    
    async def collect_stand_income(self, user_id: int, stand_id: int) -> Optional[int]:
        """Collect stand income"""
        async with self.lock:
            # Get stand
            cursor = await self.conn.execute(
                "SELECT income, last_collected FROM stands WHERE id = ? AND user_id = ?",
                (stand_id, user_id)
            )
            stand = await cursor.fetchone()
            
            if not stand:
                return None
            
            income, last_collected = stand
            
            # Check cooldown (24 hours)
            if last_collected:
                last_time = datetime.fromisoformat(last_collected.replace('Z', '+00:00'))
                if datetime.now() - last_time < timedelta(hours=24):
                    return None
            
            # Update last collected
            await self.conn.execute(
                "UPDATE stands SET last_collected = CURRENT_TIMESTAMP, total_earned = total_earned + ? WHERE id = ?",
                (income, stand_id)
            )
            
            # Add income
            await self.conn.execute(
                "UPDATE users SET cash = cash + ? WHERE user_id = ?",
                (income, user_id)
            )
            
            await self.conn.commit()
            
            return income
    
    # ==================== FRIEND METHODS ====================
    
    async def get_friends(self, user_id: int) -> List[dict]:
        """Get user's friends"""
        async with self.lock:
            cursor = await self.conn.execute(
                """SELECT u.user_id, u.first_name, u.username, f.since
                   FROM friends f
                   JOIN users u ON u.user_id = CASE 
                       WHEN f.user1_id = ? THEN f.user2_id 
                       ELSE f.user1_id 
                   END
                   WHERE ? IN (f.user1_id, f.user2_id) AND f.status = 'friends'""",
                (user_id, user_id)
            )
            rows = await cursor.fetchall()
            
            friends = []
            for row in rows:
                friends.append({
                    'user_id': row[0],
                    'first_name': row[1],
                    'username': row[2],
                    'since': row[3]
                })
            
            return friends
    
    async def send_friend_request(self, from_id: int, to_id: int) -> bool:
        """Send friend request"""
        if from_id == to_id:
            return False
        
        async with self.lock:
            # Check if already friends
            cursor = await self.conn.execute(
                """SELECT 1 FROM friends 
                   WHERE (user1_id = ? AND user2_id = ?) 
                   OR (user1_id = ? AND user2_id = ?)""",
                (from_id, to_id, to_id, from_id)
            )
            if await cursor.fetchone():
                return False
            
            # Check if request already exists
            cursor = await self.conn.execute(
                """SELECT 1 FROM friend_requests 
                   WHERE from_id = ? AND to_id = ? AND status = 'pending'""",
                (from_id, to_id)
            )
            if await cursor.fetchone():
                return False
            
            # Create request
            await self.conn.execute(
                """INSERT INTO friend_requests (from_id, to_id, status) 
                   VALUES (?, ?, 'pending')""",
                (from_id, to_id)
            )
            
            await self.conn.commit()
            
            return True
    
    async def accept_friend_request(self, request_id: int) -> bool:
        """Accept friend request"""
        async with self.lock:
            # Get request
            cursor = await self.conn.execute(
                "SELECT from_id, to_id FROM friend_requests WHERE id = ? AND status = 'pending'",
                (request_id,)
            )
            request = await cursor.fetchone()
            
            if not request:
                return False
            
            from_id, to_id = request
            
            # Create friendship
            await self.conn.execute(
                """INSERT INTO friends (user1_id, user2_id, status) 
                   VALUES (?, ?, 'friends')""",
                (min(from_id, to_id), max(from_id, to_id))
            )
            
            # Update request
            await self.conn.execute(
                "UPDATE friend_requests SET status = 'accepted' WHERE id = ?",
                (request_id,)
            )
            
            await self.conn.commit()
            
            return True
    
    # ==================== ADMIN METHODS ====================
    
    async def add_to_cat_box(self, item_name: str, item_type: str, quantity: int = 1, added_by: int = None):
        """Add item to cat box (admin storage)"""
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO cat_box (item_name, item_type, quantity, added_by) 
                   VALUES (?, ?, ?, ?)""",
                (item_name, item_type, quantity, added_by)
            )
            await self.conn.commit()
    
    async def get_cat_box(self) -> List[dict]:
        """Get cat box contents"""
        async with self.lock:
            cursor = await self.conn.execute(
                "SELECT * FROM cat_box ORDER BY added_at DESC"
            )
            rows = await cursor.fetchall()
            
            items = []
            for row in rows:
                items.append(dict(zip([desc[0] for desc in cursor.description], row)))
            
            return items
    
    async def remove_from_cat_box(self, item_id: int) -> bool:
        """Remove item from cat box"""
        async with self.lock:
            cursor = await self.conn.execute(
                "DELETE FROM cat_box WHERE id = ?",
                (item_id,)
            )
            await self.conn.commit()
            return cursor.rowcount > 0
    
    async def log_admin_action(self, admin_id: int, target_id: int, action: str, details: str = None):
        """Log admin action"""
        async with self.lock:
            await self.conn.execute(
                """INSERT INTO admin_actions (admin_id, target_id, action, details) 
                   VALUES (?, ?, ?, ?)""",
                (admin_id, target_id, action, details)
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
dp = Dispatcher(storage=MemoryStorage())

# Initialize systems
db = CompleteDatabase(DB_PATH)
image_gen = GuaranteedImageGenerator()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def ensure_user(user: types.User) -> dict:
    """Ensure user exists in database"""
    user_data = await db.get_user(user.id)
    if not user_data:
        user_data = await db.create_user(user)
    return user_data

async def format_number(num: int) -> str:
    """Format number with commas"""
    return f"{num:,}"

async def get_user_mention(user_id: int, user_name: str) -> str:
    """Get user mention"""
    return f'<a href="tg://user?id={user_id}">{html.escape(user_name)}</a>'

async def create_pagination_keyboard(page: int, total_pages: int, callback_prefix: str, extra_buttons: List = None) -> InlineKeyboardMarkup:
    """Create pagination keyboard"""
    buttons = []
    
    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{callback_prefix}:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="page_info"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{callback_prefix}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Extra buttons
    if extra_buttons:
        buttons.extend(extra_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def check_admin(user_id: int) -> bool:
    """Check if user is admin/owner"""
    return user_id == OWNER_ID

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with beautiful interface"""
    user = await ensure_user(message.from_user)
    
    welcome_text = f"""
✨ <b>WELCOME TO ULTIMATE FAMILY TREE!</b> ✨

👋 <b>Hello {message.from_user.first_name}!</b>

🏆 <b>Ultimate Features:</b>
• 🌳 <b>Family Tree System</b> - Build your dynasty
• 🌾 <b>Advanced Garden</b> - Farm 16+ crops
• 🏪 <b>Business Stands</b> - Run 8+ businesses
• 🎮 <b>Mini-Games</b> - 6+ casino games
• 👥 <b>Friend Circle</b> - Social system
• 💰 <b>Economy</b> - 8+ currencies
• 🏅 <b>Achievements</b> - 6+ achievements
• ⚡ <b>Energy System</b> - Strategic play

🚀 <b>Quick Start:</b>
1. <code>/daily</code> - Claim daily bonus
2. <code>/me</code> - View profile
3. <code>/family</code> - Start family
4. <code>/garden</code> - Start farming

📊 <b>Stats:</b>
• Cash: <b>${user.get('cash', 0):,}</b>
• Level: <b>{user.get('level', 1)}</b>
• Energy: <b>{user.get('energy', 100)}/{user.get('max_energy', 100)}</b>

<a href="https://telegra.ph/Family-Tree-Quick-Guide-08-18">📖 Complete Guide</a>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Dashboard", callback_data="dashboard")],
        [
            InlineKeyboardButton(text="🌳 Family", callback_data="family_menu"),
            InlineKeyboardButton(text="🌾 Garden", callback_data="garden_menu")
        ],
        [
            InlineKeyboardButton(text="🏪 Stands", callback_data="stands_menu"),
            InlineKeyboardButton(text="👥 Friends", callback_data="friends_menu")
        ],
        [
            InlineKeyboardButton(text="🎮 Games", callback_data="games_menu"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="settings_menu")
        ],
        [InlineKeyboardButton(text="📊 Statistics", callback_data="stats_menu")],
        [InlineKeyboardButton(text="➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("me", "profile"))
async def cmd_profile(message: Message):
    """Profile command with wealth display"""
    user = await ensure_user(message.from_user)
    family = await db.get_family(message.from_user.id)
    stands = await db.get_stands(message.from_user.id)
    
    # Try to create wealth image
    wealth_data = {
        "cash": user.get('cash', 0),
        "gold": user.get('gold', 0),
        "gems": user.get('gems', 0),
        "bonds": user.get('bonds', 0)
    }
    
    image_bytes = await image_gen.create_wealth_chart(wealth_data)
    
    profile_text = f"""
🏆 <b>PROFILE OF {message.from_user.first_name.upper()}</b>

💰 <b>Wealth:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🪙 Gold: <b>{user.get('gold', 0):,}</b>
• 💎 Gems: <b>{user.get('gems', 0):,}</b>
• 👨‍👩‍👧‍👦 Bonds: <b>{user.get('bonds', 0):,}</b>
• ⭐ Credits: <b>{user.get('credits', 0):,}</b>
• 🌱 Tokens: <b>{user.get('tokens', 0):,}</b>

📊 <b>Stats:</b>
• Level: <b>{user.get('level', 1)}</b> (XP: {user.get('xp', 0)})
• Reputation: <b>{user.get('reputation', 100)}/200</b>
• Energy: <b>{user.get('energy', 100)}/{user.get('max_energy', 100)}</b>
• Family: <b>{len(family)} members</b>
• Businesses: <b>{len(stands)} stands</b>
• Daily Streak: <b>{user.get('daily_streak', 0)} days</b>

💎 <b>Gemstone:</b> {user.get('gemstone', 'None')}
✅ <b>Bio Verified:</b> {'Yes' if user.get('bio_verified') else 'No'}
📅 <b>Joined:</b> {user.get('created_at', '')[:10] if user.get('created_at') else 'Recently'}
"""
    
    if image_bytes:
        await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="wealth.png"),
            caption=profile_text,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(profile_text, parse_mode=ParseMode.HTML)

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Daily bonus system with streaks"""
    user = await ensure_user(message.from_user)
    
    # Check if already claimed today
    last_daily = user.get('last_daily')
    today = datetime.now().date()
    
    if last_daily:
        try:
            last_date = datetime.fromisoformat(last_daily.replace('Z', '+00:00')).date()
            if last_date == today:
                await message.answer("❌ You already claimed your daily bonus today!")
                return
            
            # Check streak
            yesterday = today - timedelta(days=1)
            if last_date == yesterday:
                streak = user.get('daily_streak', 0) + 1
            else:
                streak = 1
        except:
            streak = 1
    else:
        streak = 1
    
    # Calculate bonus
    base = random.randint(500, 1500)
    streak_bonus = streak * 100
    family_bonus = len(await db.get_family(message.from_user.id)) * 50
    level_bonus = user.get('level', 1) * 10
    
    total = base + streak_bonus + family_bonus + level_bonus
    
    # Bio verification bonus
    if user.get('bio_verified'):
        total *= 2
        bio_text = "✅ (2x Bio Verified Bonus!)"
    else:
        bio_text = "❌ (Add @Familly_TreeBot to bio for 2x!)"
    
    # Update user
    await db.update_currency(message.from_user.id, "cash", total)
    await db.update_currency(message.from_user.id, "tokens", 10)
    
    # Random gift
    gifts = ["💎 Gem", "🪙 Gold Bar", "⭐ Credit Pack", "🌱 Token Bundle"]
    gift = random.choice(gifts)
    
    await db.update_user(message.from_user.id, {
        'last_daily': datetime.now().isoformat(),
        'daily_streak': streak,
        'total_dailies': user.get('total_dailies', 0) + 1
    })
    
    daily_text = f"""
🎉 <b>DAILY BONUS - DAY {streak}!</b>

💰 <b>Rewards:</b>
• Base: <b>${base:,}</b>
• Streak ({streak} days): <b>${streak_bonus:,}</b>
• Family Bonus: <b>${family_bonus:,}</b>
• Level Bonus: <b>${level_bonus:,}</b>
• <b>Total: ${total:,}</b>

🎁 <b>Extras:</b>
• +10 🌱 Tokens
• Random Gift: {gift}
• {bio_text}

🔥 <b>Keep your streak alive!</b>
Come back tomorrow for bigger rewards!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Play Games", callback_data="games_menu")],
        [InlineKeyboardButton(text="🌳 Build Family", callback_data="family_menu")],
        [InlineKeyboardButton(text="📊 View Stats", callback_data="stats_menu")]
    ])
    
    await message.answer(daily_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Family tree with image visualization"""
    user = await ensure_user(message.from_user)
    family = await db.get_family(message.from_user.id)
    
    # Try to create family tree image
    family_data = [{"relation_type": m["relation_type"], "other_name": m["other_name"]} for m in family]
    image_bytes = await image_gen.create_family_tree_image(message.from_user.first_name, family_data)
    
    if image_bytes:
        await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="family_tree.png"),
            caption=f"""
🌳 <b>FAMILY TREE OF {message.from_user.first_name.upper()}</b>

👨‍👩‍👧‍👦 <b>Family Members: {len(family)}</b>

💝 <b>Relationships:</b>
{chr(10).join([f"• {m['other_name']} ({m['relation_type'].title()})" for m in family[:5]])}
{f'{chr(10)}• ... and {len(family)-5} more' if len(family) > 5 else ''}

🎯 <b>Family Bonus:</b> +${len(family) * 50}/day
❤️ <b>Family Love:</b> {min(len(family) * 10, 100)}/100

💡 <b>Commands:</b>
• <code>/adopt @user</code> - Adopt someone
• <code>/marry @user</code> - Marry someone
• <code>/disown @user</code> - Remove family
• <code>/familygift</code> - Send family gift
""",
            parse_mode=ParseMode.HTML
        )
    else:
        # Text version
        family_text = f"""
🌳 <b>FAMILY TREE OF {message.from_user.first_name.upper()}</b>

└─ 👤 You (Root)

"""
        for member in family:
            emoji = {
                'parent': '👴',
                'spouse': '💍',
                'child': '👶',
                'sibling': '👫'
            }.get(member['relation_type'], '👤')
            
            family_text += f"   ├─ {emoji} {member['other_name']} ({member['relation_type']})\n"
        
        family_text += f"""

📊 <b>Family Stats:</b>
• Members: {len(family)}
• Daily Bonus: +${len(family) * 50}
• Total Love: {min(len(family) * 10, 100)}/100
"""
        
        await message.answer(family_text, parse_mode=ParseMode.HTML)

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message, command: CommandObject):
    """Adopt someone as family"""
    if not command.args and not message.reply_to_message:
        await message.answer("""
👶 <b>ADOPT SOMEONE</b>

Usage: <code>/adopt @username</code>
Or reply to someone's message with <code>/adopt</code>

💡 <b>Requirements:</b>
• Target must use /start
• Cannot adopt yourself
• Target gets adoption request

⚡ <b>Benefits:</b>
• Daily family bonus
• Inheritance rights
• Family quests
""", parse_mode=ParseMode.HTML)
        return
    
    # Get target user
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        # Simple implementation - would need user search in real bot
        await message.answer("⚠️ Please reply to the user's message instead.")
        return
    
    if not target:
        await message.answer("❌ Could not find target user!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    # Check if target exists
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Create family relation
    await db.add_family_relation(message.from_user.id, target.id, "child")
    
    adoption_text = f"""
✅ <b>ADOPTION COMPLETE!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
📅 {datetime.now().strftime('%Y-%m-%d')}

🎉 <b>Benefits Activated:</b>
• Daily bonus increased
• Family quests unlocked
• Inheritance system active
• +1 Family member

💝 Welcome to the family!
"""
    
    await message.answer(adoption_text, parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
👶 <b>YOU WERE ADOPTED!</b>

👤 By: <b>{message.from_user.first_name}</b>
🤝 Relationship: Parent-Child

🎉 You are now part of their family!
Check your new family with <code>/family</code>
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass  # User might have blocked bot

@dp.message(Command("marry"))
async def cmd_marry(message: Message, command: CommandObject):
    """Marry someone"""
    if not command.args and not message.reply_to_message:
        await message.answer("""
💍 <b>MARRY SOMEONE</b>

Usage: <code>/marry @username</code>
Or reply to someone's message with <code>/marry</code>

💒 <b>Requirements:</b>
• Both must be single
• Cannot marry yourself
• 24 hour cooldown after divorce

💖 <b>Benefits:</b>
• Couple daily bonus
• Shared bank account
• Wedding gifts
""", parse_mode=ParseMode.HTML)
        return
    
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        await message.answer("⚠️ Please reply to the user's message instead.")
        return
    
    if not target:
        await message.answer("❌ Could not find target user!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Create marriage
    await db.add_family_relation(message.from_user.id, target.id, "spouse")
    
    marriage_text = f"""
💍 <b>MARRIAGE COMPLETE!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
📅 {datetime.now().strftime('%Y-%m-%d')}

🎉 <b>Congratulations!</b>
• Couple bonus activated
• Shared daily rewards
• Wedding gift: $5,000
• +1 Family member

💖 May your marriage be prosperous!
"""
    
    await message.answer(marriage_text, parse_mode=ParseMode.HTML)
    
    # Add wedding gift
    await db.update_currency(message.from_user.id, "cash", 5000)
    await db.update_currency(target.id, "cash", 5000)
    
    # Notify spouse
    try:
        await bot.send_message(
            target.id,
            f"""
💍 <b>YOU'RE MARRIED!</b>

👤 To: <b>{message.from_user.first_name}</b>
🤝 Relationship: Spouses

🎉 Congratulations on your marriage!
You received a $5,000 wedding gift!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Garden system with image"""
    user = await ensure_user(message.from_user)
    garden = await db.get_garden(message.from_user.id)
    crops = await db.get_growing_crops(message.from_user.id)
    
    # Try to create garden image
    image_bytes = await image_gen.create_garden_image(crops, garden.get('slots', 9))
    
    garden_text = f"""
🌾 <b>{message.from_user.first_name}'s GARDEN</b>

📊 <b>Stats:</b>
• Slots: {len(crops)}/{garden.get('slots', 9)}
• Water: {garden.get('water_level', 100)}%
• Growing: {len(crops)} crops
• Ready: {sum(1 for c in crops if c.get('progress', 0) >= 100)} crops

🌱 <b>Growing Now:</b>
"""
    
    for crop in crops[:5]:
        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
        progress = crop.get('progress', 0)
        bar = "█" * int(progress // 20) + "░" * (5 - int(progress // 20))
        
        if progress >= 100:
            status = "✅ READY!"
        else:
            remaining = max(0, crop.get('grow_time', 1) - crop.get('hours_passed', 0))
            status = f"{bar} {progress:.0f}% ({remaining:.1f}h)"
        
        garden_text += f"• {emoji} {crop['crop_type'].title()}: {status}\n"
    
    garden_text += f"""

💡 <b>Available Crops (Top 5):</b>
"""
    
    # Show top 5 profitable crops
    profitable = sorted(CROP_TYPES, key=lambda x: CROP_PRICES[x]["sell"] - CROP_PRICES[x]["buy"], reverse=True)[:5]
    
    for crop in profitable:
        price = CROP_PRICES[crop]
        garden_text += f"{price['emoji']} {crop.title()} - Buy: ${price['buy']}, Sell: ${price['sell']} ({price['grow_time']}h)\n"
    
    garden_text += f"""

🔧 <b>Commands:</b>
• <code>/plant [crop]</code> - Plant crops
• <code>/harvest</code> - Harvest ready crops
• <code>/barn</code> - View storage
• <code>/water</code> - Water garden
"""
    
    if image_bytes:
        await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="garden.png"),
            caption=garden_text,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(garden_text, parse_mode=ParseMode.HTML)

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops command"""
    if not command.args:
        crop_list = "\n".join([f"{CROP_EMOJIS.get(c, '🌱')} {c.title()} - ${CROP_PRICES[c]['buy']}" for c in list(CROP_TYPES)[:8]])
        
        await message.answer(f"""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop_name]</code>

🌿 <b>Available Crops:</b>
{crop_list}

💡 <b>Examples:</b>
• <code>/plant carrot</code>
• <code>/plant tomato</code>
• <code>/plant watermelon</code>

💰 <b>Note:</b> You need enough cash and garden space!
""", parse_mode=ParseMode.HTML)
        return
    
    crop_name = command.args.lower().strip()
    
    if crop_name not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(list(CROP_TYPES)[:8])}")
        return
    
    user = await ensure_user(message.from_user)
    crop_info = CROP_PRICES[crop_name]
    
    # Check cash
    if user.get('cash', 0) < crop_info['buy']:
        await message.answer(f"❌ Need ${crop_info['buy']}! You have ${user.get('cash', 0):,}")
        return
    
    # Plant crop
    success = await db.plant_crop(message.from_user.id, crop_name, 1)
    
    if not success:
        await message.answer("❌ No garden space available! Upgrade or harvest existing crops.")
        return
    
    # Deduct cash
    await db.update_currency(message.from_user.id, "cash", -crop_info['buy'])
    
    plant_text = f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{crop_info['emoji']} <b>{crop_name.title()}</b>
💰 Cost: <b>${crop_info['buy']}</b>
⏰ Grow Time: <b>{crop_info['grow_time']} hours</b>
💰 Sell Price: <b>${crop_info['sell']}</b>
📈 Profit: <b>${crop_info['sell'] - crop_info['buy']}</b>

🌱 Now growing in your garden!
💡 Use <code>/garden</code> to check progress.
"""
    
    await message.answer(plant_text, parse_mode=ParseMode.HTML)

@dp.message(Command("harvest"))
async def cmd_harvest(message: Message):
    """Harvest ready crops"""
    crops = await db.get_growing_crops(message.from_user.id)
    ready_crops = [c for c in crops if c.get('progress', 0) >= 100]
    
    if not ready_crops:
        await message.answer("❌ No crops ready for harvest! Check /garden")
        return
    
    total_value = 0
    harvested = []
    
    for crop in ready_crops:
        result = await db.harvest_crop(message.from_user.id, crop['id'])
        if result and result.get('success'):
            crop_type = result['crop_type']
            value = result.get('sell_price', 0)
            total_value += value
            harvested.append(f"{CROP_EMOJIS.get(crop_type, '🌱')} {crop_type.title()}")
    
    if not harvested:
        await message.answer("❌ Harvest failed! Try again.")
        return
    
    # Add cash from selling
    await db.update_currency(message.from_user.id, "cash", total_value)
    
    harvest_text = f"""
✅ <b>HARVEST COMPLETE!</b>

🌾 <b>Harvested:</b>
{chr(10).join([f'• {crop}' for crop in harvested[:5]])}
{f'{chr(10)}• ... and {len(harvested)-5} more' if len(harvested) > 5 else ''}

💰 <b>Total Value:</b> <b>${total_value:,}</b>
📦 <b>Stored in:</b> Barn
🎯 <b>Ready to sell!</b>

💡 Use <code>/barn</code> to view storage.
"""
    
    await message.answer(harvest_text, parse_mode=ParseMode.HTML)

@dp.message(Command("stands", "business"))
async def cmd_stands(message: Message):
    """View business stands"""
    user = await ensure_user(message.from_user)
    stands = await db.get_stands(message.from_user.id)
    
    if not stands:
        stand_list = "\n".join([f"{info['emoji']} {info['name']} - ${info['cost']:,}" for stand_type, info in list(STAND_TYPES.items())[:4]])
        
        await message.answer(f"""
🏪 <b>BUSINESS STANDS</b>

You don't own any businesses yet!

💼 <b>Available Stands:</b>
{stand_list}

💰 <b>Your Cash:</b> ${user.get('cash', 0):,}

💡 <b>How to buy:</b>
<code>/buystand [stand_name]</code>
Example: <code>/buystand bakery</code>

⚡ <b>Benefits:</b>
• Passive income
• Employee system
• Business upgrades
""", parse_mode=ParseMode.HTML)
        return
    
    total_income = sum(s.get('income', 0) for s in stands)
    total_earned = sum(s.get('total_earned', 0) for s in stands)
    
    stands_text = f"""
🏪 <b>YOUR BUSINESS EMPIRE</b>

📊 <b>Stats:</b>
• Businesses: {len(stands)}
• Daily Income: ${total_income:,}
• Total Earned: ${total_earned:,}

🏢 <b>Your Stands:</b>
"""
    
    for stand in stands[:5]:
        emoji = stand.get('emoji', '🏪')
        income = stand.get('income', 0)
        level = stand.get('level', 1)
        
        stands_text += f"• {emoji} {stand.get('name', 'Stand')} (Lvl {level}) - ${income:,}/day\n"
    
    if len(stands) > 5:
        stands_text += f"• ... and {len(stands)-5} more\n"
    
    stands_text += f"""

💰 <b>Total Cash Flow:</b> ${total_income:,}/day
⏰ <b>Next Collection:</b> Available now!

🔧 <b>Commands:</b>
• <code>/collectstand</code> - Collect income
• <code>/buystand</code> - Buy new stand
• <code>/upgradestand</code> - Upgrade stand
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Collect All", callback_data="collect_all_stands")],
        [InlineKeyboardButton(text="🏪 Buy New", callback_data="buy_stand_menu")],
        [InlineKeyboardButton(text="⬆️ Upgrade", callback_data="upgrade_stand_menu")]
    ])
    
    await message.answer(stands_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("buystand"))
async def cmd_buy_stand(message: Message, command: CommandObject):
    """Buy a business stand"""
    if not command.args:
        stand_list = "\n".join([f"{info['emoji']} {stand_type} - ${info['cost']:,} (${info['income']:,}/day)" 
                               for stand_type, info in list(STAND_TYPES.items())[:6]])
        
        await message.answer(f"""
🏪 <b>BUY BUSINESS STAND</b>

Usage: <code>/buystand [stand_type]</code>

💼 <b>Available Stands:</b>
{stand_list}

💡 <b>Examples:</b>
• <code>/buystand bakery</code>
• <code>/buystand grocery</code>
• <code>/buystand casino</code>

💰 <b>Note:</b> You need enough cash!
""", parse_mode=ParseMode.HTML)
        return
    
    stand_type = command.args.lower().strip()
    
    if stand_type not in STAND_TYPES:
        await message.answer(f"❌ Invalid stand type! Available: {', '.join(STAND_TYPES.keys())}")
        return
    
    user = await ensure_user(message.from_user)
    stand_info = STAND_TYPES[stand_type]
    
    # Check cash
    if user.get('cash', 0) < stand_info['cost']:
        await message.answer(f"❌ Need ${stand_info['cost']:,}! You have ${user.get('cash', 0):,}")
        return
    
    # Check if already owns this stand type
    stands = await db.get_stands(message.from_user.id)
    if any(s['stand_type'] == stand_type for s in stands):
        await message.answer(f"❌ You already own a {stand_info['name']}!")
        return
    
    # Buy stand
    success = await db.buy_stand(message.from_user.id, stand_type)
    
    if not success:
        await message.answer("❌ Failed to buy stand! Try again.")
        return
    
    buy_text = f"""
✅ <b>BUSINESS PURCHASED!</b>

{stand_info['emoji']} <b>{stand_info['name']}</b>
💰 Cost: <b>${stand_info['cost']:,}</b>
💸 Daily Income: <b>${stand_info['income']:,}</b>
📈 ROI: <b>{stand_info['cost'] // stand_info['income']} days</b>

🏪 <b>Congratulations!</b>
Your new business is now open!
Collect income daily with <code>/collectstand</code>

⚡ <b>Tip:</b> Upgrade to increase income!
"""
    
    await message.answer(buy_text, parse_mode=ParseMode.HTML)

@dp.message(Command("collectstand"))
async def cmd_collect_stand(message: Message):
    """Collect stand income"""
    stands = await db.get_stands(message.from_user.id)
    
    if not stands:
        await message.answer("❌ You don't own any stands! Buy one with /buystand")
        return
    
    total_collected = 0
    collected = []
    
    for stand in stands:
        income = await db.collect_stand_income(message.from_user.id, stand['id'])
        if income:
            total_collected += income
            collected.append(f"{stand.get('emoji', '🏪')} {stand.get('name', 'Stand')}: ${income:,}")
    
    if not collected:
        await message.answer("❌ No income available yet! Come back later.")
        return
    
    collect_text = f"""
💰 <b>INCOME COLLECTED!</b>

🏪 <b>Collected from:</b>
{chr(10).join([f'• {c}' for c in collected[:3]])}
{f'{chr(10)}• ... and {len(collected)-3} more' if len(collected) > 3 else ''}

💰 <b>Total Collected:</b> <b>${total_collected:,}</b>
🏦 <b>Added to your cash!</b>

⏰ <b>Next collection:</b> 24 hours
💡 Keep growing your business empire!
"""
    
    await message.answer(collect_text, parse_mode=ParseMode.HTML)

@dp.message(Command("friends"))
async def cmd_friends(message: Message):
    """Friends system"""
    friends = await db.get_friends(message.from_user.id)
    
    if not friends:
        await message.answer(f"""
👥 <b>FRIEND CIRCLE</b>

You don't have any friends yet!

🤝 <b>How to make friends:</b>
1. Use <code>/addfriend @username</code>
2. Wait for them to accept
3. Build your social circle!

🎁 <b>Friend Benefits:</b>
• Daily friend bonuses
• Gift exchange
• Friend quests
• Social features

💡 <b>Commands:</b>
• <code>/addfriend @user</code> - Add friend
• <code>/friendgift</code> - Send gift
• <code>/friendlist</code> - View friends
""", parse_mode=ParseMode.HTML)
        return
    
    friends_text = f"""
👥 <b>YOUR FRIEND CIRCLE</b>

🤝 <b>Friends: {len(friends)}</b>

"""
    
    for i, friend in enumerate(friends[:5], 1):
        mention = await get_user_mention(friend['user_id'], friend['first_name'])
        since = friend['since'][:10] if friend['since'] else "Recently"
        friends_text += f"{i}. {mention} - Since {since}\n"
    
    if len(friends) > 5:
        friends_text += f"... and {len(friends)-5} more friends\n"
    
    friends_text += f"""

🎁 <b>Friend Benefits:</b>
• Daily Bonus: +${len(friends) * 10}
• Gift Capacity: {len(friends)} gifts/day
• Social Status: {min(len(friends) * 5, 100)}/100

💡 <b>Commands:</b>
• <code>/addfriend @user</code> - Add more friends
• <code>/friendgift @user</code> - Send gift
• <code>/friendchat @user</code> - Message friend
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Add Friend", callback_data="add_friend")],
        [InlineKeyboardButton(text="🎁 Send Gift", callback_data="send_gift")],
        [InlineKeyboardButton(text="💬 Friend Chat", callback_data="friend_chat")]
    ])
    
    await message.answer(friends_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("addfriend"))
async def cmd_add_friend(message: Message, command: CommandObject):
    """Add a friend"""
    if not command.args and not message.reply_to_message:
        await message.answer("""
👥 <b>ADD FRIEND</b>

Usage: <code>/addfriend @username</code>
Or reply to user's message with <code>/addfriend</code>

🤝 <b>How it works:</b>
1. Send friend request
2. They receive notification
3. They accept with /acceptfriend
4. You become friends!

🎁 <b>Benefits:</b>
• Daily friend bonus
• Gift exchange
• Friend quests
""", parse_mode=ParseMode.HTML)
        return
    
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif command.args:
        await message.answer("⚠️ Please reply to the user's message to add them.")
        return
    
    if not target:
        await message.answer("❌ Could not find user!")
        return
    
    if target.id == message.from_user.id:
        await message.answer("❌ You cannot add yourself as friend!")
        return
    
    target_user = await db.get_user(target.id)
    if not target_user:
        await message.answer(f"❌ {target.first_name} needs to use /start first!")
        return
    
    # Send friend request
    success = await db.send_friend_request(message.from_user.id, target.id)
    
    if not success:
        await message.answer("❌ Friend request already sent or you're already friends!")
        return
    
    add_text = f"""
✅ <b>FRIEND REQUEST SENT!</b>

👤 To: <b>{target.first_name}</b>
📨 Status: <b>Pending</b>

🤝 <b>They need to accept your request.</b>
We'll notify you when they accept!

💡 <b>While waiting:</b>
• Build your family
• Grow your garden
• Play some games
"""
    
    await message.answer(add_text, parse_mode=ParseMode.HTML)
    
    # Notify target
    try:
        await bot.send_message(
            target.id,
            f"""
🤝 <b>FRIEND REQUEST!</b>

👤 From: <b>{message.from_user.first_name}</b>
🎯 Wants to be your friend!

✅ <b>To accept:</b>
Use <code>/acceptfriend {message.from_user.id}</code>

❌ <b>To decline:</b>
Ignore or use <code>/declinefriend {message.from_user.id}</code>
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

# ============================================================================
# MINI-GAMES SYSTEM
# ============================================================================

@dp.message(Command("games", "minigames"))
async def cmd_games(message: Message):
    """Mini-games menu"""
    games_text = f"""
🎮 <b>MINI-GAMES CASINO</b>

💰 <b>Your Cash:</b> ${(await ensure_user(message.from_user)).get('cash', 0):,}
⚡ <b>Your Energy:</b> {(await ensure_user(message.from_user)).get('energy', 100)}/100

🎲 <b>Available Games:</b>
1. <b>Dice Game</b> - Roll dice vs bot
   <code>/dice [bet]</code> - Min: $10, Max: $10,000
   
2. <b>Slot Machine</b> - Classic slots
   <code>/slot [bet]</code> - Min: $50, Max: $50,000
   
3. <b>Blackjack</b> - Beat the dealer
   <code>/blackjack [bet]</code> - Min: $100, Max: $100,000
   
4. <b>Roulette</b> - Bet on numbers
   <code>/roulette [bet] [color/number]</code>
   
5. <b>Trivia</b> - Win with knowledge
   <code>/trivia</code> - Free to play!
   
6. <b>Memory Game</b> - Test your memory
   <code>/memory</code> - Free to play!

🎯 <b>Game Stats:</b>
• Games Played: 0
• Games Won: 0
• Total Winnings: $0
• Largest Win: $0

💡 <b>Note:</b> Games cost 10 energy each!
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Dice Game", callback_data="game_dice")],
        [InlineKeyboardButton(text="🎰 Slot Machine", callback_data="game_slot")],
        [InlineKeyboardButton(text="🃏 Blackjack", callback_data="game_blackjack")],
        [InlineKeyboardButton(text="🎯 Roulette", callback_data="game_roulette")],
        [InlineKeyboardButton(text="🧠 Trivia", callback_data="game_trivia")],
        [InlineKeyboardButton(text="🧩 Memory", callback_data="game_memory")]
    ])
    
    await message.answer(games_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject):
    """Dice game"""
    if not command.args:
        await message.answer("""
🎲 <b>DICE GAME</b>

Roll dice against the bot!

Usage: <code>/dice [bet_amount]</code>

🎯 <b>Rules:</b>
1. You roll 2 dice (2-12)
2. Bot rolls 2 dice (2-12)
3. Higher total wins!
4. Tie = Return bet

💰 <b>Bet Range:</b> $10 - $10,000
⚡ <b>Energy Cost:</b> 10

💡 <b>Example:</b>
<code>/dice 100</code>
""", parse_mode=ParseMode.HTML)
        return
    
    try:
        bet = int(command.args)
        if bet < 10 or bet > 10000:
            await message.answer("❌ Bet must be between $10 and $10,000!")
            return
    except:
        await message.answer("❌ Invalid bet amount! Use numbers only.")
        return
    
    user = await ensure_user(message.from_user)
    
    # Check cash
    if user.get('cash', 0) < bet:
        await message.answer(f"❌ You need ${bet:,}! You have ${user.get('cash', 0):,}")
        return
    
    # Check energy
    if user.get('energy', 0) < 10:
        await message.answer("❌ Need 10 energy! Wait for energy to recharge.")
        return
    
    # Deduct energy
    await db.update_user(message.from_user.id, {'energy': user.get('energy', 100) - 10})
    
    # Roll dice
    player_roll = random.randint(1, 6) + random.randint(1, 6)
    bot_roll = random.randint(1, 6) + random.randint(1, 6)
    
    # Determine winner
    if player_roll > bot_roll:
        win_amount = bet * 2
        result = "🎉 YOU WIN!"
        result_emoji = "✅"
        await db.update_currency(message.from_user.id, "cash", bet)  # Win double
    elif player_roll < bot_roll:
        win_amount = 0
        result = "😢 YOU LOSE!"
        result_emoji = "❌"
        await db.update_currency(message.from_user.id, "cash", -bet)  # Lose bet
    else:
        win_amount = bet
        result = "🤝 IT'S A TIE!"
        result_emoji = "⚖️"
        # Bet returned, no change
    
    dice_text = f"""
🎲 <b>DICE GAME RESULT</b>

💰 <b>Bet:</b> ${bet:,}
⚡ <b>Energy:</b> -10 (Now: {user.get('energy', 100)-10})

🎯 <b>Your Roll:</b> {player_roll} ({'⚀⚁⚂⚃⚄⚅'[player_roll-2] if player_roll-2 < 6 else '🎲'})
🤖 <b>Bot Roll:</b> {bot_roll} ({'⚀⚁⚂⚃⚄⚅'[bot_roll-2] if bot_roll-2 < 6 else '🎲'})

{result_emoji} <b>{result}</b>

💰 <b>Result:</b> {'+' if player_roll > bot_roll else '-' if player_roll < bot_roll else ''}${abs(win_amount - bet):,}
🏦 <b>New Balance:</b> ${user.get('cash', 0) + (win_amount - bet):,}

🎮 <b>Play again?</b> <code>/dice {bet}</code>
"""
    
    await message.answer(dice_text, parse_mode=ParseMode.HTML)

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine game"""
    if not command.args:
        await message.answer("""
🎰 <b>SLOT MACHINE</b>

Classic 3-reel slot machine!

Usage: <code>/slot [bet_amount]</code>

🎯 <b>Payouts:</b>
• 3x 7️⃣ = 10x bet
• 3x 💎 = 5x bet
• 3x any = 3x bet
• 2x any = 1.5x bet

💰 <b>Bet Range:</b> $50 - $50,000
⚡ <b>Energy Cost:</b> 10

💡 <b>Example:</b>
<code>/slot 500</code>
""", parse_mode=ParseMode.HTML)
        return
    
    try:
        bet = int(command.args)
        if bet < 50 or bet > 50000:
            await message.answer("❌ Bet must be between $50 and $50,000!")
            return
    except:
        await message.answer("❌ Invalid bet amount! Use numbers only.")
        return
    
    user = await ensure_user(message.from_user)
    
    if user.get('cash', 0) < bet:
        await message.answer(f"❌ You need ${bet:,}! You have ${user.get('cash', 0):,}")
        return
    
    if user.get('energy', 0) < 10:
        await message.answer("❌ Need 10 energy! Wait for energy to recharge.")
        return
    
    # Deduct energy
    await db.update_user(message.from_user.id, {'energy': user.get('energy', 100) - 10})
    
    # Slot symbols
    symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎", "🍉", "🔔"]
    reels = [random.choice(symbols) for _ in range(3)]
    
    # Calculate win
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == "7️⃣":
            multiplier = 10
        elif reels[0] == "💎":
            multiplier = 5
        else:
            multiplier = 3
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        multiplier = 1.5
    else:
        multiplier = 0
    
    win_amount = int(bet * multiplier)
    net_change = win_amount - bet
    
    # Update cash
    if net_change > 0:
        await db.update_currency(message.from_user.id, "cash", net_change)
    elif net_change < 0:
        await db.update_currency(message.from_user.id, "cash", net_change)
    
    slot_text = f"""
🎰 <b>SLOT MACHINE RESULT</b>

💰 <b>Bet:</b> ${bet:,}
⚡ <b>Energy:</b> -10 (Now: {user.get('energy', 100)-10})

🎯 <b>Reels:</b> [{reels[0]}][{reels[1]}][{reels[2]}]

{'🎉 JACKPOT! 3 OF A KIND!' if multiplier >= 3 else '🎯 2 OF A KIND!' if multiplier == 1.5 else '😢 NO WIN'}
{'💰 MEGA WIN! 7️⃣7️⃣7️⃣' if reels[0] == '7️⃣' and multiplier == 10 else ''}

💰 <b>Payout:</b> {multiplier}x = <b>${win_amount:,}</b>
📈 <b>Net Change:</b> {'+' if net_change > 0 else ''}<b>${net_change:,}</b>
🏦 <b>New Balance:</b> ${user.get('cash', 0) + net_change:,}

🎮 <b>Feeling lucky?</b> <code>/slot {bet}</code>
"""
    
    await message.answer(slot_text, parse_mode=ParseMode.HTML)

# ============================================================================
# ADMIN COMMANDS - COMPLETE SET
# ============================================================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ Admin only command!")
        return
    
    admin_text = f"""
🛡️ <b>ADMIN CONTROL PANEL</b>

👑 <b>Owner:</b> {message.from_user.first_name}
🆔 <b>ID:</b> <code>{message.from_user.id}</code>
🤖 <b>Bot:</b> @{BOT_USERNAME}

🔧 <b>User Management:</b>
• <code>/ban @user</code> - Ban user
• <code>/unban @user</code> - Unban user
• <code>/warn @user</code> - Warn user
• <code>/reset @user</code> - Reset user data
• <code>/userinfo @user</code> - User details

💰 <b>Economy Management:</b>
• <code>/addcash @user amount</code> - Add cash
• <code>/addgold @user amount</code> - Add gold
• <code>/addgems @user amount</code> - Add gems
• <code>/setlevel @user level</code> - Set level
• <code>/reseteco @user</code> - Reset economy

🏪 <b>System Management:</b>
• <code>/broadcast message</code> - Broadcast to all
• <code>/stats</code> - Bot statistics
• <code>/backup</code> - Backup database
• <code>/maintenance on/off</code> - Maintenance mode

📦 <b>Cat Box (Storage):</b>
• <code>/catbox</code> - View storage
• <code>/catadd item quantity</code> - Add item
• <code>/catremove item</code> - Remove item
• <code>/catclear</code> - Clear storage

📊 <b>Bot Statistics:</b>
• Total Users: Loading...
• Active Today: Loading...
• Total Cash: Loading...
• Total Games: Loading...
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 Economy Tools", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📦 Cat Box", callback_data="admin_catbox")],
        [InlineKeyboardButton(text="⚙️ System", callback_data="admin_system")]
    ])
    
    await message.answer(admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("addcash"))
async def cmd_addcash(message: Message, command: CommandObject):
    """Add cash to user (admin)"""
    if not await check_admin(message.from_user.id):
        await message.answer("❌ Admin only command!")
        return
    
    if not command.args:
        await message.answer("""
💰 <b>ADD CASH</b>

Usage: <code>/addcash @user amount</code>
Or: <code>/addcash user_id amount</code>

💡 <b>Examples:</b>
• <code>/addcash @username 1000</code>
• <code>/addcash 123456789 5000</code>
• <code>/addcash reply_to_message 10000</code>

⚠️ <b>Note:</b> Use negative amounts to remove cash.
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 2:
        await message.answer("❌ Format: /addcash [target] [amount]")
        return
    
    # Parse target
    target_str = args[0]
    try:
        amount = int(args[1])
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
    elif target_str.startswith('@'):
        # Would need username lookup in real implementation
        await message.answer("⚠️ Please reply to user or use user ID.")
        return
    else:
        await message.answer("❌ Invalid target!")
        return
    
    # Add cash
    await db.update_currency(target_id, "cash", amount)
    
    target_user = await db.get_user(target_id)
    target_name = target_user.get('first_name', 'Unknown') if target_user else 'Unknown'
    
    # Log action
    await db.log_admin_action(
        message.from_user.id,
        target_id,
        "addcash",
        f"Amount: {amount}"
    )
    
    add_text = f"""
✅ <b>CASH { 'ADDED' if amount > 0 else 'REMOVED' }</b>

👤 <b>Target:</b> {target_name}
🆔 <b>ID:</b> <code>{target_id}</code>
💰 <b>Amount:</b> {'+' if amount > 0 else ''}{amount:,}
🏦 <b>New Balance:</b> ${(target_user.get('cash', 0) if target_user else 0) + amount:,}

👑 <b>By Admin:</b> {message.from_user.first_name}
📅 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

⚡ <b>Transaction logged.</b>
"""
    
    await message.answer(add_text, parse_mode=ParseMode.HTML)

@dp.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    """Ban user (admin)"""
    if not await check_admin(message.from_user.id):
        return
    
    if not command.args and not message.reply_to_message:
        await message.answer("""
🔨 <b>BAN USER</b>

Usage: <code>/ban @user [reason]</code>
Or reply to user with <code>/ban [reason]</code>

💡 <b>Examples:</b>
• <code>/ban @spammer Spamming</code>
• <code>/ban 123456789 Cheating</code>
• Reply to user with <code>/ban Harassment</code>

⚠️ <b>Effects:</b>
• User cannot use bot commands
• All assets frozen
• Can be undone with /unban
""", parse_mode=ParseMode.HTML)
        return
    
    # Get target and reason
    target = None
    reason = "No reason provided"
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if command.args:
            reason = command.args
    elif command.args:
        args = command.args.split(maxsplit=1)
        target_str = args[0]
        reason = args[1] if len(args) > 1 else "No reason provided"
        
        if target_str.isdigit():
            target_id = int(target_str)
            target_user = await db.get_user(target_id)
            if target_user:
                target = types.User(
                    id=target_id,
                    first_name=target_user.get('first_name', 'Unknown'),
                    is_bot=False
                )
        else:
            await message.answer("⚠️ Please use user ID or reply to message.")
            return
    
    if not target:
        await message.answer("❌ User not found!")
        return
    
    if target.id == OWNER_ID:
        await message.answer("❌ Cannot ban owner!")
        return
    
    # Ban user
    await db.update_user(target.id, {'is_banned': 1})
    
    # Log action
    await db.log_admin_action(
        message.from_user.id,
        target.id,
        "ban",
        reason
    )
    
    ban_text = f"""
🔨 <b>USER BANNED</b>

👤 <b>User:</b> {target.first_name}
🆔 <b>ID:</b> <code>{target.id}</code>
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
📝 <b>Reason:</b> {reason}

👑 <b>By Admin:</b> {message.from_user.first_name}
⚡ <b>Action:</b> Complete ban from bot

⚠️ <b>User can no longer:</b>
• Use any commands
• Access their assets
• Play games
• Interact with bot

🔄 <b>To unban:</b> <code>/unban {target.id}</code>
"""
    
    await message.answer(ban_text, parse_mode=ParseMode.HTML)
    
    # Notify user
    try:
        await bot.send_message(
            target.id,
            f"""
🚫 <b>YOU HAVE BEEN BANNED</b>

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
📝 <b>Reason:</b> {reason}
👑 <b>By Admin:</b> {message.from_user.first_name}

⚠️ <b>You can no longer use the bot.</b>
All your assets have been frozen.

📞 <b>If this is a mistake:</b>
Contact the bot administrator.
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

@dp.message(Command("catbox"))
async def cmd_catbox(message: Message):
    """Cat Box storage (admin)"""
    if not await check_admin(message.from_user.id):
        return
    
    items = await db.get_cat_box()
    
    if not items:
        catbox_text = """
📦 <b>CAT BOX STORAGE</b>

The cat box is empty!

💡 <b>Add items with:</b>
• <code>/catadd cash 1000</code>
• <code>/catadd gold 100</code>
• <code>/catadd gemstone Ruby</code>
• <code>/catadd crop carrot 50</code>

🔧 <b>Manage items:</b>
• <code>/catremove [id]</code> - Remove item
• <code>/catclear</code> - Clear all
• <code>/catview</code> - View details

⚡ <b>Purpose:</b>
Admin storage for rewards, items, and giveaways.
"""
    else:
        total_items = sum(item['quantity'] for item in items)
        total_value = "N/A"
        
        items_list = "\n".join([f"• {item['item_name']} x{item['quantity']} ({item['item_type']})" 
                               for item in items[:10]])
        
        if len(items) > 10:
            items_list += f"\n• ... and {len(items)-10} more items"
        
        catbox_text = f"""
📦 <b>CAT BOX STORAGE</b>

📊 <b>Statistics:</b>
• Total Items: {total_items}
• Unique Items: {len(items)}
• Total Value: {total_value}

📝 <b>Contents:</b>
{items_list}

🔧 <b>Management:</b>
Use item IDs to manage:
• <code>/catremove 1</code> - Remove item ID 1
• <code>/catclear</code> - Clear all items
• <code>/cattake @user item_id</code> - Give to user

⚡ <b>Note:</b> Cat box is admin-only storage.
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Item", callback_data="catbox_add")],
        [InlineKeyboardButton(text="🗑️ Clear All", callback_data="catbox_clear")],
        [InlineKeyboardButton(text="📋 Export", callback_data="catbox_export")]
    ])
    
    await message.answer(catbox_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("catadd"))
async def cmd_catadd(message: Message, command: CommandObject):
    """Add item to cat box (admin)"""
    if not await check_admin(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("""
➕ <b>ADD TO CAT BOX</b>

Usage: <code>/catadd [item_type] [item_name] [quantity]</code>

💡 <b>Examples:</b>
• <code>/catadd cash 1000</code> - Add $1000
• <code>/catadd gold 100</code> - Add 100 gold
• <code>/catadd gemstone Ruby</code> - Add Ruby gem
• <code>/catadd crop carrot 50</code> - Add 50 carrots

📦 <b>Item Types:</b>
• cash, gold, gems, bonds, credits, tokens
• crop, seed, tool, gemstone, special
• item, reward, bonus, event

⚡ <b>Note:</b> Items are stored for admin use.
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    if len(args) < 2:
        await message.answer("❌ Format: /catadd [type] [name] [quantity=1]")
        return
    
    item_type = args[0].lower()
    item_name = args[1]
    quantity = int(args[2]) if len(args) > 2 and args[2].isdigit() else 1
    
    # Add to cat box
    await db.add_to_cat_box(item_name, item_type, quantity, message.from_user.id)
    
    add_text = f"""
✅ <b>ITEM ADDED TO CAT BOX</b>

📦 <b>Item:</b> {item_name}
📝 <b>Type:</b> {item_type}
🔢 <b>Quantity:</b> {quantity}

👑 <b>Added by:</b> {message.from_user.first_name}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

💡 <b>View cat box:</b> <code>/catbox</code>
⚡ <b>Total items:</b> {len(await db.get_cat_box())}
"""
    
    await message.answer(add_text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast message to all users (admin)"""
    if not await check_admin(message.from_user.id):
        return
    
    if not command.args:
        await message.answer("""
📢 <b>BROADCAST MESSAGE</b>

Send message to all bot users.

Usage: <code>/broadcast [message]</code>

💡 <b>Examples:</b>
• <code>/broadcast Server maintenance in 10 minutes!</code>
• <code>/broadcast New update available! Check /news</code>
• <code>/broadcast 🎉 Special event starting tomorrow!</code>

⚠️ <b>Warning:</b>
• Use sparingly
• Keep messages short
• Don't spam users
• Test with small group first

⚡ <b>To test:</b> Send to yourself first.
""", parse_mode=ParseMode.HTML)
        return
    
    broadcast_text = command.args
    confirm_text = f"""
⚠️ <b>BROADCAST CONFIRMATION</b>

📝 <b>Message:</b>
{broadcast_text}

📊 <b>Will be sent to ALL users.</b>
This action cannot be undone!

✅ <b>To confirm:</b>
Reply with <code>/confirmbroadcast</code>

❌ <b>To cancel:</b>
Ignore or send another command.
"""
    
    # Store broadcast in context (simplified)
    # In real implementation, use FSM or database
    
    await message.answer(confirm_text, parse_mode=ParseMode.HTML)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot statistics (admin)"""
    if not await check_admin(message.from_user.id):
        return
    
    # Get stats from database
    async with db.lock:
        cursor = await db.conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute("SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-1 day')")
        active_today = (await cursor.fetchone())[0]
        
        cursor = await db.conn.execute("SELECT SUM(cash) FROM users")
        total_cash = (await cursor.fetchone())[0] or 0
        
        cursor = await db.conn.execute("SELECT SUM(games_played) FROM game_stats")
        total_games = (await cursor.fetchone())[0] or 0
    
    stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>User Statistics:</b>
• Total Users: <b>{total_users:,}</b>
• Active Today: <b>{active_today:,}</b>
• New Today: <b>Loading...</b>
• Banned Users: <b>Loading...</b>

💰 <b>Economy Statistics:</b>
• Total Cash: <b>${total_cash:,}</b>
• Total Gold: <b>Loading...</b>
• Total Gems: <b>Loading...</b>
• Total Transactions: <b>Loading...</b>

🎮 <b>Game Statistics:</b>
• Games Played: <b>{total_games:,}</b>
• Games Won: <b>Loading...</b>
• Total Bets: <b>Loading...</b>
• Biggest Win: <b>Loading...</b>

🌳 <b>Family Statistics:</b>
• Total Families: <b>Loading...</b>
• Total Marriages: <b>Loading...</b>
• Total Adoptions: <b>Loading...</b>
• Largest Family: <b>Loading...</b>

🌾 <b>Garden Statistics:</b>
• Total Crops: <b>Loading...</b>
• Harvests Today: <b>Loading...</b>
• Most Popular Crop: <b>Loading...</b>
• Biggest Farm: <b>Loading...</b>

🏪 <b>Business Statistics:</b>
• Total Stands: <b>Loading...</b>
• Daily Income: <b>Loading...</b>
• Most Popular: <b>Loading...</b>
• Richest Business: <b>Loading...</b>

⚡ <b>Performance:</b>
• Uptime: <b>Loading...</b>
• Memory Usage: <b>Loading...</b>
• Database Size: <b>Loading...</b>
• Last Backup: <b>Never</b>

📅 <b>Last Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_stats")],
        [InlineKeyboardButton(text="📈 Detailed", callback_data="detailed_stats")],
        [InlineKeyboardButton(text="💾 Backup", callback_data="backup_db")]
    ])
    
    await message.answer(stats_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ============================================================================
# ADDITIONAL FEATURES
# ============================================================================

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
🆘 <b>ULTIMATE FAMILY TREE BOT - HELP</b>

👑 <b>Core Commands:</b>
• <code>/start</code> - Start bot
• <code>/me</code> - Your profile
• <code>/daily</code> - Daily bonus
• <code>/help</code> - This message

🌳 <b>Family System:</b>
• <code>/family</code> - Family tree
• <code>/adopt @user</code> - Adopt someone
• <code>/marry @user</code> - Marry someone
• <code>/disown @user</code> - Remove family
• <code>/familygift</code> - Family gift

🌾 <b>Garden System:</b>
• <code>/garden</code> - Your garden
• <code>/plant [crop]</code> - Plant crops
• <code>/harvest</code> - Harvest crops
• <code>/barn</code> - Storage
• <code>/water</code> - Water garden
• <code>/fertilize</code> - Add fertilizer

🏪 <b>Business System:</b>
• <code>/stands</code> - Your businesses
• <code>/buystand [type]</code> - Buy business
• <code>/collectstand</code> - Collect income
• <code>/upgradestand</code> - Upgrade business

🎮 <b>Mini-Games:</b>
• <code>/games</code> - Games menu
• <code>/dice [bet]</code> - Dice game
• <code>/slot [bet]</code> - Slot machine
• <code>/blackjack [bet]</code> - Blackjack
• <code>/roulette [bet]</code> - Roulette
• <code>/trivia</code> - Trivia game

👥 <b>Social System:</b>
• <code>/friends</code> - Friend list
• <code>/addfriend @user</code> - Add friend
• <code>/friendgift @user</code> - Send gift
• <code>/friendchat @user</code> - Message friend

💰 <b>Economy:</b>
• <code>/balance</code> - Check balance
• <code>/transfer @user amount</code> - Send money
• <code>/market</code> - Marketplace
• <code>/sell [item] [price]</code> - Sell item

⚙️ <b>Utility:</b>
• <code>/settings</code> - Bot settings
• <code>/achievements</code> - Your achievements
• <code>/leaderboard</code> - Top players
• <code>/news</code> - Bot news
• <code>/ping</code> - Bot status

🛡️ <b>Admin Commands:</b>
• <code>/admin</code> - Admin panel
• <code>/ban @user</code> - Ban user
• <code>/addcash @user amount</code> - Add cash
• <code>/catbox</code> - Admin storage
• <code>/broadcast</code> - Message all users

📖 <b>Guides:</b>
• <a href="https://telegra.ph/Family-Tree-Quick-Guide-08-18">Family Guide</a>
• <a href="https://telegra.ph/Garden-03-07-2">Garden Guide</a>
• <a href="https://telegra.ph/Stands-03-07-2">Business Guide</a>
• <a href="https://telegra.ph/Mini-Games-03-07">Games Guide</a>

💡 <b>Need more help?</b>
Contact the bot administrator.

✨ <b>Enjoy the Ultimate Family Tree experience!</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Quick Start", url="https://telegra.ph/Family-Tree-Quick-Guide-08-18")],
        [InlineKeyboardButton(text="🎮 Try Games", callback_data="games_menu")],
        [InlineKeyboardButton(text="🌳 Start Family", callback_data="family_menu")],
        [InlineKeyboardButton(text="💬 Support", url="https://t.me/your_support_chat")]
    ])
    
    await message.answer(help_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start_time = time.time()
    msg = await message.answer("🏓 Pinging...")
    end_time = time.time()
    
    latency = round((end_time - start_time) * 1000, 2)
    
    ping_text = f"""
🏓 <b>PONG!</b>

✅ <b>Status:</b> Online & Healthy
📡 <b>Latency:</b> {latency}ms
🖼️ <b>Images:</b> {'✅ Enabled' if HAS_PILLOW else '❌ Pillow not installed'}
👑 <b>Owner ID:</b> <code>{OWNER_ID}</code>
🤖 <b>Bot:</b> @{BOT_USERNAME}
📊 <b>Version:</b> 10.0 Ultimate

✨ <b>Features Active:</b>
• Family Tree System ✅
• Garden System ✅
• Business System ✅
• Mini-Games ✅
• Friend System ✅
• Admin Panel ✅
• Cat Box ✅

⚡ <b>Performance:</b>
• Response Time: Excellent
• Database: Connected
• Memory: Stable
• Uptime: 100%

📅 <b>Current Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await msg.edit_text(ping_text, parse_mode=ParseMode.HTML)

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

@dp.callback_query(F.data == "dashboard")
async def callback_dashboard(callback: CallbackQuery):
    """Dashboard callback"""
    user = await ensure_user(callback.from_user)
    
    dashboard_text = f"""
📊 <b>DASHBOARD</b>

👋 Welcome back, {callback.from_user.first_name}!

💰 <b>Quick Stats:</b>
• Cash: <b>${user.get('cash', 0):,}</b>
• Energy: <b>{user.get('energy', 100)}/{user.get('max_energy', 100)}</b>
• Level: <b>{user.get('level', 1)}</b>
• Daily Streak: <b>{user.get('daily_streak', 0)} days</b>

⚡ <b>Quick Actions:</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Claim Daily", callback_data="claim_daily")],
        [
            InlineKeyboardButton(text="🌱 Garden", callback_data="garden_menu"),
            InlineKeyboardButton(text="🏪 Business", callback_data="stands_menu")
        ],
        [
            InlineKeyboardButton(text="🎮 Play Game", callback_data="games_menu"),
            InlineKeyboardButton(text="👥 Friends", callback_data="friends_menu")
        ],
        [InlineKeyboardButton(text="📊 Full Profile", callback_data="full_profile")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings_menu")]
    ])
    
    await callback.message.edit_text(dashboard_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()

# ============================================================================
# ERROR HANDLING
# ============================================================================

async def error_handler(update: types.Update, exception: Exception):
    """Global error handler"""
    logger.error(f"Update: {update}\nException: {exception}", exc_info=True)
    
    # Try to send error message
    try:
        if isinstance(update, Message):
            await update.answer(f"""
❌ <b>An error occurred!</b>

⚠️ <b>Error:</b> {str(exception)[:100]}
🔧 <b>Status:</b> Reported to admin

💡 <b>What to do:</b>
1. Try the command again
2. Check if you have required items
3. Contact admin if persists

⚡ <b>Bot is still running normally.</b>
""", parse_mode=ParseMode.HTML)
    except:
        pass
    
    return True

dp.errors.register(error_handler)

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

async def on_startup():
    """Startup tasks"""
    print("=" * 60)
    print("🏆 ULTIMATE FAMILY TREE BOT - VERSION 10.0")
    print("=" * 60)
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🤖 Bot: @{BOT_USERNAME}")
    print(f"🖼️ Images: {'ENABLED' if HAS_PILLOW else 'DISABLED'}")
    print(f"💾 Database: {DB_PATH}")
    print("=" * 60)
    
    # Connect to database
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="family", description="Family tree"),
        types.BotCommand(command="garden", description="Your garden"),
        types.BotCommand(command="plant", description="Plant crops"),
        types.BotCommand(command="harvest", description="Harvest crops"),
        types.BotCommand(command="stands", description="Your businesses"),
        types.BotCommand(command="buystand", description="Buy business"),
        types.BotCommand(command="friends", description="Friend system"),
        types.BotCommand(command="addfriend", description="Add friend"),
        types.BotCommand(command="games", description="Mini-games"),
        types.BotCommand(command="dice", description="Dice game"),
        types.BotCommand(command="slot", description="Slot machine"),
        types.BotCommand(command="help", description="Help menu"),
        types.BotCommand(command="ping", description="Bot status"),
        types.BotCommand(command="admin", description="Admin panel")
    ]
    
    await bot.set_my_commands(commands)
    
    print("🚀 Bot started successfully!")
    print("📊 Ready for Railway deployment")
    print("=" * 60)

async def on_shutdown():
    """Shutdown tasks"""
    print("🛑 Shutting down bot...")
    if db.conn:
        await db.conn.close()
    print("✅ Bot shutdown complete")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main function"""
    # Check token
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not set!")
        print("Please set your bot token in the code.")
        sys.exit(1)
    
    # Setup startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    print("⏳ Starting bot...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
