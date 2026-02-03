"""
👨‍👩‍👧‍👦 FAMILY COMMAND HANDLERS
Family tree, marriage, adoption, relationships
"""

import logging
from typing import Optional
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import F

from config import Config
from database import Database, image_gen
from utils.logger import log_to_channel
from utils.helpers import get_target_user, format_money

# Create router
family_router = Router()
logger = logging.getLogger(__name__)

@family_router.message(Command("start"))
async def cmd_start(message: Message, db: Database):
    """Start command with user registration"""
    try:
        user = message.from_user
        
        # Check if user exists
        existing = await db.get_user(user.id)
        if not existing:
            # Create new user
            user_data = await db.create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or ""
            )
            
            if user_data:
                # Log new user
                await log_to_channel(
                    message.bot,
                    f"👤 **NEW USER REGISTERED**\n"
                    f"ID: `{user.id}`\n"
                    f"Name: {user.first_name}\n"
                    f"Username: @{user.username or 'None'}\n"
                    f"Total Users: {await db.get_user_count()}"
                )
        
        # Welcome message
        welcome_text = f"""
👋 Welcome to <b>Family Tree Bot</b>, {user.first_name}!

🌳 <b>Build Your Legacy</b>
• Create a family dynasty
• Grow your farming empire  
• Build business wealth
• Trade stocks & crypto
• Battle in the arena

💰 <b>Get Started:</b>
• Use /daily for bonus money
• Check /help for all commands
• Add me to groups for family fun!

🎮 <b>New Features:</b>
• 💹 Crypto Trading
• 🏘️ Real Estate
• 💼 Job System
• ⚔️ Battle Arena
• 🎓 Education System
• 🚗 Vehicle Collection

📱 <b>Quick Commands:</b>
/me - Your profile
/family - Family tree
/garden - Your farm  
/bank - Banking system
"""
        
        # Add to group button (inline keyboard)
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="➕ Add to Group",
                        url=f"https://t.me/{(await message.bot.get_me()).username}?startgroup=true"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="📚 Help",
                        callback_data="help_menu"
                    ),
                    types.InlineKeyboardButton(
                        text="💰 Daily Bonus",
                        callback_data="daily_bonus"
                    )
                ]
            ]
        )
        
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command with all features"""
    help_text = """
🆘 <b>FAMILY TREE BOT - HELP</b>

👤 <b>PROFILE & ECONOMY:</b>
/me - Your profile card with image
/daily - Daily bonus ($500-$1500)
/balance - Check all balances
/leaderboard - Top players ranking
/achievements - Your achievements

👨‍👩‍👧‍👦 <b>FAMILY SYSTEM:</b>
/family - View your family tree
/adopt - Adopt someone as child (reply)
/marry - Marry someone (reply)  
/divorce - End marriage (reply)
/friends - View friends list
/friend @user - Add friend

🌾 <b>FARMING SYSTEM:</b>
/garden - Your garden with image
/crops - Available crops list
/plant [crop] [qty] - Plant crops
/harvest - Harvest ready crops
/barn - Crop storage
/sell [crop] [qty] - Sell crops

💰 <b>ECONOMY SYSTEM:</b>
/bank - Banking system
/deposit [amount] - Deposit to bank
/withdraw [amount] - Withdraw from bank
/interest - Collect daily interest
/statement - Transaction history

💹 <b>INVESTMENT SYSTEM:</b>
/stocks - Stock market prices
/buystock [symbol] [qty] - Buy stocks
/sellstock [symbol] [qty] - Sell stocks
/portfolio - Your investments
/crypto - Cryptocurrency prices
/buycrypto [coin] [amount] - Buy crypto

🏢 <b>BUSINESS SYSTEM:</b>
/business - Your businesses
/buybusiness [type] - Buy business
/collect - Collect business income
/upgradebusiness - Upgrade business

🏘️ <b>NEW: REAL ESTATE:</b>
/properties - Your properties
/buyproperty [type] - Buy property
/rent - Collect rent income
/upgradeproperty - Upgrade property

💼 <b>NEW: JOB SYSTEM:</b>
/jobs - Available jobs
/work - Start work shift
/career - Career progress
/promotion - Request promotion

⚔️ <b>NEW: BATTLE ARENA:</b>
/arena - Battle arena info
/fight @user - Challenge to battle
/train - Training session
/rankings - Battle rankings

🎮 <b>GAMES & FUN:</b>
/lottery - Lottery system
/scratch [id] - Scratch ticket
/slot [bet] - Slot machine
/dice [bet] - Dice game
/blackjack [bet] - Blackjack
/race [bet] - Horse racing

