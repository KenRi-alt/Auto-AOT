#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - ULTIMATE EDITION
With Admin Dashboard, Image Visualizations & Advanced Features
Bot: @Familly_TreeBot
"""

import os
import sys
import json
import asyncio
import logging
import random
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import html
import uuid
import hashlib
import time
import aiofiles
import io
import base64
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ============================================================================
# CORRECT IMPORTS FOR AIOGRAM 3.0.0b7 (NO DefaultBotProperties)
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, FSInputFile, BufferedInputFile,
        InputMediaPhoto
    )
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    
    # CORRECT: Using parse_mode in bot initialization
    from aiogram.enums import ParseMode
    from aiogram.client.session.aiohttp import AiohttpSession
    
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
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
LOG_CHANNEL = -1003662720845
BOT_USERNAME = "@Familly_TreeBot"
DB_PATH = os.getenv("DB_PATH", "family_bot.db")

# Game Constants
CURRENCIES = ["cash", "gold", "bonds", "credits", "tokens", "event_coins"]
CURRENCY_EMOJIS = {
    "cash": "💵", "gold": "🪙", "bonds": "👨‍👩‍👧‍👦", 
    "credits": "⭐", "tokens": "🌱", "event_coins": "🎪"
}

CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "pepper", "watermelon", "pumpkin"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔", 
    "eggplant": "🍆", "corn": "🌽", "pepper": "🫑",
    "watermelon": "🍉", "pumpkin": "🎃"
}

# Colors for visualizations
COLORS = {
    "primary": "#4CAF50",
    "secondary": "#2196F3", 
    "accent": "#FF9800",
    "success": "#8BC34A",
    "warning": "#FFC107",
    "danger": "#F44336",
    "background": "#121212",
    "card": "#1E1E1E",
    "text": "#FFFFFF"
}

# ============================================================================
# IMAGE VISUALIZATION SYSTEM
# ============================================================================

class ImageVisualizer:
    """Create image-based visualizations"""
    
    def __init__(self):
        self.font_path = None
        # Try to find a font
        try:
            # Common font paths
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/SFNS.ttf",
                "arial.ttf"
            ]
            for path in font_paths:
                if os.path.exists(path):
                    self.font_path = path
                    break
        except:
            self.font_path = None
    
    def _get_font(self, size=20):
        """Get font with fallback"""
        try:
            if self.font_path:
                return ImageFont.truetype(self.font_path, size)
        except:
            pass
        return ImageFont.load_default()
    
    async def create_family_tree_image(self, user_name: str, family_data: List[dict]) -> bytes:
        """Create family tree as image"""
        # Create image
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color=COLORS["background"])
        draw = ImageDraw.Draw(image)
        
        # Title
        title = f"Family Tree of {user_name}"
        font_large = self._get_font(30)
        title_bbox = draw.textbbox((0, 0), title, font=font_large)
        title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 30), title, fill=COLORS["primary"], font=font_large)
        
        # Draw user at center
        user_circle = (width // 2, 150)
        draw.ellipse([user_circle[0]-40, user_circle[1]-40, 
                     user_circle[0]+40, user_circle[1]+40], 
                    fill=COLORS["secondary"], outline=COLORS["accent"], width=3)
        
        font_medium = self._get_font(20)
        user_text = textwrap.fill(user_name, width=10)
        text_bbox = draw.textbbox((0, 0), user_text, font=font_medium)
        text_x = user_circle[0] - (text_bbox[2] - text_bbox[0]) // 2
        text_y = user_circle[1] - (text_bbox[3] - text_bbox[1]) // 2
        draw.text((text_x, text_y), user_text, fill=COLORS["text"], font=font_medium)
        
        # Draw family members
        positions = []
        relations = ["parent", "spouse", "child", "sibling"]
        
        for i, rel in enumerate(relations):
            members = [m for m in family_data if m['relation_type'] == rel]
            if not members:
                continue
                
            # Calculate position
            angle = (i * 90) - 45  # Spread around user
            radius = 200
            x = user_circle[0] + radius * (i % 2) * (1 if i < 2 else -1)
            y = user_circle[1] + radius * (1 if i in [1, 2] else -1)
            
            # Draw connecting line
            draw.line([user_circle, (x, y)], fill=COLORS["accent"], width=2)
            
            # Draw member circle
            draw.ellipse([x-30, y-30, x+30, y+30], 
                        fill=COLORS["success"], outline=COLORS["warning"], width=2)
            
            # Draw member name
            if members:
                member = members[0]
                name = textwrap.fill(member['first_name'][:8], width=6)
                font_small = self._get_font(16)
                text_bbox = draw.textbbox((0, 0), name, font=font_small)
                text_x = x - (text_bbox[2] - text_bbox[0]) // 2
                text_y = y - (text_bbox[3] - text_bbox[1]) // 2
                draw.text((text_x, text_y), name, fill=COLORS["text"], font=font_small)
                
                # Draw relation label
                rel_text = f"({rel})"
                rel_bbox = draw.textbbox((0, 0), rel_text, font=self._get_font(14))
                rel_x = x - (rel_bbox[2] - rel_bbox[0]) // 2
                draw.text((rel_x, y+25), rel_text, fill=COLORS["warning"], font=self._get_font(14))
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    async def create_garden_image(self, garden_data: dict) -> bytes:
        """Create garden visualization image"""
        width, height = 600, 800
        image = Image.new('RGB', (width, height), color=COLORS["background"])
        draw = ImageDraw.Draw(image)
        
        # Title
        title = "🌾 Your Garden"
        font_large = self._get_font(35)
        draw.text((width//4, 30), title, fill=COLORS["primary"], font=font_large)
        
        # Garden grid
        slots = garden_data.get('slots', 9)
        plants = garden_data.get('plants', [])
        used = len(plants)
        
        grid_size = 3
        cell_size = 80
        start_x = (width - (grid_size * cell_size)) // 2
        start_y = 150
        
        for row in range(grid_size):
            for col in range(grid_size):
                idx = row * grid_size + col
                x1 = start_x + col * cell_size
                y1 = start_y + row * cell_size
                x2 = x1 + cell_size - 5
                y2 = y1 + cell_size - 5
                
                if idx < slots:
                    if idx < used and plants:
                        # Draw plant
                        plant = plants[min(idx, len(plants)-1)]
                        crop_type = plant['crop_type']
                        progress = plant.get('progress', 0)
                        
                        # Plant color based on progress
                        if progress >= 100:
                            color = COLORS["success"]
                        elif progress >= 50:
                            color = COLORS["warning"]
                        else:
                            color = COLORS["secondary"]
                        
                        draw.rounded_rectangle([x1, y1, x2, y2], radius=10, 
                                             fill=color, outline=COLORS["accent"], width=2)
                        
                        # Plant emoji/text
                        emoji = CROP_EMOJIS.get(crop_type, "🌱")
                        font_medium = self._get_font(30)
                        emoji_bbox = draw.textbbox((0, 0), emoji, font=font_medium)
                        emoji_x = x1 + (cell_size - (emoji_bbox[2] - emoji_bbox[0])) // 2
                        emoji_y = y1 + (cell_size - (emoji_bbox[3] - emoji_bbox[1])) // 2
                        draw.text((emoji_x, emoji_y), emoji, fill=COLORS["text"], font=font_medium)
                        
                        # Progress text
                        progress_text = f"{progress}%"
                        font_small = self._get_font(12)
                        prog_bbox = draw.textbbox((0, 0), progress_text, font=font_small)
                        prog_x = x1 + (cell_size - (prog_bbox[2] - prog_bbox[0])) // 2
                        draw.text((prog_x, y2-15), progress_text, fill=COLORS["text"], font=font_small)
                    else:
                        # Empty slot
                        draw.rounded_rectangle([x1, y1, x2, y2], radius=10, 
                                             fill=COLORS["card"], outline=COLORS["secondary"], width=1)
                        draw.text((x1+25, y1+25), "🟫", fill=COLORS["text"], font=self._get_font(25))
                else:
                    # Locked slot
                    draw.rounded_rectangle([x1, y1, x2, y2], radius=10, 
                                         fill=(50, 50, 50), outline=COLORS["danger"], width=1)
                    draw.text((x1+25, y1+25), "🔒", fill=COLORS["text"], font=self._get_font(25))
        
        # Stats
        stats_y = start_y + (grid_size * cell_size) + 30
        stats = [
            f"Slots: {used}/{slots}",
            f"Ready: {sum(1 for p in plants if p.get('progress', 0) >= 100)}",
            f"Growing: {len(plants)}"
        ]
        
        font_stats = self._get_font(20)
        for i, stat in enumerate(stats):
            draw.text((50, stats_y + i*30), stat, fill=COLORS["accent"], font=font_stats)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    async def create_wealth_chart(self, wealth_data: dict) -> bytes:
        """Create wealth chart image"""
        width, height = 600, 400
        image = Image.new('RGB', (width, height), color=COLORS["background"])
        draw = ImageDraw.Draw(image)
        
        # Title
        title = "💰 Wealth Overview"
        font_large = self._get_font(28)
        draw.text((width//3, 20), title, fill=COLORS["primary"], font=font_large)
        
        # Draw bars
        currencies = ["cash", "gold", "bonds", "credits", "tokens"]
        max_value = max([wealth_data.get(c, 0) for c in currencies] + [1])
        bar_width = 80
        spacing = 20
        start_x = 50
        start_y = 150
        
        for i, currency in enumerate(currencies):
            value = wealth_data.get(currency, 0)
            normalized = min(200, int((value / max_value) * 200)) if max_value > 0 else 0
            
            # Bar
            x1 = start_x + i * (bar_width + spacing)
            y1 = start_y + (200 - normalized)
            x2 = x1 + bar_width
            y2 = start_y + 200
            
            # Gradient effect
            for j in range(normalized):
                color_factor = j / normalized
                r = int(76 * color_factor)
                g = int(175 * color_factor)
                b = int(80 * color_factor)
                draw.rectangle([x1, y1+j, x2, y1+j+1], fill=(r, g, b))
            
            # Currency label
            emoji = CURRENCY_EMOJIS.get(currency, "💵")
            font_small = self._get_font(25)
            emoji_bbox = draw.textbbox((0, 0), emoji, font=font_small)
            emoji_x = x1 + (bar_width - (emoji_bbox[2] - emoji_bbox[0])) // 2
            draw.text((emoji_x, start_y-40), emoji, fill=COLORS["accent"], font=font_small)
            
            # Value
            value_text = f"{value:,}"
            font_value = self._get_font(14)
            value_bbox = draw.textbbox((0, 0), value_text, font=font_value)
            value_x = x1 + (bar_width - (value_bbox[2] - value_bbox[0])) // 2
            draw.text((value_x, y1-20), value_text, fill=COLORS["warning"], font=font_value)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

# ============================================================================
# ADMIN DASHBOARD & EVENT SYSTEM
# ============================================================================

class AdminDashboard:
    """Admin dashboard for managing bot events and surprises"""
    
    def __init__(self, db):
        self.db = db
        self.active_events = {}
        self.secret_codes = {}
    
    async def create_event(self, event_type: str, event_data: dict) -> str:
        """Create a new event"""
        event_id = f"event_{int(time.time())}_{random.randint(1000, 9999)}"
        self.active_events[event_id] = {
            "id": event_id,
            "type": event_type,
            "data": event_data,
            "created_at": datetime.now(),
            "active": True,
            "participants": [],
            "rewards_distributed": 0
        }
        
        # Log event creation
        await self._log_admin_action(f"Created event: {event_type} ({event_id})")
        return event_id
    
    async def trigger_event(self, event_id: str) -> dict:
        """Trigger an active event"""
        if event_id not in self.active_events:
            return {"success": False, "error": "Event not found"}
        
        event = self.active_events[event_id]
        event_type = event["type"]
        
        if event_type == "double_daily":
            result = await self._trigger_double_daily(event)
        elif event_type == "market_sale":
            result = await self._trigger_market_sale(event)
        elif event_type == "family_bonus":
            result = await self._trigger_family_bonus(event)
        elif event_type == "secret_code":
            result = await self._trigger_secret_code(event)
        elif event_type == "lottery":
            result = await self._trigger_lottery(event)
        else:
            result = {"success": False, "error": "Unknown event type"}
        
        if result["success"]:
            await self._log_admin_action(f"Triggered event: {event_id}")
        
        return result
    
    async def _trigger_double_daily(self, event: dict) -> dict:
        """Trigger double daily rewards event"""
        duration = event["data"].get("duration", 24)  # hours
        multiplier = event["data"].get("multiplier", 2)
        
        # Create announcement
        announcement = f"""
