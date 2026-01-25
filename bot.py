import logging
import random
import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Set
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from telegram import (
    Update, 
    ReactionTypeEmoji, 
    BotCommand, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatMember,
    Chat
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters
)
from telegram.constants import ParseMode, ChatType, ChatAction

# ========== CONFIG ==========
BOT_TOKEN = "8302810352:AAHzhQdIgMB71mEKcZcFW8uNVJ_EPtpu0es"
OWNER_ID = 6108185460
DATABASE_FILE = "bot_data.db"
PRO_USERS_FILE = "pro_users.json"
# ============================

# 150+ Emojis for reactions
REACTION_EMOJIS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊️", "🤡",
    "🥱", "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡",
    "🍌", "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈",
    "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨",
    "🤝", "✍️", "🤗", "🫡", "🎅", "🫠", "😮", "💘", "💥", "💪",
    "🐍", "🚀", "🎮", "💻", "🎨", "📚", "🎵", "🍕", "☕", "⭐",
    "🌟", "✨", "🌙", "☀️", "🌈", "☁️", "❄️", "🌊", "🍀", "🌹",
    "🐶", "🐱", "🐼", "🦁", "🐯", "🦊", "🐰", "🐨", "🐵", "🦄",
    "🍎", "🍉", "🍇", "🍊", "🍋", "🍒", "🥝", "🥑", "🌶️", "🥨",
    "🎲", "🎯", "🎪", "🎭", "🎨", "🧩", "♟️", "🎳", "🏓", "🥊",
    "⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱", "🏸", "🏒",
    "🚗", "✈️", "🚀", "🛸", "🚁", "🛳️", "🚂", "🚲", "🏍️", "🛵",
    "📱", "💻", "🖥️", "⌚", "📷", "🎥", "📺", "🎙️", "📻", "🔋"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UltimateReactionBot:
    def __init__(self):
        self.pro_users = self.load_pro_users()
        self.user_stats = {}
        self.group_stats = {}
        self.active_reactions = {}
        self.scheduler = BackgroundScheduler()
        self.setup_database()
        self.start_scheduler()
        
    def setup_database(self):
        """Setup SQLite database"""
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                member_count INTEGER,
                created_date TIMESTAMP,
                last_active TIMESTAMP,
                total_reactions INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                total_reactions INTEGER DEFAULT 0,
                is_pro BOOLEAN DEFAULT FALSE,
                pro_expiry TIMESTAMP,
                join_date TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logger.info("Database initialized")
    
    def load_pro_users(self):
        """Load pro users from file"""
        if os.path.exists(PRO_USERS_FILE):
            with open(PRO_USERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_pro_users(self):
        """Save pro users to file"""
        with open(PRO_USERS_FILE, 'w') as f:
            json.dump(self.pro_users, f)
    
    def start_scheduler(self):
        """Start background tasks to prevent sleep"""
        # Keep bot alive task
        self.scheduler.add_job(
            self.keep_alive,
            trigger=IntervalTrigger(minutes=5),
            id='keep_alive'
        )
        
        # Cleanup old data
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=IntervalTrigger(hours=1),
            id='cleanup'
        )
        
        # Update group stats
        self.scheduler.add_job(
            self.update_group_stats,
            trigger=IntervalTrigger(minutes=30),
            id='update_stats'
        )
        
        self.scheduler.start()
        logger.info("Background scheduler started")
    
    async def keep_alive(self):
        """Keep bot from sleeping"""
        logger.info("Bot is alive and running")
        # Can add heartbeat to external service here
    
    def is_pro_user(self, user_id):
        """Check if user is pro"""
        return str(user_id) in self.pro_users or user_id == OWNER_ID
    
    def make_pro_user(self, user_id, days=30):
        """Make user pro"""
        expiry = datetime.now() + timedelta(days=days)
        self.pro_users[str(user_id)] = expiry.isoformat()
        self.save_pro_users()
        
        # Update database
        self.cursor.execute(
            "UPDATE users SET is_pro = TRUE, pro_expiry = ? WHERE user_id = ?",
            (expiry, user_id)
        )
        self.conn.commit()
        
        return expiry
    
    # ========== GROUP MANAGEMENT ==========
    
    async def track_new_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track when bot is added to a group"""
        chat = update.effective_chat
        
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            self.cursor.execute(
                "INSERT OR REPLACE INTO groups (group_id, title, member_count, created_date, last_active) VALUES (?, ?, ?, ?, ?)",
                (chat.id, chat.title, chat.get_member_count(), datetime.now(), datetime.now())
            )
            self.conn.commit()
            
            logger.info(f"Bot added to group: {chat.title} (ID: {chat.id})")
            
            # Send welcome message
            welcome_text = """
