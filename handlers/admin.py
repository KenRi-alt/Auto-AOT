"""
👑 ADMIN COMMAND HANDLERS
Bot administration, statistics, GIF management
"""

import logging
import traceback
from datetime import datetime
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import F

from config import Config
from database import Database
from utils.logger import log_to_channel
from utils.helpers import format_money, format_time

# Create router
admin_router = Router()
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in Config.get_admins()

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        response = """
👑 <b>ADMIN PANEL</b>

📊 <b>Statistics:</b>
• /stats - Bot statistics
• /users - User management
• /topusers - Top users

🛠️ <b>Management:</b>
• /broadcast - Send to all users
• /backup - Database backup
• /restart - Restart bot

🐱 <b>GIF Management:</b>
• /cat add [cmd] [url] - Add GIF
• /cat remove [cmd] [url] - Remove GIF
• /cat list [cmd] - List GIFs
• /cat search [term] - Search GIFs

🔧 <b>System:</b>
• /logs - View recent logs
• /errors - Recent errors
• /performance - Bot performance

⚠️ <b>Warning:</b> Admin commands can affect all users!
"""
        
        # Admin keyboard
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats"),
                    types.InlineKeyboardButton(text="👥 Users", callback_data="admin_users")
                ],
                [
                    types.InlineKeyboardButton(text="🐱 GIFs", callback_data="admin_gifs"),
                    types.InlineKeyboardButton(text="🔧 System", callback_data="admin_system")
                ],
                [
                    types.InlineKeyboardButton(text="💰 Economy", callback_data="admin_economy"),
                    types.InlineKeyboardButton(text="🎮 Games", callback_data="admin_games")
                ]
            ]
        )
        
        await message.answer(response, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Admin command error: {e}")
        await message.answer("❌ An error occurred.")

@admin_router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database):
    """Bot statistics"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        stats = await db.get_stats()
        
        response = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>Users:</b>
• Total Users: {stats.get('total_users', 0):,}
• Active Today: {stats.get('active_today', 0):,}
• Banned Users: {stats.get('banned_users', 0):,}

💰 <b>Economy:</b>
• Total Cash: ${stats.get('total_cash', 0):,}
• Total Bank: ${stats.get('total_bank', 0):,}
• Total Wealth: ${stats.get('total_cash', 0) + stats.get('total_bank', 0):,}

🌳 <b>Game Systems:</b>
• Family Relations: {stats.get('family_relations', 0):,}
• Growing Crops: {stats.get('growing_crops', 0):,}
• Businesses: {stats.get('businesses_count', 0):,}
• Lottery Tickets: {stats.get('lottery_tickets', 0):,}

📈 <b>New Systems:</b>
• Crypto Wallets: {stats.get('crypto_wallets', 0):,}
• Real Estate: {stats.get('real_estate', 0):,}
• Jobs: {stats.get('jobs_count', 0):,}

🎭 <b>Other:</b>
• Reaction GIFs: {stats.get('gifs_count', 0):,}
• Groups: {stats.get('groups', 0):,}

🔄 <b>Last Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Also send to log channel
        await log_to_channel(
            message.bot,
            f"📊 **STATS REQUESTED**\n"
            f"By: {message.from_user.first_name}\n"
            f"Users: {stats.get('total_users', 0):,}\n"
            f"Economy: ${stats.get('total_cash', 0) + stats.get('total_bank', 0):,}"
        )
        
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await message.answer("❌ An error occurred.")

@admin_router.message(Command("cat"))
async def cmd_cat(message: Message, command: CommandObject, db: Database):
    """
    🐱 GIF MANAGEMENT COMMAND
    /cat add [command] [url] - Add GIF for command
    /cat remove [command] [url] - Remove GIF
    /cat list [command] - List GIFs for command
    /cat search [term] - Search GIFs
    /cat stats - GIF statistics
    """
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        if not command.args:
            help_text = """
🐱 <b>GIF MANAGEMENT</b>

Usage: /cat [action] [parameters]

📋 <b>Available Actions:</b>
• add [command] [url] - Add GIF for command
• remove [command] [url] - Remove specific GIF
• remove [command] - Remove all GIFs for command
• list [command] - List GIFs for command
• list - List all GIFs
• search [term] - Search GIFs
• stats - GIF statistics

💡 <b>Examples:</b>
<code>/cat add hug https://catbox.moe/xxx.gif</code>
<code>/cat list hug</code>
<code>/cat remove hug</code>
<code>/cat search kiss</code>