🎉 **SPECIAL EVENT: DOUBLE DAILY REWARDS!** 🎉

⏰ Duration: {duration} hours
💰 Multiplier: {multiplier}x
🎁 Bonus: All daily rewards multiplied!
👥 Applies to all users

🚀 Use `/daily` now for {multiplier}x rewards!

#Event #DoubleRewards
"""
        
        return {
            "success": True,
            "announcement": announcement,
            "duration": duration,
            "multiplier": multiplier
        }
    
    async def _trigger_secret_code(self, event: dict) -> dict:
        """Trigger secret code event"""
        code = event["data"].get("code", secrets.token_urlsafe(8))
        reward = event["data"].get("reward", 1000)
        uses_left = event["data"].get("max_uses", 100)
        
        self.secret_codes[code] = {
            "reward": reward,
            "uses_left": uses_left,
            "used_by": [],
            "created_at": datetime.now()
        }
        
        announcement = f"""
🔐 **SECRET CODE EVENT!** 🔐

🎯 Code: `{code}`
💰 Reward: ${reward:,}
👥 Uses: {uses_left} times
⏰ First come, first served!

💡 Use: `/redeem {code}`

#SecretCode #Event #Rewards
"""
        
        return {
            "success": True,
            "announcement": announcement,
            "code": code,
            "reward": reward
        }
    
    async def _trigger_lottery(self, event: dict) -> dict:
        """Trigger lottery event"""
        prize_pool = event["data"].get("prize_pool", 10000)
        ticket_price = event["data"].get("ticket_price", 100)
        duration = event["data"].get("duration", 48)  # hours
        
        lottery_id = f"lottery_{int(time.time())}"
        
        announcement = f"""
