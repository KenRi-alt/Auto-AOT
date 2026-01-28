#!/usr/bin/env python3
"""
FAMILY TREE TELEGRAM BOT
Complete production-ready implementation
Owner ID: 6108185460
Bot Token: 8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc
Log Channel: -1003662720845
"""

import os
import json
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import html
import uuid

# Telegram Bot Framework
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, URLInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Database
import asyncpg
from asyncpg.pool import Pool

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Your credentials
OWNER_ID = 6108185460
BOT_TOKEN = "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc"
LOG_CHANNEL = -1003662720845

# Database configuration (Railway will provide DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/famtree")

# Bot configuration
CURRENCIES = {
    "cash": "💵",
    "gold": "🪙", 
    "bonds": "👨‍👩‍👧‍👦",
    "credits": "⭐",
    "tokens": "🌱"
}

# Constants
DAILY_BONUS = 500
FRIEND_BONUS = 3000
GEMSTONE_BONUS = 5000
KILL_REWARD = 100
MAX_ROB_DAILY = 8
MAX_KILL_DAILY = 5

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MODELS & SCHEMA
# ============================================================================

class RelationType(Enum):
    PARENT = "parent"
    SPOUSE = "spouse"
    CHILD = "child"
    SIBLING = "sibling"

@dataclass
class User:
    """User data model"""
    id: int
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    cash: int = 1000
    gold: int = 0
    bonds: int = 0
    credits: int = 100
    tokens: int = 50
    gemstone: Optional[str] = None
    gemstone_date: Optional[datetime] = None
    weapon: str = "none"
    reputation: int = 100
    job: Optional[str] = None
    is_alive: bool = True
    last_daily: Optional[datetime] = None
    rob_count: int = 0
    kill_count: int = 0
    rob_reset: datetime = field(default_factory=datetime.utcnow)
    kill_reset: datetime = field(default_factory=datetime.utcnow)
    language: str = "en"
    
@dataclass
class FamilyRelation:
    """Family relationship model"""
    id: int
    user1_id: int
    user2_id: int
    relation_type: RelationType
    created_at: datetime
    
@dataclass
class Friendship:
    """Friend relationship model"""
    user1_id: int
    user2_id: int
    created_at: datetime
    rating: Optional[int] = None

@dataclass  
class Insurance:
    """Insurance model for kill mechanics"""
    id: int
    insurer_id: int
    insured_id: int
    amount: int
    created_at: datetime
    is_active: bool = True

