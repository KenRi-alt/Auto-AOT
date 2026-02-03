#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - MAIN FILE
Professional modular bot with crash prevention
"""

import os
import sys
import asyncio
import logging
import traceback
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from utils.logger import setup_logger, log_to_channel

# Import routers
from handlers.family import family_router
from handlers.economy import economy_router
from handlers.games import games_router
from handlers.admin import admin_router
from handlers.utils import utils_router

# Global instances
bot_instance = None
dp_instance = None
db_instance = None
logger = None

async def startup():
    """Initialize bot on startup"""
    global bot_instance, dp_instance, db_instance, logger
    
    try:
        # Setup logging
        logger = setup_logger()
        logger.info("🚀 Starting Family Tree Bot v2.0...")
        
        # Initialize database
        db_instance = Database()
        await db_instance.connect()
        logger.info("✅ Database connected")
        
        # Initialize bot
        bot_instance = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Initialize dispatcher
        storage = MemoryStorage()
        dp_instance = Dispatcher()
        
        # Include routers with dependency injection
        dp_instance.include_router(family_router)
        dp_instance.include_router(economy_router)
        dp_instance.include_router(games_router)
        dp_instance.include_router(admin_router)
        dp_instance.include_router(utils_router)
        
        # Set dependencies
        dp_instance["db"] = db_instance
        dp_instance["bot"] = bot_instance
        
        # Send startup notification to log channel
        try:
            await log_to_channel(
                bot_instance, 
                f"🚀 **BOT STARTED SUCCESSFULLY**\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⚙️ Version: {Config.VERSION}\n"
                f"✅ All systems operational"
            )
        except Exception as e:
            logger.warning(f"Could not send startup log: {e}")
        
        logger.info("✅ Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        logger.error(traceback.format_exc())
        raise

async def shutdown():
    """Graceful shutdown"""
    global bot_instance, dp_instance, db_instance
    
    try:
        logger.info("🛑 Shutting down bot...")
        
        # Send shutdown notification
        if bot_instance:
            try:
                await log_to_channel(
                    bot_instance,
                    f"🛑 **BOT SHUTTING DOWN**\n"
                    f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🔌 Graceful shutdown initiated"
                )
            except:
                pass
        
        # Close database
        if db_instance:
            await db_instance.close()
            logger.info("✅ Database closed")
        
        # Close bot session
        if bot_instance:
            await bot_instance.session.close()
            logger.info("✅ Bot session closed")
            
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    finally:
        logger.info("👋 Bot stopped")

async def error_handler(update, exception):
    """Global error handler"""
    try:
        logger.error(f"Global error: {exception}", exc_info=True)
        
        # Send to log channel
        if bot_instance:
            error_msg = f"❌ **ERROR**\nType: `{type(exception).__name__}`\n"
            error_msg += f"Message: `{str(exception)[:200]}`\n"
            
            if update and update.message:
                error_msg += f"User: {update.message.from_user.id}\n"
                error_msg += f"Command: {update.message.text[:50]}"
            
            try:
                await log_to_channel(bot_instance, error_msg)
            except:
                pass
        
        # Send user-friendly message
        if update and update.message:
            try:
                await update.message.answer(
                    "⚠️ An error occurred. Our team has been notified.\n"
                    "Please try again in a moment."
                )
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def main():
    """Main bot loop"""
    try:
        # Initialize
        await startup()
        
        # Add error handler
        dp_instance.errors.register(error_handler)
        
        logger.info("🤖 Bot is now running...")
        logger.info(f"👑 Owner: {Config.OWNER_ID}")
        logger.info(f"📊 Log Channel: {Config.LOG_CHANNEL}")
        
        # Start polling
        await dp_instance.start_polling(
            bot_instance, 
            allowed_updates=dp_instance.resolve_used_update_types(),
            skip_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error in main loop: {e}")
        logger.error(traceback.format_exc())
        
        # Try to send crash report
        try:
            if bot_instance:
                await log_to_channel(
                    bot_instance,
                    f"💥 **BOT CRASHED**\nError: `{str(e)[:300]}`\n"
                    "Attempting auto-recovery..."
                )
        except:
            pass
            
        # Wait and restart
        await asyncio.sleep(10)
        logger.info("🔄 Attempting restart...")
        await main()
        
    finally:
        await shutdown()

if __name__ == "__main__":
    # Run bot
    asyncio.run(main())