🎰 **GRAND LOTTERY EVENT!** 🎰

🏆 Prize Pool: ${prize_pool:,}
🎫 Ticket Price: ${ticket_price}
⏰ Duration: {duration} hours
👑 Jackpot: ${prize_pool // 2:,}

💡 Buy tickets with: `/lottery buy {ticket_price}`
🎯 Check with: `/lottery info`

#Lottery #Event #Jackpot
"""
        
        return {
            "success": True,
            "announcement": announcement,
            "lottery_id": lottery_id,
            "prize_pool": prize_pool,
            "ticket_price": ticket_price
        }
    
    async def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics"""
        async with self.db.lock:
            cursor = await self.db.conn.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]
            
            cursor = await self.db.conn.execute(
                "SELECT COUNT(*) FROM users WHERE last_daily > datetime('now', '-1 day')"
            )
            active_today = (await cursor.fetchone())[0]
            
            cursor = await self.db.conn.execute("SELECT SUM(cash) FROM users")
            total_cash = (await cursor.fetchone())[0] or 0
            
            cursor = await self.db.conn.execute("SELECT COUNT(*) FROM family_relations")
            total_families = (await cursor.fetchone())[0] // 2
        
        return {
            "total_users": total_users,
            "active_today": active_today,
            "total_cash": total_cash,
            "total_families": total_families,
            "active_events": len(self.active_events),
            "secret_codes": len(self.secret_codes)
        }
    
    async def _log_admin_action(self, action: str):
        """Log admin action"""
        try:
            await bot.send_message(
                LOG_CHANNEL,
                f"👑 **Admin Action:** {action}\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except:
            pass

# ============================================================================
# ADVANCED FAMILY FEATURES
# ============================================================================

class AdvancedFamilySystem:
    """Advanced family features with inheritance, events, and more"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_family_event(self, family_id: int, event_type: str, data: dict) -> dict:
        """Create family-only event"""
        event_id = f"family_event_{int(time.time())}"
        
        async with self.db.lock:
            await self.db.conn.execute(
                """INSERT INTO family_events 
                   (event_id, family_id, event_type, data, created_at) 
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (event_id, family_id, event_type, json.dumps(data))
            )
            await self.db.conn.commit()
        
        return {"event_id": event_id, "success": True}
    
    async def distribute_inheritance(self, from_user_id: int, to_user_id: int) -> dict:
        """Distribute inheritance when user is inactive"""
        async with self.db.lock:
            # Get user's wealth
            cursor = await self.db.conn.execute(
                "SELECT cash, gold, bonds FROM users WHERE user_id = ?",
                (from_user_id,)
            )
            user = await cursor.fetchone()
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            cash, gold, bonds = user
            
            # Calculate inheritance (50% of wealth)
            inherit_cash = cash // 2
            inherit_gold = gold // 2
            inherit_bonds = bonds // 2
            
            # Transfer to heir
            await self.db.conn.execute(
                "UPDATE users SET cash = cash - ?, gold = gold - ?, bonds = bonds - ? WHERE user_id = ?",
                (inherit_cash, inherit_gold, inherit_bonds, from_user_id)
            )
            
            await self.db.conn.execute(
                "UPDATE users SET cash = cash + ?, gold = gold + ?, bonds = bonds + ? WHERE user_id = ?",
                (inherit_cash, inherit_gold, inherit_bonds, to_user_id)
            )
            
            await self.db.conn.commit()
        
        return {
            "success": True,
            "inheritance": {
                "cash": inherit_cash,
                "gold": inherit_gold,
                "bonds": inherit_bonds
            }
        }
    
    async def organize_family_reunion(self, family_members: List[int]) -> dict:
        """Organize family reunion with bonuses"""
        reunion_bonus = len(family_members) * 500
        
        async with self.db.lock:
            for member_id in family_members:
                await self.db.conn.execute(
                    "UPDATE users SET cash = cash + ?, bonds = bonds + 10 WHERE user_id = ?",
                    (reunion_bonus, member_id)
                )
            
            await self.db.conn.commit()
        
        return {
            "success": True,
            "bonus_per_member": reunion_bonus,
            "total_members": len(family_members),
            "total_bonus": reunion_bonus * len(family_members)
        }
    
    async def create_family_quest(self, family_id: int, quest_data: dict) -> dict:
        """Create family quest"""
        quest_id = f"family_quest_{int(time.time())}"
        
        quest = {
            "id": quest_id,
            "family_id": family_id,
            "type": quest_data.get("type", "collection"),
            "target": quest_data.get("target", {}),
            "reward": quest_data.get("reward", {}),
            "progress": {},
            "completed": False,
            "created_at": datetime.now()
        }
        
        # Store quest in database
        async with self.db.lock:
            await self.db.conn.execute(
                """INSERT INTO family_quests 
                   (quest_id, family_id, quest_data) 
                   VALUES (?, ?, ?)""",
                (quest_id, family_id, json.dumps(quest))
            )
            await self.db.conn.commit()
        
        return {"quest_id": quest_id, "quest": quest}