@dataclass
class PendingProposal:
    """Pending proposal model"""
    id: str
    from_id: int
    to_id: int
    proposal_type: str  # 'adopt', 'marry', 'friend'
    created_at: datetime

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class Database:
    """Handles all database operations"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        
    async def connect(self):
        """Connect to PostgreSQL database"""
        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        await self.init_tables()
        logger.info("Database connected successfully")
        
    async def init_tables(self):
        """Initialize all database tables"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW(),
                    cash INTEGER DEFAULT 1000,
                    gold INTEGER DEFAULT 0,
                    bonds INTEGER DEFAULT 0,
                    credits INTEGER DEFAULT 100,
                    tokens INTEGER DEFAULT 50,
                    gemstone VARCHAR(50),
                    gemstone_date TIMESTAMP,
                    weapon VARCHAR(50) DEFAULT 'none',
                    reputation INTEGER DEFAULT 100,
                    job VARCHAR(100),
                    is_alive BOOLEAN DEFAULT TRUE,
                    last_daily TIMESTAMP,
                    rob_count INTEGER DEFAULT 0,
                    kill_count INTEGER DEFAULT 0,
                    rob_reset TIMESTAMP DEFAULT NOW(),
                    kill_reset TIMESTAMP DEFAULT NOW(),
                    language VARCHAR(10) DEFAULT 'en'
                )
            ''')
            
            # Family relations
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS family_relations (
                    id SERIAL PRIMARY KEY,
                    user1_id BIGINT NOT NULL,
                    user2_id BIGINT NOT NULL,
                    relation_type VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user1_id, user2_id, relation_type),
                    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Friendships
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS friendships (
                    user1_id BIGINT NOT NULL,
                    user2_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    PRIMARY KEY (user1_id, user2_id),
                    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Insurance
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS insurance (
                    id SERIAL PRIMARY KEY,
                    insurer_id BIGINT NOT NULL,
                    insured_id BIGINT NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (insurer_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (insured_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Pending proposals
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS pending_proposals (
                    id VARCHAR(50) PRIMARY KEY,
                    from_id BIGINT NOT NULL,
                    to_id BIGINT NOT NULL,
                    proposal_type VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Custom GIFs
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS custom_gifs (
                    id SERIAL PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    gif_type VARCHAR(20) NOT NULL,
                    file_id VARCHAR(255) NOT NULL,
                    added_by BIGINT NOT NULL,
                    added_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            logger.info("Database tables initialized")
    
    # User operations
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM users WHERE id = $1', user_id
            )
            if row:
                return User(**dict(row))
        return None
    
    async def create_user(self, user: types.User) -> User:
        """Create new user"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
            ''', user.id, user.username, user.first_name, user.last_name)
            
            # Get the created user
            row = await conn.fetchrow(
                'SELECT * FROM users WHERE id = $1', user.id
            )
            return User(**dict(row))
    
    async def update_user(self, user_id: int, **kwargs):
        """Update user fields"""
        if not kwargs:
            return
            
        async with self.pool.acquire() as conn:
            set_clause = ', '.join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
            query = f'UPDATE users SET {set_clause} WHERE id = $1'
            await conn.execute(query, user_id, *kwargs.values())
    
    # Family operations
    async def add_family_relation(self, user1_id: int, user2_id: int, relation_type: RelationType) -> bool:
        """Add family relationship"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO family_relations (user1_id, user2_id, relation_type)
                    VALUES ($1, $2, $3), ($2, $1, $3)
                ''', user1_id, user2_id, relation_type.value)
                return True
            except Exception as e:
                logger.error(f"Failed to add family relation: {e}")
                return False
    
    async def remove_family_relation(self, user1_id: int, user2_id: int, relation_type: RelationType):
        """Remove family relationship"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                DELETE FROM family_relations 
                WHERE (user1_id = $1 AND user2_id = $2 AND relation_type = $3)
                   OR (user1_id = $2 AND user2_id = $1 AND relation_type = $3)
            ''', user1_id, user2_id, relation_type.value)
    
    async def get_family(self, user_id: int) -> List[Tuple[int, str]]:
        """Get all family members for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT DISTINCT 
                    CASE WHEN user1_id = $1 THEN user2_id ELSE user1_id END as family_member_id,
                    relation_type
                FROM family_relations 
                WHERE user1_id = $1 OR user2_id = $1
                ORDER BY relation_type
            ''', user_id)
            
            return [(row['family_member_id'], row['relation_type']) for row in rows]
    
    # Friend operations
    async def add_friend(self, user1_id: int, user2_id: int) -> bool:
        """Add friendship (bidirectional)"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO friendships (user1_id, user2_id)
                    VALUES ($1, $2), ($2, $1)
                    ON CONFLICT (user1_id, user2_id) DO NOTHING
                ''', user1_id, user2_id)
                return True
            except Exception as e:
                logger.error(f"Failed to add friend: {e}")
                return False
    
    async def remove_friend(self, user1_id: int, user2_id: int):
        """Remove friendship"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                DELETE FROM friendships 
                WHERE (user1_id = $1 AND user2_id = $2)
                   OR (user1_id = $2 AND user2_id = $1)
            ''', user1_id, user2_id)
    
    async def get_friends(self, user_id: int) -> List[int]:
        """Get all friends for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user2_id FROM friendships WHERE user1_id = $1
                UNION
                SELECT user1_id FROM friendships WHERE user2_id = $1
            ''', user_id)
            
            return [row['user2_id'] for row in rows]
    
    async def are_friends(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are friends"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT 1 FROM friendships 
                WHERE (user1_id = $1 AND user2_id = $2)
                   OR (user1_id = $2 AND user2_id = $1)
                LIMIT 1
            ''', user1_id, user2_id)
            return row is not None
    
    # Proposal operations
    async def create_proposal(self, proposal_id: str, from_id: int, to_id: int, proposal_type: str):
        """Create a pending proposal"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO pending_proposals (id, from_id, to_id, proposal_type)
                VALUES ($1, $2, $3, $4)
            ''', proposal_id, from_id, to_id, proposal_type)
    
    async def get_proposal(self, proposal_id: str) -> Optional[PendingProposal]:
        """Get proposal by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM pending_proposals WHERE id = $1', proposal_id
            )
            if row:
                return PendingProposal(**dict(row))
        return None
    
    async def delete_proposal(self, proposal_id: str):
        """Delete a proposal"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM pending_proposals WHERE id = $1', proposal_id
            )
    
    # Insurance operations
    async def add_insurance(self, insurer_id: int, insured_id: int, amount: int) -> int:
        """Add insurance policy"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO insurance (insurer_id, insured_id, amount)
                VALUES ($1, $2, $3)
                RETURNING id
            ''', insurer_id, insured_id, amount)
            return row['id']
    
    async def get_active_insurances(self, insured_id: int) -> List[Insurance]:
        """Get active insurance policies for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM insurance 
                WHERE insured_id = $1 AND is_active = TRUE
            ''', insured_id)
            
            return [Insurance(**dict(row)) for row in rows]
    
    async def deactivate_insurance(self, insurance_id: int):
        """Deactivate insurance policy"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE insurance SET is_active = FALSE WHERE id = $1', insurance_id
            )
    
    # Utility methods
    async def reset_daily_counts(self):
        """Reset daily rob/kill counts for all users"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET rob_count = 0, kill_count = 0,
                    rob_reset = NOW(), kill_reset = NOW()
                WHERE rob_reset < NOW() - INTERVAL '1 day'
                   OR kill_reset < NOW() - INTERVAL '1 day'
            ''')
    
    async def get_leaderboard(self, chat_id: int) -> List[Tuple[int, str, int]]:
        """Get money leaderboard for a group"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT u.id, u.first_name, u.cash
                FROM users u
                ORDER BY u.cash DESC
                LIMIT 10
            ''')
            
            return [(row['id'], row['first_name'], row['cash']) for row in rows]

# ============================================================================
# BOT STATE & STORAGE
# ============================================================================

class Form(StatesGroup):
    """FSM states for various operations"""
    waiting_for_rating = State()
    waiting_for_broadcast = State()
    waiting_for_admin_action = State()

# Global instances
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None
db: Database = Database()

# Reaction GIFs mapping
REACTION_GIFS = {
    "hug": ["CAACAgIAAxkBAAIBAAABX7-vHtIjVtPQpeQ8WvMClMs_AAIiJwACChqQS_ij4UoiIi_CIwQ", 
            "CAACAgIAAxkBAAIBAAACX7-vL6B3cSUAAYVJpZogLpQQJskAAjsAAwoakEslb5h1NG1JfyME"],
    "pat": ["CAACAgIAAxkBAAIBAAADX7-vR-13T0QPGdPGt-LFe58GAAJvAANWnb0K4h5MbER2k50jBA", 
            "CAACAgIAAxkBAAIBAAAFX7-vVhJ0lN_B22xQzDON6a0oAAKGAAMKGpBLpJ62Oo-7u8UjBA"],
    "kiss": ["CAACAgIAAxkBAAIBAAAGX7-vYx4Nbz9mswABGg0k8M4rWQACYAADVp29CkqTT-5O2PAoIwQ", 
             "CAACAgIAAxkBAAIBAAAHX7-vb5JpSj1A0JXxU5C9S3P3AAKIAANWnb0KQHw7QrSH_HYjBA"],
    "cry": ["CAACAgIAAxkBAAIBAAAIX7-vfNYG-IFMp8WUlmOAcakHAAKQAANWnb0K4mYHQG_3sCgjBA", 
            "CAACAgIAAxkBAAIBAAAJX7-vhj6pA86oIAXW6fFQ0k4nAAKTAANWnb0Kc9_IJJVUc2kjBA"],
    "smile": ["CAACAgIAAxkBAAIBAAAJX7-vhj6pA86oIAXW6fFQ0k4nAAKTAANWnb0Kc9_IJJVUc2kjBA",
              "CAACAgIAAxkBAAIBAAAKX7-vkkY0XAZ0rS1CM7bQxQYFAAKUAANWnb0K3Mp-j_hdTMsjBA"]
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_or_create_user(user: types.User) -> User:
    """Get user from DB or create if doesn't exist"""
    db_user = await db.get_user(user.id)
    if not db_user:
        db_user = await db.create_user(user)
        logger.info(f"Created new user: {user.id} - {user.first_name}")
        
        # Send welcome message
        await bot.send_message(
            user.id,
            f"👋 Welcome to Family Tree Bot, {user.first_name}!\n\n"
            f"Use /help to see available commands.\n"
            f"Start by using /me to see your profile!"
        )
    
    return db_user

async def send_log(message: str):
    """Send log message to owner's channel"""
    try:
        await bot.send_message(LOG_CHANNEL, f"📊 {message}")
    except Exception as e:
        logger.error(f"Failed to send log: {e}")

async def format_money(user: User) -> str:
    """Format user's money for display"""
    return (
        f"💵 Cash: {user.cash:,}\n"
        f"🪙 Gold: {user.gold:,}\n"  
        f"👨‍👩‍👧‍👦 Bonds: {user.bonds:,}\n"
        f"⭐ Credits: {user.credits:,}\n"
        f"🌱 Tokens: {user.tokens:,}"
    )

async def can_perform_action(user: User, action: str) -> Tuple[bool, str]:
    """Check if user can perform rob/kill action"""
    now = datetime.utcnow()
    
    if action == "rob":
        if user.rob_reset.date() < now.date():
            await db.update_user(user.id, rob_count=0, rob_reset=now)
            user.rob_count = 0
        
        if user.rob_count >= MAX_ROB_DAILY:
            return False, f"You can only rob {MAX_ROB_DAILY} times per day!"
            
    elif action == "kill":
        if user.kill_reset.date() < now.date():
            await db.update_user(user.id, kill_count=0, kill_reset=now)
            user.kill_count = 0
        
        if user.kill_count >= MAX_KILL_DAILY:
            return False, f"You can only kill {MAX_KILL_DAILY} times per day!"
    
    if not user.is_alive:
        return False, "You are dead! Use /medical to revive first."
    
    return True, ""

async def process_daily_bonus(user: User) -> Tuple[int, str, Optional[str]]:
    """Process daily bonus and gemstone"""
    now = datetime.utcnow()
    bonus = DAILY_BONUS
    gemstone = user.gemstone
    
    # Check if already claimed today
    if user.last_daily and user.last_daily.date() == now.date():
        return 0, None, "You already claimed your daily bonus today!"
    
    # Assign new gemstone if needed
    gemstones = ["Ruby", "Sapphire", "Emerald", "Diamond", "Amethyst"]
    if not user.gemstone or (user.gemstone_date and user.gemstone_date.date() < now.date()):
        gemstone = random.choice(gemstones)
        await db.update_user(
            user.id, 
            gemstone=gemstone,
            gemstone_date=now,
            last_daily=now
        )
    else:
        await db.update_user(user.id, last_daily=now)
    
    # Add family bonus
    family = await db.get_family(user.id)
    family_bonus = len(family) * 50
    bonus += family_bonus
    
    # Update user cash
    await db.update_user(user.id, cash=user.cash + bonus)
    
    return bonus, gemstone, None

