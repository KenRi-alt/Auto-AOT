"""
🛠️ HELPER FUNCTIONS
Utility functions used across the bot
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple
import random

from aiogram.types import Message, User

from config import Config

def get_target_user(message: Message) -> Optional[User]:
    """Get target user from reply"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None

def format_time(seconds: int) -> str:
    """Format seconds to human readable time"""
    if seconds >= 86400:
        days = seconds // 86400
        return f"{days}d"
    elif seconds >= 3600:
        hours = seconds // 3600
        return f"{hours}h"
    elif seconds >= 60:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        return f"{seconds}s"

def format_money(amount: int) -> str:
    """Format money with commas"""
    return f"${amount:,}"

def create_progress_bar(progress: float, width: int = 20) -> str:
    """Create text progress bar"""
    filled = int(width * progress / 100)
    empty = width - filled
    return "█" * filled + "░" * empty

def generate_random_name() -> str:
    """Generate random name for NPCs"""
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def calculate_level_xp(level: int) -> int:
    """Calculate XP needed for level"""
    return level * 1000

def calculate_interest(principal: int, rate: float, days: int = 1) -> int:
    """Calculate interest"""
    return int(principal * (rate / 100) * days)

def validate_url(url: str) -> bool:
    """Validate URL"""
    return url.startswith(('http://', 'https://'))

async def check_cooldown(user_id: int, command: str, cooldown_seconds: int, db) -> Tuple[bool, int]:
    """Check if command is on cooldown"""
    try:
        result = await db.fetch_one(
            "SELECT last_used FROM cooldowns WHERE user_id = ? AND command = ?",
            (user_id, command)
        )
        
        if not result:
            return True, 0
        
        last_used = datetime.fromisoformat(result['last_used'].replace('Z', '+00:00'))
        elapsed = (datetime.now() - last_used).total_seconds()
        
        if elapsed >= cooldown_seconds:
            return True, 0
        
        remaining = int(cooldown_seconds - elapsed)
        return False, remaining
        
    except Exception as e:
        return True, 0

async def set_cooldown(user_id: int, command: str, db):
    """Set command cooldown"""
    try:
        await db.execute(
            """INSERT OR REPLACE INTO cooldowns (user_id, command, last_used)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (user_id, command)
        )
    except Exception as e:
        pass

def get_emoji_for_level(level: int) -> str:
    """Get emoji for user level"""
    if level >= 100:
        return "👑"
    elif level >= 50:
        return "⭐"
    elif level >= 20:
        return "🔥"
    elif level >= 10:
        return "💎"
    elif level >= 5:
        return "✨"
    else:
        return "🌱"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date"""
    today = datetime.now()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age