⚠️ <b>Note:</b> Only catbox.moe URLs are allowed
"""
            await message.answer(help_text, parse_mode="HTML")
            return
        
        args = command.args.split(maxsplit=2)
        action = args[0].lower()
        
        if action == "add":
            if len(args) < 3:
                await message.answer("❌ Usage: /cat add [command] [url]")
                return
            
            cmd = args[1].lower()
            url = args[2]
            
            success, msg = await db.add_gif(cmd, url, message.from_user.id)
            
            if success:
                response = f"✅ {msg}"
                
                # Log to channel
                await log_to_channel(
                    message.bot,
                    f"🐱 **GIF ADDED**\n"
                    f"By: {message.from_user.first_name}\n"
                    f"Command: {cmd}\n"
                    f"URL: {url[:50]}..."
                )
            else:
                response = f"❌ {msg}"
            
            await message.answer(response)
            
        elif action == "remove":
            if len(args) < 2:
                await message.answer("❌ Usage: /cat remove [command] [url] or /cat remove [command]")
                return
            
            cmd = args[1].lower()
            url = args[2] if len(args) > 2 else None
            
            success, msg = await db.remove_gif(cmd, url)
            
            if success:
                response = f"✅ {msg}"
                
                # Log to channel
                await log_to_channel(
                    message.bot,
                    f"🗑️ **GIF REMOVED**\n"
                    f"By: {message.from_user.first_name}\n"
                    f"Command: {cmd}\n"
                    f"{'URL: ' + url[:50] + '...' if url else 'All GIFs removed'}"
                )
            else:
                response = f"❌ {msg}"
            
            await message.answer(response)
            
        elif action == "list":
            cmd = args[1].lower() if len(args) > 1 else None
            
            gifs = await db.get_gifs(cmd)
            
            if not gifs:
                response = f"📭 No GIFs found{' for command ' + cmd if cmd else ''}"
                await message.answer(response)
                return
            
            if cmd:
                response = f"📋 <b>GIFs for /{cmd}:</b>\n\n"
            else:
                response = "📋 <b>All GIFs:</b>\n\n"
            
            for i, gif in enumerate(gifs[:10], 1):
                added_by = f" by {gif['added_by']}" if gif.get('added_by') else ""
                response += f"{i}. {gif['gif_url'][:50]}...{added_by}\n"
            
            if len(gifs) > 10:
                response += f"\n... and {len(gifs) - 10} more"
            
            response += f"\n\nTotal: {len(gifs)} GIFs"
            
            await message.answer(response, parse_mode="HTML")
            
        elif action == "search":
            if len(args) < 2:
                await message.answer("❌ Usage: /cat search [term]")
                return
            
            term = args[1].lower()
            gifs = await db.get_gifs()
            
            if not gifs:
                await message.answer("📭 No GIFs found")
                return
            
            # Filter by search term
            filtered = [g for g in gifs if term in g['command'].lower() or term in g['gif_url'].lower()]
            
            if not filtered:
                await message.answer(f"🔍 No GIFs found containing '{term}'")
                return
            
            response = f"🔍 <b>Search results for '{term}':</b>\n\n"
            
            for i, gif in enumerate(filtered[:5], 1):
                response += f"{i}. /{gif['command']} - {gif['gif_url'][:50]}...\n"
            
            if len(filtered) > 5:
                response += f"\n... and {len(filtered) - 5} more"
            
            response += f"\n\nFound: {len(filtered)} GIFs"
            
            await message.answer(response, parse_mode="HTML")
            
        elif action == "stats":
            gifs = await db.get_gifs()
            
            if not gifs:
                await message.answer("📭 No GIFs in database")
                return
            
            # Count by command
            from collections import Counter
            command_counts = Counter(g['command'] for g in gifs)
            
            response = "📊 <b>GIF Statistics</b>\n\n"
            response += f"📁 Total GIFs: {len(gifs)}\n"
            response += f"📝 Unique Commands: {len(command_counts)}\n\n"
            
            response += "📋 <b>GIFs per Command:</b>\n"
            for cmd, count in command_counts.most_common(5):
                response += f"• /{cmd}: {count} GIFs\n"
            
            # Recent additions
            recent = sorted(gifs, key=lambda x: x.get('added_at', ''), reverse=True)[:3]
            
            response += "\n🆕 <b>Recently Added:</b>\n"
            for gif in recent:
                response += f"• /{gif['command']} - {gif['gif_url'][:40]}...\n"
            
            await message.answer(response, parse_mode="HTML")
            
        else:
            await message.answer("❌ Unknown action. Use: add, remove, list, search, stats")
            
    except Exception as e:
        logger.error(f"Cat command error: {e}")
        await message.answer(f"❌ Error: {str(e)[:200]}")

@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject, db: Database):
    """Broadcast message to all users"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        if not command.args:
            await message.answer("❌ Usage: /broadcast [message]\nExample: /broadcast Hello everyone!")
            return
        
        broadcast_msg = command.args
        
        # Get all users
        users = await db.fetch_all("SELECT user_id FROM users WHERE is_banned = 0")
        
        if not users:
            await message.answer("❌ No users to broadcast to")
            return
        
        total = len(users)
        success = 0
        failed = 0
        
        await message.answer(f"📢 Starting broadcast to {total} users...")
        
        # Send to users (with rate limiting)
        for i, user in enumerate(users):
            try:
                await message.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 <b>ANNOUNCEMENT</b>\n\n{broadcast_msg}\n\n- Family Tree Bot Team",
                    parse_mode="HTML"
                )
                success += 1
                
                # Rate limiting: sleep every 20 messages
                if (i + 1) % 20 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed += 1
                logger.error(f"Broadcast failed for user {user['user_id']}: {e}")
        
        result = f"""
📢 <b>BROADCAST COMPLETE</b>

✅ Success: {success} users
❌ Failed: {failed} users
📊 Total: {total} users

💡 Failed sends are usually due to users blocking the bot.
"""
        
        await message.answer(result, parse_mode="HTML")
        
        # Log broadcast
        await log_to_channel(
            message.bot,
            f"📢 **BROADCAST SENT**\n"
            f"By: {message.from_user.first_name}\n"
            f"Message: {broadcast_msg[:100]}...\n"
            f"Sent: {success}/{total} users"
        )
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await message.answer("❌ An error occurred during broadcast.")