# ============================================================================
# ENHANCED DATABASE
# ============================================================================

class UltimateDatabase:
    """Enhanced database with all features"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.lock = asyncio.Lock()
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.init_tables()
        logging.info("Database connected")
    
    async def init_tables(self):
        tables = [
            # Users with extended fields
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cash INTEGER DEFAULT 1000,
                gold INTEGER DEFAULT 0,
                bonds INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                tokens INTEGER DEFAULT 50,
                event_coins INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 100,
                is_alive BOOLEAN DEFAULT 1,
                last_daily TIMESTAMP,
                daily_count INTEGER DEFAULT 0,
                gemstone TEXT,
                gemstone_date TIMESTAMP,
                weapon TEXT DEFAULT 'fist',
                job TEXT,
                bio_verified BOOLEAN DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                family_title TEXT DEFAULT 'Member',
                inheritance_claimed BOOLEAN DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'en'
            )""",
            
            # Daily limits
            """CREATE TABLE IF NOT EXISTS daily_limits (
                user_id INTEGER PRIMARY KEY,
                last_daily_date DATE,
                daily_count INTEGER DEFAULT 0,
                bio_required_since DATE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )""",
            
            # Enhanced family relations
            """CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                strength INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user1_id, user2_id, relation_type)
            )""",
            
            # Family events
            """CREATE TABLE IF NOT EXISTS family_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )""",
            
            # Family quests
            """CREATE TABLE IF NOT EXISTS family_quests (
                quest_id TEXT PRIMARY KEY,
                family_id INTEGER NOT NULL,
                quest_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )""",
            
            # Admin events
            """CREATE TABLE IF NOT EXISTS admin_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                triggered_at TIMESTAMP
            )""",
            
            # Secret codes
            """CREATE TABLE IF NOT EXISTS secret_codes (
                code TEXT PRIMARY KEY,
                reward INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                uses_left INTEGER,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )""",
            
            # Code redemptions
            """CREATE TABLE IF NOT EXISTS code_redemptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reward_received INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (code) REFERENCES secret_codes(code)
            )""",
            
            # Gardens
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                barn_capacity INTEGER DEFAULT 50,
                last_fertilized TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Garden plants
            """CREATE TABLE IF NOT EXISTS garden_plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                is_ready BOOLEAN DEFAULT 0,
                fertilized_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Barn
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Market
            """CREATE TABLE IF NOT EXISTS market_stands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_sold BOOLEAN DEFAULT 0,
                FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Create indexes
            """CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)""",
            """CREATE INDEX IF NOT EXISTS idx_family_strength ON family_relations(strength)""",
            """CREATE INDEX IF NOT EXISTS idx_events_active ON admin_events(active)""",
            """CREATE INDEX IF NOT EXISTS idx_codes_expires ON secret_codes(expires_at)""",
        ]
        
        async with self.lock:
            for table in tables:
                try:
                    await self.conn.execute(table)
                except Exception as e:
                    logging.error(f"Table error: {e}")
            
            await self.conn.commit()

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize with correct session
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Initialize components
db = UltimateDatabase(DB_PATH)
visualizer = ImageVisualizer()
admin_dashboard = AdminDashboard(db)
family_system = AdvancedFamilySystem(db)

# ============================================================================
# ADMIN COMMANDS & DASHBOARD
# ============================================================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin dashboard - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 Owner only command!")
        return
    
    # Get dashboard stats
    stats = await admin_dashboard.get_dashboard_stats()
    
    dashboard_text = f"""
👑 <b>ADMIN DASHBOARD</b>

📊 <b>Bot Statistics:</b>
• Total Users: <b>{stats['total_users']:,}</b>
• Active Today: <b>{stats['active_today']:,}</b>
• Total Cash: <b>${stats['total_cash']:,}</b>
• Total Families: <b>{stats['total_families']:,}</b>

🎪 <b>Active Events:</b> <b>{stats['active_events']}</b>
🔐 <b>Secret Codes:</b> <b>{stats['secret_codes']}</b>

⚡ <b>Quick Actions:</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎉 Create Event", callback_data="admin_create_event"),
            InlineKeyboardButton(text="🔐 Create Code", callback_data="admin_create_code")
        ],
        [
            InlineKeyboardButton(text="📊 Detailed Stats", callback_data="admin_detailed_stats"),
            InlineKeyboardButton(text="👥 User Management", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="💰 Economy Control", callback_data="admin_economy"),
            InlineKeyboardButton(text="🌾 Garden Control", callback_data="admin_garden")
        ],
        [
            InlineKeyboardButton(text="🎮 Trigger Surprise", callback_data="admin_surprise"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_refresh"),
            InlineKeyboardButton(text="❌ Close", callback_data="close_menu")
        ]
    ])
    
    await message.answer(dashboard_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("admin_event"))
async def cmd_admin_event(message: Message, command: CommandObject):
    """Create admin event - owner only"""
    if message.from_user.id != OWNER_ID:
        return
    
    if not command.args:
        await message.answer("""
🎪 <b>Create Admin Event</b>

Usage: <code>/admin_event [type] [params]</code>

🎉 <b>Event Types:</b>
• <code>double_daily</code> - Double daily rewards
• <code>market_sale</code> - Market discounts
• <code>family_bonus</code> - Family reward bonus
• <code>secret_code</code> - Secret code event
• <code>lottery</code> - Lottery event

💡 <b>Examples:</b>
<code>/admin_event double_daily duration=24 multiplier=2</code>
<code>/admin_event secret_code code=SUPER2024 reward=5000 max_uses=50</code>
<code>/admin_event lottery prize_pool=10000 ticket_price=100 duration=48</code>
""", parse_mode=ParseMode.HTML)
        return
    
    args = command.args.split()
    event_type = args[0]
    
    # Parse parameters
    params = {}
    for arg in args[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Try to convert to int if possible
            try:
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)
            except:
                pass
            params[key] = value
    
    # Create event
    event_id = await admin_dashboard.create_event(event_type, params)
    
    # Trigger event
    result = await admin_dashboard.trigger_event(event_id)
    
    if result["success"]:
        await message.answer(f"""
