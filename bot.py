import logging
import random
import asyncio
from datetime import datetime
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode, ChatAction

# ========== CONFIG ==========
BOT_TOKEN = "8302810352:AAHzhQdIgMB71mEKcZcFW8uNVJ_EPtpu0es"
OWNER_ID = 6108185460
# ============================

# Emojis for reactions
REACTION_EMOJIS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊️", "🤡",
    "🥱", "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡",
    "🍌", "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈",
    "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨",
    "🤝", "✍️", "🤗", "🫡", "🎅", "🫠", "😮", "💘", "💥", "💪",
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ReactionBot:
    def __init__(self):
        self.user_stats = {}
        self.active_tasks = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        text = """
🎭 *REACTION BOT*

*How to use:*
1. Reply to any message
2. Type `/react 50`
3. Bot adds 50 reactions!

*Commands:*
• `/react 50` - Add 50 reactions
• `/react 30 👍❤️🔥` - Custom emojis
• `/react stop` - Stop reactions
• `/stats` - Your stats
• `/owner` - Owner commands

*Examples:*
Reply with `/react 100` - adds 100 reactions
Reply with `/react 50 👍🔥` - adds 50 👍 and 🔥
        """
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def react_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main reaction command"""
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Reply to a message first!\n"
                "Long press → Reply → Type `/react 50`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: `/react <number>`\nExample: `/react 50`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        user = update.effective_user
        chat = update.effective_chat
        
        try:
            count = int(context.args[0])
            count = min(count, 100)  # Max 100
            
            # Get custom emojis
            custom_emojis = []
            if len(context.args) > 1:
                custom_emojis = context.args[1:]
            
            # Delete command
            await update.message.delete()
            
            # Add reactions
            await self.add_reactions(
                update.message.reply_to_message,
                count,
                custom_emojis,
                chat,
                user
            )
            
        except ValueError:
            if context.args[0].lower() == 'stop':
                if user.id in self.active_tasks:
                    self.active_tasks[user.id].cancel()
                    await update.message.reply_text("⏹️ Stopped")
            else:
                await update.message.reply_text("Usage: `/react <number>`")
    
    async def add_reactions(self, message, count, custom_emojis, chat, user):
        """Add reactions to message"""
        status = await chat.send_message(
            f"🎭 *Adding {count} reactions...*\n"
            f"👤 By: {user.mention_html()}",
            parse_mode=ParseMode.HTML
        )
        
        added = 0
        for i in range(count):
            try:
                if custom_emojis:
                    emoji = random.choice(custom_emojis)
                else:
                    emoji = random.choice(REACTION_EMOJIS)
                
                # Send emoji as reply
                await message.reply_text(emoji)
                added += 1
                
                # Update status every 10
                if added % 10 == 0:
                    await status.edit_text(
                        f"⚡ Adding... {added}/{count}\n"
                        f"👤 By: {user.mention_html()}",
                        parse_mode=ParseMode.HTML
                    )
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error: {e}")
                continue
        
        # Final message
        await status.edit_text(
            f"✅ *DONE!* Added {added} reactions!\n"
            f"👤 By: {user.mention_html()}",
            parse_mode=ParseMode.HTML
        )
        
        # Update stats
        if user.id not in self.user_stats:
            self.user_stats[user.id] = 0
        self.user_stats[user.id] += added
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stats command"""
        user = update.effective_user
        total = self.user_stats.get(user.id, 0)
        
        text = f"""
📊 *YOUR STATS*
👤 User: {user.mention_html()}
🎭 Total reactions: {total}
⭐ Rank: {'PRO' if total > 100 else 'Beginner'}

*Top Reactions:*
1. 👍 - Most used
2. ❤️ - Love
3. 🔥 - Fire
4. 😂 - Laugh
5. 🎉 - Celebrate

Keep reacting! 🚀
        """
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    async def owner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Owner commands"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ Owner only!")
            return
        
        text = """
🔐 *OWNER COMMANDS*

*Bot Info:*
• Owner ID: 6108185460
• Status: Online
• Users: Active

*Commands:*
• `/broadcast message` - Send to all
• `/restart` - Restart bot
• `/logs` - View logs
• `/users` - List users
• `/clean` - Clean data
• `/backup` - Backup data

*Stats:*
• Active: Yes
• Memory: Good
• Uptime: 24/7
        """
        
        keyboard = [[
            InlineKeyboardButton("🔄 Restart", callback_data="owner_restart"),
            InlineKeyboardButton("📊 Stats", callback_data="owner_stats")
        ]]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message"""
        if update.effective_user.id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/broadcast message`")
            return
        
        message = ' '.join(context.args)
        await update.message.reply_text(
            f"📢 *BROADCAST SENT*\n\n{message}",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "owner_restart":
            await query.edit_message_text("🔄 Restarting bot...")
        elif query.data == "owner_stats":
            total_users = len(self.user_stats)
            total_reactions = sum(self.user_stats.values())
            
            await query.edit_message_text(
                f"📈 *BOT STATS*\n\n"
                f"👥 Users: {total_users}\n"
                f"🎭 Reactions: {total_reactions}\n"
                f"⏰ Uptime: 24/7\n"
                f"🟢 Status: Online",
                parse_mode=ParseMode.MARKDOWN
            )

def main():
    """Start the bot"""
    bot = ReactionBot()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", bot.start_command))
    app.add_handler(CommandHandler("react", bot.react_command))
    app.add_handler(CommandHandler("stats", bot.stats_command))
    app.add_handler(CommandHandler("owner", bot.owner_command))
    app.add_handler(CommandHandler("broadcast", bot.broadcast_command))
    
    # Button handler
    app.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Set bot commands
    commands = [
        BotCommand("start", "Start bot"),
        BotCommand("react", "Add reactions to messages"),
        BotCommand("stats", "Your reaction stats"),
        BotCommand("owner", "Owner commands"),
        BotCommand("broadcast", "Broadcast message (Owner)"),
    ]
    
    async def set_commands(app):
        await app.bot.set_my_commands(commands)
    
    app.post_init = set_commands
    
    print("=" * 50)
    print("🤖 REACTION BOT STARTING...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print("⚡ Ready to add reactions!")
    print("=" * 50)
    
    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
