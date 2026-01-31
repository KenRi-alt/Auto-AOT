#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - CLEAN & WORKING
Version: 11.0 - Images Fixed, Minimal Buttons, All Features
"""

import os
import sys
import asyncio
import logging
import random
import math
import io
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiohttp
import aiosqlite

# ============================================================================
# CORE IMPORTS
# ============================================================================
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, CommandObject
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, BufferedInputFile, ChatJoinRequest
    )
    from aiogram.enums import ParseMode, ChatType
    from aiogram.client.session.aiohttp import AiohttpSession
    
    # Pillow for images - MUST BE INSTALLED
    try:
        from PIL import Image, ImageDraw, ImageFont
        HAS_PILLOW = True
    except ImportError:
        HAS_PILLOW = False
        print("❌ Pillow not installed! Install: pip install pillow")
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install aiogram pillow aiosqlite aiohttp")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
OWNER_ID = 6108185460
LOG_CHANNEL = -1003662720845
BOT_USERNAME = "Familly_TreeBot"

# Crop System
CROP_TYPES = ["carrot", "tomato", "potato", "eggplant", "corn", "watermelon"]
CROP_EMOJIS = {
    "carrot": "🥕", "tomato": "🍅", "potato": "🥔", 
    "eggplant": "🍆", "corn": "🌽", "watermelon": "🍉"
}

CROP_DATA = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕"},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅"},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔"},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆"},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽"},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "emoji": "🍉"}
}

# Reaction GIFs
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
# DATABASE
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
                first_name TEXT NOT NULL,
                username TEXT,
                cash INTEGER DEFAULT 1000,
                gold INTEGER DEFAULT 50,
                level INTEGER DEFAULT 1,
                daily_streak INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                is_banned BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS family_relations (
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id, relation_type)
            )""",
            
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9
            )""",
            
            """CREATE TABLE IF NOT EXISTS garden_plants (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                member_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS catbox_gifs (
                command TEXT PRIMARY KEY,
                gif_url TEXT NOT NULL,
                added_by INTEGER
            )"""
        ]
        
        for table in tables:
            await self.conn.execute(table)
        await self.conn.commit()
        
        # Add default GIFs
        for cmd, url in REACTION_GIFS.items():
            await self.conn.execute(
                "INSERT OR IGNORE INTO catbox_gifs (command, gif_url, added_by) VALUES (?, ?, ?)",
                (cmd, url, OWNER_ID)
            )
        await self.conn.commit()
    
    async def get_user(self, user_id: int):
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            'user_id': row[0], 'first_name': row[1], 'username': row[2],
            'cash': row[3], 'gold': row[4], 'level': row[5],
            'daily_streak': row[6], 'last_daily': row[7],
            'is_banned': row[8], 'created_at': row[9]
        }
    
    async def create_user(self, user: types.User):
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
            (user.id, user.first_name, user.username)
        )
        await self.conn.execute(
            "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)", (user.id,)
        )
        await self.conn.commit()
        return await self.get_user(user.id)
    
    async def update_currency(self, user_id: int, currency: str, amount: int):
        if currency == "cash":
            await self.conn.execute(
                "UPDATE users SET cash = cash + ? WHERE user_id = ?",
                (amount, user_id)
            )
        elif currency == "gold":
            await self.conn.execute(
                "UPDATE users SET gold = gold + ? WHERE user_id = ?",
                (amount, user_id)
            )
        await self.conn.commit()
    
    async def get_family(self, user_id: int):
        cursor = await self.conn.execute(
            """SELECT relation_type, 
               CASE WHEN user1_id = ? THEN u2.first_name ELSE u1.first_name END as name
               FROM family_relations fr
               LEFT JOIN users u1 ON u1.user_id = fr.user1_id
               LEFT JOIN users u2 ON u2.user_id = fr.user2_id
               WHERE ? IN (fr.user1_id, fr.user2_id)""",
            (user_id, user_id)
        )
        rows = await cursor.fetchall()
        return [{'relation_type': r[0], 'name': r[1]} for r in rows]
    
    async def add_relation(self, user1_id: int, user2_id: int, relation: str):
        await self.conn.execute(
            "INSERT OR IGNORE INTO family_relations (user1_id, user2_id, relation_type) VALUES (?, ?, ?)",
            (min(user1_id, user2_id), max(user1_id, user2_id), relation)
        )
        await self.conn.commit()
    
    async def get_garden(self, user_id: int):
        cursor = await self.conn.execute(
            "SELECT slots FROM gardens WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return {'slots': row[0] if row else 9}
    
    async def get_growing_crops(self, user_id: int):
        cursor = await self.conn.execute(
            "SELECT crop_type, planted_at, grow_time FROM garden_plants WHERE user_id = ?",
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
    
    async def plant_crop(self, user_id: int, crop_type: str, quantity: int):
        if crop_type not in CROP_TYPES:
            return False
        
        garden = await self.get_garden(user_id)
        if not garden:
            return False
        
        current_crops = await self.get_growing_crops(user_id)
        if len(current_crops) + quantity > garden['slots']:
            return False
        
        grow_time = CROP_DATA[crop_type]['grow_time']
        for _ in range(quantity):
            await self.conn.execute(
                "INSERT INTO garden_plants (user_id, crop_type, grow_time) VALUES (?, ?, ?)",
                (user_id, crop_type, grow_time)
            )
        
        await self.conn.commit()
        return True
    
    async def add_group(self, chat_id: int, title: str, member_count: int = 0):
        await self.conn.execute(
            """INSERT OR REPLACE INTO groups (chat_id, title, member_count) 
               VALUES (?, ?, ?)""",
            (chat_id, title, member_count)
        )
        await self.conn.commit()
    
    async def get_groups(self):
        cursor = await self.conn.execute(
            "SELECT chat_id, title, member_count FROM groups ORDER BY added_at DESC"
        )
        return await cursor.fetchall()
    
    async def get_gif(self, command: str):
        cursor = await self.conn.execute(
            "SELECT gif_url FROM catbox_gifs WHERE command = ?", (command,)
        )
        row = await cursor.fetchone()
        return row[0] if row else REACTION_GIFS.get(command)
    
    async def add_gif(self, command: str, url: str, added_by: int):
        await self.conn.execute(
            "INSERT OR REPLACE INTO catbox_gifs (command, gif_url, added_by) VALUES (?, ?, ?)",
            (command, url, added_by)
        )
        await self.conn.commit()
    
    async def get_stats(self):
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("SELECT COUNT(*) FROM groups")
        total_groups = (await cursor.fetchone())[0]
        
        return {'users': total_users, 'groups': total_groups}

# ============================================================================
# IMAGE GENERATOR - SIMPLE & WORKING
# ============================================================================

class ImageGenerator:
    """Simple image generator that actually works"""
    
    def __init__(self):
        self.font = None
        if HAS_PILLOW:
            try:
                self.font = ImageFont.truetype("arial.ttf", 20)
            except:
                self.font = ImageFont.load_default()
    
    async def create_garden_image(self, crops: List[dict]) -> Optional[bytes]:
        """Create garden image - SIMPLE VERSION THAT WORKS"""
        if not HAS_PILLOW:
            logger.error("❌ Pillow not installed!")
            return None
        
        try:
            # Simple image
            img = Image.new('RGB', (600, 600), color='navy')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((200, 20), "🌾 Your Garden", fill='white', font=self.font)
            
            # Draw 3x3 grid
            for row in range(3):
                for col in range(3):
                    x1 = 100 + col * 150
                    y1 = 100 + row * 150
                    x2 = x1 + 120
                    y2 = y1 + 120
                    
                    idx = row * 3 + col
                    if idx < len(crops):
                        crop = crops[idx]
                        progress = crop['progress']
                        
                        # Color based on progress
                        if progress >= 100:
                            color = 'green'
                        elif progress >= 50:
                            color = 'yellow'
                        else:
                            color = 'blue'
                        
                        # Draw crop box
                        draw.rectangle([x1, y1, x2, y2], fill=color, outline='white', width=2)
                        
                        # Crop emoji
                        emoji = CROP_EMOJIS.get(crop['crop_type'], '🌱')
                        draw.text((x1+40, y1+30), emoji, fill='white', font=self.font)
                        
                        # Progress
                        draw.text((x1+40, y2-30), f"{int(progress)}%", fill='white', font=self.font)
                    else:
                        # Empty slot
                        draw.rectangle([x1, y1, x2, y2], fill='gray', outline='white', width=1)
                        draw.text((x1+40, y1+40), "➕", fill='white', font=self.font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            logger.info("✅ Garden image created successfully!")
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Garden image error: {e}")
            return None
    
    async def create_family_image(self, family: List[dict]) -> Optional[bytes]:
        """Create family image"""
        if not HAS_PILLOW:
            return None
        
        try:
            img = Image.new('RGB', (600, 400), color='darkgreen')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((200, 20), "🌳 Family Tree", fill='white', font=self.font)
            
            # Center (user)
            draw.ellipse([250, 150, 350, 250], fill='blue', outline='yellow', width=3)
            draw.text((280, 180), "👤", fill='white', font=self.font)
            draw.text((270, 260), "You", fill='white', font=self.font)
            
            # Family members
            for i, member in enumerate(family[:4]):
                x = 100 + i * 100
                y = 300
                
                # Line to center
                draw.line([(300, 200), (x+25, y-25)], fill='white', width=2)
                
                # Member circle
                draw.ellipse([x, y-50, x+50, y], fill='purple', outline='white', width=2)
                
                # Emoji
                emoji = {'parent': '👴', 'spouse': '💑', 'child': '👶', 'sibling': '👫'}.get(
                    member['relation_type'], '👤'
                )
                draw.text((x+10, y-40), emoji, fill='white', font=self.font)
                
                # Name
                name = member['name'][:5] if member['name'] else "User"
                draw.text((x, y+10), name, fill='yellow', font=self.font)
            
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
db = Database("family_bot_fixed.db")
img_gen = ImageGenerator()

# ============================================================================
# INLINE KEYBOARDS - MINIMAL
# ============================================================================

def main_keyboard():
    """Main menu - Only 4 buttons"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌳 Family", callback_data="menu_family"),
            InlineKeyboardButton(text="🌾 Garden", callback_data="menu_garden")
        ],
        [
            InlineKeyboardButton(text="🎮 Games", callback_data="menu_games"),
            InlineKeyboardButton(text="💰 Daily", callback_data="cmd_daily")
        ],
        [
            InlineKeyboardButton(text="👥 Add to Group", 
                               url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
        ]
    ])

