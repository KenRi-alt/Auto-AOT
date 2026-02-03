# ============================================
# handlers/family.py - COMPLETE FIXED VERSION
# No emoji encoding issues
# ============================================

"""
FAMILY COMMAND HANDLERS
Complete with profile pictures and family tree images
"""

import logging
import random
from typing import Optional
from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram import Bot

from config import Config
from database import Database
from images import image_gen
from utils.logger import log_to_channel
from utils.helpers import get_target_user, format_money, format_time, check_cooldown, set_cooldown

# Create router
family_router = Router()
logger = logging.getLogger(__name__)

# Crop data
CROP_DATA = {
    "carrot": {"buy": 10, "sell": 15, "grow_time": 2, "emoji": "🥕", "xp": 5},
    "tomato": {"buy": 15, "sell": 22, "grow_time": 3, "emoji": "🍅", "xp": 8},
    "potato": {"buy": 8, "sell": 12, "grow_time": 2.5, "emoji": "🥔", "xp": 6},
    "eggplant": {"buy": 20, "sell": 30, "grow_time": 4, "emoji": "🍆", "xp": 12},
    "corn": {"buy": 12, "sell": 18, "grow_time": 5, "emoji": "🌽", "xp": 10},
    "pepper": {"buy": 25, "sell": 38, "grow_time": 6, "emoji": "🫑", "xp": 15},
    "watermelon": {"buy": 30, "sell": 45, "grow_time": 7, "emoji": "🍉", "xp": 18},
    "pumpkin": {"buy": 40, "sell": 60, "grow_time": 8, "emoji": "🎃", "xp": 20}
}

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
                    "**NEW USER REGISTERED**\n"
                    f"ID: `{user.id}`\n"
                    f"Name: {user.first_name}\n"
                    f"Username: @{user.username or 'None'}\n"
                    f"Total Users: {await db.get_user_count()}"
                )
        
        # Welcome message
        welcome_text = f"""
Welcome to **Family Tree Bot**, {user.first_name}!

**Build Your Legacy**
• Create a family dynasty
• Grow your farming empire  
• Build business wealth
• Trade stocks & crypto
• Battle in the arena

**Get Started:**
• Use /daily for bonus money
• Check /help for all commands
• Add me to groups for family fun!

**Quick Commands:**
/me - Your profile with photo
/family - Family tree
/garden - Your farm  
/bank - Banking system
/lottery - Try your luck
"""
        
        # Add to group button
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
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command with all features"""
    help_text = """
**FAMILY TREE BOT - HELP**

**PROFILE & ECONOMY:**
/me - Your profile card with photo
/daily - Daily bonus ($500-$1500)
/balance - Check all balances
/leaderboard - Top players ranking

**FAMILY SYSTEM:**
/family - View your family tree
/adopt - Adopt someone as child (reply)
/marry - Marry someone (reply)  
/divorce - End marriage (reply)

**FARMING SYSTEM:**
/garden - Your garden with image
/crops - Available crops list
/plant [crop] [qty] - Plant crops
/harvest - Harvest ready crops
/barn - Crop storage
/sell [crop] [qty] - Sell crops

**ECONOMY SYSTEM:**
/bank - Banking system
/deposit [amount] - Deposit to bank
/withdraw [amount] - Withdraw from bank
/interest - Collect daily interest
/statement - Transaction history

**INVESTMENT SYSTEM:**
/stocks - Stock market prices
/buystock [symbol] [qty] - Buy stocks
/sellstock [symbol] [qty] - Sell stocks
/portfolio - Your investments

**BUSINESS SYSTEM:**
/business - Your businesses
/buybusiness [type] - Buy business
/collect - Collect business income

**GAMES & FUN:**
/lottery - Lottery system
/scratch [id] - Scratch ticket
/slot [bet] - Slot machine
/dice [bet] - Dice game
/blackjack [bet] - Blackjack

**REACTIONS (reply to user):**
/hug, /kiss, /slap, /pat
/punch, /cuddle, /rob, /kill

**ADMIN COMMANDS:**
/admin - Admin panel (owner only)
/stats - Bot statistics
/cat - GIF management