✅ <b>Event Created Successfully!</b>

🎪 Event ID: <code>{event_id}</code>
📝 Type: <code>{event_type}</code>
📊 Parameters: <code>{json.dumps(params)}</code>

📢 <b>Announcement:</b>
{result.get('announcement', 'Event triggered!')}

🚀 Event is now active and visible to all users!
""", parse_mode=ParseMode.HTML)
        
        # Broadcast to all users
        try:
            await bot.send_message(
                LOG_CHANNEL,
                f"🎉 **NEW EVENT CREATED!**\n\n"
                f"Event: {event_type}\n"
                f"ID: {event_id}\n"
                f"By: {message.from_user.full_name}\n\n"
                f"{result.get('announcement', '')}"
            )
        except:
            pass
    else:
        await message.answer(f"❌ Event creation failed: {result.get('error', 'Unknown error')}")

@dp.message(Command("redeem"))
async def cmd_redeem(message: Message, command: CommandObject):
    """Redeem secret code"""
    if not command.args:
        await message.answer("Usage: /redeem [code]\nExample: /redeem SUPER2024")
        return
    
    code = command.args.strip().upper()
    
    # Check if code exists
    if code not in admin_dashboard.secret_codes:
        await message.answer("❌ Invalid or expired code!")
        return
    
    code_data = admin_dashboard.secret_codes[code]
    
    if code_data["uses_left"] <= 0:
        await message.answer("❌ This code has been used up!")
        del admin_dashboard.secret_codes[code]
        return
    
    # Check if user already used this code
    if message.from_user.id in code_data["used_by"]:
        await message.answer("❌ You've already redeemed this code!")
        return
    
    # Give reward
    reward = code_data["reward"]
    async with db.lock:
        await db.conn.execute(
            "UPDATE users SET cash = cash + ?, event_coins = event_coins + 10 WHERE user_id = ?",
            (reward, message.from_user.id)
        )
        await db.conn.commit()
    
    # Update code usage
    code_data["uses_left"] -= 1
    code_data["used_by"].append(message.from_user.id)
    
    if code_data["uses_left"] <= 0:
        del admin_dashboard.secret_codes[code]
    
    await message.answer(f"""
🎉 <b>CODE REDEEMED SUCCESSFULLY!</b>

🔐 Code: <code>{code}</code>
💰 Reward: <b>${reward:,}</b>
🎪 Event Coins: <b>+10</b>

💡 <b>Event coins can be used for:</b>
• Special event items
• Limited edition cosmetics
• Exclusive mini-games

📊 <b>Remaining uses:</b> {code_data['uses_left']}
🎯 Be quick before it's gone!
""", parse_mode=ParseMode.HTML)

# ============================================================================
# ENHANCED FAMILY COMMANDS WITH IMAGES
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family_image(message: Message):
    """Enhanced family command with IMAGE visualization"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Show loading
    loading_msg = await message.answer("🖼️ Generating family tree image...")
    
    # Get family data
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT fr.relation_type, 
               CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as first_name,
               CASE WHEN fr.user1_id = ? THEN u2.user_id ELSE u1.user_id END as user_id
               FROM family_relations fr
               LEFT JOIN users u1 ON u1.user_id = fr.user1_id
               LEFT JOIN users u2 ON u2.user_id = fr.user2_id
               WHERE ? IN (fr.user1_id, fr.user2_id)
               ORDER BY fr.relation_type, fr.strength DESC""",
            (message.from_user.id, message.from_user.id, message.from_user.id)
        )
        family_data = await cursor.fetchall()
    
    # Convert to list of dicts
    family_list = []
    for relation, name, member_id in family_data:
        family_list.append({
            "first_name": name,
            "relation_type": relation,
            "user_id": member_id
        })
    
    # Generate image
    try:
        image_bytes = await visualizer.create_family_tree_image(
            user.get('first_name', 'User'),
            family_list
        )
        
        # Send image
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=BufferedInputFile(image_bytes, filename="family_tree.png"),
            caption=f"""
🌳 <b>FAMILY TREE OF {user.get('first_name', 'User').upper()}</b>

👨‍👩‍👧‍👦 <b>Family Members:</b> <b>{len(family_list)}</b>
💝 <b>Relationships:</b> {', '.join(set([f['relation_type'] for f in family_list]))}

🎯 <b>Advanced Features:</b>
• <code>/family_inheritance</code> - Set inheritance
• <code>/family_reunion</code> - Organize reunion
• <code>/family_quest</code> - Start family quest
• <code>/family_strength</code> - Check bond strength

💡 <b>Family Benefits:</b>
• Daily bonus increases
• Special family events
• Inheritance system
• Quest rewards
""",
            parse_mode=ParseMode.HTML
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        await loading_msg.edit_text(f"❌ Failed to generate image: {str(e)[:100]}")
        # Fallback to text version
        await cmd_family_text(message)

async def cmd_family_text(message: Message):
    """Fallback text version of family command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT fr.relation_type, fr.strength,
               CASE WHEN fr.user1_id = ? THEN u2.first_name ELSE u1.first_name END as first_name
               FROM family_relations fr
               LEFT JOIN users u1 ON u1.user_id = fr.user1_id
               LEFT JOIN users u2 ON u2.user_id = fr.user2_id
               WHERE ? IN (fr.user1_id, fr.user2_id)
               ORDER BY fr.relation_type, fr.strength DESC""",
            (message.from_user.id, message.from_user.id)
        )
        family = await cursor.fetchall()
    
    if not family:
        await message.answer("""
🌳 <b>YOUR FAMILY TREE</b>

└─ You (No family yet)

💡 <b>How to grow your family:</b>
1. Use <code>/adopt @username</code> to adopt someone
2. Use <code>/marry @username</code> to marry someone
3. Wait for them to accept
4. Strengthen bonds with interactions

👑 <b>Advanced Family Features:</b>
• <b>Inheritance System</b> - Pass wealth to family
• <b>Family Quests</b> - Complete quests together
• <b>Family Reunions</b> - Earn bonus rewards
• <b>Bond Strength</b> - Stronger bonds = better bonuses
""", parse_mode=ParseMode.HTML)
        return
    
    family_text = f"""
🌳 <b>FAMILY TREE OF {user.get('first_name', 'User').upper()}</b>

