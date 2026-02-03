"""
💰 ECONOMY COMMAND HANDLERS
Banking, stocks, crypto, real estate, jobs
"""

import logging
import random
from typing import Optional
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import F

from config import Config
from database import Database, image_gen
from utils.logger import log_to_channel
from utils.helpers import format_money, format_time

# Create router
economy_router = Router()
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

# Stock data
STOCKS = {
    "TECH": {"name": "Tech Corp", "base_price": 100, "volatility": 0.2},
    "FARM": {"name": "Farm Inc", "base_price": 50, "volatility": 0.15},
    "GOLD": {"name": "Gold Mining", "base_price": 200, "volatility": 0.1},
    "OIL": {"name": "Oil Co", "base_price": 80, "volatility": 0.25},
    "BIO": {"name": "Bio Tech", "base_price": 150, "volatility": 0.3}
}

# Business types
BUSINESS_TYPES = {
    "farm": {"name": "🌾 Farm", "price": 5000, "income": 500, "upgrade": 2000},
    "store": {"name": "🏪 Store", "price": 10000, "income": 1000, "upgrade": 5000},
    "restaurant": {"name": "🍽️ Restaurant", "price": 25000, "income": 2500, "upgrade": 12000},
    "hotel": {"name": "🏨 Hotel", "price": 50000, "income": 5000, "upgrade": 25000},
    "casino": {"name": "🎰 Casino", "price": 100000, "income": 10000, "upgrade": 50000}
}

# Crypto data
CRYPTO_DATA = {
    "BTC": {"name": "Bitcoin", "emoji": "₿", "volatility": 0.1},
    "ETH": {"name": "Ethereum", "emoji": "Ξ", "volatility": 0.15},
    "DOGE": {"name": "Dogecoin", "emoji": "🐕", "volatility": 0.25},
    "LTC": {"name": "Litecoin", "emoji": "Ł", "volatility": 0.2},
    "ADA": {"name": "Cardano", "emoji": "🔷", "volatility": 0.18}
}

@economy_router.message(Command("bank"))
async def cmd_bank(message: Message, db: Database):
    """Bank system"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        # Get bank account
        bank_account = await db.fetch_one(
            "SELECT * FROM bank_accounts WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        if not bank_account:
            bank_account = {
                "total_interest": 0,
                "last_interest": None
            }
        
        # Calculate next interest
        next_interest = "Now!"
        if bank_account.get('last_interest'):
            try:
                last_interest = datetime.fromisoformat(bank_account['last_interest'])
                next_time = last_interest + timedelta(days=1)
                if next_time > datetime.now():
                    hours_left = int((next_time - datetime.now()).total_seconds() / 3600)
                    next_interest = f"{hours_left}h"
            except:
                pass
        
        response = f"""
🏦 <b>BANK OF FAMILY TREE</b>

💰 <b>Your Accounts:</b>
• 💵 Cash: <b>${user.get('cash', 0):,}</b>
• 🏦 Savings: <b>${user.get('bank_balance', 0):,}</b>
• 📈 Interest Earned: <b>${bank_account.get('total_interest', 0):,}</b>

📊 <b>Bank Features:</b>
• Daily Interest: {Config.BANK_INTEREST_RATE}%
• Next Interest: {next_interest}
• Safe from robbery
• Transaction history

💡 <b>Commands:</b>
• /deposit [amount] - Deposit to bank
• /withdraw [amount] - Withdraw from bank  
• /interest - Collect interest
• /statement - View transactions

