"""
DATABASE MANAGER
SQLite database operations
"""

import aiosqlite
import logging
import json
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.conn = None
        
    async def connect(self):
        """Connect to database"""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            await self.conn.execute("PRAGMA journal_mode=WAL")
            await self.init_tables()
            logger.info(f"✅ Database connected: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            return False
    
    async def init_tables(self):
        """Initialize all tables"""
        tables = [
            # Users table
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                cash INTEGER DEFAULT 1000,
                bank_balance INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 100,
                daily_streak INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                bio_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Family relations
            """CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                relation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id),
                FOREIGN KEY (user2_id) REFERENCES users(user_id)
            )""",
            
            # Garden
            """CREATE TABLE IF NOT EXISTS gardens (
                user_id INTEGER PRIMARY KEY,
                slots INTEGER DEFAULT 9,
                greenhouse_level INTEGER DEFAULT 0,
                last_collection TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )""",
            
            # Plants
            """CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_progress REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )""",
            
            # Barn storage
            """CREATE TABLE IF NOT EXISTS barn (
                user_id INTEGER NOT NULL,
                crop_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, crop_type),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )""",
            
            # Stocks
            """CREATE TABLE IF NOT EXISTS stocks (
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                shares INTEGER DEFAULT 0,
                avg_price REAL DEFAULT 0,
                total_invested REAL DEFAULT 0,
                PRIMARY KEY (user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )""",
            
            # GIFs
            """CREATE TABLE IF NOT EXISTS gifs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                url TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Cooldowns
            """CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, command)
            )"""
        ]
        
        try:
            for table_sql in tables:
                await self.conn.execute(table_sql)
            await self.conn.commit()
            logger.info("✅ All tables initialized")
        except Exception as e:
            logger.error(f"❌ Table initialization error: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("✅ Database connection closed")
    
    async def execute(self, query, params=()):
        """Execute a query"""
        try:
            await self.conn.execute(query, params)
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Execute error: {e}")
            return False
    
    async def fetch_one(self, query, params=()):
        """Fetch one row"""
        try:
            cursor = await self.conn.execute(query, params)
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Fetch one error: {e}")
            return None
    
    async def fetch_all(self, query, params=()):
        """Fetch all rows"""
        try:
            cursor = await self.conn.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Fetch all error: {e}")
            return []
    
    async def get_user(self, user_id):
        """Get user by ID"""
        return await self.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
    
    async def create_user(self, user_id, username, first_name, last_name=""):
        """Create new user"""
        try:
            await self.execute(
                """INSERT OR IGNORE INTO users 
                   (user_id, username, first_name, last_name, cash)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, first_name, last_name, Config.STARTING_BALANCE)
            )
            
            # Create garden for user
            await self.execute(
                "INSERT OR IGNORE INTO gardens (user_id) VALUES (?)",
                (user_id,)
            )
            
            return await self.get_user(user_id)
        except Exception as e:
            logger.error(f"Create user error: {e}")
            return None
    
    async def update_currency(self, user_id, currency_type, amount):
        """Update user's cash or bank balance"""
        try:
            if currency_type == "cash":
                await self.execute(
                    "UPDATE users SET cash = cash + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            elif currency_type == "bank":
                await self.execute(
                    "UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            return True
        except Exception as e:
            logger.error(f"Update currency error: {e}")
            return False
    
    async def get_family(self, user_id):
        """Get all family members for a user"""
        query = """
        SELECT u.user_id, u.username, u.first_name, u.last_name, f.relation
        FROM family f
        JOIN users u ON (u.user_id = f.user2_id OR u.user_id = f.user1_id)
        WHERE (f.user1_id = ? OR f.user2_id = ?) AND u.user_id != ?
        """
        return await self.fetch_all(query, (user_id, user_id, user_id))
    
    async def add_family_member(self, user1_id, user2_id, relation):
        """Add family relationship"""
        try:
            await self.execute(
                "INSERT INTO family (user1_id, user2_id, relation) VALUES (?, ?, ?)",
                (user1_id, user2_id, relation)
            )
            return True
        except Exception as e:
            logger.error(f"Add family member error: {e}")
            return False
    
    async def get_garden(self, user_id):
        """Get user's garden info"""
        garden = await self.fetch_one(
            "SELECT * FROM gardens WHERE user_id = ?",
            (user_id,)
        )
        if not garden:
            # Create garden if not exists
            await self.execute(
                "INSERT INTO gardens (user_id) VALUES (?)",
                (user_id,)
            )
            garden = {"user_id": user_id, "slots": 9, "greenhouse_level": 0}
        return garden
    
    async def get_plants(self, user_id):
        """Get user's plants"""
        return await self.fetch_all(
            "SELECT * FROM plants WHERE user_id = ?",
            (user_id,)
        )
    
    async def get_random_gif(self, category):
        """Get random GIF for category"""
        gif = await self.fetch_one(
            "SELECT url FROM gifs WHERE category = ? ORDER BY RANDOM() LIMIT 1",
            (category,)
        )
        return gif['url'] if gif else None
    
    async def get_user_count(self):
        """Get total user count"""
        result = await self.fetch_one("SELECT COUNT(*) as count FROM users")
        return result['count'] if result else 0
    
    async def get_achievements(self, user_id):
        """Get user achievements (simplified)"""
        # Return empty list for now
        return []