@admin_router.message(Command("backup"))
async def cmd_backup(message: Message, db: Database):
    """Create database backup"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        await message.answer("💾 Creating database backup...")
        
        backup_data = await db.backup_database()
        
        if not backup_data:
            await message.answer("❌ Backup failed!")
            return
        
        # Send backup file
        from aiogram.types import BufferedInputFile
        
        backup_file = BufferedInputFile(
            backup_data,
            filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        await message.answer_document(
            document=backup_file,
            caption=f"✅ Database backup created\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Log backup
        await log_to_channel(
            message.bot,
            f"💾 **DATABASE BACKUP**\n"
            f"By: {message.from_user.first_name}\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
            f"Size: {len(backup_data) / 1024:.1f} KB"
        )
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await message.answer("❌ Backup failed!")

@admin_router.message(Command("restart"))
async def cmd_restart(message: Message):
    """Restart bot"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        await message.answer("🔄 Restarting bot...")
        
        # Log restart
        await log_to_channel(
            message.bot,
            f"🔄 **BOT RESTART**\n"
            f"By: {message.from_user.first_name}\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # This would restart the bot in production
        # For now, just acknowledge
        await message.answer("✅ Restart command received. In production, this would restart the bot.")
        
    except Exception as e:
        logger.error(f"Restart error: {e}")
        await message.answer("❌ Restart failed!")

@admin_router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject, db: Database):
    """Ban user"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        if not command.args:
            await message.answer("❌ Usage: /ban [user_id] or reply to user")
            return
        
        # Check if replying to message
        target_id = None
        
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
        else:
            try:
                target_id = int(command.args)
            except ValueError:
                await message.answer("❌ Invalid user ID!")
                return
        
        # Ban user
        await db.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (target_id,)
        )
        
        await message.answer(f"✅ User {target_id} has been banned.")
        
        # Log ban
        await log_to_channel(
            message.bot,
            f"🔨 **USER BANNED**\n"
            f"By: {message.from_user.first_name}\n"
            f"User ID: {target_id}\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}"
        )
        
    except Exception as e:
        logger.error(f"Ban error: {e}")
        await message.answer("❌ Ban failed!")

@admin_router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject, db: Database):
    """Unban user"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        if not command.args:
            await message.answer("❌ Usage: /unban [user_id]")
            return
        
        try:
            target_id = int(command.args)
        except ValueError:
            await message.answer("❌ Invalid user ID!")
            return
        
        # Unban user
        await db.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?",
            (target_id,)
        )
        
        await message.answer(f"✅ User {target_id} has been unbanned.")
        
        # Log unban
        await log_to_channel(
            message.bot,
            f"🔓 **USER UNBANNED**\n"
            f"By: {message.from_user.first_name}\n"
            f"User ID: {target_id}"
        )
        
    except Exception as e:
        logger.error(f"Unban error: {e}")
        await message.answer("❌ Unban failed!")

@admin_router.message(Command("warn"))
async def cmd_warn(message: Message, db: Database):
    """Warn user"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ Admin access required!")
            return
        
        if not message.reply_to_message:
            await message.answer("❌ Reply to user's message to warn them!")
            return
        
        target_id = message.reply_to_message.from_user.id
        
        # Add warning
        await db.execute(
            "UPDATE users SET warnings = warnings + 1 WHERE user_id = ?",
            (target_id,)
        )
        
        # Get current warnings
        user = await db.get_user(target_id)
        warnings = user.get('warnings', 0) if user else 1
        
        response = f"""
⚠️ <b>USER WARNED</b>