async def send_proposal(from_user: User, to_user: User, proposal_type: str, message: Message):
    """Send a proposal to another user"""
    proposal_id = str(uuid.uuid4())
    
    # Create proposal in DB
    await db.create_proposal(proposal_id, from_user.id, to_user.id, proposal_type)
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Accept", 
                callback_data=f"proposal_{proposal_id}_accept"
            ),
            InlineKeyboardButton(
                text="❌ Decline", 
                callback_data=f"proposal_{proposal_id}_decline"
            )
        ]
    ])
    
    proposal_texts = {
        "adopt": f"👶 {from_user.first_name} wants to adopt you!",
        "marry": f"💖 {from_user.first_name} wants to marry you!",
        "friend": f"🤝 {from_user.first_name} wants to be your friend!"
    }
    
    # Try to send private message
    try:
        await bot.send_message(
            to_user.id,
            f"{proposal_texts[proposal_type]}\n\n"
            f"You'll receive ${FRIEND_BONUS if proposal_type == 'friend' else 0} bonus if accepted!",
            reply_markup=keyboard
        )
        
        await message.reply_text(
            f"✅ {proposal_type.capitalize()} proposal sent to {to_user.first_name}!"
        )
        
    except Exception as e:
        await message.reply_text(
            f"❌ Cannot send proposal. User might have blocked the bot or not started it."
        )
        await db.delete_proposal(proposal_id)

async def generate_tree(user_id: int) -> str:
    """Generate text-based family tree"""
    family = await db.get_family(user_id)
    
    if not family:
        return "Your family tree is empty. Use /adopt or /marry to add family members!"
    
    # Get user
    user = await db.get_user(user_id)
    if not user:
        return "User not found!"
    
    tree_lines = [f"🌳 Family Tree of {user.first_name}:"]
    
    # Group by relation type
    relations = {}
    for member_id, rel_type in family:
        member = await db.get_user(member_id)
        if member:
            if rel_type not in relations:
                relations[rel_type] = []
            relations[rel_type].append(member.first_name)
    
    # Build tree
    for rel_type, names in relations.items():
        icon = {
            "parent": "👴",
            "spouse": "💑", 
            "child": "👶",
            "sibling": "👫"
        }.get(rel_type, "👤")
        
        tree_lines.append(f"\n{icon} {rel_type.capitalize()}s:")
        for name in names:
            tree_lines.append(f"  └─ {name}")
    
    return "\n".join(tree_lines)

