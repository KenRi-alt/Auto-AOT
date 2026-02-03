"""
⚙️ CONFIGURATION SETTINGS
All bot configuration in one place
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration"""
    
    # Bot credentials
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
    OWNER_ID = int(os.getenv("OWNER_ID", "6108185460"))
    
    # Log channel (your channel)
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1003662720845"))
    
    # Additional admin IDs (comma separated)
    ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "6108185460").split(",") if id.strip()]
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "family_bot.db")
    DB_BACKUP_DIR = os.getenv("DB_BACKUP_DIR", "backups")
    
    # Redis for caching (optional)
    REDIS_URL = os.getenv("REDIS_URL", "")
    
    # Bot settings
    BOT_USERNAME = "FamilyTreeBot"
    VERSION = "2.0.0"
    SUPPORT_CHAT = "@FamilyTreeSupport"
    
    # Security
    MAX_WARNINGS = 3
    RATE_LIMIT_PER_USER = 30  # Commands per minute
    BAN_DURATION = 24  # Hours
    
    # Economy settings
    START_CASH = 1000
    START_BANK = 0
    DAILY_MIN = 500
    DAILY_MAX = 1500
    BANK_INTEREST_RATE = 0.5  # 0.5% daily
    
    # Garden settings
    GARDEN_SLOTS = 9
    GREENHOUSE_SLOT_BONUS = 3
    GROW_TIME_REDUCTION = 0.1  # 10% per greenhouse level
    
    # Lottery settings
    LOTTERY_TICKET_PRICE = 50
    LOTTERY_PRIZE_POOL = 70   # 70% of sales
    LOTTERY_DRAW_DAY = 6      # Sunday
    
    # Game settings
    MIN_BET = 10
    MAX_BET = 10000
    
    # Family settings
    ADOPT_BONUS = 500
    MARRY_BONUS = 1000
    FAMILY_DAILY_BONUS = 100
    
    # Business settings
    BUSINESS_INCOME_INTERVAL = 24  # Hours
    MIN_BUSINESS_PRICE = 5000
    
    # New Crypto System
    CRYPTO_UPDATE_INTERVAL = 3600  # 1 hour
    CRYPTO_VOLATILITY = 0.15  # 15% max change
    
    # Real Estate System
    PROPERTY_INCOME_INTERVAL = 24  # Hours
    PROPERTY_UPGRADE_COST_MULTIPLIER = 1.5
    
    # Job System
    WORK_HOURS_PER_DAY = 8
    JOB_SALARY_INTERVAL = 24  # Hours
    
    # Battle System
    BATTLE_COOLDOWN = 300  # 5 minutes
    MIN_BATTLE_BET = 50
    
    # Performance
    CACHE_DURATION = 300  # 5 minutes
    HEALTH_CHECK_INTERVAL = 3600  # 1 hour
    HEALTH_CHECK_ENABLED = True
    
    # Paths
    LOGS_DIR = "logs"
    IMAGES_DIR = "images"
    DATA_DIR = "data"
    
    @classmethod
    def get_admins(cls):
        """Get all admin IDs including owner"""
        return [cls.OWNER_ID] + cls.ADMIN_IDS
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.get_admins()

# Create required directories
for directory in [Config.LOGS_DIR, Config.IMAGES_DIR, Config.DATA_DIR, Config.DB_BACKUP_DIR]:
    os.makedirs(directory, exist_ok=True)