**Need help? Contact support!**
"""
    
    await message.answer(help_text, parse_mode="HTML")

@family_router.message(Command("me"))
async def cmd_me(message: Message, db: Database, bot: Bot):
    """User profile with profile picture"""
    try:
        user_data = await db.get_user(message.from_user.id)
        if not user_data:
            await message.answer("Please use /start first!")
            return
        
        # Get user achievements
        achievements = await db.get_achievements(message.from_user.id)
        
        # Get family members
        family = await db.get_family(message.from_user.id)
        
        # Get garden info
        garden = await db.get_garden(message.from_user.id)
        plants = await db.get_plants(message.from_user.id)
        
        # Create profile image WITH profile picture
        image_bytes = image_gen.create_profile_card(
            bot=bot,
            user_data=user_data,
            achievements=achievements,
            family=family[:4]  # Show first 4 family members
        )
        
        # Calculate total wealth
        total_wealth = user_data.get('cash', 0) + user_data.get('bank_balance', 0)
        
        caption = f"""
**{user_data['first_name']}'s Profile**

**Wealth Summary:**
• Cash: ${user_data.get('cash', 0):,}
• Bank: ${user_data.get('bank_balance', 0):,}
• **Total: ${total_wealth:,}**

**Stats:**
• Level: {user_data.get('level', 1)}
• XP: {user_data.get('xp', 0)}/{(user_data.get('level', 1) * 1000)}
• Reputation: {user_data.get('reputation', 100)}
• Daily Streak: {user_data.get('daily_streak', 0)} days

**Family:** {len(family)} members
**Garden:** {len(plants)}/{garden.get('slots', 9)} slots
**Achievements:** {sum(1 for a in achievements if a.get('unlocked'))}/{len(achievements)}

Use /family for detailed family tree
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
                logger.error(f"Profile photo error: {e}")
                await message.answer(caption, parse_mode="HTML")
        else:
            # Fallback to text only
            await message.answer(caption, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Me command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("family"))
async def cmd_family(message: Message, db: Database):
    """Family tree command with image"""
    try:
        user_data = await db.get_user(message.from_user.id)
        if not user_data:
            await message.answer("Please use /start first!")
            return
        
        family = await db.get_family(message.from_user.id)
        
        if not family:
            response = """
**Your Family Tree**

└─ You (Just starting!)

**How to grow your family:**
• Reply to someone with /adopt to make them your child
• Reply with /marry to get married
• Build your legacy together!

**Benefits:**
• Daily bonus increases per family member
• Family quests and events
• Inheritance system
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        # Try to create family tree image
        image_bytes = image_gen.create_family_tree_image(user_data, family)
        
        # Build family tree text
        tree_text = f"**Family Tree of {user_data['first_name']}**\n\n"
        tree_text += f"└─ {user_data['first_name']} (You)\n"
        
        for member in family:
            emoji = "💑" if member['relation'] == "spouse" else "👶" if member['relation'] == "child" else "👴"
            tree_text += f"   ├─ {emoji} {member['first_name']} ({member['relation']})\n"
        
        stats_text = f"""
**Family Stats:**
• Members: {len(family)}
• Spouses: {sum(1 for m in family if m['relation'] == 'spouse')}
• Children: {sum(1 for m in family if m['relation'] == 'child')}
• Daily Bonus: +${len(family) * Config.FAMILY_DAILY_BONUS}

