"""
CONFIGURATION SETTINGS
Environment variables and constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8296250010:AAFSZ9psxmooDvODWCTvnvn4y7K3SsZN_Rc")
    
    # Your Telegram User ID
    OWNER_ID = int(os.getenv("OWNER_ID", "6108185460"))
    
    # Log Channel ID
    LOG_CHANNEL = os.getenv("LOG_CHANNEL", "-1003662720845")
    
    # Admin IDs (comma separated)
    admin_ids_str = os.getenv("ADMIN_IDS", "6108185460")
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")] if admin_ids_str else []
    
    # Database Path
    DB_PATH = os.getenv("DB_PATH", "/data/family_bot.db")
    
    # Bot Settings
    BOT_USERNAME = os.getenv("BOT_USERNAME", "FamilyTreeBot")
    VERSION = os.getenv("VERSION", "2.0.0")
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "@FamilyTreeSupport")
    
    # Economy Settings
    STARTING_BALANCE = 1000
    DAILY_MIN = 500
    DAILY_MAX = 1500
    INTEREST_RATE = 0.05  # 5% daily interest
    
    # Family Settings
    ADOPT_BONUS = 1000
    MARRY_BONUS = 5000
    FAMILY_DAILY_BONUS = 50
    
    # Garden Settings
    STARTING_GARDEN_SLOTS = 9
    MAX_GARDEN_SLOTS = 25
    
    # Game Settings
    LOTTERY_TICKET_PRICE = 100
    SLOT_MIN_BET = 10
    SLOT_MAX_BET = 10000
    
    # Business Settings
    BUSINESS_INTERVAL = 3600  # 1 hour