"""
    
    # Group by relation type
    relations = {}
    for relation, strength, name in family:
        if relation not in relations:
            relations[relation] = []
        relations[relation].append((name, strength))
    
    for relation, members in relations.items():
        emoji = {"parent": "👴", "spouse": "💑", "child": "👶", "sibling": "👫"}.get(relation, "👤")
        family_text += f"\n{emoji} <b>{relation.upper()}S</b>:\n"
        
        for name, strength in members:
            strength_bar = "█" * (strength // 20) + "░" * (5 - (strength // 20))
            family_text += f"• {name} [{strength_bar}] {strength}%\n"
    
    family_text += f"""
    
💝 <b>Total Family Members:</b> <b>{len(family)}</b>
🎯 <b>Average Bond Strength:</b> <b>{sum(f[1] for f in family)//len(family)}%</b>

👑 <b>Advanced Commands:</b>
• <code>/family_inheritance @username</code> - Set heir
• <code>/family_reunion</code> - Organize reunion (+500 per member)
• <code>/family_quest start</code> - Start family quest
• <code>/family_strength @username</code> - Check bond
• <code>/family_event create</code> - Create family event
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 Adopt Member", callback_data="family_adopt"),
            InlineKeyboardButton(text="💑 Marry", callback_data="family_marry")
        ],
        [
            InlineKeyboardButton(text="🎯 Start Quest", callback_data="family_quest"),
            InlineKeyboardButton(text="🎪 Family Event", callback_data="family_event")
        ],
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="family_stats"),
            InlineKeyboardButton(text="🖼️ View Image", callback_data="family_image")
        ]
    ])
    
    await message.answer(family_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("family_inheritance"))
async def cmd_family_inheritance(message: Message, command: CommandObject):
    """Set inheritance heir"""
    if not command.args:
        await message.answer("Usage: /family_inheritance @username\nSets who inherits your wealth if inactive.")
        return
    
    # This would require parsing username and setting heir
    await message.answer("""
👑 <b>INHERITANCE SYSTEM</b>

🎯 <b>How it works:</b>
1. Set an heir with <code>/family_inheritance @username</code>
2. If you're inactive for 30 days, 50% of your wealth goes to heir
3. Heir receives notification
4. Inheritance can only be set for family members

💰 <b>What gets inherited:</b>
• 50% of cash
• 50% of gold  
• 50% of bonds
• Selected rare items

🔒 <b>Safety Features:</b>
• 7-day cooldown to change heir
• Heir must be active family member
• Can only inherit once per month
• Notification sent to original owner

💡 <b>Protect your legacy!</b>
""", parse_mode=ParseMode.HTML)

@dp.message(Command("family_reunion"))
async def cmd_family_reunion(message: Message):
    """Organize family reunion"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Get family members
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT DISTINCT 
               CASE WHEN fr.user1_id = ? THEN fr.user2_id ELSE fr.user1_id END as family_id
               FROM family_relations fr
               WHERE ? IN (fr.user1_id, fr.user2_id)""",
            (message.from_user.id, message.from_user.id)
        )
        family_ids = [row[0] for row in await cursor.fetchall()]
    
    if len(family_ids) < 2:
        await message.answer("❌ Need at least 2 family members for a reunion!")
        return
    
    # Calculate cost (100 per member)
    cost = len(family_ids) * 100
    
    if user.get('cash', 0) < cost:
        await message.answer(f"❌ Need ${cost:,} to organize reunion! You have ${user.get('cash', 0):,}")
        return
    
    # Organize reunion
    result = await family_system.organize_family_reunion([message.from_user.id] + family_ids)
    
    if result["success"]:
        # Deduct cost
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET cash = cash - ? WHERE user_id = ?",
                (cost, message.from_user.id)
            )
            await db.conn.commit()
        
        await message.answer(f"""
🎉 <b>FAMILY REUNION ORGANIZED!</b>

👨‍👩‍👧‍👦 <b>Participants:</b> <b>{result['total_members']}</b>
💰 <b>Cost:</b> <b>${cost:,}</b>
🎁 <b>Bonus per member:</b> <b>${result['bonus_per_member']:,}</b>
🏆 <b>Total distributed:</b> <b>${result['total_bonus']:,}</b>

💝 <b>Effects:</b>
• Bond strength increased by 10%
• Family reputation boosted
• Special reunion badge unlocked
• 24-hour family bonus active

🎯 <b>Next reunion available in 7 days</b>
""", parse_mode=ParseMode.HTML)

# ============================================================================
# ENHANCED GARDEN WITH IMAGE
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden_image(message: Message):
    """Enhanced garden command with IMAGE visualization"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Show loading
    loading_msg = await message.answer("🖼️ Generating garden image...")
    
    # Get garden data
    async with db.lock:
        cursor = await db.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?",
            (message.from_user.id,)
        )
        garden = await cursor.fetchone()
        
        cursor = await db.conn.execute(
            """SELECT crop_type, 
               ROUND((julianday('now') - julianday(planted_at)) * 24, 1) as hours_passed,
               grow_time,
               CASE WHEN (julianday('now') - julianday(planted_at)) * 24 >= grow_time THEN 100
                    ELSE ROUND(((julianday('now') - julianday(planted_at)) * 24 / grow_time) * 100, 0)
               END as progress
               FROM garden_plants 
               WHERE user_id = ? AND is_ready = 0
               ORDER BY planted_at""",
            (message.from_user.id,)
        )
        plants = await cursor.fetchall()
        
        cursor = await db.conn.execute(
            "SELECT SUM(quantity) FROM barn WHERE user_id = ?",
            (message.from_user.id,)
        )
        barn_total = (await cursor.fetchone())[0] or 0
    
    if not garden:
        await loading_msg.edit_text("No garden found! Use /start first.")
        return
    
    slots = garden[0]
    
    # Prepare garden data for visualization
    garden_data = {
        "slots": slots,
        "plants": [
            {
                "crop_type": plant[0],
                "progress": plant[3]
            }
            for plant in plants
        ]
    }
    
    # Generate image
    try:
        image_bytes = await visualizer.create_garden_image(garden_data)
        
        # Send image
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=BufferedInputFile(image_bytes, filename="garden.png"),
            caption=f"""
🌾 <b>{user.get('first_name', 'User')}'s GARDEN</b>

📊 <b>Garden Stats:</b>
• Slots: <b>{len(plants)}/{slots}</b>
• Ready: <b>{sum(1 for p in plants if p[3] >= 100)} crops</b>
• Growing: <b>{len(plants)} crops</b>
• Barn Storage: <b>{barn_total} items</b>

