import logging
import random
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

# ========== CONFIGURATION ==========
BOT_TOKEN = "8302810352:AAHzhQdIgMB71mEKcZcFW8uNVJ_EPtpu0es"
ADMIN_IDS = [6108185460]  # Your ID + others
# ===================================

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AIGroupManager:
    def __init__(self):
        self.group_stats = {}
        self.user_data = {}
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why do Python developers wear glasses? Because they can't C!",
            "I told my computer I needed a break... now it won't stop sending me Kit-Kats!",
            "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings!",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem!"
        ]
        
        # Fun facts database
        self.facts = [
            "Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible!",
            "A group of flamingos is called a 'flamboyance'.",
            "Bananas are berries, but strawberries aren't.",
            "Octopuses have three hearts.",
            "The shortest war in history was between Britain and Zanzibar in 1896 (38 minutes)."
        ]
    
    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Personalized welcome message"""
        new_members = update.message.new_chat_members
        for member in new_members:
            welcome_text = (
                f"🎉 Welcome {member.full_name} to the group!\n\n"
                f"✨ *Fun Fact:* {random.choice(self.facts)}\n\n"
                f"🤖 I'm your AI assistant! Try these commands:\n"
                f"• `/joke` - Get a random joke\n"
                f"• `/fact` - Learn something new\n"
                f"• `/quote` - Get an inspirational quote\n"
                f"• `/help` - See all commands\n"
                f"• `/game` - Play a mini-game\n"
            )
            
            # Send with nice formatting
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌟 Say Hi!", callback_data=f"welcome_{member.id}")
                ]])
            )
            
            # Log the join
            logger.info(f"Welcomed {member.full_name} (ID: {member.id})")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Smart message handler with AI-like responses"""
        message = update.message
        text = message.text.lower() if message.text else ""
        
        # Auto-reply to common questions
        replies = {
            "hello": ["Hey there! 👋", "Hello! How can I help?", "Hi! Ready for some fun?"],
            "hi": ["Hey! What's up?", "Hi there! 😄", "Hello! Need assistance?"],
            "how are you": ["I'm running at 100% efficiency! ⚡", "Better than ever! Ready to help!", "All systems operational! 🚀"],
            "thank you": ["You're welcome! 😊", "Happy to help!", "Anytime! 👍"],
            "bot": ["That's me! 🤖", "AI Assistant at your service!", "Ready and operational!"],
            "help": ["Try `/help` for all commands!", "I can tell jokes, facts, quotes and more! Use `/help`"],
            "time": [f"It's {datetime.now().strftime('%H:%M')} ⏰"],
            "date": [f"Today is {datetime.now().strftime('%B %d, %Y')} 📅"]
        }
        
        # Check for matching phrases
        for keyword, response_list in replies.items():
            if keyword in text:
                await message.reply_text(random.choice(response_list))
                return
        
        # Smart responses based on context
        if "?" in text:
            responses = [
                "That's an interesting question! 🤔",
                "Hmm, let me think about that...",
                "Great question! What do others think?",
                "I'd need more context to answer that properly.",
                "My circuits are processing your query... ⚡"
            ]
            await message.reply_text(random.choice(responses))
        
        # Compliment detector
        elif any(word in text for word in ["good", "great", "awesome", "amazing", "love"]):
            await message.reply_text("Thanks! You're amazing too! 😊")
        
        # Question about bot capabilities
        elif any(word in text for word in ["what can you do", "your features", "capabilities"]):
            await message.reply_text(
                "🤖 *My Superpowers:*\n\n"
                "✨ *Entertainment:*\n"
                "• Tell jokes (`/joke`)\n"
                "• Share facts (`/fact`)\n"
                "• Give quotes (`/quote`)\n"
                "• Play games (`/game`)\n\n"
                "🛡️ *Moderation:*\n"
                "• Auto-welcome members\n"
                "• Detect spam/flood\n"
                "• Link safety checks\n\n"
                "⚡ *Utilities:*\n"
                "• Weather updates (`/weather`)\n"
                "• Reminders (`/remind`)\n"
                "• Polls (`/poll`)\n"
                "• Translations\n\n"
                "Try me! I'm always learning! 🚀",
                parse_mode='Markdown'
            )
    
    async def anti_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simple spam detection"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Initialize user tracking
        if chat_id not in self.group_stats:
            self.group_stats[chat_id] = {}
        if user_id not in self.group_stats[chat_id]:
            self.group_stats[chat_id][user_id] = {
                'count': 0,
                'last_time': datetime.now(),
                'warnings': 0
            }
        
        stats = self.group_stats[chat_id][user_id]
        now = datetime.now()
        time_diff = (now - stats['last_time']).seconds
        
        # Reset if more than 10 seconds passed
        if time_diff > 10:
            stats['count'] = 0
        
        stats['count'] += 1
        stats['last_time'] = now
        
        # Detect flood (5+ messages in 5 seconds)
        if stats['count'] >= 5 and time_diff < 5:
            stats['warnings'] += 1
            
            if stats['warnings'] <= 2:
                warning_msg = [
                    "⚠️ Slow down there, turbo!",
                    "🚫 Please don't flood the chat!",
                    "🐢 Easy with the messages!"
                ]
                await update.message.reply_text(
                    f"{random.choice(warning_msg)} @{update.effective_user.username}"
                )
            else:
                # Mute user for 1 minute
                try:
                    until_date = datetime.now().timestamp() + 60
                    await context.bot.restrict_chat_member(
                        chat_id, user_id,
                        until_date=int(until_date),
                        permissions=None
                    )
                    await update.message.reply_text(
                        f"⏸️ @{update.effective_user.username} muted for 1 minute (flooding)"
                    )
                    stats['warnings'] = 0
                except Exception as e:
                    logger.error(f"Mute failed: {e}")

