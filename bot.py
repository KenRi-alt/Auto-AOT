#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - MAIN ENTRY POINT
Professional modular architecture with crash prevention
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
from utils.logger import setup_logger, log_to_channel
from utils.security import SecurityManager
from database import Database

# Import all handlers
from handlers.family import family_router
from handlers.economy import economy_router
from handlers.games import games_router
from handlers.admin import admin_router
from handlers.utils import utils_router

# Global variables
bot = None
dp = None
db = None
security = None
logger = None

async def startup():
    """Initialize bot on startup"""
    global bot, dp, db, security, logger
    
    try:
        # Setup logging
        logger = setup_logger()
        logger.info("🚀 Starting Family Tree Bot...")
        
        # Initialize security manager
        security = SecurityManager()
        
        # Initialize database
        db = Database()
        await db.connect()
        logger.info("✅ Database connected")
        
        # Initialize bot with default properties
        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Initialize dispatcher
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Include all routers
        dp.include_router(family_router)
        dp.include_router(economy_router)
        dp.include_router(games_router)
        dp.include_router(admin_router)
        dp.include_router(utils_router)
        
        # Send startup notification to log channel
        await log_to_channel(bot, "🚀 **BOT STARTED**\n"
                                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                f"⚙️ Version: {Config.VERSION}\n"
                                "✅ All systems operational")
        
        logger.info("✅ Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        logger.error(traceback.format_exc())
        raise

async def shutdown():
    """Graceful shutdown"""
    global bot, dp, db
    
    try:
        logger.info("🛑 Shutting down bot...")
        
        # Send shutdown notification to log channel
        if bot:
            await log_to_channel(bot, "🛑 **BOT SHUTTING DOWN**\n"
                                    f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                    "🔌 Graceful shutdown initiated")
        
        # Close database connection
        if db:
            await db.close()
            logger.info("✅ Database connection closed")
        
        # Close bot session
        if bot:
            await bot.session.close()
            logger.info("✅ Bot session closed")
            
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    finally:
        logger.info("👋 Bot stopped")

async def error_handler(update, exception):
    """Global error handler"""
    try:
        error_msg = f"❌ **ERROR OCCURRED**\n\n"
        error_msg += f"⚠️ Type: `{type(exception).__name__}`\n"
        error_msg += f"💬 Message: `{str(exception)[:200]}`\n"
        
        if update:
            if update.message:
                error_msg += f"👤 User: {update.message.from_user.id}\n"
                error_msg += f"📝 Command: {update.message.text}\n"
            elif update.callback_query:
                error_msg += f"👤 User: {update.callback_query.from_user.id}\n"
                error_msg += f"🔘 Callback: {update.callback_query.data}\n"
        
        # Log to console
        logger.error(f"Global error: {exception}", exc_info=True)
        
        # Send to log channel
        if bot:
            await log_to_channel(bot, error_msg)
        
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

async def health_check():
    """Periodic health check"""
    try:
        if bot and db:
            # Check database connection
            await db.health_check()
            
            # Send periodic health status to log channel
            if Config.HEALTH_CHECK_ENABLED:
                await log_to_channel(
                    bot,
                    f"❤️ **HEALTH CHECK**\n"
                    f"🕒 {datetime.now().strftime('%H:%M:%S')}\n"
                    f"✅ All systems normal\n"
                    f"👥 Users: {await db.get_user_count()}"
                )
    except Exception as e:
        logger.error(f"Health check failed: {e}")

async def main():
    """Main bot loop"""
    try:
        # Initialize bot
        await startup()
        
        # Setup periodic tasks
        from utils.scheduler import start_scheduler
        scheduler = start_scheduler(bot, db)
        
        # Add error handler
        dp.errors.register(error_handler)
        
        logger.info("🤖 Bot is now running...")
        
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        logger.error(traceback.format_exc())
        
        # Try to send crash report
        try:
            if bot:
                crash_msg = f"💥 **BOT CRASHED**\n\n"
                crash_msg += f"Error: `{str(e)[:300]}`\n"
                crash_msg += "Attempting auto-recovery..."
                await log_to_channel(bot, crash_msg)
        except:
            pass
            
        # Wait and restart
        await asyncio.sleep(30)
        logger.info("🔄 Attempting auto-restart...")
        await main()
        
    finally:
        await shutdown()

if __name__ == "__main__":
    # Create event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        loop.close()