async def get_custom_gif(chat_id: int, gif_type: str) -> Optional[str]:
    """Get custom GIF for rob/kill actions"""
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT file_id FROM custom_gifs 
            WHERE chat_id = $1 AND gif_type = $2
            ORDER BY RANDOM() 
            LIMIT 1
        ''', chat_id, gif_type)
        
        if row:
            return row['file_id']
    
    # Fallback to default GIFs
    default_gifs = {
        "robyes": ["CAACAgIAAxkBAAIBAAABX7-vHtIjVtPQpeQ8WvMClMs_AAIiJwACChqQS_ij4UoiIi_CIwQ"],
        "robno": ["CAACAgIAAxkBAAIBAAACX7-vL6B3cSUAAYVJpZogLpQQJskAAjsAAwoakEslb5h1NG1JfyME"],
        "killyes": ["CAACAgIAAxkBAAIBAAADX7-vR-13T0QPGdPGt-LFe58GAAJvAANWnb0K4h5MbER2k50jBA"],
        "killno": ["CAACAgIAAxkBAAIBAAAFX7-vVhJ0lN_B22xQzDON6a0oAAKGAAMKGpBLpJ62Oo-7u8UjBA"]
    }
    
    if gif_type in default_gifs and default_gifs[gif_type]:
        return random.choice(default_gifs[gif_type])
    
    return None

# ============================================================================
# COMMAND HANDLERS - USER COMMANDS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command handler"""
    user = await get_or_create_user(message.from_user)
    
    welcome_text = (
        f"👋 Welcome to Family Tree Bot, {user.first_name}!\n\n"
        f"🌳 Create your virtual family\n"
        f"🤝 Make friends globally\n"  
        f"💰 Earn money and buy items\n"
        f"⚔️ Engage in PvP battles\n\n"
        f"Use /help to see all commands\n"
        f"Use /me to see your profile"
    )
    
    # Create main menu keyboard
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Profile"), KeyboardButton(text="🌳 Family")],
            [KeyboardButton(text="🤝 Friends"), KeyboardButton(text="💰 Economy")],
            [KeyboardButton(text="⚔️ PvP"), KeyboardButton(text="🎮 Games")],
            [KeyboardButton(text="🆘 Help")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(welcome_text, reply_markup=keyboard)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command handler"""
    help_text = (
        "📚 **Family Tree Bot - Command Guide**\n\n"
        
        "👨‍👩‍👧‍👦 **Family Commands:**\n"
        "• /adopt (reply) - Adopt someone as child\n"
        "• /marry (reply) - Propose marriage\n"  
        "• /divorce - End a marriage\n"
        "• /disown - Remove family member\n"
        "• /tree - View your family tree\n"
        "• /family - List family members\n\n"
        
        "🤝 **Friend Circle:**\n"
        "• /friend (reply) - Add as friend\n"
        "• /circle - View friend circle\n"
        "• /unfriend - Remove friend\n"
        "• /suggestions - Friend suggestions\n"
        "• /flink - Get friend link\n\n"
        
        "💰 **Economy & Daily:**\n"
        "• /me or /account - Your profile\n"
        "• /daily - Claim daily bonus\n"
        "• /fuse (reply) - Fuse gemstones\n"
        "• /pay [amount] - Send money\n"
        "• /shop - Buy items\n"
        "• /leaderboard - Money rankings\n\n"
        
        "⚔️ **PvP & Combat:**\n"
        "• /rob (reply) - Rob someone\n"
        "• /kill (reply) - Kill someone\n"
        "• /weapon - Buy weapons\n"
        "• /insurance (reply) - Insure someone\n"
        "• /medical - Revive yourself\n\n"
        
        "😄 **Fun & Social:**\n"
        "• ,hug ,pat ,kiss etc. - Send GIFs\n"
        "• /reactions - List all reactions\n"
        "• /addgif - Add custom GIF\n"
        "• /setpic (reply to image) - Set profile pic\n\n"
        
        "⚙️ **Settings:**\n"
        "• /setlang - Change language\n"
        "• /commands - Full command list\n\n"
        
        "👑 **Admin Commands:**\n"
        "• /admin help - Show admin commands\n"
        "(Only for bot owner)"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("me", "account", "profile"))
async def cmd_me(message: Message):
    """Show user profile"""
    user = await get_or_create_user(message.from_user)
    
    # Get family and friend counts
    family = await db.get_family(user.id)
    friends = await db.get_friends(user.id)
    
    profile_text = (
        f"👤 **Profile of {user.first_name}**\n\n"
        f"📊 **Stats:**\n"
        f"• 🆔 ID: `{user.id}`\n"
        f"• 👨‍👩‍👧‍👦 Family: {len(family)} members\n"
        f"• 🤝 Friends: {len(friends)} friends\n"
        f"• ⭐ Reputation: {user.reputation}/200\n"
        f"• 💼 Job: {user.job or 'Unemployed'}\n"
        f"• ❤️ Status: {'Alive ✅' if user.is_alive else 'Dead 💀'}\n\n"
        
        f"💰 **Economy:**\n"
        f"{await format_money(user)}\n\n"
        
        f"💎 **Daily Gemstone:** {user.gemstone or 'None'}\n"
        f"🔫 **Weapon:** {user.weapon.capitalize()}\n\n"
        
        f"📈 **Daily Limits:**\n"
        f"• Robs: {user.rob_count}/{MAX_ROB_DAILY}\n"
        f"• Kills: {user.kill_count}/{MAX_KILL_DAILY}"
    )
    
    # Create action buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Daily Bonus", callback_data="daily_bonus"),
            InlineKeyboardButton(text="🛒 Shop", callback_data="open_shop")
        ],
        [
            InlineKeyboardButton(text="🌳 View Tree", callback_data="view_tree"),
            InlineKeyboardButton(text="🤝 Friends", callback_data="view_friends")
        ],
        [
            InlineKeyboardButton(text="🔫 Weapons", callback_data="weapons"),
            InlineKeyboardButton(text="📊 Stats", callback_data="stats")
        ]
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Claim daily bonus"""
    user = await get_or_create_user(message.from_user)
    
    bonus, gemstone, error = await process_daily_bonus(user)
    
    if error:
        await message.answer(f"❌ {error}")
        return
    
    # Create gemstone fusion button if user has gemstone
    keyboard = None
    if gemstone:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💎 Find {gemstone} Match", 
                    callback_data="find_gem_match"
                )
            ]
        ])
    
    response = (
        f"🎉 **Daily Bonus Claimed!**\n\n"
        f"💰 Received: ${bonus:,}\n"
        f"💎 Today's Gemstone: **{gemstone}**\n\n"
        f"💵 New Balance: ${user.cash + bonus:,}\n\n"
        f"Find someone with the same gemstone and use /fuse (reply to them) "
        f"to get ${GEMSTONE_BONUS:,} bonus each!"
    )
    
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("tree"))
async def cmd_tree(message: Message):
    """Show family tree"""
    user = await get_or_create_user(message.from_user)
    tree_text = await generate_tree(user.id)
    await message.answer(tree_text)

@dp.message(Command("family"))
async def cmd_family(message: Message):
    """List family members"""
    user = await get_or_create_user(message.from_user)
    family = await db.get_family(user.id)
    
    if not family:
        await message.answer("You have no family members yet. Use /adopt or /marry to start a family!")
        return
    
    family_text = f"👨‍👩‍👧‍👦 **Family of {user.first_name}:**\n\n"
    
    for member_id, rel_type in family:
        member = await db.get_user(member_id)
        if member:
            icon = {
                "parent": "👴",
                "spouse": "💑",
                "child": "👶", 
                "sibling": "👫"
            }.get(rel_type, "👤")
            
            status = "❤️" if member.is_alive else "💀"
            family_text += f"{icon} {member.first_name} - {rel_type} {status}\n"
    
    await message.answer(family_text, parse_mode="Markdown")

@dp.message(Command("adopt"))
async def cmd_adopt(message: Message):
    """Adopt someone as child"""
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of the person you want to adopt!")
        return
    
    from_user = await get_or_create_user(message.from_user)
    to_user = await get_or_create_user(message.reply_to_message.from_user)
    
    # Check if trying to adopt self
    if from_user.id == to_user.id:
        await message.answer("❌ You cannot adopt yourself!")
        return
    
    # Check if already in family
    family = await db.get_family(from_user.id)
    for member_id, _ in family:
        if member_id == to_user.id:
            await message.answer("❌ This user is already in your family!")
            return
    
    await send_proposal(from_user, to_user, "adopt", message)

@dp.message(Command("marry"))
async def cmd_marry(message: Message):
    """Propose marriage"""
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of the person you want to marry!")
        return
    
    from_user = await get_or_create_user(message.from_user)
    to_user = await get_or_create_user(message.reply_to_message.from_user)
    
    # Check if trying to marry self
    if from_user.id == to_user.id:
        await message.answer("❌ You cannot marry yourself!")
        return
    
    # Check if already married
    family = await db.get_family(from_user.id)
    for member_id, rel_type in family:
        if member_id == to_user.id and rel_type == "spouse":
            await message.answer("❌ You are already married to this person!")
            return
    
    await send_proposal(from_user, to_user, "marry", message)

@dp.message(Command("friend"))
async def cmd_friend(message: Message):
    """Send friend request"""
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of the person you want to befriend!")
        return
    
    from_user = await get_or_create_user(message.from_user)
    to_user = await get_or_create_user(message.reply_to_message.from_user)
    
    # Check if trying to friend self
    if from_user.id == to_user.id:
        await message.answer("❌ You cannot befriend yourself!")
        return
    
    # Check if already friends
    if await db.are_friends(from_user.id, to_user.id):
        await message.answer("❌ You are already friends with this person!")
        return
    
    await send_proposal(from_user, to_user, "friend", message)

@dp.message(Command("circle", "friends"))
async def cmd_circle(message: Message):
    """Show friend circle"""
    user = await get_or_create_user(message.from_user)
    friends = await db.get_friends(user.id)
    
    if not friends:
        await message.answer("You have no friends yet. Use /friend to add someone!")
        return
    
    circle_text = f"🤝 **Friend Circle of {user.first_name}:**\n\n"
    
    for i, friend_id in enumerate(friends[:20], 1):  # Limit to 20 for readability
        friend = await db.get_user(friend_id)
        if friend:
            status = "🟢" if friend.is_alive else "🔴"
            circle_text += f"{i}. {friend.first_name} {status}\n"
    
    if len(friends) > 20:
        circle_text += f"\n... and {len(friends) - 20} more friends!"
    
    # Add friend actions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Suggestions", callback_data="friend_suggestions"),
            InlineKeyboardButton(text="📊 Active", callback_data="active_friends")
        ],
        [
            InlineKeyboardButton(text="🔗 Get Friend Link", callback_data="get_flink"),
            InlineKeyboardButton(text="⭐ Rate Friends", callback_data="rate_friends")
        ]
    ])
    
    await message.answer(circle_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("unfriend"))
async def cmd_unfriend(message: Message):
    """Unfriend someone"""
    user = await get_or_create_user(message.from_user)
    friends = await db.get_friends(user.id)
    
    if not friends:
        await message.answer("You have no friends to unfriend!")
        return
    
    # Create inline keyboard with friends
    buttons = []
    for friend_id in friends[:10]:  # Limit to 10 for button layout
        friend = await db.get_user(friend_id)
        if friend:
            buttons.append([InlineKeyboardButton(
                text=f"❌ {friend.first_name}",
                callback_data=f"unfriend_{friend.id}"
            )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Select a friend to unfriend:", reply_markup=keyboard)

@dp.message(Command("rob"))
async def cmd_rob(message: Message):
    """Rob another user"""
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of the person you want to rob!")
        return
    
    robber = await get_or_create_user(message.from_user)
    victim = await get_or_create_user(message.reply_to_message.from_user)
    
    # Check conditions
    can_rob, error = await can_perform_action(robber, "rob")
    if not can_rob:
        await message.answer(f"❌ {error}")
        return
    
    if robber.id == victim.id:
        await message.answer("❌ You cannot rob yourself!")
        return
    
    if not victim.is_alive:
        await message.answer("❌ Cannot rob dead people!")
        return
    
    # Calculate success chance based on weapon
    success_chance = 30  # Base chance
    if robber.weapon == "knife":
        success_chance += 10
    elif robber.weapon == "gun":
        success_chance += 25
    elif robber.weapon == "shotgun":
        success_chance += 40
    
    success = random.randint(1, 100) <= success_chance
    
    # Get appropriate GIF
    gif_type = "robyes" if success else "robno"
    gif_file_id = await get_custom_gif(message.chat.id, gif_type)
    
    if success:
        # Calculate stolen amount (10-20% of victim's cash, max $1000)
        steal_percent = random.uniform(0.1, 0.2)
        stolen = min(int(victim.cash * steal_percent), 1000)
        
        if stolen > 0:
            # Update balances
            await db.update_user(robber.id, cash=robber.cash + stolen)
            await db.update_user(victim.id, cash=victim.cash - stolen)
            
            # Update rob count
            await db.update_user(robber.id, rob_count=robber.rob_count + 1)
            
            # Decrease reputation
            new_rep = max(0, robber.reputation - 5)
            await db.update_user(robber.id, reputation=new_rep)
            
            response = (
                f"💰 **Robbery Successful!**\n\n"
                f"🦹 {robber.first_name} robbed ${stolen:,} from {victim.first_name}!\n"
                f"🎯 Success Chance: {success_chance}%\n"
                f"📉 Reputation: -5 (Now: {new_rep})\n\n"
                f"💵 {robber.first_name}: ${robber.cash + stolen:,}\n"
                f"💵 {victim.first_name}: ${victim.cash - stolen:,}"
            )
            
            # Send notification to victim if possible
            try:
                await bot.send_message(
                    victim.id,
                    f"⚠️ You were robbed by {robber.first_name}!\n"
                    f"💰 Lost: ${stolen:,}\n"
                    f"💵 New Balance: ${victim.cash - stolen:,}"
                )
            except:
                pass
            
        else:
            success = False
            response = f"💰 {victim.first_name} has no money to rob!"
    
    if not success:
        # Update rob count even on failure
        await db.update_user(robber.id, rob_count=robber.rob_count + 1)
        
        # Decrease reputation more on failure
        new_rep = max(0, robber.reputation - 10)
        await db.update_user(robber.id, reputation=new_rep)
        
        response = (
            f"🚫 **Robbery Failed!**\n\n"
            f"🦹 {robber.first_name} tried to rob {victim.first_name} but failed!\n"
            f"🎯 Success Chance: {success_chance}%\n"
            f"📉 Reputation: -10 (Now: {new_rep})"
        )
    
    # Send message with GIF if available
    if gif_file_id:
        await message.answer_animation(gif_file_id, caption=response, parse_mode="Markdown")
    else:
        await message.answer(response, parse_mode="Markdown")

@dp.message(Command("kill"))
async def cmd_kill(message: Message):
    """Kill another user"""
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of the person you want to kill!")
        return
    
    killer = await get_or_create_user(message.from_user)
    victim = await get_or_create_user(message.reply_to_message.from_user)
    
    # Check conditions
    can_kill, error = await can_perform_action(killer, "kill")
    if not can_kill:
        await message.answer(f"❌ {error}")
        return
    
    if killer.id == victim.id:
        await message.answer("❌ You cannot kill yourself!")
        return
    
    if not victim.is_alive:
        await message.answer("❌ This person is already dead!")
        return
    
    # Calculate success chance based on weapon
    success_chance = 20  # Base chance
    if killer.weapon == "knife":
        success_chance += 15
    elif killer.weapon == "gun":
        success_chance += 30
    elif killer.weapon == "shotgun":
        success_chance += 50
    
    success = random.randint(1, 100) <= success_chance
    
    # Get appropriate GIF
    gif_type = "killyes" if success else "killno"
    gif_file_id = await get_custom_gif(message.chat.id, gif_type)
    
    if success:
        # Kill the victim
        await db.update_user(victim.id, is_alive=False)
        
        # Update kill count
        await db.update_user(killer.id, kill_count=killer.kill_count + 1)
        
        # Decrease reputation significantly
        new_rep = max(0, killer.reputation - 20)
        await db.update_user(killer.id, reputation=new_rep)
        
        # Killer gets reward
        reward = KILL_REWARD
        await db.update_user(killer.id, cash=killer.cash + reward)
        
        # Process insurance payouts
        insurances = await db.get_active_insurances(victim.id)
        total_payout = 0
        
        for insurance in insurances:
            # Payout to insurer
            insurer = await db.get_user(insurance.insurer_id)
            if insurer:
                await db.update_user(
                    insurer.id, 
                    cash=insurer.cash + insurance.amount
                )
                total_payout += insurance.amount
            
            # Deactivate insurance
            await db.deactivate_insurance(insurance.id)
        
        response = (
            f"🔪 **Assassination Successful!**\n\n"
            f"💀 {killer.first_name} killed {victim.first_name}!\n"
            f"💰 Reward: ${reward:,}\n"
            f"🎯 Success Chance: {success_chance}%\n"
            f"📉 Reputation: -20 (Now: {new_rep})\n\n"
            f"📊 Insurance Payouts: ${total_payout:,} distributed"
        )
        
        # Send death notification to victim
        try:
            await bot.send_message(
                victim.id,
                f"💀 **You were killed by {killer.first_name}!**\n\n"
                f"You are now dead. Use /medical to revive yourself.\n"
                f"💰 Insurance paid out: ${total_payout:,}"
            )
        except:
            pass
        
        # Log the kill
        await send_log(
            f"🔪 Kill: {killer.first_name} killed {victim.first_name}\n"
            f"Reward: ${reward} | Insurance: ${total_payout}"
        )
    
    else:
        # Update kill count even on failure
        await db.update_user(killer.id, kill_count=killer.kill_count + 1)
        
        # Decrease reputation
        new_rep = max(0, killer.reputation - 15)
        await db.update_user(killer.id, reputation=new_rep)
        
        response = (
            f"🛡️ **Assassination Failed!**\n\n"
            f"💀 {killer.first_name} tried to kill {victim.first_name} but failed!\n"
            f"🎯 Success Chance: {success_chance}%\n"
            f"📉 Reputation: -15 (Now: {new_rep})"
        )
    
    # Send message with GIF if available
    if gif_file_id:
        await message.answer_animation(gif_file_id, caption=response, parse_mode="Markdown")
    else:
        await message.answer(response, parse_mode="Markdown")

@dp.message(Command("fuse"))
async def cmd_fuse(message: Message):
    """Fuse gemstones with another user"""
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of someone with the same gemstone!")
        return
    
    user1 = await get_or_create_user(message.from_user)
    user2 = await get_or_create_user(message.reply_to_message.from_user)
    
    if user1.id == user2.id:
        await message.answer("❌ You cannot fuse with yourself!")
        return
    
    if not user1.gemstone or not user2.gemstone:
        await message.answer("❌ One of you doesn't have a gemstone!")
        return
    
    if user1.gemstone != user2.gemstone:
        await message.answer(f"❌ Gemstones don't match! You have {user1.gemstone}, they have {user2.gemstone}")
        return
    
    # Check if gemstones are from today
    now = datetime.utcnow()
    if user1.gemstone_date and user1.gemstone_date.date() < now.date():
        await message.answer("❌ Your gemstone is from yesterday! Get a new one with /daily")
        return
    
    if user2.gemstone_date and user2.gemstone_date.date() < now.date():
        await message.answer("❌ Their gemstone is from yesterday! Tell them to use /daily")
        return
    
    # Successful fusion - give bonus to both
    await db.update_user(user1.id, 
        cash=user1.cash + GEMSTONE_BONUS,
        gemstone=None,
        gemstone_date=None
    )
    
    await db.update_user(user2.id,
        cash=user2.cash + GEMSTONE_BONUS,
        gemstone=None,
        gemstone_date=None
    )
    
    response = (
        f"💎 **Gemstone Fusion Successful!**\n\n"
        f"✨ {user1.first_name} and {user2.first_name} fused their {user1.gemstone} gemstones!\n"
        f"💰 Each received: ${GEMSTONE_BONUS:,}\n\n"
        f"💵 {user1.first_name}: ${user1.cash + GEMSTONE_BONUS:,}\n"
        f"💵 {user2.first_name}: ${user2.cash + GEMSTONE_BONUS:,}"
    )
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(Command("pay"))
async def cmd_pay(message: Message, command: CommandObject):
    """Pay money to another user"""
    if not command.args:
        await message.answer("❌ Usage: /pay [amount] (reply to user's message)")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Please reply to the message of the person you want to pay!")
        return
    
    try:
        amount = int(command.args)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Please provide a valid positive number!")
        return
    
    sender = await get_or_create_user(message.from_user)
    receiver = await get_or_create_user(message.reply_to_message.from_user)
    
    if sender.id == receiver.id:
        await message.answer("❌ You cannot pay yourself!")
        return
    
    if sender.cash < amount:
        await message.answer(f"❌ Insufficient funds! You have ${sender.cash:,}, need ${amount:,}")
        return
    
    # Process payment
    await db.update_user(sender.id, cash=sender.cash - amount)
    await db.update_user(receiver.id, cash=receiver.cash + amount)
    
    # Increase sender's reputation
    new_rep = min(200, sender.reputation + 2)
    await db.update_user(sender.id, reputation=new_rep)
    
    response = (
        f"💰 **Payment Successful!**\n\n"
        f"📤 {sender.first_name} paid ${amount:,} to {receiver.first_name}\n"
        f"⭐ Reputation: +2 (Now: {new_rep})\n\n"
        f"💵 {sender.first_name}: ${sender.cash - amount:,}\n"
        f"💵 {receiver.first_name}: ${receiver.cash + amount:,}"
    )
    
    await message.answer(response, parse_mode="Markdown")
    
    # Notify receiver
    try:
        await bot.send_message(
            receiver.id,
            f"💰 You received ${amount:,} from {sender.first_name}!\n"
            f"💵 New Balance: ${receiver.cash + amount:,}"
        )
    except:
        pass

@dp.message(Command("leaderboard", "mb"))
async def cmd_leaderboard(message: Message):
    """Show money leaderboard"""
    leaderboard = await db.get_leaderboard(message.chat.id)
    
    if not leaderboard:
        await message.answer("No users found!")
        return
    
    lb_text = "💰 **Money Leaderboard**\n\n"
    
    for i, (user_id, name, cash) in enumerate(leaderboard, 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        lb_text += f"{medal} {name}: ${cash:,}\n"
    
    await message.answer(lb_text, parse_mode="Markdown")

@dp.message(Command("reactions", "rxns"))
async def cmd_reactions(message: Message):
    """Show available reactions"""
    reactions_text = (
        "😄 **Available Reactions**\n\n"
        "Use a comma (,) or dot (.) before these words to send GIFs:\n\n"
        
        "• ,hug or .hug - Send a hug GIF\n"
        "• ,pat or .pat - Send a pat GIF\n"
        "• ,kiss or .kiss - Send a kiss GIF\n"
        "• ,cry or .cry - Send a cry GIF\n"
        "• ,smile or .smile - Send a smile GIF\n\n"
        
        "Example: `,hug` or `.pat`\n\n"
        
        "You can also add custom GIFs for rob/kill actions:\n"
        "• /addgif robyes|robno|killyes|killno (reply to GIF)\n"
        "• /showgifs - View custom GIFs\n"
        "• /remgifs - Remove all custom GIFs"
    )
    
    await message.answer(reactions_text, parse_mode="Markdown")

# Reaction GIF handler
@dp.message(F.text.startswith(",") | F.text.startswith("."))
async def handle_reaction(message: Message):
    """Handle reaction commands like ,hug or .pat"""
    text = message.text.lower().strip()
    reaction = text[1:]  # Remove the , or .
    
    if reaction in REACTION_GIFS:
        gif_id = random.choice(REACTION_GIFS[reaction])
        await message.answer_animation(gif_id)
    else:
        # Not a valid reaction, ignore
        return

@dp.message(Command("addgif"))
async def cmd_addgif(message: Message, command: CommandObject):
    """Add custom GIF for rob/kill actions"""
    if not command.args:
        await message.answer(
            "❌ Usage: /addgif robyes|robno|killyes|killno (reply to a GIF)"
        )
        return
    
    gif_type = command.args.lower()
    if gif_type not in ["robyes", "robno", "killyes", "killno"]:
        await message.answer(
            "❌ Invalid type! Use: robyes, robno, killyes, or killno"
        )
        return
    
    if not message.reply_to_message or not message.reply_to_message.animation:
        await message.answer("❌ Please reply to a GIF message!")
        return
    
    gif_file_id = message.reply_to_message.animation.file_id
    
    # Save to database
    async with db.pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO custom_gifs (chat_id, gif_type, file_id, added_by)
            VALUES ($1, $2, $3, $4)
        ''', message.chat.id, gif_type, gif_file_id, message.from_user.id)
    
    await message.answer(f"✅ Custom GIF added for {gif_type} actions!")