😊 <b>REACTIONS (reply to user):</b>
/hug, /kiss, /slap, /pat
/punch, /cuddle, /rob, /kill

👑 <b>ADMIN COMMANDS:</b>
/admin - Admin panel
/stats - Bot statistics
/cat - GIF management

📱 <b>Need help? Contact support!</b>
"""
    
    await message.answer(help_text, parse_mode="HTML")

@family_router.message(Command("me"))
async def cmd_me(message: Message, db: Database):
    """User profile with image"""
    try:
        user_data = await db.get_user(message.from_user.id)
        if not user_data:
            await message.answer("❌ Please use /start first!")
            return
        
        # Get user achievements
        achievements = await db.get_achievements(message.from_user.id)
        
        # Get additional data
        family = await db.get_family(message.from_user.id)
        garden = await db.get_garden(message.from_user.id)
        plants = await db.get_plants(message.from_user.id)
        
        # Create profile image
        image_bytes = image_gen.create_profile_card(user_data, achievements)
        
        # Calculate total wealth
        total_wealth = user_data.get('cash', 0) + user_data.get('bank_balance', 0)
        
        caption = f"""
👤 <b>{user_data['first_name']}'s Profile</b>

💰 <b>Wealth Summary:</b>
• Cash: ${user_data.get('cash', 0):,}
• Bank: ${user_data.get('bank_balance', 0):,}
• <b>Total: ${total_wealth:,}</b>

📊 <b>Stats:</b>
• Level: {user_data.get('level', 1)}
• XP: {user_data.get('xp', 0)}/{(user_data.get('level', 1) * 1000)}
• Reputation: {user_data.get('reputation', 100)}
• Daily Streak: {user_data.get('daily_streak', 0)} days

👨‍👩‍👧‍👦 <b>Family:</b> {len(family)} members
🌾 <b>Garden:</b> {len(plants)} crops growing
🏆 <b>Achievements:</b> {sum(1 for a in achievements if a.get('unlocked'))}/{len(achievements)}

💡 Use /help for all commands
"""
        
        if image_bytes:
            try:
                from aiogram.types import BufferedInputFile
                photo = BufferedInputFile(image_bytes, filename="profile.png")
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Photo send error: {e}")
                await message.answer(caption, parse_mode="HTML")
        else:
            await message.answer(caption, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Me command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("family"))
async def cmd_family(message: Message, db: Database):
    """Family tree command"""
    try:
        user_data = await db.get_user(message.from_user.id)
        if not user_data:
            await message.answer("❌ Please use /start first!")
            return
        
        family = await db.get_family(message.from_user.id)
        
        if not family:
            response = """
🌳 <b>Your Family Tree</b>

└─ You (Just starting!)

💡 <b>How to grow your family:</b>
• Reply to someone with /adopt to make them your child
• Reply with /marry to get married
• Use /friend @username to add friends

👑 <b>Benefits:</b>
• Daily bonus increases per family member
• Family quests and events
• Inheritance system
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        # Build family tree
        tree_text = f"🌳 <b>Family Tree of {user_data['first_name']}</b>\n\n"
        tree_text += f"└─ {user_data['first_name']} (You)\n"
        
        for member in family:
            emoji = "💑" if member['relation'] == "spouse" else "👶" if member['relation'] == "child" else "👴"
            tree_text += f"   ├─ {emoji} {member['first_name']} ({member['relation']})\n"
        
        stats_text = f"""
📊 <b>Family Stats:</b>
• Members: {len(family)}
• Daily Bonus: +${len(family) * Config.FAMILY_DAILY_BONUS}

💡 <b>Commands:</b>
• /adopt - Make someone your child
• /marry - Marry someone
• /divorce - End marriage
• /friend @username - Add friend
"""
        
        await message.answer(tree_text + stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Family command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("adopt"))
async def cmd_adopt(message: Message, db: Database):
    """Adopt someone as child"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer("❌ Please reply to someone's message to adopt them!")
            return
        
        if target.id == message.from_user.id:
            await message.answer("❌ You cannot adopt yourself!")
            return
        
        if target.is_bot:
            await message.answer("❌ Cannot adopt bots!")
            return
        
        # Get users
        user = await db.get_user(message.from_user.id)
        target_user = await db.get_user(target.id)
        
        if not user or not target_user:
            await message.answer("❌ Both users need to use /start first!")
            return
        
        # Add relation
        success = await db.add_family_member(message.from_user.id, target.id, "child")
        
        if not success:
            await message.answer("❌ Error creating family relationship!")
            return
        
        # Give adoption bonuses
        await db.update_currency(message.from_user.id, "cash", Config.ADOPT_BONUS)
        await db.update_currency(target.id, "cash", Config.ADOPT_BONUS // 2)
        
        # Get updated family count
        family = await db.get_family(message.from_user.id)
        
        response = f"""