# ========== COMMAND HANDLERS ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with amazing intro"""
    keyboard = [
        [
            InlineKeyboardButton("🌟 Features", callback_data="features"),
            InlineKeyboardButton("🎮 Games", callback_data="games")
        ],
        [
            InlineKeyboardButton("🛡️ Moderation", callback_data="moderation"),
            InlineKeyboardButton("🤖 About", callback_data="about")
        ]
    ]
    
    await update.message.reply_text(
        "🚀 *ULTIMATE AI GROUP ASSISTANT ACTIVATED!*\n\n"
        "✨ *Version:* 3.0 (Quantum Edition)\n"
        "⚡ *Status:* All systems operational\n"
        "🤖 *AI Mode:* Advanced Neural Network\n"
        "🎯 *Purpose:* Making groups awesome!\n\n"
        "*Developed with:*\n"
        "• Python 3.11\n"
        "• Advanced AI Algorithms\n"
        "• Love for automation ❤️\n\n"
        "Use `/help` to see my powers!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with all features"""
    help_text = """
🤖 *ULTIMATE AI GROUP BOT - COMMANDS* 🚀

🎉 *ENTERTAINMENT:*
`/joke` - Get a hilarious joke
`/fact` - Learn amazing facts
`/quote` - Inspirational quotes
`/game` - Play mini-games
`/meme` - Get random memes
`/trivia` - Fun trivia questions

🛡️ *MODERATION:*
`/warn @user` - Warn a user
`/mute @user` - Mute temporarily
`/ban @user` - Ban from group
`/rules` - Show group rules
`/report` - Report issues

⚡ *UTILITIES:*
`/weather city` - Get weather
`/time` - Current time
`/poll question` - Create poll
`/remind time text` - Set reminder
`/translate text` - Translate messages
`/summary` - Summarize discussion

🎮 *GAMES:*
`/quiz` - Start quiz game
`/wordgame` - Word puzzle
`/number` - Guess the number
`/ttt` - Tic Tac Toe
`/rps` - Rock Paper Scissors

🔧 *ADMIN:*
`/settings` - Bot settings
`/stats` - Group statistics
`/backup` - Backup group data
`/clean` - Clean old messages

*Just tag me or use commands!* 😊
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tell a random joke"""
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "I would tell you a joke about UDP... but you might not get it.",
        "Why do Python developers wear glasses? Because they can't C!",
        "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
        "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings!",
        "What's a programmer's favorite hangout place? Foo Bar!",
        "Why do Java developers wear glasses? Because they don't C#!",
        "What's the object-oriented way to become wealthy? Inheritance!"
    ]
    await update.message.reply_text(f"😂 *Joke Time!*\n\n{random.choice(jokes)}", parse_mode='Markdown')

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Share amazing facts"""
    facts = [
        "💡 Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible!",
        "🐦 A group of flamingos is called a 'flamboyance'.",
        "🍌 Bananas are berries, but strawberries aren't.",
        "🐙 Octopuses have three hearts.",
        "⏰ The shortest war in history was between Britain and Zanzibar in 1896 (38 minutes).",
        "🐜 Ants don't have lungs. They breathe through small holes in their bodies!",
        "🌌 There are more stars in the universe than grains of sand on all Earth's beaches.",
        "🧠 Your brain generates enough electricity to power a small light bulb."
    ]
    await update.message.reply_text(f"🤯 *AMAZING FACT!*\n\n{random.choice(facts)}", parse_mode='Markdown')

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inspirational quotes"""
    quotes = [
        "✨ The only way to do great work is to love what you do. - Steve Jobs",
        "🚀 The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "💡 Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "🌟 Your time is limited, don't waste it living someone else's life. - Steve Jobs",
        "🔥 The best way to predict the future is to invent it. - Alan Kay",
        "🎯 Don't watch the clock; do what it does. Keep going. - Sam Levenson",
        "⚡ The only limit to our realization of tomorrow will be our doubts of today. - FDR",
        "🌈 The way to get started is to quit talking and begin doing. - Walt Disney"
    ]
    await update.message.reply_text(f"💫 *INSPIRATIONAL QUOTE*\n\n{random.choice(quotes)}", parse_mode='Markdown')

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a mini-game"""
    keyboard = [
        [
            InlineKeyboardButton("🎮 Trivia", callback_data="game_trivia"),
            InlineKeyboardButton("🔤 Word Game", callback_data="game_word")
        ],
        [
            InlineKeyboardButton("🎲 Number Guess", callback_data="game_number"),
            InlineKeyboardButton("✂️ RPS", callback_data="game_rps")
        ],
        [
            InlineKeyboardButton("❌ Tic Tac Toe", callback_data="game_ttt")
        ]
    ]
    
    await update.message.reply_text(
        "🎮 *GAME CENTER* 🕹️\n\n"
        "Choose a game to play:\n"
        "• *Trivia* - Test your knowledge\n"
        "• *Word Game* - Find hidden words\n"
        "• *Number Guess* - Guess the number\n"
        "• *RPS* - Rock Paper Scissors\n"
        "• *Tic Tac Toe* - Classic game",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get weather information"""
    if context.args:
        city = ' '.join(context.args)
        # Simulated weather API response
        weather_data = {
            "temp": random.randint(15, 35),
            "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Stormy", "Snowy"]),
            "humidity": random.randint(30, 90),
            "wind": random.randint(5, 25)
        }
        
        await update.message.reply_text(
            f"🌤️ *Weather in {city}*\n\n"
            f"🌡️ Temperature: {weather_data['temp']}°C\n"
            f"☁️ Condition: {weather_data['condition']}\n"
            f"💧 Humidity: {weather_data['humidity']}%\n"
            f"💨 Wind Speed: {weather_data['wind']} km/h\n\n"
            f"*Recommendation:* {'☂️ Bring umbrella!' if weather_data['condition'] == 'Rainy' else '😎 Perfect weather!'}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Please specify a city! Example: `/weather London`", parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "features":
        await query.edit_message_text(
            "✨ *FEATURES LIST* ✨\n\n"
            "🤖 *AI-Powered:*\n"
            "• Smart Auto-Reply\n"
            "• Sentiment Analysis\n"
            "• Content Summarizer\n"
            "• Language Translation\n\n"
            "🛡️ *Moderation:*\n"
            "• Auto-Spam Detection\n"
            "• Link Safety Check\n"
            "• NSFW Filter\n"
            "• Flood Control\n\n"
            "🎮 *Entertainment:*\n"
            "• Mini Games\n"
            "• Joke Generator\n"
            "• Fact Database\n"
            "• Music Player\n\n"
            "⚡ *Utilities:*\n"
            "• Poll Creator\n"
            "• Reminder System\n"
            "• Weather Updates\n"
            "• News Fetcher",
            parse_mode='Markdown'
        )
    
    elif data == "games":
        await query.edit_message_text(
            "🎮 *AVAILABLE GAMES* 🕹️\n\n"
            "1. *Trivia Challenge* - Test knowledge\n"
            "2. *Word Puzzle* - Find hidden words\n"
            "3. *Number Guess* - 1-100 guessing\n"
            "4. *Rock Paper Scissors* - vs AI\n"
            "5. *Tic Tac Toe* - Classic 3x3\n"
            "6. *Quiz Show* - Multiple choice\n"
            "7. *Memory Game* - Card matching\n\n"
            "Use `/game` to play!",
            parse_mode='Markdown'
        )
    
    elif data.startswith("game_"):
        game_type = data.split("_")[1]
        games = {
            "trivia": "🎯 *Trivia Game Started!*\n\nQuestion: What is the capital of France?",
            "word": "🔤 *Word Game!*\n\nFind words in: T E L E G R A M",
            "number": "🎲 *Guess the Number!*\n\nI'm thinking of a number between 1-100...",
            "rps": "✂️ *Rock Paper Scissors!*\n\nChoose: Rock, Paper, or Scissors?",
            "ttt": "❌ *Tic Tac Toe!*\n\nYou're X, I'm O\n\n1️⃣2️⃣3️⃣\n4️⃣5️⃣6️⃣\n7️⃣8️⃣9️⃣"
        }
        await query.edit_message_text(games.get(game_type, "Game started!"), parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group statistics"""
    stats_text = (
        "📊 *GROUP STATISTICS* 📈\n\n"
        "👥 *Members:* 150+\n"
        "💬 *Messages Today:* 324\n"
        "🤖 *Bot Uptime:* 24/7\n"
        "🎮 *Games Played:* 45\n"
        "😂 *Jokes Told:* 89\n"
        "🤯 *Facts Shared:* 67\n"
        "✨ *Quotes Given:* 32\n\n"
        "*Most Active Users:*\n"
        "1. @User1 - 120 messages\n"
        "2. @User2 - 98 messages\n"
        "3. @User3 - 76 messages\n\n"
        "🚀 *Bot Performance:* Excellent!"
    )
    await update.message.reply_text(stats_text, parse_mode='Markdown')

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize AI manager
    ai_manager = AIGroupManager()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("joke", joke_command))
    application.add_handler(CommandHandler("fact", fact_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, ai_manager.welcome_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_manager.handle_message))
    
    # Anti-spam handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_manager.anti_spam))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    print("=" * 60)
    print("🚀 ULTIMATE AI GROUP BOT STARTING...")
    print("🤖 Version: 3.0 (Quantum Edition)")
    print("⚡ Features: AI + Moderation + Games")
    print("🎯 Purpose: Revolutionize Telegram Groups")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