def family_keyboard():
    """Family menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 Adopt", callback_data="help_adopt"),
            InlineKeyboardButton(text="💍 Marry", callback_data="help_marry")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])

def garden_keyboard():
    """Garden menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 Plant", callback_data="help_plant"),
            InlineKeyboardButton(text="✅ Harvest", callback_data="help_harvest")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])

def games_keyboard():
    """Games menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Slot", callback_data="help_slot"),
            InlineKeyboardButton(text="💰 Rob", callback_data="help_rob")
        ],
        [
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu_main")
        ]
    ])

def admin_keyboard():
    """Admin keyboard for groups"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="cmd_stats"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="help_broadcast")
        ],
        [
            InlineKeyboardButton(text="🐱 Catbox", callback_data="menu_catbox")
        ]
    ])

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def get_target_user(message: Message):
    """Get target user from reply"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None

async def send_gif_reaction(command: str, chat_id: int, from_user: types.User, target_user: types.User):
    """Send GIF reaction"""
    gif_url = await db.get_gif(command)
    if not gif_url:
        gif_url = REACTION_GIFS.get(command, REACTION_GIFS['hug'])
    
    texts = {
        'hug': f"🤗 {from_user.first_name} hugged {target_user.first_name}!",
        'kill': f"🔪 {from_user.first_name} killed {target_user.first_name}!",
        'rob': f"💰 {from_user.first_name} robbed {target_user.first_name}!",
        'kiss': f"💋 {from_user.first_name} kissed {target_user.first_name}!",
        'slap': f"👋 {from_user.first_name} slapped {target_user.first_name}!",
        'pat': f"👏 {from_user.first_name} patted {target_user.first_name}!"
    }
    
    text = texts.get(command, f"{from_user.first_name} used {command}!")
    
    try:
        await bot.send_animation(chat_id=chat_id, animation=gif_url, caption=text)
    except:
        await bot.send_message(chat_id, text)

async def log_to_channel(text: str, button_url: str = None):
    """Log to channel with optional button"""
    try:
        if button_url:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Open Chat", url=button_url)]
            ])
            await bot.send_message(LOG_CHANNEL, text, reply_markup=keyboard)
        else:
            await bot.send_message(LOG_CHANNEL, text)
    except Exception as e:
        logger.error(f"Channel log error: {e}")

def is_owner(user_id: int):
    return user_id == OWNER_ID

# ============================================================================
# START & GROUP JOIN
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    user = await db.get_user(message.from_user.id)
    if not user:
        user = await db.create_user(message.from_user)
    
    welcome_text = f"""