✅ <b>ADOPTION SUCCESSFUL!</b>

👤 You adopted <b>{target.first_name}</b>
🤝 Relationship: Parent-Child
💰 Bonus: ${Config.ADOPT_BONUS:,} for you, ${Config.ADOPT_BONUS // 2:,} for {target.first_name}

👨‍👩‍👧‍👦 Your family now has {len(family)} members
💡 Daily bonus increased!
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log adoption
        await log_to_channel(
            message.bot,
            f"👶 **ADOPTION**\n"
            f"Parent: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Child: {target.first_name} ({target.id})\n"
            f"Family size: {len(family)}"
        )
        
    except Exception as e:
        logger.error(f"Adopt command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("marry"))
async def cmd_marry(message: Message, db: Database):
    """Marry someone"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer("❌ Please reply to someone's message to marry them!")
            return
        
        if target.id == message.from_user.id:
            await message.answer("❌ You cannot marry yourself!")
            return
        
        # Get users
        user = await db.get_user(message.from_user.id)
        target_user = await db.get_user(target.id)
        
        if not user or not target_user:
            await message.answer("❌ Both users need to use /start first!")
            return
        
        # Add relation
        success = await db.add_family_member(message.from_user.id, target.id, "spouse")
        
        if not success:
            await message.answer("❌ Error creating marriage!")
            return
        
        # Give marriage bonuses
        await db.update_currency(message.from_user.id, "cash", Config.MARRY_BONUS)
        await db.update_currency(target.id, "cash", Config.MARRY_BONUS)
        
        response = f"""
💍 <b>MARRIAGE SUCCESSFUL!</b>

👤 You married <b>{target.first_name}</b>
🤝 Relationship: Spouses
💰 Gift: ${Config.MARRY_BONUS:,} each

🎉 <b>Congratulations on your wedding!</b>

💡 Now you can build your family together!
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log marriage
        await log_to_channel(
            message.bot,
            f"💍 **MARRIAGE**\n"
            f"Spouse 1: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Spouse 2: {target.first_name} ({target.id})\n"
            f"Bonus: ${Config.MARRY_BONUS:,} each"
        )
        
    except Exception as e:
        logger.error(f"Marry command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("divorce"))
async def cmd_divorce(message: Message, db: Database):
    """Divorce spouse"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer("❌ Reply to someone's message to divorce them!")
            return
        
        user = await db.get_user(message.from_user.id)
        target_user = await db.get_user(target.id)
        
        if not user or not target_user:
            await message.answer("❌ Both users need to use /start first!")
            return
        
        # Remove marriage
        await db.execute(
            """DELETE FROM family 
               WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
               AND relation = 'spouse'""",
            (message.from_user.id, target.id, target.id, message.from_user.id)
        )
        
        response = f"""
💔 <b>DIVORCE COMPLETE</b>

You are no longer married to {target.first_name}.

Relationship ended.
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log divorce
        await log_to_channel(
            message.bot,
            f"💔 **DIVORCE**\n"
            f"Spouse 1: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Spouse 2: {target.first_name} ({target.id})"
        )
        
    except Exception as e:
        logger.error(f"Divorce command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("daily"))
async def cmd_daily(message: Message, db: Database):
    """Daily bonus command"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        # Check cooldown
        from utils.helpers import check_cooldown
        can_use, remaining = await check_cooldown(message.from_user.id, "daily", 86400, db)
        
        if not can_use:
            from utils.helpers import format_time
            await message.answer(f"⏳ Come back in {format_time(remaining)}!")
            return
        
        # Calculate bonus
        import random
        base_bonus = random.randint(Config.DAILY_MIN, Config.DAILY_MAX)
        family = await db.get_family(message.from_user.id)
        family_bonus = len(family) * Config.FAMILY_DAILY_BONUS
        
        streak = user.get('daily_streak', 0) + 1
        streak_bonus = min(500, streak * 50)
        
        # Bio verification bonus
        bio_multiplier = 2 if user.get('bio_verified') else 1
        
        total_bonus = (base_bonus + family_bonus + streak_bonus) * bio_multiplier
        
        # Give bonus
        await db.update_currency(message.from_user.id, "cash", total_bonus)
        
        # Update streak
        await db.execute(
            """UPDATE users 
               SET daily_streak = ?, last_daily = CURRENT_TIMESTAMP
               WHERE user_id = ?""",
            (streak, message.from_user.id)
        )
        
        # Set cooldown
        from utils.helpers import set_cooldown
        await set_cooldown(message.from_user.id, "daily", db)
        
        # Give random gemstone
        gemstones = ["💎 Diamond", "🔴 Ruby", "🔵 Sapphire", "🟢 Emerald", "🟣 Amethyst"]
        gemstone = random.choice(gemstones)
        
        response = f"""
🎉 <b>DAILY BONUS COLLECTED!</b>

💰 <b>Breakdown:</b>
• Base Bonus: ${base_bonus:,}
• Family Bonus ({len(family)}): ${family_bonus:,}
• Streak Bonus ({streak} days): ${streak_bonus:,}
• Multiplier: {bio_multiplier}x

🎁 <b>Total: ${total_bonus:,}</b>

{gemstone} You found a {gemstone}!
💵 New Balance: ${user.get('cash', 0) + total_bonus:,}

{"✅ Bio verified (2x bonus!)" if bio_multiplier > 1 else "💡 Add me to bio for 2x bonus!"}
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log daily bonus
        await log_to_channel(
            message.bot,
            f"💰 **DAILY BONUS**\n"
            f"User: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Amount: ${total_bonus:,}\n"
            f"Streak: {streak} days"
        )
        
    except Exception as e:
        logger.error(f"Daily command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@family_router.message(Command("balance"))
async def cmd_balance(message: Message, db: Database):
    """Check balance"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        # Get portfolio value (simplified)
        stocks = await db.fetch_all(
            "SELECT SUM(shares * avg_price) as value FROM stocks WHERE user_id = ?",
            (message.from_user.id,)
        )
        stock_value = stocks[0]['value'] if stocks and stocks[0]['value'] else 0
        
        total_wealth = user.get('cash', 0) + user.get('bank_balance', 0) + stock_value
        
        response = f"""
💰 <b>BALANCE SUMMARY</b>

💵 <b>Cash:</b> ${user.get('cash', 0):,}
🏦 <b>Bank:</b> ${user.get('bank_balance', 0):,}
📈 <b>Investments:</b> ${stock_value:,.2f}

🏆 <b>Total Wealth:</b> ${total_wealth:,}

💡 Use /bank to manage money
💹 Use /portfolio for investments
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Balance command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

# Reaction commands
reaction_commands = ["hug", "kiss", "slap", "pat", "punch", "cuddle", "rob", "kill"]

for cmd in reaction_commands:
    @family_router.message(Command(cmd))
    async def reaction_command(message: Message, db: Database, command: str = cmd):
        """Handle reaction commands"""
        try:
            target = get_target_user(message)
            
            if not target:
                await message.answer(f"❌ Please reply to someone to {command} them!")
                return
            
            # Get GIF from database
            gif_url = await db.get_random_gif(command)
            
            if not gif_url:
                # Fallback GIFs
                fallback_gifs = {
                    "hug": "https://files.catbox.moe/34u6a1.gif",
                    "kiss": "https://files.catbox.moe/zu3p40.gif",
                    "slap": "https://files.catbox.moe/8x5f6d.gif",
                    "pat": "https://files.catbox.moe/9k7j2v.gif",
                    "punch": "https://files.catbox.moe/l2m5n8.gif",
                    "cuddle": "https://files.catbox.moe/r4t9y1.gif",
                    "rob": "https://files.catbox.moe/1x4z9u.gif",
                    "kill": "https://files.catbox.moe/p6og82.gif"
                }
                gif_url = fallback_gifs.get(command)
            
            actions = {
                "hug": "hugged",
                "kiss": "kissed", 
                "slap": "slapped",
                "pat": "patted",
                "punch": "punched",
                "cuddle": "cuddled",
                "rob": "robbed",
                "kill": "killed"
            }
            
            action = actions.get(command, "interacted with")
            
            caption = f"🤗 {message.from_user.first_name} {action} {target.first_name}!"
            
            try:
                await message.bot.send_animation(
                    chat_id=message.chat.id,
                    animation=gif_url,
                    caption=caption
                )
            except Exception as e:
                logger.error(f"GIF send error: {e}")
                await message.answer(caption)
                
        except Exception as e:
            logger.error(f"Reaction command {command} error: {e}")
            await message.answer("❌ An error occurred. Please try again.")

# Add dependency injection
from aiogram import Dispatcher
def setup_family_handlers(dp: Dispatcher, db: Database):
    """Setup family handlers with dependencies"""
    # This function would be called from main.py
    pass
