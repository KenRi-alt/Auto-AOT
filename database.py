"""
🗄️ DATABASE MANAGEMENT
Fixed connection handling with crash prevention
"""

import aiosqlite
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import traceback

from config import Config

logger = logging.getLogger(__name__)

class CropType(Enum):
    """Crop types enumeration"""
    CARROT = "carrot"
    TOMATO = "tomato" 
    POTATO = "potato"
    EGGPLANT = "eggplant"
    CORN = "corn"
    PEPPER = "pepper"
    WATERMELON = "watermelon"
    PUMPKIN = "pumpkin"

class CryptoType(Enum):
    """Cryptocurrency types"""
    BTC = "bitcoin"
    ETH = "ethereum"
    DOGE = "dogecoin"
    LTC = "litecoin"
    ADA = "cardano"

class PropertyType(Enum):
    """Real estate property types"""
    HOUSE = "house"
    APARTMENT = "apartment"
    VILLA = "villa"
    COMMERCIAL = "commercial"
    LAND = "land"

class JobType(Enum):
    """Job types"""
    FARMER = "farmer"
    TRADER = "trader"
    DEVELOPER = "developer"
    DOCTOR = "doctor"
    TEACHER = "teacher"
    ENGINEER = "engineer"
    CHEF = "chef"
    DRIVER = "driver"

