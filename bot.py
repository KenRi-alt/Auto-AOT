#!/usr/bin/env python3
"""
🌳 FAMILY TREE BOT - MAIN FILE
Fixed imports for Railway
"""

import os
import sys
import asyncio
import logging
import traceback
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# ✅ CORRECT IMPORTS:
try:
    from config import Config
    from database import Database       # Database class
    from images import image_gen        # ✅ FIXED: image_gen is in images.py
    from utils.logger import setup_logger, log_to_channel
    from utils.helpers import get_target_user, format_money
    
    # Import handlers
    from handlers.family import family_router
    from handlers.economy import economy_router
    from handlers.games import games_router
    from handlers.admin import admin_router
    from handlers.utils import utils_router
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"📁 Current directory: {current_dir}")
    print(f"📂 Files in directory: {os.listdir(current_dir)}")
    
    # Show what's available
    print("\n🔍 Available modules:")
    for file in os.listdir(current_dir):
        if file.endswith('.py'):
            print(f"  - {file}")
    
    sys.exit(1)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

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
        dp_instance = Dispatcher(storage=storage)
        
        # Include routers
        dp_instance.include_router(family_router)
        dp_instance.include_router(economy_router)
        dp_instance.include_router(games_router)
        dp_instance.include_router(admin_router)
        dp_instance.include_router(utils_router)
        
        # Set dependencies
        dp_instance["db"] = db_instance
        dp_instance["bot"] = bot_instance
        
        # Send startup notification
        try:
            await log_to_channel(
                bot_instance, 
                "🚀 **BOT STARTED**\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⚙️ Version: {Config.VERSION}\n"
                "✅ All systems ready"
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
        
        # Send user-friendly message
        if update and update.message:
            try:
                await update.message.answer(
                    "⚠️ An error occurred. Please try again later."
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
        logger.info(f"👑 Owner ID: {Config.OWNER_ID}")
        
        # Start polling
        await dp_instance.start_polling(
            bot_instance, 
            allowed_updates=dp_instance.resolve_used_update_types(),
            skip_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.error(traceback.format_exc())
        
        # Wait and restart
        await asyncio.sleep(10)
        logger.info("🔄 Attempting restart...")
        await main()
        
    finally:
        await shutdown()

if __name__ == "__main__":
    # Run bot
    asyncio.run(main())
