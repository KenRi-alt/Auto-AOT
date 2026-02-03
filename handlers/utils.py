"""
🛠️ UTILITY COMMAND HANDLERS
General utility commands
"""

import logging
from aiogram import Router, types
from aiogram.filters import Command

# Create router
utils_router = Router()
logger = logging.getLogger(__name__)

@utils_router.message(Command("ping"))
async def cmd_ping(message: types.Message):
    """Simple ping command"""
    await message.answer("🏓 Pong! Bot is alive and working.")

@utils_router.message(Command("id"))
async def cmd_id(message: types.Message):
    """Get user and chat ID"""
    response = f"""
📋 <b>ID Information</b>

👤 <b>Your ID:</b> <code>{message.from_user.id}</code>
💬 <b>Chat ID:</b> <code>{message.chat.id}</code>
"""
    await message.answer(response, parse_mode="HTML")

@utils_router.message(Command("support"))
async def cmd_support(message: types.Message):
    """Support information"""
    from config import Config
    await message.answer(
        f"📞 <b>Support</b>\n\n"
        f"Need help? Contact us!\n"
        f"Support Chat: {Config.SUPPORT_CHAT}\n"
        f"Bot Version: {Config.VERSION}",
        parse_mode="HTML"
    )
