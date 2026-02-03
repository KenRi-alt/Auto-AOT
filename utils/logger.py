"""
📊 LOGGING SYSTEM
Enhanced logging with Telegram channel integration
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
from typing import Optional

from aiogram import Bot

from config import Config

# Global logger instance
_logger = None

class TelegramLogHandler(logging.Handler):
    """Custom handler to send logs to Telegram channel"""
    
    def __init__(self, bot: Optional[Bot] = None):
        super().__init__()
        self.bot = bot
        self.setLevel(logging.ERROR)  # Only send errors by default
    
    def set_bot(self, bot: Bot):
        """Set bot instance for sending messages"""
        self.bot = bot
    
    def emit(self, record):
        """Send log record to Telegram"""
        try:
            if self.bot and hasattr(record, 'message'):
                # Format message for Telegram
                level = record.levelname
                message = record.getMessage()
                
                # Truncate long messages
                if len(message) > 1000:
                    message = message[:1000] + "..."
                
                log_msg = f"""
⚠️ <b>BOT ERROR</b>

📝 <b>Level:</b> {level}
💬 <b>Message:</b> {message}
🕒 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

📍 <b>Location:</b> {record.filename}:{record.lineno}
"""
                
                # Try to send to log channel
                import asyncio
                try:
                    asyncio.create_task(
                        self.bot.send_message(
                            chat_id=Config.LOG_CHANNEL,
                            text=log_msg,
                            parse_mode="HTML"
                        )
                    )
                except:
                    pass
                    
        except Exception as e:
            # Avoid recursion if logging fails
            print(f"Telegram log handler error: {e}")

def setup_logger() -> logging.Logger:
    """Setup comprehensive logging system"""
    global _logger
    
    if _logger:
        return _logger
    
    # Create logger
    logger = logging.getLogger("FamilyTreeBot")
    logger.setLevel(logging.INFO)
    
    # Create logs directory
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    
    # File handler (rotating, max 5MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(Config.LOGS_DIR, "bot.log"),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Telegram handler (will be configured later with bot)
    telegram_handler = TelegramLogHandler()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(telegram_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    _logger = logger
    return logger

async def log_to_channel(bot: Bot, message: str, level: str = "INFO"):
    """
    Send message to log channel
    
    Args:
        bot: Bot instance
        message: Message to send
        level: Log level (INFO, WARNING, ERROR, etc.)
    """
    try:
        # Format message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if level == "INFO":
            prefix = "📝"
        elif level == "WARNING":
            prefix = "⚠️"
        elif level == "ERROR":
            prefix = "❌"
        elif level == "CRITICAL":
            prefix = "💥"
        else:
            prefix = "📊"
        
        formatted_msg = f"""
{prefix} <b>{level}</b>

{message}

🕒 {timestamp}
"""
        
        # Send to log channel
        await bot.send_message(
            chat_id=Config.LOG_CHANNEL,
            text=formatted_msg,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        # Also log locally
        logger = logging.getLogger("FamilyTreeBot")
        if level == "INFO":
            logger.info(f"Log channel: {message[:100]}...")
        elif level == "WARNING":
            logger.warning(f"Log channel: {message[:100]}...")
        elif level == "ERROR":
            logger.error(f"Log channel: {message[:100]}...")
        
    except Exception as e:
        # Fallback to console if Telegram fails
        print(f"Failed to send to log channel: {e}")
        print(f"Original message: {message}")

def log_command_usage(user_id: int, username: str, command: str):
    """Log command usage for analytics"""
    logger = logging.getLogger("FamilyTreeBot")
    logger.info(f"Command used - User: {user_id} (@{username}), Command: {command}")

def log_economy_transaction(user_id: int, transaction_type: str, amount: int, details: str = ""):
    """Log economy transactions"""
    logger = logging.getLogger("FamilyTreeBot")
    logger.info(f"Economy - User: {user_id}, Type: {transaction_type}, Amount: {amount}, Details: {details}")

def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    logger = logging.getLogger("FamilyTreeBot")
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)

def get_logger() -> logging.Logger:
    """Get logger instance"""
    if _logger is None:
        return setup_logger()
    return _logger

# Initialize logger on import
setup_logger()