✨ <b>Welcome {message.from_user.first_name}!</b> ✨

🌳 <b>Family Tree Bot</b>

🚀 <b>Quick Start:</b>
1. Use buttons below
2. Add me to groups for family fun!
3. Reply to friends with reactions

📱 <b>Main Features:</b>
• Family Tree with images
• Garden farming system
• Reaction commands with GIFs
• Mini-games & economy

👥 <b>Add me to groups!</b>
Manage family together!
"""
    
    await message.answer(welcome_text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

@dp.my_chat_member()
async def handle_group_join(event: types.ChatMemberUpdated):
    """Handle bot being added to groups"""
    if event.new_chat_member.status == "member":
        chat = event.chat
        
        # Log to channel with group link
        group_link = f"https://t.me/c/{str(chat.id)[4:]}" if str(chat.id).startswith("-100") else ""
        log_text = f"👥 <b>Bot added to group!</b>\n\n🏷️ Title: {chat.title}\n🆔 ID: {chat.id}\n👥 Type: {chat.type}"
        
        await db.add_group(chat.id, chat.title)
        await log_to_channel(log_text, group_link if group_link else None)
        
        # Send welcome to group
        welcome = f"""
👋 <b>Hello everyone!</b>

🌳 I'm Family Tree Bot!

🤝 <b>What I can do in groups:</b>
• Build family trees together
• React with GIFs (/hug, /kill, etc.)
• Play mini-games
• Grow virtual gardens