**Commands:**
• /adopt - Make someone your child
• /marry - Marry someone
• /divorce - End marriage
"""
        
        if image_bytes:
            try:
                from aiogram.types import BufferedInputFile
                photo = BufferedInputFile(image_bytes, filename="family_tree.png")
                await message.answer_photo(
                    photo=photo,
                    caption=tree_text + stats_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Family tree image error: {e}")
                await message.answer(tree_text + stats_text, parse_mode="HTML")
        else:
            await message.answer(tree_text + stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Family command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("adopt"))
async def cmd_adopt(message: Message, db: Database):
    """Adopt someone as child"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer("Please reply to someone's message to adopt them!")
            return
        
        if target.id == message.from_user.id:
            await message.answer("You cannot adopt yourself!")
            return
        
        if target.is_bot:
            await message.answer("Cannot adopt bots!")
            return
        
        # Get users
        user = await db.get_user(message.from_user.id)
        target_user = await db.get_user(target.id)
        
        if not user or not target_user:
            await message.answer("Both users need to use /start first!")
            return
        
        # Check if already family
        existing = await db.fetch_one(
            """SELECT 1 FROM family 
               WHERE (user1_id = ? AND user2_id = ?) 
               OR (user1_id = ? AND user2_id = ?)""",
            (message.from_user.id, target.id, target.id, message.from_user.id)
        )
        
        if existing:
            await message.answer("Already family members!")
            return
        
        # Add relation
        success = await db.add_family_member(message.from_user.id, target.id, "child")
        
        if not success:
            await message.answer("Error creating family relationship!")
            return
        
        # Give adoption bonuses
        await db.update_currency(message.from_user.id, "cash", Config.ADOPT_BONUS)
        await db.update_currency(target.id, "cash", Config.ADOPT_BONUS // 2)
        
        # Get updated family count
        family = await db.get_family(message.from_user.id)
        
        response = f"""
**ADOPTION SUCCESSFUL!**

You adopted **{target.first_name}**
Relationship: Parent-Child
Bonus: ${Config.ADOPT_BONUS:,} for you, ${Config.ADOPT_BONUS // 2:,} for {target.first_name}

Your family now has {len(family)} members
Daily bonus increased by ${Config.FAMILY_DAILY_BONUS:,}!
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log adoption
        await log_to_channel(
            message.bot,
            "**ADOPTION**\n"
            f"Parent: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Child: {target.first_name} ({target.id})\n"
            f"Family size: {len(family)}"
        )
        
    except Exception as e:
        logger.error(f"Adopt command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("marry"))
async def cmd_marry(message: Message, db: Database):
    """Marry someone"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer("Please reply to someone's message to marry them!")
            return
        
        if target.id == message.from_user.id:
            await message.answer("You cannot marry yourself!")
            return
        
        if target.is_bot:
            await message.answer("Cannot marry bots!")
            return
        
        # Get users
        user = await db.get_user(message.from_user.id)
        target_user = await db.get_user(target.id)
        
        if not user or not target_user:
            await message.answer("Both users need to use /start first!")
            return
        
        # Check if already married
        existing = await db.fetch_one(
            """SELECT 1 FROM family 
               WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
               AND relation = 'spouse'""",
            (message.from_user.id, target.id, target.id, message.from_user.id)
        )
        
        if existing:
            await message.answer("Already married!")
            return
        
        # Add relation
        success = await db.add_family_member(message.from_user.id, target.id, "spouse")
        
        if not success:
            await message.answer("Error creating marriage!")
            return
        
        # Give marriage bonuses
        await db.update_currency(message.from_user.id, "cash", Config.MARRY_BONUS)
        await db.update_currency(target.id, "cash", Config.MARRY_BONUS)
        
        # Get family count
        family = await db.get_family(message.from_user.id)
        
        response = f"""
**MARRIAGE SUCCESSFUL!**

You married **{target.first_name}**
Relationship: Spouses
Gift: ${Config.MARRY_BONUS:,} each

Your family now has {len(family)} members

**Congratulations on your wedding!**

Now you can build your family together!
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log marriage
        await log_to_channel(
            message.bot,
            "**MARRIAGE**\n"
            f"Spouse 1: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Spouse 2: {target.first_name} ({target.id})\n"
            f"Family size: {len(family)}"
        )
        
    except Exception as e:
        logger.error(f"Marry command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("divorce"))
async def cmd_divorce(message: Message, db: Database):
    """Divorce spouse"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer("Reply to someone's message to divorce them!")
            return
        
        user = await db.get_user(message.from_user.id)
        target_user = await db.get_user(target.id)
        
        if not user or not target_user:
            await message.answer("Both users need to use /start first!")
            return
        
        # Check if married
        existing = await db.fetch_one(
            """SELECT 1 FROM family 
               WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
               AND relation = 'spouse'""",
            (message.from_user.id, target.id, target.id, message.from_user.id)
        )
        
        if not existing:
            await message.answer("You are not married to this person!")
            return
        
        # Remove marriage
        await db.execute(
            """DELETE FROM family 
               WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
               AND relation = 'spouse'""",
            (message.from_user.id, target.id, target.id, message.from_user.id)
        )
        
        response = f"""
**DIVORCE COMPLETE**

You are no longer married to {target.first_name}.

Relationship ended.
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log divorce
        await log_to_channel(
            message.bot,
            "**DIVORCE**\n"
            f"Spouse 1: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Spouse 2: {target.first_name} ({target.id})"
        )
        
    except Exception as e:
        logger.error(f"Divorce command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("daily"))
async def cmd_daily(message: Message, db: Database):
    """Daily bonus command"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("Please use /start first!")
            return
        
        # Check cooldown
        can_use, remaining = await check_cooldown(message.from_user.id, "daily", 86400, db)
        
        if not can_use:
            await message.answer(f"Come back in {format_time(remaining)}!")
            return
        
        # Calculate bonus
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
        await set_cooldown(message.from_user.id, "daily", db)
        
        # Give random gemstone
        gemstones = ["💎 Diamond", "🔴 Ruby", "🔵 Sapphire", "🟢 Emerald", "🟣 Amethyst"]
        gemstone = random.choice(gemstones)
        
        response = f"""
**DAILY BONUS COLLECTED!**

**Breakdown:**
• Base Bonus: ${base_bonus:,}
• Family Bonus ({len(family)}): ${family_bonus:,}
• Streak Bonus ({streak} days): ${streak_bonus:,}
• Multiplier: {bio_multiplier}x

**Total: ${total_bonus:,}**

{gemstone} You found a {gemstone}!
New Balance: ${user.get('cash', 0) + total_bonus:,}

{"Bio verified (2x bonus!)" if bio_multiplier > 1 else "Add me to bio for 2x bonus!"}
"""
        
        await message.answer(response, parse_mode="HTML")
        
        # Log daily bonus
        await log_to_channel(
            message.bot,
            "**DAILY BONUS**\n"
            f"User: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Amount: ${total_bonus:,}\n"
            f"Streak: {streak} days\n"
            f"Family: {len(family)} members"
        )
        
    except Exception as e:
        logger.error(f"Daily command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("balance"))
async def cmd_balance(message: Message, db: Database):
    """Check balance"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("Please use /start first!")
            return
        
        # Get portfolio value
        stocks = await db.fetch_all(
            "SELECT SUM(shares * avg_price) as value FROM stocks WHERE user_id = ?",
            (message.from_user.id,)
        )
        stock_value = stocks[0]['value'] if stocks and stocks[0]['value'] else 0
        
        total_wealth = user.get('cash', 0) + user.get('bank_balance', 0) + stock_value
        
        response = f"""
**BALANCE SUMMARY**

Cash: ${user.get('cash', 0):,}
Bank: ${user.get('bank_balance', 0):,}
Investments: ${stock_value:,.2f}

**Total Wealth:** ${total_wealth:,}

Family Bonus: +${len(await db.get_family(message.from_user.id)) * Config.FAMILY_DAILY_BONUS:,}/day

Use /bank to manage money
Use /portfolio for investments
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Balance command error: {e}")
        await message.answer("Error occurred. Please try again.")

@family_router.message(Command("garden"))
async def cmd_garden(message: Message, db: Database):
    """Garden with image"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("Please use /start first!")
            return
        
        garden_info = await db.get_garden(message.from_user.id)
        plants = await db.get_plants(message.from_user.id)
        
        # Create garden image
        image_bytes = image_gen.create_garden_image(
            user['first_name'], 
            plants, 
            garden_info
        )
        
        # Calculate stats
        ready_count = sum(1 for p in plants if p.get('current_progress', 0) >= 100)
        total_slots = garden_info.get('slots', 9)
        
        caption = f"""
**{user['first_name']}'s Garden**

**Stats:**
• Growing: {len(plants)}/{total_slots} slots
• Ready: {ready_count} crops
• Greenhouse: Level {garden_info.get('greenhouse_level', 0)}
• Growth Speed: +{garden_info.get('greenhouse_level', 0) * 10}%

**Commands:**
• /plant [crop] [qty] - Plant crops
• /harvest - Collect ready crops
• /barn - View storage
• /sell [crop] [qty] - Sell crops

**Available Crops:**
"""
        
        # Add crop list
        for crop_name, data in list(CROP_DATA.items())[:6]:
            caption += f"{data['emoji']} {crop_name.title()} - ${data['buy']} ({data['grow_time']}h)\n"
        
        if len(plants) > 0:
            caption += "\n**Current Crops:**\n"
            for plant in plants[:3]:
                progress = plant.get('current_progress', 0)
                emoji = CROP_DATA.get(plant.get('crop_type', ''), {}).get('emoji', '🌱')
                caption += f"{emoji} {plant['crop_type'].title()}: {int(progress)}%\n"
        
        if image_bytes:
            try:
                from aiogram.types import BufferedInputFile
                photo = BufferedInputFile(image_bytes, filename="garden.png")
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Garden photo error: {e}")
                await message.answer(caption, parse_mode="HTML")
        else:
            await message.answer(caption, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Garden command error: {e}")
        await message.answer("Error occurred. Please try again.")

# Reaction commands - defined separately to avoid closure issues
@family_router.message(Command("hug"))
async def cmd_hug(message: Message, db: Database):
    """Hug someone"""
    await send_reaction(message, db, "hug")

@family_router.message(Command("kiss"))
async def cmd_kiss(message: Message, db: Database):
    """Kiss someone"""
    await send_reaction(message, db, "kiss")

@family_router.message(Command("slap"))
async def cmd_slap(message: Message, db: Database):
    """Slap someone"""
    await send_reaction(message, db, "slap")

@family_router.message(Command("pat"))
async def cmd_pat(message: Message, db: Database):
    """Pat someone"""
    await send_reaction(message, db, "pat")

@family_router.message(Command("punch"))
async def cmd_punch(message: Message, db: Database):
    """Punch someone"""
    await send_reaction(message, db, "punch")

@family_router.message(Command("cuddle"))
async def cmd_cuddle(message: Message, db: Database):
    """Cuddle someone"""
    await send_reaction(message, db, "cuddle")

@family_router.message(Command("rob"))
async def cmd_rob(message: Message, db: Database):
    """Rob someone"""
    await send_reaction(message, db, "rob")

@family_router.message(Command("kill"))
async def cmd_kill(message: Message, db: Database):
    """Kill someone"""
    await send_reaction(message, db, "kill")

async def send_reaction(message: Message, db: Database, command: str):
    """Send reaction GIF"""
    try:
        target = get_target_user(message)
        
        if not target:
            await message.answer(f"Please reply to someone to {command} them!")
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
        
        caption = f"{message.from_user.first_name} {action} {target.first_name}!"
        
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
        await message.answer("Error occurred. Please try again.")

@family_router.callback_query(F.data == "help_menu")
async def help_menu_callback(callback: CallbackQuery):
    """Help menu callback"""
    try:
        help_text = """
**QUICK HELP MENU**

**Popular Commands:**
• /me - Your profile with photo
• /daily - Daily bonus
• /family - Family tree
• /garden - Your farm
• /bank - Banking

**Money Making:**
• Plant and sell crops
• Collect daily interest
• Buy businesses
• Play games

**Family Fun:**
• Adopt friends as children
• Marry your partner
• Build a family legacy

Use /help for complete command list
"""
        
        await callback.message.edit_text(help_text, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Help menu callback error: {e}")
        await callback.answer("Error loading help menu")

@family_router.callback_query(F.data == "daily_bonus")
async def daily_bonus_callback(callback: CallbackQuery):
    """Daily bonus callback"""
    try:
        # Create a simple response
        response = """
**DAILY BONUS**

Click the button below or use /daily in chat to collect your daily bonus!

**Features:**
• $500-$1,500 base bonus
• Family member bonuses
• Streak bonuses
• 2x bonus if bot in bio

Your daily bonus increases with:
• More family members
• Longer streaks
• Bio verification
"""
        
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🎁 Collect Now",
                        url=f"https://t.me/{(await callback.bot.get_me()).username}?start"
                    )
                ]
            ]
        )
        
        await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Daily bonus callback error: {e}")
        await callback.answer("Error loading daily bonus")

# Add error handler for this router
@family_router.errors()
async def family_error_handler(event, db: Database):
    """Handle errors in family router"""
    logger.error(f"Family router error: {event.exception}")
    return True