🔒 <b>Your money is safe with us!</b>
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Bank command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("deposit"))
async def cmd_deposit(message: Message, command: CommandObject, db: Database):
    """Deposit money to bank"""
    try:
        if not command.args:
            await message.answer("❌ Usage: /deposit [amount]\nExample: /deposit 1000")
            return
        
        try:
            amount = int(command.args)
            if amount <= 0:
                await message.answer("❌ Amount must be positive!")
                return
        except ValueError:
            await message.answer("❌ Amount must be a number!")
            return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        if user['cash'] < amount:
            await message.answer(f"❌ You only have ${user['cash']:,} cash!")
            return
        
        # Deposit
        await db.update_currency(message.from_user.id, "cash", -amount)
        await db.update_currency(message.from_user.id, "bank_balance", amount)
        
        # Record transaction
        await db.execute(
            """INSERT INTO transactions (user_id, type, amount, description, balance_after)
               VALUES (?, 'deposit', ?, 'Cash deposit', ?)""",
            (message.from_user.id, amount, user.get('bank_balance', 0) + amount)
        )
        
        response = f"""
✅ <b>DEPOSIT SUCCESSFUL!</b>

💰 <b>Amount:</b> ${amount:,}
🏦 <b>New Bank Balance:</b> ${user.get('bank_balance', 0) + amount:,}
💵 <b>Cash Left:</b> ${user['cash'] - amount:,}

📈 <b>Daily Interest:</b> ${int((user.get('bank_balance', 0) + amount) * (Config.BANK_INTEREST_RATE / 100)):,}
💡 Use /interest daily to collect!
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Deposit command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("withdraw"))
async def cmd_withdraw(message: Message, command: CommandObject, db: Database):
    """Withdraw money from bank"""
    try:
        if not command.args:
            await message.answer("❌ Usage: /withdraw [amount]\nExample: /withdraw 500")
            return
        
        try:
            amount = int(command.args)
            if amount <= 0:
                await message.answer("❌ Amount must be positive!")
                return
        except ValueError:
            await message.answer("❌ Amount must be a number!")
            return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        if user.get('bank_balance', 0) < amount:
            await message.answer(f"❌ You only have ${user.get('bank_balance', 0):,} in bank!")
            return
        
        # Withdraw
        await db.update_currency(message.from_user.id, "bank_balance", -amount)
        await db.update_currency(message.from_user.id, "cash", amount)
        
        # Record transaction
        await db.execute(
            """INSERT INTO transactions (user_id, type, amount, description, balance_after)
               VALUES (?, 'withdraw', ?, 'Cash withdrawal', ?)""",
            (message.from_user.id, amount, user.get('bank_balance', 0) - amount)
        )
        
        response = f"""
✅ <b>WITHDRAWAL SUCCESSFUL!</b>

💰 <b>Amount:</b> ${amount:,}
🏦 <b>New Bank Balance:</b> ${user.get('bank_balance', 0) - amount:,}
💵 <b>Cash Now:</b> ${user['cash'] + amount:,}

💡 Your money is ready to use!
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Withdraw command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("interest"))
async def cmd_interest(message: Message, db: Database):
    """Collect bank interest"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        bank_balance = user.get('bank_balance', 0)
        
        if bank_balance <= 0:
            await message.answer("❌ You need money in bank to earn interest!")
            return
        
        # Check last interest
        last_interest = await db.fetch_one(
            "SELECT last_interest FROM bank_accounts WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        if last_interest and last_interest.get('last_interest'):
            try:
                last_time = datetime.fromisoformat(last_interest['last_interest'].replace('Z', '+00:00'))
                if (datetime.now() - last_time).total_seconds() < 86400:
                    next_time = last_time + timedelta(days=1)
                    hours_left = int((next_time - datetime.now()).total_seconds() / 3600)
                    await message.answer(f"⏳ Interest already collected today. Next in {hours_left}h")
                    return
            except:
                pass
        
        # Calculate interest
        interest = int(bank_balance * (Config.BANK_INTEREST_RATE / 100))
        
        if interest > 0:
            # Add interest
            await db.update_currency(message.from_user.id, "bank_balance", interest)
            
            # Update bank account
            await db.execute(
                """UPDATE bank_accounts 
                   SET last_interest = CURRENT_TIMESTAMP,
                       total_interest = total_interest + ?
                   WHERE user_id = ?""",
                (interest, message.from_user.id)
            )
            
            # Record transaction
            await db.execute(
                """INSERT INTO transactions (user_id, type, amount, description, balance_after)
                   VALUES (?, 'interest', ?, 'Daily interest', ?)""",
                (message.from_user.id, interest, bank_balance + interest)
            )
            
            response = f"""
✅ <b>INTEREST COLLECTED!</b>

💰 <b>Amount:</b> ${interest:,}
🏦 <b>New Bank Balance:</b> ${bank_balance + interest:,}
📈 <b>Daily Rate:</b> {Config.BANK_INTEREST_RATE}%