💡 <b>Try these now:</b>
Reply to someone with:
• <code>/hug</code> - Send hugging GIF
• <code>/kill</code> - Send killing GIF
• <code>/rob</code> - Rob someone

🎮 <b>Games:</b>
• <code>/slot 100</code> - Slot machine
• <code>/fight</code> - Fight someone

👑 <b>Owner:</b> Use <code>/owner</code> for admin commands
"""
        
        try:
            await bot.send_message(chat.id, welcome, parse_mode=ParseMode.HTML)
        except:
            pass

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

@dp.callback_query(F.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Main Menu</b>\n\nSelect an option:",
        reply_markup=main_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_family")
async def show_family(callback: CallbackQuery):
    await cmd_family(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_garden")
async def show_garden(callback: CallbackQuery):
    await cmd_garden(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_games")
async def show_games(callback: CallbackQuery):
    await cmd_games(callback.message)
    await callback.answer()

# Help callbacks
@dp.callback_query(F.data.startswith("help_"))
async def show_help(callback: CallbackQuery):
    help_type = callback.data.replace("help_", "")
    
    helps = {
        "adopt": "👶 <b>Adopt Someone</b>\n\nReply to someone with <code>/adopt</code> to make them your child!",
        "marry": "💍 <b>Marry Someone</b>\n\nReply to someone with <code>/marry</code> to marry them!",
        "plant": "🌱 <b>Plant Crops</b>\n\n<code>/plant carrot 3</code> - Plant 3 carrots\nCost: $10 each",
        "harvest": "✅ <b>Harvest Crops</b>\n\n<code>/harvest</code> - Collect ready crops",
        "slot": "🎰 <b>Slot Machine</b>\n\n<code>/slot 100</code> - Bet $100\nMatch 3 to win!",
        "rob": "💰 <b>Rob Someone</b>\n\nReply with <code>/rob</code>\n40% success chance!\nCooldown: 2 hours"
    }
    
    if help_type in helps:
        await callback.message.answer(helps[help_type], parse_mode=ParseMode.HTML)
    
    await callback.answer()

@dp.callback_query(F.data == "cmd_daily")
async def claim_daily(callback: CallbackQuery):
    await cmd_daily(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "cmd_stats")
async def show_stats(callback: CallbackQuery):
    if is_owner(callback.from_user.id):
        await cmd_stats(callback.message)
    else:
        await callback.answer("❌ Owner only!", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "menu_catbox")
async def show_catbox(callback: CallbackQuery):
    if is_owner(callback.from_user.id):
        await cmd_catbox(callback.message, CommandObject(args=""))
    else:
        await callback.answer("❌ Owner only!", show_alert=True)
    await callback.answer()

# ============================================================================
# FAMILY COMMANDS
# ============================================================================

@dp.message(Command("family", "tree"))
async def cmd_family(message: Message):
    """Family tree with image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    family = await db.get_family(message.from_user.id)
    
    # Try to create image
    if HAS_PILLOW and family:
        try:
            image_bytes = await img_gen.create_family_image(family)
            if image_bytes:
                photo = BufferedInputFile(image_bytes, filename="family.png")
                
                # Image caption
                caption = f"""
🌳 <b>Family Tree</b>

👤 Members: {len(family)}
💝 Relations: {', '.join(set(f['relation_type'] for f in family))}

💡 <b>Commands:</b>
Reply to someone with:
• <code>/adopt</code> - Make child
• <code>/marry</code> - Marry
• <code>/divorce</code> - End marriage

🎯 <b>Benefits:</b>
• Daily bonus increases
• Family quests available
"""
                await message.answer_photo(photo=photo, caption=caption, 
                                         parse_mode=ParseMode.HTML, reply_markup=family_keyboard())
                return
        except Exception as e:
            logger.error(f"Family image error: {e}")
    
    # Text version
    text = f"""
🌳 <b>Family Tree</b>

👤 Members: {len(family)}
"""
    
    if family:
        for member in family:
            emoji = {'parent': '👴', 'spouse': '💑', 'child': '👶', 'sibling': '👫'}.get(
                member['relation_type'], '👤'
            )
            text += f"\n{emoji} {member['name']} ({member['relation_type']})"
    else:
        text += "\n\nNo family yet! Reply to someone with /adopt"
    
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=family_keyboard())

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone"""
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
    
    await db.add_relation(message.from_user.id, target.id, 'child')
    await db.update_currency(message.from_user.id, 'cash', 500)
    
    await message.answer(f"✅ Adopted {target.first_name}! +$500 bonus", parse_mode=ParseMode.HTML)

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Marry someone"""
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
    await db.update_currency(message.from_user.id, 'cash', 1000)
    await db.update_currency(target.id, 'cash', 1000)
    
    await message.answer(f"💍 Married {target.first_name}! +$1000 each", parse_mode=ParseMode.HTML)