💡 <b>Plant Progress:</b>
"""
            + "\n".join([
                f"• {CROP_EMOJIS.get(p[0], '🌱')} {p[0].title()}: {p[3]}% ({p[1]}/{p[2]}h)"
                for p in plants[:5]
            ])
            + f"""

🎯 <b>Advanced Commands:</b>
• <code>/garden_expand</code> - Buy more slots (${slots*500:,})
• <code>/garden_auto</code> - Auto-planting system
• <code>/garden_upgrade</code> - Upgrade barn capacity
• <code>/garden_design</code> - Custom garden layout

🌱 <b>New Crops:</b> Watermelon 🍉, Pumpkin 🎃
""",
            parse_mode=ParseMode.HTML
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        await loading_msg.edit_text(f"❌ Failed to generate image: {str(e)[:100]}")
        # Fallback to text version
        await cmd_garden_text(message)

# ============================================================================
# WEALTH VISUALIZATION
# ============================================================================

@dp.message(Command("wealth"))
async def cmd_wealth_image(message: Message):
    """Show wealth as image chart"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    # Show loading
    loading_msg = await message.answer("📈 Generating wealth chart...")
    
    # Prepare wealth data
    wealth_data = {
        "cash": user.get("cash", 0),
        "gold": user.get("gold", 0),
        "bonds": user.get("bonds", 0),
        "credits": user.get("credits", 0),
        "tokens": user.get("tokens", 0),
        "event_coins": user.get("event_coins", 0)
    }
    
    # Generate image
    try:
        image_bytes = await visualizer.create_wealth_chart(wealth_data)
        
        # Send image
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=BufferedInputFile(image_bytes, filename="wealth_chart.png"),
            caption=f"""
💰 <b>WEALTH OVERVIEW</b>

💵 Cash: <b>${wealth_data['cash']:,}</b>
🪙 Gold: <b>{wealth_data['gold']:,}</b>
👨‍👩‍👧‍👦 Bonds: <b>{wealth_data['bonds']:,}</b>
⭐ Credits: <b>{wealth_data['credits']:,}</b>
🌱 Tokens: <b>{wealth_data['tokens']:,}</b>
🎪 Event Coins: <b>{wealth_data['event_coins']:,}</b>

📈 <b>Total Value:</b> <b>${wealth_data['cash'] + (wealth_data['gold'] * 100) + (wealth_data['bonds'] * 50):,}</b>

🎯 <b>Wealth Management:</b>
• <code>/invest</code> - Invest cash for interest
• <code>/exchange</code> - Convert between currencies
• <code>/portfolio</code> - View investments
• <code>/wealth_goal</code> - Set savings goal

💡 <b>Event coins</b> can buy exclusive items during events!
""",
            parse_mode=ParseMode.HTML
        )
        
        await loading_msg.delete()
        
    except Exception as e:
        await loading_msg.edit_text(f"❌ Failed to generate chart: {str(e)[:100]}")

# ============================================================================
# OTHER ESSENTIAL COMMANDS (Backup, Refresh, Ping, HMK)
# ============================================================================

@dp.message(Command("backup"))
async def cmd_backup(message: Message):
    """Backup command - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 Owner only command!")
        return
    
    backup_msg = await message.answer("💾 Creating backup...")
    
    try:
        # Create backup data
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "Ultimate",
            "tables": {}
        }
        
        async with db.lock:
            cursor = await db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]
            
            for table in tables:
                cursor = await db.conn.execute(f"SELECT * FROM {table}")
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                table_data = []
                for row in rows:
                    table_data.append(dict(zip(columns, row)))
                
                backup_data["tables"][table] = table_data
        
        # Create backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
        backup_json = json.dumps(backup_data, indent=2, default=str)
        
        await bot.send_document(
            chat_id=OWNER_ID,
            document=BufferedInputFile(
                backup_json.encode(),
                filename=filename
            ),
            caption=f"🔐 Backup created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await backup_msg.edit_text("✅ Backup created and sent!")
        
    except Exception as e:
        await backup_msg.edit_text(f"❌ Backup failed: {str(e)[:100]}")

@dp.message(Command("refresh"))
async def cmd_refresh(message: Message):
    """Refresh system - owner only"""
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 Owner only command!")
        return
    
    refresh_msg = await message.answer("🔄 Refreshing system...")
    
    try:
        updates = []
        
        async with db.lock:
            # Update crop growth
            await db.conn.execute(
                "UPDATE garden_plants SET is_ready = 1 WHERE "
                "(julianday('now') - julianday(planted_at)) * 24 >= grow_time"
            )
            cursor = await db.conn.execute("SELECT changes()")
            crop_updates = (await cursor.fetchone())[0]
            updates.append(f"🌱 Crops: {crop_updates} ready")
            
            # Update user activity
            await db.conn.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE "
                "last_active < datetime('now', '-30 days') AND is_alive = 1"
            )
            cursor = await db.conn.execute("SELECT changes()")
            activity_updates = (await cursor.fetchone())[0]
            updates.append(f"👤 Activity: {activity_updates} updated")
            
            # Process inheritance for inactive users
            cursor = await db.conn.execute(
                """SELECT u.user_id, u.cash, u.gold, u.bonds,
                   (SELECT heir_id FROM inheritance WHERE user_id = u.user_id) as heir_id
                   FROM users u
                   WHERE u.last_active < datetime('now', '-30 days') 
                   AND u.is_alive = 1
                   AND u.inheritance_claimed = 0"""
            )
            inactive_users = await cursor.fetchall()
            
            inheritance_count = 0
            for user_id, cash, gold, bonds, heir_id in inactive_users:
                if heir_id:
                    # Distribute inheritance
                    inherit_cash = cash // 2
                    inherit_gold = gold // 2
                    inherit_bonds = bonds // 2
                    
                    await db.conn.execute(
                        """UPDATE users 
                           SET cash = cash - ?, gold = gold - ?, bonds = bonds - ?,
                               inheritance_claimed = 1
                           WHERE user_id = ?""",
                        (inherit_cash, inherit_gold, inherit_bonds, user_id)
                    )
                    
                    await db.conn.execute(
                        """UPDATE users 
                           SET cash = cash + ?, gold = gold + ?, bonds = bonds + ?,
                               event_coins = event_coins + 5
                           WHERE user_id = ?""",
                        (inherit_cash, inherit_gold, inherit_bonds, heir_id)
                    )
                    
                    inheritance_count += 1
            
            updates.append(f"👑 Inheritance: {inheritance_count} processed")
            
            await db.conn.commit()
        
        result = f"""