💡 Come back tomorrow for more!
"""
        else:
            response = "❌ No interest to collect. Deposit more money!"
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Interest command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("statement"))
async def cmd_statement(message: Message, command: CommandObject, db: Database):
    """Bank statement"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        limit = 10
        if command.args:
            try:
                limit = min(int(command.args), 50)
            except:
                pass
        
        transactions = await db.fetch_all(
            """SELECT type, amount, description, created_at
               FROM transactions 
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (message.from_user.id, limit)
        )
        
        if not transactions:
            response = """
📄 <b>BANK STATEMENT</b>

No transactions yet.

💡 Make your first deposit:
<code>/deposit 100</code>
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        statement_text = "📄 <b>BANK STATEMENT</b>\n\n"
        statement_text += f"🏦 Current Balance: <b>${user.get('bank_balance', 0):,}</b>\n\n"
        statement_text += "📋 <b>Recent Transactions:</b>\n"
        
        for trans in transactions:
            emoji = "📥" if trans['type'] == 'deposit' else "📤" if trans['type'] == 'withdraw' else "💰"
            sign = "+" if trans['type'] in ['deposit', 'interest'] else "-"
            
            # Format date
            try:
                trans_date = datetime.fromisoformat(trans['created_at'])
                date_str = trans_date.strftime('%m/%d %H:%M')
            except:
                date_str = str(trans['created_at'])[:16]
            
            amount_text = f"${abs(trans['amount']):,}"
            statement_text += f"{emoji} {sign}{amount_text} - {trans.get('description', 'Transaction')} ({date_str})\n"
        
        statement_text += f"\n💡 Showing last {len(transactions)} transactions"
        statement_text += "\n💡 Use /statement [number] to see more"
        
        await message.answer(statement_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Statement command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("garden"))
async def cmd_garden(message: Message, db: Database):
    """Garden with image"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        garden_info = await db.get_garden(message.from_user.id)
        plants = await db.get_plants(message.from_user.id)
        
        # Create garden image
        image_bytes = image_gen.create_garden_image(user['first_name'], plants, garden_info)
        
        # Calculate stats
        ready_count = sum(1 for p in plants if p.get('current_progress', 0) >= 100)
        total_slots = garden_info.get('slots', 9)
        
        caption = f"""
🌾 <b>{user['first_name']}'s Garden</b>

📊 <b>Stats:</b>
• Growing: {len(plants)}/{total_slots} slots
• Ready: {ready_count} crops
• Greenhouse: Level {garden_info.get('greenhouse_level', 0)}
• Growth Speed: +{garden_info.get('greenhouse_level', 0) * 10}%

💡 <b>Commands:</b>
• /plant [crop] [qty] - Plant crops
• /harvest - Collect ready crops
• /barn - View storage
• /sell [crop] [qty] - Sell crops

🌱 <b>Available Crops:</b>
"""
        
        # Add crop list
        for crop_name, data in list(CROP_DATA.items())[:6]:
            caption += f"{data['emoji']} {crop_name.title()} - ${data['buy']} ({data['grow_time']}h)\n"
        
        if len(plants) > 0:
            caption += "\n📈 <b>Current Crops:</b>\n"
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
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("plant"))
async def cmd_plant(message: Message, command: CommandObject, db: Database):
    """Plant crops"""
    try:
        if not command.args:
            crops_list = "\n".join([
                f"{data['emoji']} {crop.title()} - ${data['buy']} ({data['grow_time']}h)"
                for crop, data in list(CROP_DATA.items())[:6]
            ])
            
            response = f"""
🌱 <b>PLANT CROPS</b>

Usage: <code>/plant [crop] [quantity]</code>

🌿 <b>Available Crops:</b>
{crops_list}

💡 <b>Examples:</b>
<code>/plant carrot 3</code>
<code>/plant tomato 2</code>  
<code>/plant watermelon 1</code>

📊 <b>Your Garden:</b>
Use /garden to check available space
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        args = command.args.lower().split()
        if len(args) < 2:
            await message.answer("❌ Format: /plant [crop] [quantity]\nExample: /plant carrot 3")
            return
        
        crop_type = args[0]
        try:
            quantity = int(args[1])
        except ValueError:
            await message.answer("❌ Quantity must be a number!")
            return
        
        if crop_type not in CROP_DATA:
            available_crops = ", ".join(CROP_DATA.keys())
            await message.answer(f"❌ Invalid crop! Available: {available_crops}")
            return
        
        if quantity < 1 or quantity > 9:
            await message.answer("❌ Quantity must be between 1 and 9!")
            return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        # Check garden space
        plants = await db.get_plants(message.from_user.id)
        garden_info = await db.get_garden(message.from_user.id)
        total_slots = garden_info.get('slots', 9)
        
        if len(plants) + quantity > total_slots:
            await message.answer(f"❌ Not enough space! You have {len(plants)}/{total_slots} slots used.")
            return
        
        # Check cost
        crop_data = CROP_DATA[crop_type]
        total_cost = crop_data['buy'] * quantity
        
        if user['cash'] < total_cost:
            await message.answer(f"❌ You need ${total_cost:,}! You have ${user['cash']:,}")
            return
        
        # Plant crops
        grow_time = crop_data['grow_time']
        
        for _ in range(quantity):
            await db.execute(
                """INSERT INTO plants (user_id, crop_type, grow_time)
                   VALUES (?, ?, ?)""",
                (message.from_user.id, crop_type, grow_time)
            )
        
        # Deduct money
        await db.update_currency(message.from_user.id, "cash", -total_cost)
        
        response = f"""
✅ <b>PLANTED SUCCESSFULLY!</b>

{crop_data['emoji']} <b>Crop:</b> {crop_type.title()}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Cost:</b> ${total_cost:,}
⏰ <b>Grow Time:</b> {grow_time} hours
⭐ <b>XP per crop:</b> {crop_data['xp']}

🌱 {quantity} {crop_type.title()}{'s' if quantity > 1 else ''} now growing in your garden!

💡 Use /garden to check progress
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Plant command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("harvest"))
async def cmd_harvest(message: Message, db: Database):
    """Harvest crops"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        # Get ready plants
        ready_plants = await db.fetch_all(
            """SELECT crop_type, COUNT(*) as count
               FROM plants 
               WHERE user_id = ? AND is_ready = 0
               GROUP BY crop_type""",
            (message.from_user.id,)
        )
        
        if not ready_plants:
            await message.answer("❌ No crops ready for harvest!")
            return
        
        total_value = 0
        total_xp = 0
        harvest_text = "✅ <b>HARVEST COMPLETE!</b>\n\n"
        
        for plant in ready_plants:
            crop_type = plant['crop_type']
            count = plant['count']
            
            if crop_type in CROP_DATA:
                crop_data = CROP_DATA[crop_type]
                sell_price = crop_data['sell'] * count
                crop_xp = crop_data['xp'] * count
                total_value += sell_price
                total_xp += crop_xp
                
                # Add to barn
                await db.execute(
                    """INSERT INTO barn (user_id, crop_type, quantity)
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, crop_type) 
                       DO UPDATE SET quantity = quantity + ?""",
                    (message.from_user.id, crop_type, count, count)
                )
                
                harvest_text += f"{crop_data['emoji']} {crop_type.title()}: {count} × ${crop_data['sell']} = ${sell_price}\n"
        
        # Remove harvested plants
        await db.execute(
            "DELETE FROM plants WHERE user_id = ? AND is_ready = 0",
            (message.from_user.id,)
        )
        
        # Add money and XP
        if total_value > 0:
            await db.update_currency(message.from_user.id, "cash", total_value)
        
        harvest_text += f"\n💰 <b>Total Earned: ${total_value:,}</b>"
        harvest_text += f"\n💵 New Balance: ${user['cash'] + total_value:,}"
        
        if total_xp > 0:
            # Add XP
            await db.execute(
                "UPDATE users SET xp = xp + ? WHERE user_id = ?",
                (total_xp, message.from_user.id)
            )
            harvest_text += f"\n⭐ <b>XP Gained:</b> {total_xp}"
        
        await message.answer(harvest_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Harvest command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("stocks"))
async def cmd_stocks(message: Message):
    """Stock market overview"""
    response = """
📈 <b>STOCK MARKET</b>

Welcome to the Family Tree Stock Exchange!

💹 <b>Available Stocks:</b>
• TECH - Tech Corp (Volatile)
• FARM - Farm Inc (Stable)
• GOLD - Gold Mining (Safe)
• OIL - Oil Co (Risky)
• BIO - Bio Tech (High Risk)

💡 <b>How it works:</b>
• Prices change randomly every hour
• Buy low, sell high
• Monitor market trends

📊 <b>Commands:</b>
• /buystock [symbol] [qty] - Buy stocks
• /sellstock [symbol] [qty] - Sell stocks
• /portfolio - Your investments
• /stockprice [symbol] - Check price

🎯 <b>Tip:</b> Diversify your portfolio!
"""
    
    await message.answer(response, parse_mode="HTML")

@economy_router.message(Command("crypto"))
async def cmd_crypto(message: Message):
    """Cryptocurrency market"""
    response = """
💹 <b>CRYPTOCURRENCY MARKET</b>

Welcome to Crypto Exchange!

💰 <b>Available Cryptocurrencies:</b>
• BTC - Bitcoin (Digital Gold)
• ETH - Ethereum (Smart Contracts)
• DOGE - Dogecoin (Meme Coin)
• LTC - Litecoin (Silver to BTC)
• ADA - Cardano (Research Based)

⚡ <b>Features:</b>
• Real-time price simulation
• High volatility (10-25% daily)
• Leverage trading (up to 10x)
• Crypto wallets

📊 <b>Commands:</b>
• /buycrypto [coin] [amount] - Buy crypto
• /sellcrypto [coin] [amount] - Sell crypto
• /cryptoprice [coin] - Check price
• /wallet - Your crypto wallet

⚠️ <b>Warning:</b> Crypto is highly volatile!
"""
    
    await message.answer(response, parse_mode="HTML")

@economy_router.message(Command("business"))
async def cmd_business(message: Message, db: Database):
    """Business system"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        businesses = await db.fetch_all(
            "SELECT business_type, level, last_collected, total_earned FROM businesses WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        if not businesses:
            response = """
🏢 <b>BUSINESS EMPIRE</b>

You don't own any businesses yet!

💼 <b>Available Businesses:</b>
"""
            for biz_type, data in BUSINESS_TYPES.items():
                response += f"{data['name']} - ${data['price']:,} (${data['income']:,}/day)\n"
            
            response += """
💡 <b>How it works:</b>
• Buy businesses to generate passive income
• Collect income every 24 hours
• Upgrade businesses for more income
• Multiple business types available

📊 <b>Commands:</b>
• /buybusiness [type] - Buy business
• /collect - Collect business income
• /upgradebusiness - Upgrade business
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        response = "🏢 <b>YOUR BUSINESSES</b>\n\n"
        total_income = 0
        
        for biz in businesses:
            biz_data = BUSINESS_TYPES.get(biz['business_type'], {})
            income = biz_data.get('income', 0) * biz['level']
            total_income += income
            
            response += f"{biz_data.get('name', 'Business')} - Level {biz['level']}\n"
            response += f"  Income: ${income:,}/day\n"
            response += f"  Total Earned: ${biz['total_earned'] or 0:,}\n\n"
        
        response += f"💰 <b>Total Daily Income:</b> ${total_income:,}\n"
        response += "💡 Use /collect to collect income"
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Business command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@economy_router.message(Command("jobs"))
async def cmd_jobs(message: Message):
    """Job system"""
    response = """
💼 <b>JOB SYSTEM</b>

Get a job and earn daily salary!

👔 <b>Available Jobs:</b>
• Farmer - $200/day (Beginner)
• Trader - $500/day (Intermediate)
• Developer - $1000/day (Advanced)
• Doctor - $1500/day (Expert)
• Engineer - $1200/day (Advanced)

📊 <b>Features:</b>
• Work 8 hours per day
• Career progression
• Promotions & raises
• Skill requirements

🎮 <b>Commands:</b>
• /work - Start work shift
• /career - Career progress
• /promotion - Request promotion
• /quitjob - Quit current job

💡 Start with a simple job and work your way up!
"""
    
    await message.answer(response, parse_mode="HTML")

@economy_router.message(Command("properties"))
async def cmd_properties(message: Message, db: Database):
    """Real estate properties"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        properties = await db.fetch_all(
            "SELECT property_type, location, level, value, income FROM real_estate WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        if not properties:
            response = """
🏘️ <b>REAL ESTATE PORTFOLIO</b>

You don't own any properties yet!

🏠 <b>Property Types:</b>
• House - $10,000 (Basic home)
• Apartment - $25,000 (City living)
• Villa - $50,000 (Luxury)
• Commercial - $100,000 (Business)
• Land - $5,000 (Investment)

💰 <b>Benefits:</b>
• Collect rent every 24 hours
• Property value appreciation
• Upgrade for more income
• Location bonuses

📊 <b>Commands:</b>
• /buyproperty [type] - Buy property
• /rent - Collect rent income
• /upgradeproperty - Upgrade property
• /sellproperty - Sell property
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        response = "🏘️ <b>YOUR PROPERTIES</b>\n\n"
        total_value = 0
        total_income = 0
        
        for prop in properties:
            total_value += prop['value']
            total_income += prop['income']
            
            response += f"🏠 {prop['property_type'].title()} in {prop['location']}\n"
            response += f"  Level: {prop['level']} | Value: ${prop['value']:,}\n"
            response += f"  Rent: ${prop['income']:,}/day\n\n"
        
        response += f"💰 <b>Total Portfolio Value:</b> ${total_value:,}\n"
        response += f"🏦 <b>Total Daily Rent:</b> ${total_income:,}\n"
        response += "💡 Use /rent to collect income"
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Properties command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")
