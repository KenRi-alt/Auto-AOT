"""
🎮 GAME COMMAND HANDLERS
Lottery, casino, battles, racing, etc.
"""

import logging
import random
import asyncio
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
games_router = Router()
logger = logging.getLogger(__name__)

@games_router.message(Command("lottery"))
async def cmd_lottery(message: Message, db: Database):
    """Lottery system"""
    response = """
🎰 <b>LOTTERY SYSTEM</b>

Try your luck and win big!

💰 <b>How it works:</b>
• Buy lottery tickets for $50 each
• Tickets have 6-digit numbers
• Draw happens every Sunday
• 70% of sales goes to prize pool

🎫 <b>Ticket Features:</b>
• Scratch to reveal numbers
• Automatic win checking
• Big jackpot prizes
• Multiple tickets allowed

📊 <b>Commands:</b>
• /buyticket [qty] - Buy lottery tickets
• /mytickets - View your tickets
• /scratch [id] - Scratch ticket
• /lotterystats - Lottery statistics

🎯 <b>Jackpot Alert:</b> Current prize pool growing!
"""
    
    await message.answer(response, parse_mode="HTML")

@games_router.message(Command("buyticket"))
async def cmd_buyticket(message: Message, command: CommandObject, db: Database):
    """Buy lottery tickets"""
    try:
        if not command.args:
            await message.answer("❌ Usage: /buyticket [quantity]\nExample: /buyticket 5")
            return
        
        try:
            quantity = int(command.args)
            if quantity < 1 or quantity > 20:
                await message.answer("❌ Quantity must be between 1 and 20!")
                return
        except ValueError:
            await message.answer("❌ Quantity must be a number!")
            return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        total_cost = quantity * Config.LOTTERY_TICKET_PRICE
        
        if user['cash'] < total_cost:
            await message.answer(f"❌ You need ${total_cost:,}! You have ${user['cash']:,}")
            return
        
        # Generate tickets
        tickets = []
        for _ in range(quantity):
            ticket_id = f"LOT-{random.randint(100000, 999999)}"
            numbers = ''.join(str(random.randint(0, 9)) for _ in range(6))
            
            await db.execute(
                """INSERT INTO lottery_tickets (ticket_id, user_id, numbers)
                   VALUES (?, ?, ?)""",
                (ticket_id, message.from_user.id, numbers)
            )
            
            tickets.append(ticket_id)
        
        # Deduct money
        await db.update_currency(message.from_user.id, "cash", -total_cost)
        
        # Create scratch card image for first ticket
        if tickets:
            image_bytes = image_gen.create_scratch_card(tickets[0], numbers)
        
        response = f"""
✅ <b>TICKETS PURCHASED!</b>

🎫 <b>Quantity:</b> {quantity} tickets
💰 <b>Cost:</b> ${total_cost:,}
📝 <b>Ticket IDs:</b> {', '.join(tickets[:3])}
{"..." if len(tickets) > 3 else ""}

💡 <b>What's next:</b>
1. Use /mytickets to view all tickets
2. Use /scratch [id] to reveal numbers
3. Wait for Sunday draw
4. Check if you won!

🎲 Good luck!
"""
        
        if tickets and image_bytes:
            try:
                from aiogram.types import BufferedInputFile
                photo = BufferedInputFile(image_bytes, filename="ticket.png")
                await message.answer_photo(
                    photo=photo,
                    caption=response,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ticket image error: {e}")
                await message.answer(response, parse_mode="HTML")
        else:
            await message.answer(response, parse_mode="HTML")
        
        # Log ticket purchase
        await log_to_channel(
            message.bot,
            f"🎫 **LOTTERY TICKETS**\n"
            f"User: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Tickets: {quantity}\n"
            f"Amount: ${total_cost:,}"
        )
        
    except Exception as e:
        logger.error(f"Buy ticket error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("mytickets"))
async def cmd_mytickets(message: Message, db: Database):
    """View lottery tickets"""
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        tickets = await db.fetch_all(
            """SELECT ticket_id, numbers, scratched, scratched_at, purchased_at, is_winner
               FROM lottery_tickets 
               WHERE user_id = ?
               ORDER BY purchased_at DESC""",
            (message.from_user.id,)
        )
        
        if not tickets:
            await message.answer("🎫 You don't have any lottery tickets!\nUse /buyticket to buy some.")
            return
        
        response = f"""
🎫 <b>YOUR LOTTERY TICKETS</b>

📊 <b>Total Tickets:</b> {len(tickets)}
💰 <b>Total Spent:</b> ${len(tickets) * Config.LOTTERY_TICKET_PRICE:,}

📋 <b>Recent Tickets:</b>
"""
        
        for i, ticket in enumerate(tickets[:5]):
            status = "✅ Scratched" if ticket['scratched'] else "🎴 Hidden"
            winner = "🏆 WINNER!" if ticket.get('is_winner') else ""
            
            # Format date
            try:
                date = datetime.fromisoformat(ticket['purchased_at'])
                date_str = date.strftime('%m/%d')
            except:
                date_str = str(ticket['purchased_at'])[:10]
            
            response += f"{i+1}. #{ticket['ticket_id']} - {status} {winner} ({date_str})\n"
        
        if len(tickets) > 5:
            response += f"\n... and {len(tickets) - 5} more tickets"
        
        response += "\n\n💡 Use /scratch [id] to reveal numbers"
        response += "\n💡 Next draw: Sunday"
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"My tickets error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("scratch"))
async def cmd_scratch(message: Message, command: CommandObject, db: Database):
    """Scratch lottery ticket"""
    try:
        if not command.args:
            await message.answer("❌ Usage: /scratch [ticket_id]\nExample: /scratch LOT-123456")
            return
        
        ticket_id = command.args.strip()
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        # Get ticket
        ticket = await db.fetch_one(
            """SELECT numbers, scratched, is_winner 
               FROM lottery_tickets 
               WHERE user_id = ? AND ticket_id = ?""",
            (message.from_user.id, ticket_id)
        )
        
        if not ticket:
            await message.answer("❌ Ticket not found! Use /mytickets to see your tickets.")
            return
        
        if ticket['scratched']:
            response = f"""
🎫 <b>TICKET ALREADY SCRATCHED</b>

Ticket: #{ticket_id}
Numbers: {ticket['numbers']}
Status: {"🏆 WINNER!" if ticket['is_winner'] else "Not a winner"}

💡 Check /mytickets for all tickets
"""
            await message.answer(response, parse_mode="HTML")
            return
        
        # Mark as scratched
        await db.execute(
            """UPDATE lottery_tickets 
               SET scratched = 1, scratched_at = CURRENT_TIMESTAMP
               WHERE user_id = ? AND ticket_id = ?""",
            (message.from_user.id, ticket_id)
        )
        
        # Check if winner (simplified: last digit 7 or 9)
        numbers = ticket['numbers']
        is_winner = numbers[-1] in ['7', '9']  # 20% chance
        
        if is_winner:
            prize = Config.LOTTERY_TICKET_PRICE * 10  # 10x prize
            await db.update_currency(message.from_user.id, "cash", prize)
            await db.execute(
                "UPDATE lottery_tickets SET is_winner = 1 WHERE user_id = ? AND ticket_id = ?",
                (message.from_user.id, ticket_id)
            )
            
            # Log win
            await log_to_channel(
                message.bot,
                f"🏆 **LOTTERY WIN**\n"
                f"User: {message.from_user.first_name} ({message.from_user.id})\n"
                f"Ticket: #{ticket_id}\n"
                f"Numbers: {numbers}\n"
                f"Prize: ${prize:,}"
            )
        
        response = f"""
🎉 <b>TICKET SCRATCHED!</b>

🎫 <b>Ticket ID:</b> #{ticket_id}
🔢 <b>Numbers:</b> {numbers}
{"🏆 **WINNER! $" + str(prize) + " Prize!**" if is_winner else "💔 Not a winner this time"}

{"💰 Prize added to your cash!" if is_winner else "🎯 Better luck next time!"}

💡 Buy more tickets: /buyticket
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Scratch ticket error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("slot"))
async def cmd_slot(message: Message, command: CommandObject, db: Database):
    """Slot machine game"""
    try:
        # Parse bet amount
        bet = 100
        if command.args:
            try:
                bet = int(command.args)
                if bet < Config.MIN_BET:
                    await message.answer(f"❌ Minimum bet is ${Config.MIN_BET}!")
                    return
                if bet > Config.MAX_BET:
                    await message.answer(f"❌ Maximum bet is ${Config.MAX_BET}!")
                    return
            except ValueError:
                await message.answer("❌ Bet must be a number!")
                return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        if user['cash'] < bet:
            await message.answer(f"❌ You need ${bet:,}! You have ${user['cash']:,}")
            return
        
        # Slot symbols
        symbols = ["🍒", "🍋", "🍊", "🍉", "🔔", "7️⃣", "💎"]
        
        # Spin the slots
        result = []
        for _ in range(3):
            result.append(random.choice(symbols))
        
        # Calculate winnings
        if result[0] == result[1] == result[2]:
            if result[0] == "7️⃣":
                multiplier = 10
            elif result[0] == "💎":
                multiplier = 5
            else:
                multiplier = 3
        elif result[0] == result[1] or result[1] == result[2]:
            multiplier = 2
        else:
            multiplier = 0
        
        winnings = bet * multiplier
        net = winnings - bet
        
        # Update money
        await db.update_currency(message.from_user.id, "cash", net)
        
        # Slot display
        slot_display = f"""
🎰 <b>SLOT MACHINE</b>

🎲 <b>Bet:</b> ${bet:,}
🎯 <b>Result:</b> {' | '.join(result)}

"""
        
        if multiplier > 0:
            slot_display += f"""
💰 <b>WINNER!</b>
🎁 <b>Multiplier:</b> {multiplier}x
🏆 <b>Winnings:</b> ${winnings:,}
📈 <b>Net:</b> {'+' if net > 0 else ''}${net:,}

💵 New Balance: ${user['cash'] + net:,}
"""
            
            if multiplier >= 3:
                slot_display += "\n🎉 JACKPOT! 🎉\n"
        else:
            slot_display += f"""
💔 <b>No win this time</b>
📉 <b>Loss:</b> -${bet:,}

💵 New Balance: ${user['cash'] - bet:,}
"""
        
        slot_display += "\n🎮 Play again: /slot [bet]"
        
        await message.answer(slot_display, parse_mode="HTML")
        
        # Log slot game
        await log_to_channel(
            message.bot,
            f"🎰 **SLOT MACHINE**\n"
            f"User: {message.from_user.first_name} ({message.from_user.id})\n"
            f"Bet: ${bet:,}\n"
            f"Result: {'|'.join(result)}\n"
            f"Win/Loss: {'+' if net > 0 else ''}${net:,}"
        )
        
    except Exception as e:
        logger.error(f"Slot machine error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("dice"))
async def cmd_dice(message: Message, command: CommandObject, db: Database):
    """Dice game"""
    try:
        # Parse bet amount
        bet = 100
        if command.args:
            try:
                bet = int(command.args)
                if bet < Config.MIN_BET:
                    await message.answer(f"❌ Minimum bet is ${Config.MIN_BET}!")
                    return
                if bet > Config.MAX_BET:
                    await message.answer(f"❌ Maximum bet is ${Config.MAX_BET}!")
                    return
            except ValueError:
                await message.answer("❌ Bet must be a number!")
                return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        if user['cash'] < bet:
            await message.answer(f"❌ You need ${bet:,}! You have ${user['cash']:,}")
            return
        
        # Roll dice
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        # Determine winner
        if player_roll > bot_roll:
            result = "WIN"
            winnings = bet * 2
            net = bet
        elif player_roll < bot_roll:
            result = "LOSE"
            winnings = 0
            net = -bet
        else:
            result = "DRAW"
            winnings = bet
            net = 0
        
        # Update money
        if net != 0:
            await db.update_currency(message.from_user.id, "cash", net)
        
        # Dice display
        dice_display = f"""
🎲 <b>DICE GAME</b>

💰 <b>Bet:</b> ${bet:,}

👤 <b>Your roll:</b> {player_roll} {'⚀⚁⚂⚃⚄⚅'[player_roll-1]}
🤖 <b>Bot roll:</b> {bot_roll} {'⚀⚁⚂⚃⚄⚅'[bot_roll-1]}

"""
        
        if result == "WIN":
            dice_display += f"""
✅ <b>YOU WIN!</b>
🎁 <b>Winnings:</b> ${winnings:,}
💰 <b>Profit:</b> +${bet:,}

💵 New Balance: ${user['cash'] + bet:,}
"""
        elif result == "LOSE":
            dice_display += f"""
❌ <b>YOU LOSE</b>
💸 <b>Loss:</b> -${bet:,}

💵 New Balance: ${user['cash'] - bet:,}
"""
        else:
            dice_display += f"""
🤝 <b>DRAW!</b>
💰 <b>Bet returned</b>

💵 Balance unchanged: ${user['cash']:,}
"""
        
        dice_display += "\n🎮 Play again: /dice [bet]"
        
        await message.answer(dice_display, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Dice game error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("blackjack"))
async def cmd_blackjack(message: Message, command: CommandObject, db: Database):
    """Blackjack game"""
    try:
        # Parse bet amount
        bet = 100
        if command.args:
            try:
                bet = int(command.args)
                if bet < Config.MIN_BET:
                    await message.answer(f"❌ Minimum bet is ${Config.MIN_BET}!")
                    return
                if bet > Config.MAX_BET:
                    await message.answer(f"❌ Maximum bet is ${Config.MAX_BET}!")
                    return
            except ValueError:
                await message.answer("❌ Bet must be a number!")
                return
        
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Please use /start first!")
            return
        
        if user['cash'] < bet:
            await message.answer(f"❌ You need ${bet:,}! You have ${user['cash']:,}")
            return
        
        # Simple blackjack implementation
        response = f"""
🃏 <b>BLACKJACK</b>

💰 <b>Bet:</b> ${bet:,}

🎮 <b>Game starting...</b>

💡 This is a simplified blackjack game.
The full version with hit/stand will be added soon!

For now, try our other games:
• /slot - Slot machine
• /dice - Dice game
• /lottery - Lottery tickets

🎲 Coming soon: Full blackjack with card dealing!
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Blackjack error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("arena"))
async def cmd_arena(message: Message):
    """Battle arena"""
    response = """
⚔️ <b>BATTLE ARENA</b>

Fight other players and win prizes!

🛡️ <b>How it works:</b>
• Challenge other players to fight
• Bet money on the outcome
• Win battles to increase rating
• Unlock weapons and armor

🏆 <b>Features:</b>
• PvP battles with betting
• Training system
• Battle rankings
• Special tournaments

📊 <b>Commands:</b>
• /fight @user - Challenge to battle
• /train - Training session
• /rankings - Battle rankings
• /weapons - Buy weapons
• /armor - Buy armor

🎮 <b>Coming soon:</b> Full battle system with stats!
"""
    
    await message.answer(response, parse_mode="HTML")

@games_router.message(Command("fight"))
async def cmd_fight(message: Message, db: Database):
    """Challenge to fight"""
    try:
        from handlers.utils import get_target_user
        
        target = get_target_user(message)
        
        if not target:
            await message.answer("❌ Please reply to someone to challenge them!")
            return
        
        if target.id == message.from_user.id:
            await message.answer("❌ You cannot fight yourself!")
            return
        
        if target.is_bot:
            await message.answer("❌ Cannot fight bots!")
            return
        
        response = f"""
⚔️ <b>BATTLE CHALLENGE</b>

👤 You challenged {target.first_name} to a battle!

💡 <b>Battle System Coming Soon!</b>

The full battle system with:
• Betting on outcomes
• Weapons and armor
• Battle statistics
• Tournament mode

🎮 For now, try our other games:
• /slot - Slot machine
• /dice - Dice game
• /lottery - Lottery

⚡ Full battle system launching next update!
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Fight command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("race"))
async def cmd_race(message: Message, command: CommandObject):
    """Horse racing game"""
    try:
        # Parse bet amount
        bet = 100
        if command.args:
            try:
                bet = int(command.args)
                if bet < Config.MIN_BET:
                    await message.answer(f"❌ Minimum bet is ${Config.MIN_BET}!")
                    return
                if bet > Config.MAX_BET:
                    await message.answer(f"❌ Maximum bet is ${Config.MAX_BET}!")
                    return
            except ValueError:
                await message.answer("❌ Bet must be a number!")
                return
        
        response = f"""
🏇 <b>HORSE RACING</b>

💰 <b>Bet:</b> ${bet:,}

🎮 <b>Game coming soon!</b>

The horse racing game with:
• Multiple horses to bet on
• Live race simulation
• Odds and payouts
• Jockey and horse stats

🐎 <b>Horses available:</b>
1. Lightning Bolt ⚡
2. Midnight Runner 🌙
3. Golden Star ⭐
4. Thunder Hoof 🌩️

🎲 Try our current games:
• /slot - Slot machine
• /dice - Dice game
• /blackjack - Blackjack

🏆 Horse racing launching next week!
"""
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Race command error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message, db: Database):
    """Leaderboard of top players"""
    try:
        # Get top users by cash
        top_users = await db.fetch_all(
            """SELECT user_id, first_name, username, cash, level
               FROM users 
               WHERE is_banned = 0
               ORDER BY cash DESC
               LIMIT 10""",
            ()
        )
        
        if not top_users:
            await message.answer("📊 No users found on leaderboard!")
            return
        
        response = "🏆 <b>LEADERBOARD - TOP PLAYERS</b>\n\n"
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, user in enumerate(top_users):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            name = user['first_name']
            cash = user['cash']
            level = user['level']
            
            response += f"{medal} {name} - ${cash:,} (Level {level})\n"
        
        response += "\n📊 <b>Other Rankings:</b>"
        response += "\n💡 Coming soon: Bank balance, Family size, Battle rating"
        response += "\n🎮 Keep playing to climb the ranks!"
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@games_router.callback_query(F.data == "help_menu")
async def help_menu_callback(callback: CallbackQuery):
    """Help menu callback"""
    try:
        help_text = """
📚 <b>QUICK HELP MENU</b>

🎮 <b>Popular Games:</b>
• /slot - Slot machine
• /dice - Dice game
• /lottery - Lottery tickets
• /blackjack - Blackjack

💰 <b>Money Making:</b>
• /daily - Daily bonus
• /work - Job system
• /business - Businesses
• /stocks - Stock market

👨‍👩‍👧‍👦 <b>Family:</b>
• /family - Family tree
• /adopt - Adopt someone
• /marry - Get married

🌾 <b>Farming:</b>
• /garden - Your farm
• /plant - Plant crops
• /harvest - Harvest crops

💡 Use /help for complete command list
"""
        
        await callback.message.edit_text(help_text, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Help menu callback error: {e}")
        await callback.answer("❌ Error loading help menu")

@games_router.callback_query(F.data == "daily_bonus")
async def daily_bonus_callback(callback: CallbackQuery):
    """Daily bonus callback"""
    try:
        from handlers.family import cmd_daily
        
        # Create a mock message for the daily command
        class MockMessage:
            def __init__(self):
                self.from_user = callback.from_user
                self.bot = callback.bot
                self.answer = callback.message.answer
                self.chat = callback.message.chat
        
        mock_message = MockMessage()
        
        # Import db (this would need dependency injection)
        # For now, just show message
        await callback.message.answer(
            "💰 Click the button below to collect your daily bonus!",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="🎁 Collect Daily Bonus",
                            callback_data="collect_daily"
                        )
                    ]
                ]
            )
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Daily bonus callback error: {e}")
        await callback.answer("❌ Error loading daily bonus")