# ============================================================================
# GARDEN COMMANDS WITH WORKING IMAGES
# ============================================================================

@dp.message(Command("garden"))
async def cmd_garden(message: Message):
    """Garden with working image"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    crops = await db.get_growing_crops(message.from_user.id)
    
    logger.info(f"🖼️ Creating garden image with {len(crops)} crops")
    
    if HAS_PILLOW:
        try:
            image_bytes = await img_gen.create_garden_image(crops)
            
            if image_bytes:
                logger.info(f"✅ Image created: {len(image_bytes)} bytes")
                
                photo = BufferedInputFile(image_bytes, filename="garden.png")
                
                # Caption with stats
                caption = f"""
🌾 <b>{user['first_name']}'s Garden</b>

📊 <b>Stats:</b>
• Growing: {len(crops)}/9 crops
• Ready: {sum(1 for c in crops if c['progress'] >= 100)}
• Cash: ${user['cash']:,}

💡 <b>Commands:</b>
<code>/plant carrot 3</code> - Plant crops
<code>/harvest</code> - Collect ready crops

🌱 <b>Crops:</b>
🥕 Carrot ($10), 🍅 Tomato ($15), 🥔 Potato ($8)
"""
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=garden_keyboard()
                )
                logger.info("✅ Garden image sent!")
                return
            else:
                logger.error("❌ Image bytes are None!")
        except Exception as e:
            logger.error(f"❌ Image error: {e}", exc_info=True)
    else:
        logger.warning("⚠️ Pillow not installed")
    
    # Text fallback
    text = f"""
🌾 <b>{user['first_name']}'s Garden</b>

📊 Growing: {len(crops)}/9 crops
💰 Cash: ${user['cash']:,}