@dp.message(Command("showgifs"))
async def cmd_showgifs(message: Message):
    """Show custom GIFs for this chat"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT gif_type, COUNT(*) as count 
            FROM custom_gifs 
            WHERE chat_id = $1 
            GROUP BY gif_type
        ''', message.chat.id)
    
    if not rows:
        await message.answer("No custom GIFs in this chat. Use /addgif to add some!")
        return
    
    gifs_text = "🎞 **Custom GIFs in this chat:**\n\n"
    
    for row in rows:
        gif_type = row['gif_type']
        count = row['count']
        gifs_text += f"• {gif_type}: {count} GIFs\n"
    
    await message.answer(gifs_text, parse_mode="Markdown")

@dp.message(Command("remgifs"))
async def cmd_remgifs(message: Message):
    """Remove all custom GIFs from this chat"""
    async with db.pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM custom_gifs WHERE chat_id = $1', message.chat.id
        )
    
    await message.answer("✅ All custom GIFs removed from this chat!")

@dp.message(Command("setpic"))
async def cmd_setpic(message: Message):
    """Set profile picture"""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.answer("❌ Please reply to a photo message!")
        return
    
    # In a real implementation, you'd save the photo file_id to user's profile
    # For now, we'll just acknowledge it
    await message.answer(
        "✅ Profile picture updated!\n\n"
        "Note: In full implementation, this would save your profile picture "
        "and show it in /tree and /profile commands."
    )

# ============================================================================
# ADMIN COMMAND HANDLERS
# ============================================================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message, command: CommandObject):
    """Admin commands handler"""
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ This command is only for the bot owner!")
        return
    
    if not command.args:
        # Show admin help
        help_text = (
            "👑 **Admin Commands**\n\n"
            
            "👤 **User Management:**\n"
            "• /admin userinfo [ID/reply] - View user details\n"
            "• /admin addmoney [ID] [amount] [currency] - Add currency\n"
            "• /admin reset [ID] - Reset user data\n"
            "• /admin ban [ID] - Ban user from bot\n"
            "• /admin unban [ID] - Unban user\n\n"
            
            "📊 **Bot Management:**\n"
            "• /admin stats - Show bot statistics\n"
            "• /admin broadcast [message] - Broadcast to all users\n"
            "• /admin maintenance [on/off] - Toggle maintenance\n"
            "• /admin grouplist - List all groups\n"
            "• /admin execute [SQL] - Execute SQL (DANGEROUS)\n\n"
            
            "📈 **Economy Control:**\n"
            "• /admin setrate [currency] [rate] - Set exchange rate\n"
            "• /admin giveitem [ID] [item] - Give item to user\n"
            "• /admin reloadshop - Reload shop items\n\n"
            
            "Usage: /admin [command] [arguments]"
        )
        
        await message.answer(help_text, parse_mode="Markdown")
        return
    
    args = command.args.split()
    cmd = args[0].lower()
    
    if cmd == "userinfo":
        await admin_userinfo(message, args[1:])
    elif cmd == "addmoney":
        await admin_addmoney(message, args[1:])
    elif cmd == "broadcast":
        await admin_broadcast(message, args[1:])
    elif cmd == "stats":
        await admin_stats(message)
    elif cmd == "grouplist":
        await admin_grouplist(message)
    else:
        await message.answer(f"❌ Unknown admin command: {cmd}")

async def admin_userinfo(message: Message, args: List[str]):
    """Admin: Get user information"""
    if not args:
        await message.answer("❌ Usage: /admin userinfo [user_id or reply]")
        return
    
    try:
        if args[0].isdigit():
            user_id = int(args[0])
        elif message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            await message.answer("❌ Please provide user ID or reply to user's message")
            return
    except:
        await message.answer("❌ Invalid user ID")
        return
    
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ User not found in database!")
        return
    
    # Get additional info
    family = await db.get_family(user.id)
    friends = await db.get_friends(user.id)
    insurances = await db.get_active_insurances(user.id)
    
    info_text = (
        f"👤 **User Information**\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Name: {user.first_name} {user.last_name or ''}\n"
        f"📛 Username: @{user.username or 'None'}\n"
        f"📅 Created: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"💼 Job: {user.job or 'None'}\n"
        f"❤️ Status: {'Alive ✅' if user.is_alive else 'Dead 💀'}\n\n"
        
        f"💰 **Economy:**\n"
        f"{await format_money(user)}\n\n"
        
        f"📊 **Stats:**\n"
        f"• 👨‍👩‍👧‍👦 Family: {len(family)} members\n"
        f"• 🤝 Friends: {len(friends)} friends\n"
        f"• 🛡️ Insurance: {len(insurances)} policies\n"
        f"• ⭐ Reputation: {user.reputation}/200\n"
        f"• 💎 Gemstone: {user.gemstone or 'None'}\n"
        f"• 🔫 Weapon: {user.weapon}\n\n"
        
        f"📈 **Daily Activity:**\n"
        f"• Robs: {user.rob_count}/{MAX_ROB_DAILY}\n"
        f"• Kills: {user.kill_count}/{MAX_KILL_DAILY}\n"
        f"• Last Daily: {user.last_daily.strftime('%Y-%m-%d %H:%M') if user.last_daily else 'Never'}"
    )
    
    # Create admin action buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Add Money", callback_data=f"admin_addmoney_{user.id}"),
            InlineKeyboardButton(text="🔄 Reset User", callback_data=f"admin_reset_{user.id}")
        ],
        [
            InlineKeyboardButton(text="🚫 Ban User", callback_data=f"admin_ban_{user.id}"),
            InlineKeyboardButton(text="💀 Kill/Revive", callback_data=f"admin_togglelife_{user.id}")
        ]
    ])
    
    await message.answer(info_text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_addmoney(message: Message, args: List[str]):
    """Admin: Add money to user"""
    if len(args) < 3:
        await message.answer(
            "❌ Usage: /admin addmoney [user_id] [amount] [currency]\n"
            "Currencies: cash, gold, bonds, credits, tokens"
        )
        return
    
    try:
        user_id = int(args[0])
        amount = int(args[1])
        currency = args[2].lower()
    except:
        await message.answer("❌ Invalid arguments!")
        return
    
    if currency not in CURRENCIES:
        await message.answer(f"❌ Invalid currency! Available: {', '.join(CURRENCIES.keys())}")
        return
    
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ User not found!")
        return
    
    # Update user's currency
    update_field = currency
    current_value = getattr(user, currency)
    new_value = current_value + amount
    
    await db.update_user(user.id, **{update_field: new_value})
    
    # Log the action
    await send_log(
        f"💰 Admin added {amount} {currency} to user {user_id} ({user.first_name})\n"
        f"New balance: {new_value} {CURRENCIES[currency]}"
    )
    
    await message.answer(
        f"✅ Added {amount} {CURRENCIES[currency]} to {user.first_name}!\n"
        f"New balance: {new_value} {CURRENCIES[currency]}"
    )

async def admin_broadcast(message: Message, args: List[str]):
    """Admin: Broadcast message to all users"""
    if not args:
        await message.answer("❌ Usage: /admin broadcast [message]")
        return
    
    broadcast_msg = " ".join(args)
    confirmation = (
        f"📢 **Broadcast Preview:**\n\n"
        f"{broadcast_msg}\n\n"
        f"Send to all users? This may take a while."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, Send", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel")
        ]
    ])
    
    await message.answer(confirmation, reply_markup=keyboard, parse_mode="Markdown")

async def admin_stats(message: Message):
    """Admin: Show bot statistics"""
    async with db.pool.acquire() as conn:
        # Get total users
        total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
        
        # Get active users (used in last 7 days)
        active_users = await conn.fetchval('''
            SELECT COUNT(DISTINCT user1_id) FROM family_relations 
            WHERE created_at > NOW() - INTERVAL '7 days'
            UNION
            SELECT COUNT(DISTINCT user2_id) FROM family_relations 
            WHERE created_at > NOW() - INTERVAL '7 days'
        ''')
        
        # Get total families
        total_families = await conn.fetchval('''
            SELECT COUNT(DISTINCT LEAST(user1_id, user2_id), GREATEST(user1_id, user2_id))
            FROM family_relations WHERE relation_type = 'spouse'
        ''')
        
        # Get total friendships
        total_friendships = await conn.fetchval('SELECT COUNT(*) FROM friendships') // 2
        
        # Get total cash in economy
        total_cash = await conn.fetchval('SELECT SUM(cash) FROM users')
        
        # Get today's activity
        today_rob = await conn.fetchval('''
            SELECT COUNT(*) FROM users WHERE rob_count > 0 AND rob_reset > NOW() - INTERVAL '1 day'
        ''')
        
        today_kill = await conn.fetchval('''
            SELECT COUNT(*) FROM users WHERE kill_count > 0 AND kill_reset > NOW() - INTERVAL '1 day'
        ''')
    
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        
        f"👥 **Users:**\n"
        f"• Total Users: {total_users:,}\n"
        f"• Active (7 days): {active_users or 0:,}\n\n"
        
        f"🌳 **Family System:**\n"
        f"• Total Families: {total_families or 0:,}\n"
        f"• Total Friendships: {total_friendships or 0:,}\n\n"
        
        f"💰 **Economy:**\n"
        f"• Total Cash: ${total_cash or 0:,}\n\n"
        
        f"📈 **Today's Activity:**\n"
        f"• Robberies: {today_rob or 0:,}\n"
        f"• Kills: {today_kill or 0:,}\n\n"
        
        f"⚙️ **System:**\n"
        f"• Owner: {OWNER_ID}\n"
        f"• Log Channel: {LOG_CHANNEL}"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

async def admin_grouplist(message: Message):
    """Admin: List all groups bot is in"""
    # Note: This requires storing group info in database
    # For now, return a placeholder
    await message.answer(
        "📋 **Group List (Placeholder)**\n\n"
        "In full implementation, this would show all groups where the bot is a member.\n\n"
        "To implement, you need to:\n"
        "1. Store group info when bot is added\n"
        "2. Track group membership\n"
        "3. Display with member counts and activity stats"
    )

# ============================================================================
# CALLBACK QUERY HANDLERS
# ============================================================================

@dp.callback_query(F.data.startswith("proposal_"))
async def handle_proposal_callback(callback: CallbackQuery):
    """Handle proposal accept/decline callbacks"""
    data_parts = callback.data.split("_")
    
    if len(data_parts) < 3:
        await callback.answer("Invalid callback data!")
        return
    
    proposal_id = data_parts[1]
    action = data_parts[2]
    
    proposal = await db.get_proposal(proposal_id)
    if not proposal:
        await callback.answer("Proposal expired or not found!")
        return
    
    from_user = await db.get_user(proposal.from_id)
    to_user = await db.get_user(proposal.to_id)
    
    if not from_user or not to_user:
        await callback.answer("User not found!")
        return
    
    if callback.from_user.id != to_user.id:
        await callback.answer("This proposal is not for you!")
        return
    
    if action == "accept":
        # Process accepted proposal
        if proposal.proposal_type == "friend":
            # Add as friends
            success = await db.add_friend(from_user.id, to_user.id)
            if success:
                # Give friend bonus to both
                await db.update_user(from_user.id, cash=from_user.cash + FRIEND_BONUS)
                await db.update_user(to_user.id, cash=to_user.cash + FRIEND_BONUS)
                
                # Increase reputation for both
                await db.update_user(from_user.id, reputation=min(200, from_user.reputation + 5))
                await db.update_user(to_user.id, reputation=min(200, to_user.reputation + 5))
                
                response = (
                    f"🤝 **Friendship Accepted!**\n\n"
                    f"✨ {from_user.first_name} and {to_user.first_name} are now friends!\n"
                    f"💰 Each received: ${FRIEND_BONUS:,}\n"
                    f"⭐ Reputation: +5 each\n\n"
                    f"Use /circle to see your friend circle!"
                )
                
                # Notify the other user
                try:
                    await bot.send_message(
                        from_user.id,
                        f"✅ {to_user.first_name} accepted your friend request!\n"
                        f"💰 You received: ${FRIEND_BONUS:,}\n"
                        f"⭐ Reputation: +5"
                    )
                except:
                    pass
                
            else:
                response = "❌ Failed to add friend. You might already be friends!"
        
        elif proposal.proposal_type in ["adopt", "marry"]:
            # Add family relation
            rel_type = RelationType.CHILD if proposal.proposal_type == "adopt" else RelationType.SPOUSE
            success = await db.add_family_relation(from_user.id, to_user.id, rel_type)
            
            if success:
                relation_text = "adopted as child" if proposal.proposal_type == "adopt" else "married"
                response = (
                    f"✅ **{proposal.proposal_type.capitalize()} Accepted!**\n\n"
                    f"✨ {to_user.first_name} is now {relation_text} of {from_user.first_name}!\n\n"
                    f"Use /tree to see your updated family tree!"
                )
                
                # Notify the other user
                try:
                    await bot.send_message(
                        from_user.id,
                        f"✅ {to_user.first_name} accepted your {proposal.proposal_type} proposal!\n"
                        f"Check /tree to see your updated family!"
                    )
                except:
                    pass
                
                # Log the new family relation
                await send_log(
                    f"👨‍👩‍👧‍👦 New {proposal.proposal_type}: "
                    f"{from_user.first_name} -> {to_user.first_name}"
                )
            else:
                response = f"❌ Failed to create {proposal.proposal_type} relation!"
        
        await callback.message.edit_text(response, parse_mode="Markdown")
        await callback.answer("Proposal accepted!")
    
    elif action == "decline":
        # Process declined proposal
        response = f"❌ {proposal.proposal_type.capitalize()} proposal declined."
        await callback.message.edit_text(response)
        await callback.answer("Proposal declined!")
    
    # Delete proposal from database
    await db.delete_proposal(proposal_id)

@dp.callback_query(F.data.startswith("unfriend_"))
async def handle_unfriend_callback(callback: CallbackQuery):
    """Handle unfriend callbacks"""
    try:
        friend_id = int(callback.data.split("_")[1])
    except:
        await callback.answer("Invalid callback data!")
        return
    
    user = await db.get_user(callback.from_user.id)
    friend = await db.get_user(friend_id)
    
    if not user or not friend:
        await callback.answer("User not found!")
        return
    
    # Remove friendship
    await db.remove_friend(user.id, friend.id)
    
    # Remove friend bonus from both (if they have enough cash)
    if user.cash >= FRIEND_BONUS:
        await db.update_user(user.id, cash=user.cash - FRIEND_BONUS)
    
    if friend.cash >= FRIEND_BONUS:
        await db.update_user(friend.id, cash=friend.cash - FRIEND_BONUS)
    
    # Decrease reputation
    new_rep = max(0, user.reputation - 10)
    await db.update_user(user.id, reputation=new_rep)
    
    await callback.message.edit_text(
        f"❌ Unfriended {friend.first_name}!\n"
        f"💰 Lost: ${FRIEND_BONUS:,} (if had enough)\n"
        f"📉 Reputation: -10 (Now: {new_rep})"
    )
    await callback.answer("Unfriended!")

@dp.callback_query(F.data == "daily_bonus")
async def handle_daily_bonus_callback(callback: CallbackQuery):
    """Handle daily bonus button"""
    user = await get_or_create_user(callback.from_user)
    bonus, gemstone, error = await process_daily_bonus(user)
    
    if error:
        await callback.answer(error)
        return
    
    response = (
        f"🎉 **Daily Bonus Claimed!**\n\n"
        f"💰 Received: ${bonus:,}\n"
        f"💎 Today's Gemstone: **{gemstone}**\n\n"
        f"💵 New Balance: ${user.cash + bonus:,}"
    )
    
    await callback.message.edit_text(response, parse_mode="Markdown")
    await callback.answer("Bonus claimed!")

@dp.callback_query(F.data == "find_gem_match")
async def handle_find_gem_match(callback: CallbackQuery):
    """Handle find gemstone match button"""
    user = await get_or_create_user(callback.from_user)
    
    if not user.gemstone:
        await callback.answer("You don't have a gemstone! Use /daily first.")
        return
    
    # In a full implementation, this would search for users with same gemstone
    # For now, show instructions
    response = (
        f"💎 **Find {user.gemstone} Match**\n\n"
        f"To fuse gemstones and get ${GEMSTONE_BONUS:,}:\n\n"
        f"1. Find someone with {user.gemstone} gemstone\n"
        f"2. Reply to their message with /fuse\n"
        f"3. Both of you get ${GEMSTONE_BONUS:,} each!\n\n"
        f"Ask in chat: 'Anyone has {user.gemstone} gemstone?'"
    )
    
    await callback.message.answer(response, parse_mode="Markdown")
    await callback.answer()

# ============================================================================
# MAIN BOT SETUP & ENTRY POINT
# ============================================================================

async def setup_bot():
    """Initialize and configure the bot"""
    global bot, dp
    
    # Create bot instance
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Connect to database
    await db.connect()
    
    # Reset daily counts on startup
    await db.reset_daily_counts()
    
    # Register all handlers
    # (Already decorated above, they auto-register)
    
    # Log startup
    await send_log("🤖 Family Tree Bot started successfully!")
    
    # Set bot commands menu in Telegram
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Show help"),
        types.BotCommand(command="me", description="Your profile"),
        types.BotCommand(command="daily", description="Daily bonus"),
        types.BotCommand(command="tree", description="Family tree"),
        types.BotCommand(command="family", description="List family"),
        types.BotCommand(command="adopt", description="Adopt someone"),
        types.BotCommand(command="marry", description="Marry someone"),
        types.BotCommand(command="friend", description="Add friend"),
        types.BotCommand(command="circle", description="Friend circle"),
        types.BotCommand(command="rob", description="Rob someone"),
        types.BotCommand(command="kill", description="Kill someone"),
        types.BotCommand(command="pay", description="Send money"),
        types.BotCommand(command="leaderboard", description="Money rankings"),
        types.BotCommand(command="reactions", description="Reaction GIFs"),
        types.BotCommand(command="admin", description="Admin commands"),
    ]
    
    await bot.set_my_commands(commands)

async def main():
    """Main entry point"""
    try:
        await setup_bot()
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        await send_log(f"❌ Bot crashed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