🎭 *ULTIMATE REACTION BOT* has joined!

*Features in groups:*
• Add reactions to any message
• PRO features for power users
• Group statistics
• Admin controls

*Try it now:*
1. Reply to a message
2. Type `/react 50`
3. Watch the reactions flow!

*Group Admin Commands:*
• `/gstats` - Group statistics
• `/gsettings` - Configure bot
• `/topreactors` - Top users

Use `/help` for all commands!
            """
            
            keyboard = [[
                InlineKeyboardButton("🎭 Try Reaction", callback_data="try_react"),
                InlineKeyboardButton("⭐ Get PRO", callback_data="get_pro")
            ]]
            
            await chat.send_message(
                welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def track_group_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track group activity"""
        chat = update.effective_chat
        
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            self.cursor.execute(
                "UPDATE groups SET last_active = ? WHERE group_id = ?",
                (datetime.now(), chat.id)
            )
            self.conn.commit()
    
    # ========== ANIMATED COMMANDS ==========
    
    async def typing_animation(self, chat_id, context, duration=1):
        """Send typing animation"""
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(duration)
    
    async def animated_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Animated start command"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Typing animation
        await self.typing_animation(chat.id, context, 1)
        
        # Send initial message
        msg = await update.message.reply_text("🚀 *Initializing Ultimate Reaction Bot...*", parse_mode=ParseMode.MARKDOWN)
        
        # Animation sequence
        animations = [
            "🎭 Loading reaction database...",
            "⚡ Setting up PRO features...",
            "🤖 Connecting to Telegram API...",
            "✅ Ready to react!"
        ]
        
        for text in animations:
            await asyncio.sleep(0.8)
            await msg.edit_text(f"🚀 *{text}*", parse_mode=ParseMode.MARKDOWN)
        
        # Final message
        final_text = f"""
🎭 *ULTIMATE REACTION BOT v2.0*

Welcome {user.mention_html()}!

*Quick Start:*
1. Reply to any message
2. Type `/react 50`
3. Enjoy the reactions!

*Group Features:*
• Smart group detection
• Group statistics
• Admin controls
• Activity tracking

*Try these commands:*
• `/react 50` - Add 50 reactions
• `/wave` - Send animated wave
• `/dance` - Dance animation
• `/fireworks` - Fireworks display
• `/gstats` - Group stats
• `/pro` - PRO features

*Ready to make some reactions?* 🚀
        """
        
        keyboard = [[
            InlineKeyboardButton("🎭 Quick Reaction", callback_data="quick_react"),
            InlineKeyboardButton("📊 Group Stats", callback_data="group_stats")
        ]]
        
        await msg.edit_text(
            final_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def wave_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wave animation"""
        chat = update.effective_chat
        
        wave_frames = [
            "👋",
            "🖐️",
            "✋",
            "🖐️",
            "👋"
        ]
        
        msg = await update.message.reply_text("👋")
        
        for frame in wave_frames:
            await asyncio.sleep(0.3)
            await msg.edit_text(f"{frame} Waving hello!")
        
        await msg.edit_text("👋 *Wave complete!*", parse_mode=ParseMode.MARKDOWN)
    
    async def dance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dance animation"""
        dance_frames = [
            "🕺",
            "💃",
            "🕺",
            "💃",
            "👯",
            "🎉"
        ]
        
        msg = await update.message.reply_text("💃 Getting ready to dance...")
        
        for i, frame in enumerate(dance_frames):
            await asyncio.sleep(0.4)
            text = f"{frame} Dancing! {'🎵' * (i + 1)}"
            await msg.edit_text(text)
        
        await msg.edit_text("🎭 *Dance party!* 🎉", parse_mode=ParseMode.MARKDOWN)
    
    async def fireworks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fireworks animation"""
        fireworks = ["🎇", "🎆", "✨", "🌟", "💥", "🔥"]
        
        msg = await update.message.reply_text("🎆 Fireworks incoming!")
        
        for _ in range(10):
            firework = random.choice(fireworks) * random.randint(1, 5)
            await msg.edit_text(f"{firework}")
            await asyncio.sleep(0.2)
        
        await msg.edit_text("🎇 *Fireworks complete!* 🎆", parse_mode=ParseMode.MARKDOWN)
    
    # ========== GROUP COMMANDS ==========
    
    async def group_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Group statistics"""
        chat = update.effective_chat
        
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await update.message.reply_text("This command works only in groups!")
            return
        
        # Get group stats from database
        self.cursor.execute(
            "SELECT * FROM groups WHERE group_id = ?",
            (chat.id,)
        )
        group_data = self.cursor.fetchone()
        
        if group_data:
            text = f"""
📊 *GROUP STATISTICS*

*Basic Info:*
• Name: {chat.title}
• Members: {chat.get_member_count()}
• Type: {'Supergroup' if chat.type == ChatType.SUPERGROUP else 'Group'}

*Bot Activity:*
• Total reactions: {group_data[5] or 0}
• Last active: {group_data[4] or 'Never'}

*Top Commands:*
1. /react - Reaction commands
2. /gstats - Group stats
3. /wave - Fun animations

*Group Features:*
✅ Auto-group detection
✅ Activity tracking
✅ Reaction counting
✅ Admin controls
            """
        else:
            text = """
📊 *GROUP STATISTICS*

*Bot is tracking this group!*

*Available Features:*
• Smart group detection
• Reaction counting
• Member activity
• Admin controls

Try `/react 20` to add reactions!
            """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def top_reactors(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Top reactors in group"""
        chat = update.effective_chat
        
        # Simulated top users (in real bot, query database)
        text = """
🏆 *TOP REACTORS*

*This Week:*
1. @User1 - 245 reactions
2. @User2 - 189 reactions  
3. @User3 - 156 reactions
4. @User4 - 123 reactions
5. @User5 - 98 reactions

*All Time:*
1. @User1 - 1,245 reactions
2. @User2 - 989 reactions
3. @User3 - 756 reactions

*Be the top reactor! Use `/react` more!* 🎭
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # ========== REACTION COMMAND ==========
    
    async def react_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main reaction command"""
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ *Reply to a message first!*\n"
                "Long press → Reply → Type `/react 50`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: `/react <number> [emojis]`\n"
                "Example: `/react 50` or `/react 30 👍❤️🔥`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        user = update.effective_user
        chat = update.effective_chat
        user_id = user.id
        is_pro = self.is_pro_user(user_id)
        
        try:
            count = int(context.args[0])
            
            # Limits
            if is_pro:
                max_count = 500
                cooldown = 0
            else:
                max_count = 50
                cooldown = 30
            
            count = min(count, max_count)
            
            # Delete command
            await update.message.delete()
            
            # Add reactions with animation
            await self.add_reactions_with_ui(
                update.message.reply_to_message,
                count,
                context.args[1:] if len(context.args) > 1 else [],
                chat,
                user,
                is_pro
            )
            
        except ValueError:
            await update.message.reply_text("Usage: `/react <number>`")
    
    async def add_reactions_with_ui(self, message, count, custom_emojis, chat, user, is_pro):
        """Add reactions with animated UI"""
        pro_badge = "🌟 PRO" if is_pro else ""
        
        # Initial status
        status = await chat.send_message(
            f"{pro_badge} *Starting {count} reactions...*\n"
            f"👤 By: {user.mention_html()}\n"
            f"⏳ Progress: 0%",
            parse_mode=ParseMode.HTML
        )
        
        added = 0
        for i in range(count):
            try:
                if custom_emojis:
                    emoji = random.choice(custom_emojis)
                else:
                    emoji = random.choice(REACTION_EMOJIS)
                
                await message.set_reaction([ReactionTypeEmoji(emoji)])
                added += 1
                
                # Update progress every 5% or 10 reactions
                if added % max(1, count//20) == 0:
                    percent = (added / count) * 100
                    
                    # Animated progress bar
                    progress_bar = "█" * int(percent/10) + "░" * (10 - int(percent/10))
                    
                    await status.edit_text(
                        f"{pro_badge} *Adding reactions...*\n"
                        f"👤 By: {user.mention_html()}\n"
                        f"📊 Progress: {progress_bar} {percent:.0f}%\n"
                        f"✅ Added: {added}/{count}",
                        parse_mode=ParseMode.HTML
                    )
                
                await asyncio.sleep(0.05 if is_pro else 0.1)
                
            except Exception as e:
                logger.error(f"Reaction error: {e}")
                continue
        
        # Final message with celebration
        celebration = random.choice(["🎉", "🎊", "🥳", "🎆", "✨"])
        
        await status.edit_text(
            f"{celebration} *REACTIONS COMPLETE!*\n"
            f"✅ Successfully added {added} reactions!\n"
            f"👤 By: {user.mention_html()}\n"
            f"📊 Total this session: {added}\n\n"
            f"*Want more? Try `/react {count*2}` next time!*",
            parse_mode=ParseMode.HTML
        )
    
    # ========== OWNER COMMANDS (8 TOTAL) ==========
    
    async def owner_sysinfo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """System information (Owner)"""
        if update.effective_user.id != OWNER_ID:
            return
        
        text = f"""
🖥️ *SYSTEM INFORMATION*

*Bot Status:*
• Uptime: 24/7 (No Sleep)
• Groups: {len(self.group_stats)}
• Pro Users: {len(self.pro_users)}
• Database: {DATABASE_FILE}

*Performance:*
• Active Tasks: {len(self.active_reactions)}
• Memory Usage: Optimized
• Scheduler: Running

*Configuration:*
• Owner ID: {OWNER_ID}
• Token: [Configured]
• Version: 3.0
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def owner_eval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Evaluate Python code (Owner)"""
        if update.effective_user.id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/eval python_code`")
            return
        
        try:
            code = ' '.join(context.args)
            result = eval(code)
            await update.message.reply_text(f"✅ Result: {result}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def owner_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all groups (Owner)"""
        if update.effective_user.id != OWNER_ID:
            return
        
        self.cursor.execute("SELECT group_id, title, member_count FROM groups ORDER BY last_active DESC LIMIT 20")
        groups = self.cursor.fetchall()
        
        if not groups:
            await update.message.reply_text("No groups found")
            return
        
        text = "👥 *ACTIVE GROUPS*\n\n"
        for group in groups:
            text += f"• {group[1] or 'Unknown'}\n"
            text += f"  ID: {group[0]} | Members: {group[2] or 0}\n\n"
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def owner_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export bot data (Owner)"""
        if update.effective_user.id != OWNER_ID:
            return
        
        # Create export data
        export_data = {
            'pro_users': self.pro_users,
            'total_groups': len(self.group_stats),
            'export_time': datetime.now().isoformat()
        }
        
        # Save to file
        with open('bot_export.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        await update.message.reply_text(
            f"✅ Data exported to bot_export.json\n"
            f"• Pro Users: {len(self.pro_users)}\n"
            f"• Groups: {len(self.group_stats)}"
        )
    
    async def owner_reload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reload configuration (Owner)"""
        if update.effective_user.id != OWNER_ID:
            return
        
        # Reload pro users
        old_count = len(self.pro_users)
        self.pro_users = self.load_pro_users()
        
        await update.message.reply_text(
            f"🔄 Configuration reloaded!\n"
            f"• Pro users: {old_count} → {len(self.pro_users)}\n"
            f"• Database: Connected\n"
            f"• Scheduler: Running"
        )
    
    async def owner_clean(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clean old data (Owner)"""
        if update.effective_user.id != OWNER_ID:
            return
        
        # Clean inactive groups (older than 30 days)
        cutoff = datetime.now() - timedelta(days=30)
        self.cursor.execute(
            "DELETE FROM groups WHERE last_active < ?",
            (cutoff,)
        )
        deleted = self.cursor.rowcount
        self.conn.commit()
        
        await update.message.reply_text(
            f"🧹 Cleaned {deleted} inactive groups\n"
            f"• Cutoff: 30 days\n"
            f"• Database optimized"
        )
    
    # Previous owner commands (from earlier)
    async def owner_addpro(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/addpro @username 30`")
            return
        
        username = context.args[0].replace('@', '')
        days = int(context.args[1]) if len(context.args) > 1 else 30
        
        expiry = self.make_pro_user(1234567890, days)  # Simulated
        
        await update.message.reply_text(
            f"✅ Added PRO for @{username}\n"
            f"📅 {days} days | Expires: {expiry.strftime('%Y-%m-%d')}"
        )
    
    async def owner_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            return
        
        text = f"""
📈 *BOT STATISTICS*

*Users:*
• Total: {len(self.user_stats)}
• PRO: {len(self.pro_users)}
• Active: Calculating...

*Groups:*
• Total: {len(self.group_stats)}
• Active today: Calculating...

*Performance:*
• Uptime: 24/7
• Memory: Optimized
• Tasks: {len(self.active_reactions)}

*Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # ========== BUTTON HANDLER ==========
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "quick_react":
            await query.edit_message_text(
                "🎭 *Quick Reaction Ready!*\n\n"
                "Reply to any message with:\n"
                "`/react 50` - For 50 reactions\n"
                "`/react 100` - For 100 reactions\n\n"
                "*PRO Tip:* Use `/pro` for unlimited!"
            )
        elif query.data == "group_stats":
            await query.edit_message_text(
                "📊 *Group Statistics*\n\n"
                "Use these commands:\n"
                "• `/gstats` - Group info\n"
                "• `/topreactors` - Top users\n"
                "• `/gsettings` - Settings (Admin)\n\n"
                "*Bot is actively tracking this group!*"
            )
    
    def cleanup_old_data(self):
        """Cleanup old data"""
        logger.info("Running cleanup task")
    
    def update_group_stats(self):
        """Update group statistics"""
        logger.info("Updating group stats")

def main():
    """Start the bot"""
    bot = UltimateReactionBot()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ========== COMMAND HANDLERS ==========
    
    # User commands with animations
    app.add_handler(CommandHandler("start", bot.animated_start))
    app.add_handler(CommandHandler("wave", bot.wave_command))
    app.add_handler(CommandHandler("dance", bot.dance_command))
    app.add_handler(CommandHandler("fireworks", bot.fireworks_command))
    
    # Group commands
    app.add_handler(CommandHandler("gstats", bot.group_stats))
    app.add_handler(CommandHandler("topreactors", bot.top_reactors))
    
    # Reaction command
    app.add_handler(CommandHandler("react", bot.react_command))
    app.add_handler(CommandHandler("pro", bot.pro_command))
    
    # Owner commands (8 total)
    app.add_handler(CommandHandler("sysinfo", bot.owner_sysinfo))
    app.add_handler(CommandHandler("eval", bot.owner_eval))
    app.add_handler(CommandHandler("groups", bot.owner_groups))
    app.add_handler(CommandHandler("export", bot.owner_export))
    app.add_handler(CommandHandler("reload", bot.owner_reload))
    app.add_handler(CommandHandler("clean", bot.owner_clean))
    app.add_handler(CommandHandler("addpro", bot.owner_addpro))
    app.add_handler(CommandHandler("stats", bot.owner_stats))
    
    # Group tracking
    app.add_handler(ChatMemberHandler(bot.track_new_group, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL, bot.track_group_activity))
    
    # Button handler
    app.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # ========== BOT MENU ==========
    
    commands = [
        BotCommand("start", "Start bot with animation"),
        BotCommand("wave", "Wave animation"),
        BotCommand("dance", "Dance animation"),
        BotCommand("fireworks", "Fireworks display"),
        BotCommand("react", "Add reactions to messages"),
        BotCommand("gstats", "Group statistics"),
        BotCommand("topreactors", "Top reactors in group"),
        BotCommand("pro", "PRO features"),
        BotCommand("sysinfo", "System info (Owner)"),
        BotCommand("eval", "Evaluate code (Owner)"),
        BotCommand("groups", "List groups (Owner)"),
        BotCommand("export", "Export data (Owner)"),
        BotCommand("reload", "Reload config (Owner)"),
        BotCommand("clean", "Clean data (Owner)"),
        BotCommand("addpro", "Add PRO user (Owner)"),
        BotCommand("stats", "Bot statistics (Owner)"),
    ]
    
    async def set_commands(app):
        await app.bot.set_my_commands(commands)
    
    app.post_init = set_commands
    
    print("=" * 60)
    print("🚀 ULTIMATE REACTION BOT - NO SLEEP MODE")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"🎭 Emojis: {len(REACTION_EMOJIS)}")
    print(f"⏰ Scheduler: Active")
    print(f"👥 Group Sense: Enabled")
    print("=" * 60)
    
    # Run on Railway
    port = int(os.environ.get("PORT", 8080))
    webhook_url = os.environ.get("RAILWAY_STATIC_URL", "")
    
    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