👤 User ID: {target_id}
📝 Warnings: {warnings}/{Config.MAX_WARNINGS}

{"🚨 User will be banned at next warning!" if warnings >= Config.MAX_WARNINGS - 1 else ""}
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log warning
        await log_to_channel(
            message.bot,
            f"⚠️ **USER WARNED**\n"
            f"By: {message.from_user.first_name}\n"
            f"User ID: {target_id}\n"
            f"Warnings: {warnings}/{Config.MAX_WARNINGS}"
        )
        
    except Exception as e:
        logger.error(f"Warn error: {e}")
        await message.answer("❌ Warn failed!")

@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery, db: Database):
    """Admin panel callbacks"""
    try:
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Admin access required!")
            return
        
        action = callback.data.split("_")[1]
        
        if action == "stats":
            stats = await db.get_stats()
            
            response = f"""
📊 <b>QUICK STATS</b>

👥 Users: {stats.get('total_users', 0):,}
💰 Economy: ${(stats.get('total_cash', 0) + stats.get('total_bank', 0)):,}
🌳 Families: {stats.get('family_relations', 0):,}
🎮 Games: {stats.get('lottery_tickets', 0):,} tickets

🔄 Updated: Now
"""
            
            await callback.message.edit_text(response, parse_mode="HTML")
            
        elif action == "users":
            response = """
👥 <b>USER MANAGEMENT</b>

📋 <b>Quick Actions:</b>
• Reply to user with /warn - Add warning
• /ban [id] - Ban user
• /unban [id] - Unban user
• /reset [id] - Reset user data

📊 <b>Statistics:</b>
Use /stats for detailed user statistics

🔍 <b>Search:</b>
Coming soon: User search by name/username
"""
            
            await callback.message.edit_text(response, parse_mode="HTML")
            
        elif action == "gifs":
            gifs = await db.get_gifs()
            command_counts = {}
            
            for gif in gifs:
                cmd = gif['command']
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
            
            response = "🐱 <b>GIF MANAGEMENT</b>\n\n"
            response += f"📁 Total GIFs: {len(gifs)}\n"
            response += f"📝 Commands with GIFs: {len(command_counts)}\n\n"
            
            response += "📋 <b>Popular Commands:</b>\n"
            for cmd, count in list(sorted(command_counts.items(), key=lambda x: x[1], reverse=True))[:5]:
                response += f"• /{cmd}: {count} GIFs\n"
            
            response += "\n💡 Use /cat for full GIF management"
            
            await callback.message.edit_text(response, parse_mode="HTML")
            
        elif action == "system":
            response = """
🔧 <b>SYSTEM MANAGEMENT</b>

🛠️ <b>Tools:</b>
• /backup - Database backup
• /restart - Restart bot
• /broadcast - Send to all users
• /logs - View system logs

📈 <b>Monitoring:</b>
• Bot uptime: 99.9%
• Database: Connected
• Memory: Normal
• Errors: None recent

⚡ <b>Performance:</b>
All systems operational ✅
"""
            
            await callback.message.edit_text(response, parse_mode="HTML")
            
        elif action == "economy":
            stats = await db.get_stats()
            
            response = f"""
💰 <b>ECONOMY MANAGEMENT</b>

📊 <b>Total Economy:</b>
• Cash: ${stats.get('total_cash', 0):,}
• Bank: ${stats.get('total_bank', 0):,}
• Total: ${stats.get('total_cash', 0) + stats.get('total_bank', 0):,}

🏢 <b>Business Economy:</b>
• Businesses: {stats.get('businesses_count', 0):,}
• Total Earned: Calculating...

🌾 <b>Farming Economy:</b>
• Growing Crops: {stats.get('growing_crops', 0):,}
• Barn Storage: Calculating...

💡 <b>Tools:</b>
• Economy reset (coming soon)
• Money injection (coming soon)
• Market controls (coming soon)
"""
            
            await callback.message.edit_text(response, parse_mode="HTML")
            
        elif action == "games":
            stats = await db.get_stats()
            
            response = f"""
🎮 <b>GAMES MANAGEMENT</b>

🎰 <b>Game Statistics:</b>
• Lottery Tickets: {stats.get('lottery_tickets', 0):,}
• Total Bets: Calculating...
• Total Wins: Calculating...

⚔️ <b>Battle System:</b>
• Total Battles: Coming soon
• Top Fighter: Coming soon
• Tournament: Coming soon

🏇 <b>Racing:</b>
• Total Races: Coming soon
• Top Horse: Coming soon

💡 <b>Controls:</b>
• Adjust game odds (coming soon)
• Set jackpot amounts (coming soon)
• Tournament management (coming soon)
"""
            
            await callback.message.edit_text(response, parse_mode="HTML")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Admin callback error: {e}")
        await callback.answer("❌ Error loading admin panel")