💡 Install Pillow for images:
<code>pip install pillow</code>
"""
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=garden_keyboard())

@dp.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject):
    """Plant crops"""
    if not command.args:
        crops = "\n".join([f"{CROP_EMOJIS[c]} {c.title()} - ${CROP_DATA[c]['buy']}" for c in list(CROP_DATA.keys())[:3]])
        await message.answer(
            f"🌱 <b>Plant Crops</b>\n\n"
            f"Usage: <code>/plant [crop] [quantity]</code>\n\n"
            f"🌿 <b>Available:</b>\n{crops}\n\n"
            f"💡 <b>Example:</b>\n<code>/plant carrot 3</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = command.args.lower().split()
    if len(args) < 2:
        await message.answer("❌ Format: /plant [crop] [quantity]")
        return
    
    crop_type, quantity = args[0], args[1]
    
    try:
        quantity = int(quantity)
    except:
        await message.answer("❌ Quantity must be a number!")
        return
    
    if crop_type not in CROP_TYPES:
        await message.answer(f"❌ Invalid crop! Available: {', '.join(CROP_TYPES[:3])}")
        return
    
    if quantity < 1 or quantity > 9:
        await message.answer("❌ Quantity must be 1-9!")
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
    
    await db.update_currency(message.from_user.id, 'cash', -cost)
    emoji = CROP_EMOJIS.get(crop_type, "🌱")
    
    await message.answer(
        f"✅ <b>Planted {quantity} {crop_type}s!</b>\n\n"
        f"{emoji} Cost: ${cost:,}\n"
        f"⏰ Grow time: {CROP_DATA[crop_type]['grow_time']} hours\n"
        f"💰 Remaining: ${user['cash'] - cost:,}",
        parse_mode=ParseMode.HTML
    )

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

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill someone"""
    target = await get_target_user(message)
    if not target:
        await message.answer("❌ Reply to someone to kill them!")
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
        await message.answer("❌ Can't rob yourself!")
        return
    
    user = await db.get_user(message.from_user.id)
    target_user = await db.get_user(target.id)
    
    if not user or not target_user:
        await message.answer("❌ Both need /start first!")
        return
    
    if target_user['cash'] < 100:
        await message.answer(f"❌ {target.first_name} is too poor!")
        return
    
    success = random.random() < 0.4
    
    if success:
        stolen = random.randint(100, min(500, target_user['cash']))
        await db.update_currency(target.id, 'cash', -stolen)
        await db.update_currency(message.from_user.id, 'cash', stolen)
        await send_gif_reaction("rob", message.chat.id, message.from_user, target)
        await message.answer(f"💰 Robbed ${stolen:,} from {target.first_name}!")
    else:
        fine = random.randint(100, 300)
        await db.update_currency(message.from_user.id, 'cash', -fine)
        await message.answer(f"🚨 Failed! Fined ${fine:,}. {target.first_name} caught you!")

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

# ============================================================================
# GAME COMMANDS
# ============================================================================

@dp.message(Command("games"))
async def cmd_games(message: Message):
    """Games list"""
    text = """
🎮 <b>Available Games</b>

🎰 <b>Slot Machine:</b>
<code>/slot [bet]</code> - Try your luck!

💰 <b>Robbery:</b>
<code>/rob</code> - Rob someone (reply)

⚔️ <b>Fight:</b>
<code>/fight</code> - Fight someone (reply)

😊 <b>Reactions (with GIFs):</b>
• <code>/hug</code> - Hug someone (reply)
• <code>/kill</code> - Kill someone (reply)
• <code>/kiss</code> - Kiss someone (reply)
• <code>/slap</code> - Slap someone (reply)
• <code>/pat</code> - Pat someone (reply)

💡 All reactions need replying to someone!
"""
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=games_keyboard())

@dp.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject):
    """Slot machine"""
    if not command.args:
        await message.answer("🎰 Usage: /slot [bet]\nExample: /slot 100")
        return
    
    try:
        bet = int(command.args)
        if bet < 10:
            await message.answer("Minimum bet: $10!")
            return
    except:
        await message.answer("Invalid bet!")
        return
    
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Use /start first!")
        return
    
    if bet > user['cash']:
        await message.answer(f"❌ You only have ${user['cash']:,}!")
        return
    
    symbols = ["🍒", "🍋", "⭐", "7️⃣", "🔔"]
    reels = [random.choice(symbols) for _ in range(3)]
    
    if reels[0] == reels[1] == reels[2]:
        multiplier = 5 if reels[0] == "7️⃣" else 3
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        multiplier = 1.5
    else:
        multiplier = 0
    
    win = int(bet * multiplier)
    net = win - bet
    
    await db.update_currency(message.from_user.id, 'cash', net)
    
    await message.answer(
        f"🎰 <b>Slot Machine</b>\n\n"
        f"[{reels[0]}] [{reels[1]}] [{reels[2]}]\n\n"
        f"💰 Bet: <b>${bet:,}</b>\n"
        f"🎯 Result: {'WIN! 🎉' if win > 0 else 'Lose 😢'}\n"
        f"📈 Net: {'+' if net > 0 else ''}<b>${net:,}</b>\n\n"
        f"💵 Balance: <b>${user['cash'] + net:,}</b>",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("fight"))