class Database:
    """Professional database manager with connection pooling"""
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.conn = None
        self.is_connected = False
        self.lock = asyncio.Lock()
        
    async def connect(self):
        """Connect to database with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.lock:
                    self.conn = await aiosqlite.connect(self.db_path)
                    self.conn.row_factory = aiosqlite.Row
                    self.is_connected = True
                    
                    # Enable WAL mode for better concurrency
                    await self.conn.execute("PRAGMA journal_mode=WAL")
                    await self.conn.execute("PRAGMA synchronous=NORMAL")
                    await self.conn.execute("PRAGMA foreign_keys=ON")
                    
                    await self.init_tables()
                    await self.init_data()
                    
                    logger.info(f"✅ Database connected (attempt {attempt + 1})")
                    return True
                    
            except Exception as e:
                logger.error(f"❌ Database connection failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
    
    async def close(self):
        """Close database connection"""
        try:
            if self.conn:
                await self.conn.close()
                self.is_connected = False
                logger.info("✅ Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
    
    async def health_check(self) -> bool:
        """Check if database is healthy"""
        try:
            if not self.conn or not self.is_connected:
                await self.connect()
            
            # Simple query to test connection
            await self.conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            await self.connect()  # Try to reconnect
            return False
    
    async def execute(self, query: str, params: tuple = ()):
        """Execute query with error handling"""
        try:
            async with self.lock:
                cursor = await self.conn.execute(query, params)
                await self.conn.commit()
                return cursor
        except Exception as e:
            logger.error(f"Query failed: {query[:100]}... | Error: {e}")
            await self.conn.rollback()
            raise
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch single row"""
        try:
            async with self.lock:
                cursor = await self.conn.execute(query, params)
                row = await cursor.fetchone()
                await cursor.close()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Fetch one failed: {query[:100]}... | Error: {e}")
            return None
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows"""
        try:
            async with self.lock:
                cursor = await self.conn.execute(query, params)
                rows = await cursor.fetchall()
                await cursor.close()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Fetch all failed: {query[:100]}... | Error: {e}")
            return []
    
    async def init_tables(self):
        """Initialize all database tables"""
        tables = [
            # Users table
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
            
            # Family relationships
            """CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user1_id, user2_id, relation)
            )""",
            
            # Garden system
            """CREATE TABLE IF NOT EXISTS garden (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT ?,
                greenhouse_level INTEGER DEFAULT 0,
                last_watered TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Plants growing
            """CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grow_time REAL NOT NULL,
                progress REAL DEFAULT 0,
                is_ready BOOLEAN DEFAULT 0,
                watered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Barn storage
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, crop_type)
            )""",
            
            # Bank accounts
            """CREATE TABLE IF NOT EXISTS bank_accounts (
                user_id INTEGER PRIMARY KEY,
                last_interest TIMESTAMP,
                total_interest INTEGER DEFAULT 0,
                fixed_deposit INTEGER DEFAULT 0,
                fixed_deposit_end TIMESTAMP,
                loan_amount INTEGER DEFAULT 0,
                loan_due TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Transactions
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT,
                balance_after INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # Stocks
            """CREATE TABLE IF NOT EXISTS stocks (
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                shares INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, symbol)
            )""",
            
            # Businesses
            """CREATE TABLE IF NOT EXISTS businesses (
                user_id INTEGER NOT NULL,
                business_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                last_collected TIMESTAMP,
                total_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, business_type)
            )""",
            
            # NEW: Crypto wallets
            """CREATE TABLE IF NOT EXISTS crypto_wallets (
                user_id INTEGER NOT NULL,
                crypto_type TEXT NOT NULL,
                amount REAL DEFAULT 0,
                avg_buy_price REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, crypto_type)
            )""",
            
            # NEW: Real estate
            """CREATE TABLE IF NOT EXISTS real_estate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                property_type TEXT NOT NULL,
                location TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                value INTEGER NOT NULL,
                income INTEGER DEFAULT 0,
                last_collected TIMESTAMP,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # NEW: Jobs
            """CREATE TABLE IF NOT EXISTS jobs (
                user_id INTEGER PRIMARY KEY,
                job_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                salary INTEGER NOT NULL,
                last_worked TIMESTAMP,
                total_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # NEW: Battle stats
            """CREATE TABLE IF NOT EXISTS battle_stats (
                user_id INTEGER PRIMARY KEY,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                rating INTEGER DEFAULT 1000,
                last_battle TIMESTAMP,
                total_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )""",
            
            # GIF management
            """CREATE TABLE IF NOT EXISTS reaction_gifs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                gif_url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(command, gif_url)
            )""",
            
            # Achievements
            """CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, achievement_id)
            )""",
            
            # Cooldowns
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, command)
            )"""
        ]
        
        for table_sql in tables:
            try:
                if "users" in table_sql:
                    await self.execute(table_sql, (Config.START_CASH, Config.START_BANK))
                elif "garden" in table_sql:
                    await self.execute(table_sql, (Config.GARDEN_SLOTS,))
                else:
                    await self.execute(table_sql)
            except Exception as e:
                logger.error(f"Table creation error: {e}")
    
    async def init_data(self):
        """Initialize default data"""
        try:
            # Initialize default GIFs
            default_gifs = {
                "hug": "https://files.catbox.moe/34u6a1.gif",
                "kiss": "https://files.catbox.moe/zu3p40.gif",
                "slap": "https://files.catbox.moe/8x5f6d.gif",
                "pat": "https://files.catbox.moe/9k7j2v.gif",
                "punch": "https://files.catbox.moe/l2m5n8.gif",
                "cuddle": "https://files.catbox.moe/r4t9y1.gif",
                "kill": "https://files.catbox.moe/p6og82.gif",
                "rob": "https://files.catbox.moe/1x4z9u.gif"
            }
            
            for command, url in default_gifs.items():
                await self.execute(
                    """INSERT OR IGNORE INTO reaction_gifs (command, gif_url, added_by)
                       VALUES (?, ?, ?)""",
                    (command, url, Config.OWNER_ID)
                )
            
            logger.info("✅ Default data initialized")
            
        except Exception as e:
            logger.error(f"Init data error: {e}")
    
    # ========== USER METHODS ==========
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return await self.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
    
    async def create_user(self, user_id: int, username: str, first_name: str, last_name: str = "") -> Dict:
        """Create new user"""
        try:
            # Create user
            await self.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name, cash, bank_balance)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, username, first_name, last_name, 
                 Config.START_CASH, Config.START_BANK)
            )
            
            # Initialize garden
            await self.execute(
                "INSERT OR IGNORE INTO garden (user_id) VALUES (?)",
                (user_id,)
            )
            
            # Initialize bank account
            await self.execute(
                "INSERT OR IGNORE INTO bank_accounts (user_id) VALUES (?)",
                (user_id,)
            )
            
            # Initialize battle stats
            await self.execute(
                "INSERT OR IGNORE INTO battle_stats (user_id) VALUES (?)",
                (user_id,)
            )
            
            return await self.get_user(user_id)
            
        except Exception as e:
            logger.error(f"Create user error: {e}")
            return None
    
    async def update_currency(self, user_id: int, currency: str, amount: int) -> bool:
        """Update user currency"""
        try:
            if currency == "cash":
                await self.execute(
                    "UPDATE users SET cash = cash + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            elif currency == "bank_balance":
                await self.execute(
                    "UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            elif currency == "gold":
                await self.execute(
                    "UPDATE users SET gold = gold + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            return True
        except Exception as e:
            logger.error(f"Update currency error: {e}")
            return False
    
    async def get_user_count(self) -> int:
        """Get total user count"""
        result = await self.fetch_one("SELECT COUNT(*) as count FROM users")
        return result['count'] if result else 0
    
    # ========== FAMILY METHODS ==========
    
    async def get_family(self, user_id: int) -> List[Dict]:
        """Get user's family members"""
        return await self.fetch_all(
            """SELECT 
               CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END as member_id,
               u.first_name, u.username, f.relation, f.created_at
               FROM family f
               JOIN users u ON u.user_id = CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
               WHERE ? IN (f.user1_id, f.user2_id)
               ORDER BY f.created_at""",
            (user_id, user_id, user_id)
        )
    
    async def add_family_member(self, user1_id: int, user2_id: int, relation: str) -> bool:
        """Add family relation"""
        try:
            await self.execute(
                """INSERT OR IGNORE INTO family (user1_id, user2_id, relation)
                   VALUES (?, ?, ?)""",
                (min(user1_id, user2_id), max(user1_id, user2_id), relation)
            )
            return True
        except Exception as e:
            logger.error(f"Add family member error: {e}")
            return False
    
    # ========== GARDEN METHODS ==========
    
    async def get_garden(self, user_id: int) -> Dict:
        """Get garden info"""
        result = await self.fetch_one(
            "SELECT slots, greenhouse_level FROM garden WHERE user_id = ?",
            (user_id,)
        )
        return result or {"slots": Config.GARDEN_SLOTS, "greenhouse_level": 0}
    
    async def get_plants(self, user_id: int) -> List[Dict]:
        """Get user's plants"""
        plants = await self.fetch_all(
            """SELECT id, crop_type, planted_at, grow_time, progress, is_ready
               FROM plants WHERE user_id = ? AND is_ready = 0
               ORDER BY planted_at""",
            (user_id,)
        )
        
        # Calculate progress
        for plant in plants:
            if plant['planted_at']:
                try:
                    planted_at = datetime.fromisoformat(plant['planted_at'].replace('Z', '+00:00'))
                    elapsed = (datetime.now() - planted_at).total_seconds() / 3600
                    progress = min(100, (elapsed / plant['grow_time']) * 100)
                    plant['current_progress'] = progress
                except:
                    plant['current_progress'] = 0
        
        return plants
    
    # ========== GIF MANAGEMENT ==========
    
    async def add_gif(self, command: str, gif_url: str, added_by: int) -> Tuple[bool, str]:
        """Add GIF for command"""
        try:
            # Validate URL
            if not gif_url.startswith(('http://', 'https://')):
                return False, "Invalid URL"
            
            if 'catbox.moe' not in gif_url and 'files.catbox.moe' not in gif_url:
                return False, "Only catbox.moe GIFs allowed"
            
            # Check if exists
            existing = await self.fetch_one(
                "SELECT 1 FROM reaction_gifs WHERE command = ? AND gif_url = ?",
                (command, gif_url)
            )
            if existing:
                return False, "GIF already exists"
            
            # Add GIF
            await self.execute(
                """INSERT INTO reaction_gifs (command, gif_url, added_by)
                   VALUES (?, ?, ?)""",
                (command, gif_url, added_by)
            )
            
            return True, "GIF added successfully"
            
        except Exception as e:
            logger.error(f"Add GIF error: {e}")
            return False, f"Error: {str(e)}"
    
    async def get_gifs(self, command: str = None) -> List[Dict]:
        """Get GIFs"""
        if command:
            return await self.fetch_all(
                """SELECT id, command, gif_url, added_by, added_at 
                   FROM reaction_gifs WHERE command = ? 
                   ORDER BY added_at DESC""",
                (command,)
            )
        else:
            return await self.fetch_all(
                """SELECT id, command, gif_url, added_by, added_at 
                   FROM reaction_gifs 
                   ORDER BY command, added_at DESC"""
            )
    
    async def remove_gif(self, command: str, gif_url: str = None) -> Tuple[bool, str]:
        """Remove GIF"""
        try:
            if gif_url:
                await self.execute(
                    "DELETE FROM reaction_gifs WHERE command = ? AND gif_url = ?",
                    (command, gif_url)
                )
                return True, "GIF removed"
            else:
                await self.execute(
                    "DELETE FROM reaction_gifs WHERE command = ?",
                    (command,)
                )
                return True, "All GIFs removed for command"
        except Exception as e:
            logger.error(f"Remove GIF error: {e}")
            return False, f"Error: {str(e)}"
    
    async def get_random_gif(self, command: str) -> Optional[str]:
        """Get random GIF for command"""
        result = await self.fetch_one(
            "SELECT gif_url FROM reaction_gifs WHERE command = ? ORDER BY RANDOM() LIMIT 1",
            (command,)
        )
        return result['gif_url'] if result else None
    
    # ========== STATISTICS ==========
    
    async def get_stats(self) -> Dict:
        """Get bot statistics"""
        stats = {}
        
        queries = [
            ("total_users", "SELECT COUNT(*) FROM users"),
            ("active_today", "SELECT COUNT(*) FROM users WHERE last_daily >= datetime('now', '-1 day')"),
            ("total_cash", "SELECT SUM(cash) FROM users"),
            ("total_bank", "SELECT SUM(bank_balance) FROM users"),
            ("family_relations", "SELECT COUNT(*) FROM family"),
            ("gifs_count", "SELECT COUNT(*) FROM reaction_gifs"),
            ("businesses_count", "SELECT COUNT(*) FROM businesses"),
            ("crypto_wallets", "SELECT COUNT(*) FROM crypto_wallets"),
            ("real_estate", "SELECT COUNT(*) FROM real_estate"),
            ("jobs_count", "SELECT COUNT(*) FROM jobs")
        ]
        
        for key, query in queries:
            try:
                result = await self.fetch_one(query)
                stats[key] = result[0] if result else 0
            except:
                stats[key] = 0
        
        return stats
    
    async def backup_database(self) -> bytes:
        """Create database backup"""
        import shutil
        try:
            backup_file = f"{Config.DB_BACKUP_DIR}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(self.db_path, backup_file)
            
            # Keep only last 7 backups
            import glob
            backups = sorted(glob.glob(f"{Config.DB_BACKUP_DIR}/backup_*.db"))
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    os.remove(old_backup)
            
            with open(backup_file, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return None