✅ <b>SYSTEM REFRESH COMPLETE!</b>

{' | '.join(updates)}

🔄 Next refresh: <b>1 hour</b>
📊 System running smoothly!

🎪 <b>Active Events:</b> {len(admin_dashboard.active_events)}
🔐 <b>Secret Codes:</b> {len(admin_dashboard.secret_codes)}
"""
        
        await refresh_msg.edit_text(result, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await refresh_msg.edit_text(f"❌ Refresh failed: {str(e)[:100]}")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping command"""
    start = time.time()
    msg = await message.answer("🏓 Pong! Testing...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    # Get stats
    stats = await admin_dashboard.get_dashboard_stats()
    
    status_text = f"""
🏓 <b>BOT STATUS - ULTIMATE EDITION</b>

✅ Status: <b>Online & Healthy</b>
📡 Latency: <b>{latency}ms</b>
👥 Users: <b>{stats['total_users']:,}</b>
💰 Economy: <b>${stats['total_cash']:,}</b>
👨‍👩‍👧‍👦 Families: <b>{stats['total_families']:,}</b>

🎪 Active Events: <b>{stats['active_events']}</b>
🔐 Secret Codes: <b>{stats['secret_codes']}</b>
🌾 Gardens: <b>Loading...</b>

✨ <b>Features Active:</b>
• Image Visualizations ✅
• Admin Dashboard ✅  
• Advanced Family System ✅
• Event System ✅
• Inheritance System ✅

🔄 Last checked: {datetime.now().strftime('%H:%M:%S')}
"""
    
    await msg.edit_text(status_text, parse_mode=ParseMode.HTML)

@dp.message(Command("hmk"))
async def cmd_hmk(message: Message):
    """Hired Muscle command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Use /start first!")
        return
    
    if user.get('cash', 0) < 5000:
        await message.answer(f"❌ Need $5,000! You have ${user.get('cash', 0):,}")
        return
    
    if user.get('reputation', 100) < 50:
        await message.answer(f"❌ Reputation too low! Need 50, have {user.get('reputation', 100)}")
        return
    
    # Find target
    async with db.lock:
        cursor = await db.conn.execute(
            """SELECT user_id, first_name, cash 
               FROM users 
               WHERE user_id != ? AND is_alive = 1 AND cash > 1000 
               ORDER BY RANDOM() LIMIT 1""",
            (message.from_user.id,)
        )
        target = await cursor.fetchone()
    
    if not target:
        await message.answer("❌ No suitable targets!")
        return
    
    target_id, target_name, target_cash = target
    
    # Calculate attack
    success_chance = 70 + (20 if user.get('weapon') != 'fist' else 0)
    success = random.randint(1, 100) <= success_chance
    
    if success:
        stolen = min(int(target_cash * random.uniform(0.3, 0.6)), 10000)
        stolen = max(stolen, 1000)
        
        # Update balances
        await db.update_user_currency(message.from_user.id, "cash", stolen - 5000)
        await db.update_user_currency(target_id, "cash", -stolen)
        
        # Update reputation
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET reputation = reputation - 20 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await db.conn.commit()
        
        result = f"""
💪 <b>HMK ATTACK SUCCESSFUL!</b>

💰 Cost: $5,000
🎯 Target: {target_name}
🤑 Stolen: ${stolen:,}
📈 Net Gain: ${stolen - 5000:,}
📉 Reputation: -20

⚔️ Target has been notified!
"""
        
        # Notify target
        try:
            await bot.send_message(
                target_id,
                f"⚠️ You were attacked by {user.get('first_name')}!\n"
                f"💰 Lost: ${stolen:,}\n"
                f"💸 New balance: ${target_cash - stolen:,}"
            )
        except:
            pass
        
    else:
        await db.update_user_currency(message.from_user.id, "cash", -5000)
        
        async with db.lock:
            await db.conn.execute(
                "UPDATE users SET reputation = reputation - 30 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await db.conn.commit()
        
        result = f"""
😱 <b>HMK ATTACK FAILED!</b>

💰 Lost: $5,000
🎯 Target: {target_name}
🚫 Muscle got scared!

💡 Better luck next time!
"""
    
    await message.answer(result, parse_mode=ParseMode.HTML)

# ============================================================================
# STARTUP & MAIN
# ============================================================================

async def setup_bot():
    """Initialize bot"""
    await db.connect()
    
    # Set bot commands
    commands = [
        types.BotCommand(command="start", description="Start bot"),
        types.BotCommand(command="help", description="Help"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="garden", description="Your garden (image)"),
        types.BotCommand(command="wealth", description="Wealth chart (image)"),
        types.BotCommand(command="family", description="Family tree (image)"),
        types.BotCommand(command="admin", description="Admin dashboard"),
        types.BotCommand(command="admin_event", description="Create event"),
        types.BotCommand(command="redeem", description="Redeem secret code"),
        types.BotCommand(command="family_reunion", description="Family reunion"),
        types.BotCommand(command="family_inheritance", description="Set heir"),
        types.BotCommand(command="backup", description="Backup (owner)"),
        types.BotCommand(command="refresh", description="Refresh (owner)"),
        types.BotCommand(command="ping", description="Status"),
        types.BotCommand(command="hmk", description="Hired muscle"),
    ]
    
    await bot.set_my_commands(commands)
    
    # Send startup message
    try:
        await bot.send_message(
            LOG_CHANNEL,
            f"""
🤖 <b>FAMILY TREE BOT - ULTIMATE EDITION STARTED</b>

✅ Version: <b>Ultimate</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👑 Owner: <code>{OWNER_ID}</code>
✨ Features: Images + Admin Dashboard + Advanced Family
👥 Bot: {BOT_USERNAME}

🎪 <b>Ready with:</b>
• Image visualizations
• Admin event system
• Secret codes
• Family inheritance
• Family reunions
• Wealth charts

🚀 Bot is live and ready!
""",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
    
    logger.info("✅ Bot setup complete!")

async def main():
    await setup_bot()
    logger.info("🚀 Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Set BOT_TOKEN in .env file!")
        sys.exit(1)
    
    asyncio.run(main())