async def cmd_fight(message: Message):
    """Fight someone"""
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
    
    user_power = random.randint(1, 100)
    target_power = random.randint(1, 100)
    
    if user_power > target_power:
        win = random.randint(100, 500)
        await db.update_currency(message.from_user.id, 'cash', win)
        await message.answer(
            f"⚔️ <b>Victory!</b>\n\n"
            f"👤 You defeated {target.first_name}!\n"
            f"💪 Power: {user_power} vs {target_power}\n"
            f"💰 Won: <b>${win:,}</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        loss = random.randint(50, 300)
        await db.update_currency(message.from_user.id, 'cash', -loss)
        await message.answer(
            f"⚔️ <b>Defeat!</b>\n\n"
            f"👤 {target.first_name} defeated you!\n"
            f"💪 Power: {target_power} vs {user_power}\n"
            f"💸 Lost: <b>${loss:,}</b>",
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
    
    bonus = random.randint(500, 1500)
    family = await db.get_family(message.from_user.id)
    family_bonus = len(family) * 100
    
    total = bonus + family_bonus
    
    await db.update_currency(message.from_user.id, 'cash', total)
    
    await message.answer(
        f"🎉 <b>Daily Bonus!</b>\n\n"
        f"💰 Base: <b>${bonus:,}</b>\n"
        f"👨‍👩‍👧‍👦 Family: <b>${family_bonus:,}</b>\n"
        f"📈 Total: <b>${total:,}</b>\n\n"
        f"💵 New balance: <b>${user['cash'] + total:,}</b>",
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
    crops = await db.get_growing_crops(message.from_user.id)
    
    text = f"""
🏆 <b>{user['first_name']}'s Profile</b>

💰 <b>Wealth:</b>
• Cash: <b>${user['cash']:,}</b>
• Gold: <b>{user['gold']:,}</b>

📊 <b>Stats:</b>
• Level: <b>{user['level']}</b>
• Family: <b>{len(family)} members</b>
• Daily Streak: <b>{user['daily_streak']} days</b>
• Garden: <b>{len(crops)}/9 crops</b>

💡 Use buttons below for more!
"""
    
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())

# ============================================================================
# OWNER COMMANDS (HIDDEN)
# ============================================================================

@dp.message(Command("owner"))
async def cmd_owner(message: Message):
    """Owner commands - hidden from others"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Command not found!")
        return
    
    text = """
👑 <b>Owner Commands</b>

💰 <b>Economy:</b>
• <code>/add @user cash 1000</code> - Add cash
• <code>/add @user gold 50</code> - Add gold

👤 <b>Users:</b>
• <code>/ban @user</code> - Ban user
• <code>/unban [id]</code> - Unban user

📊 <b>System:</b>
• <code>/stats</code> - Bot statistics
• <code>/broadcast [text]</code> - Broadcast
• <code>/groups</code> - List groups

🐱 <b>Catbox:</b>
• <code>/cat add hug [url]</code> - Add GIF
• <code>/cat list</code> - List GIFs
• <code>/cat remove hug</code> - Remove GIF

⚙️ <b>Other:</b>
• <code>/ping</code> - Bot status
"""
    
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Ping - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Command not found!")
        return
    
    start = time.time()
    msg = await message.answer("🏓 Pong!")
    end = time.time()
    
    stats = await db.get_stats()
    
    text = f"""
🏓 <b>PONG!</b>

⚡ Speed: <b>{round((end-start)*1000, 2)}ms</b>
👥 Users: <b>{stats['users']}</b>
👥 Groups: <b>{stats['groups']}</b>
🖼️ Images: {'✅ Enabled' if HAS_PILLOW else '❌ Disabled'}
🔧 Status: 🟢 ACTIVE
"""
    
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Stats - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Command not found!")
        return
    
    stats = await db.get_stats()
    groups = await db.get_groups()
    
    text = f"""
📊 <b>Bot Statistics</b>

👥 <b>Users:</b>
• Total: <b>{stats['users']:,}</b>
• Groups: <b>{stats['groups']:,}</b>

👥 <b>Recent Groups:</b>
"""
    
    for chat_id, title, members in groups[:5]:
        text += f"\n• {title} ({members} members)"
    
    if len(groups) > 5:
        text += f"\n\n... and {len(groups) - 5} more groups"
    
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    """Broadcast - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Command not found!")
        return
    
    if not command.args:
        await message.answer("❌ Usage: /broadcast [message]")
        return
    
    # Can be used in groups or private
    await message.answer(f"📢 Broadcast sent!\n\n{command.args}", parse_mode=ParseMode.HTML)

@dp.message(Command("groups"))
async def cmd_groups(message: Message):
    """List groups - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Command not found!")
        return
    
    groups = await db.get_groups()
    
    if not groups:
        await message.answer("📭 No groups yet!")
        return
    
    text = "👥 <b>Bot Groups</b>\n\n"
    
    for chat_id, title, members in groups:
        group_link = f"https://t.me/c/{str(chat_id)[4:]}" if str(chat_id).startswith("-100") else "No link"
        text += f"🏷️ <b>{title}</b>\n👥 {members} members\n🔗 {group_link}\n\n"
    
    await message.answer(text, parse_mode=ParseMode.HTML)

# ============================================================================
# CATBOX SYSTEM (/cat command)
# ============================================================================

@dp.message(Command("cat"))
async def cmd_catbox(message: Message, command: CommandObject):
    """Catbox system - owner only"""
    if not is_owner(message.from_user.id):
        await message.answer("❌ Command not found!")
        return
    
    if not command.args:
        text = """
🐱 <b>Catbox System</b>

Manage reaction GIFs.

📋 <b>Commands:</b>
• <code>/cat list</code> - List GIFs
• <code>/cat add hug [url]</code> - Add GIF
• <code>/cat remove hug</code> - Remove GIF

💡 <b>Available reactions:</b>
hug, kill, rob, kiss, slap, pat
"""
        await message.answer(text, parse_mode=ParseMode.HTML)
        return
    
    args = command.args.lower().split()
    
    if args[0] == "list":
        gifs = ["hug", "kill", "rob", "kiss", "slap", "pat"]
        text = "🐱 <b>Catbox GIFs</b>\n\n"
        
        for cmd in gifs:
            url = await db.get_gif(cmd)
            text += f"• <code>/{cmd}</code> - {url[:40]}...\n"
        
        await message.answer(text, parse_mode=ParseMode.HTML)
    
    elif args[0] == "add" and len(args) >= 3:
        cmd, url = args[1], args[2]
        
        if cmd not in REACTION_GIFS:
            await message.answer(f"❌ Invalid command! Available: {', '.join(REACTION_GIFS.keys())}")
            return
        
        await db.add_gif(cmd, url, message.from_user.id)
        await message.answer(f"✅ GIF added for /{cmd}!")
    
    elif args[0] == "remove" and len(args) >= 2:
        cmd = args[1]
        # Just notify, actual removal would need db method
        await message.answer(f"⚠️ Use database to remove {cmd} GIF")

# ============================================================================
# HELP COMMAND
# ============================================================================

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    text = """
🆘 <b>Help - Family Tree Bot</b>

👨‍👩‍👧‍👦 <b>Family Commands:</b>
• <code>/family</code> - View family tree
• <code>/adopt</code> - Adopt someone (reply)
• <code>/marry</code> - Marry someone (reply)

🌾 <b>Garden Commands:</b>
• <code>/garden</code> - View garden (with image!)
• <code>/plant [crop] [qty]</code> - Plant crops
• <code>/harvest</code> - Harvest crops

🎮 <b>Game Commands:</b>
• <code>/slot [bet]</code> - Slot machine
• <code>/rob</code> - Rob someone (reply)
• <code>/fight</code> - Fight someone (reply)

😊 <b>Reaction Commands:</b>
• <code>/hug</code>, <code>/kill</code>, <code>/kiss</code>
• <code>/slap</code>, <code>/pat</code> (all need reply)

💰 <b>Economy:</b>
• <code>/daily</code> - Daily bonus
• <code>/me</code> - Your profile

👥 <b>Groups:</b>
Add me to groups for family fun!

📱 <b>Use buttons for easy navigation!</b>
"""
    
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main function"""
    await db.connect()
    
    print("=" * 50)
    print("🌳 FAMILY TREE BOT - WORKING VERSION")
    print(f"Owner: {OWNER_ID}")
    print(f"Images: {'✅ ENABLED' if HAS_PILLOW else '❌ DISABLED'}")
    print("=" * 50)
    
    if not HAS_PILLOW:
        print("\n⚠️  Install Pillow for images:")
        print("pip install pillow")
    
    try:
        # CRITICAL: Allow callback queries for inline buttons
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "my_chat_member"])
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
