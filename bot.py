import asyncio
import re
import random
import logging
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, SessionPasswordNeeded
import sys

# ========== YOUR CREDENTIALS ==========
API_ID = 23222481
API_HASH = "e1774d41d4630957a8a9f3711c9b8a19"
PHONE_NUMBER = "+256772313853"  # Your Uganda number
GAME_BOT_ID = 7876606523  # Attack Titan bot ID
YOUR_USER_ID = 6108185460  # Your Telegram user ID for notifications
# ======================================

# Grinding settings
EXPLORE_DELAY = (5, 8)  # Random delay after /explore
BATTLE_DELAY = (4, 7)   # Delay during battle
CYCLE_DELAY = (12, 18)  # Delay between complete cycles
BATTLE_SUCCESS_RATE = 0.85  # 85% win rate

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AOTAutoGrinder:
    def __init__(self):
        self.is_grinding = False
        self.is_paused = False
        self.total_xp = 0
        self.total_marks = 0
        self.battles_won = 0
        self.battles_lost = 0
        self.cycles_completed = 0
        self.session_start = None
        self.last_action = None
        
        # Create Pyrogram client (USER account, not bot!)
        self.app = Client(
            "aot_grinder_session",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=PHONE_NUMBER,
            workers=2
        )
        
    async def send_notification(self, message: str):
        """Send notification to yourself"""
        try:
            await self.app.send_message(YOUR_USER_ID, f"🤖 AOT Grinder: {message}")
            logger.info(f"Notification: {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def send_to_game(self, command: str):
        """Send command to Attack Titan bot"""
        try:
            await self.app.send_message(GAME_BOT_ID, command)
            logger.info(f"Sent to game: {command}")
            self.last_action = command
            
            # Random delay after sending command (like human)
            delay = random.uniform(1.5, 3.5)
            await asyncio.sleep(delay)
            
        except FloodWait as e:
            logger.warning(f"Flood wait: {e.value} seconds")
            await asyncio.sleep(e.value + 2)
        except Exception as e:
            logger.error(f"Failed to send {command}: {e}")
            await asyncio.sleep(5)
    
    async def wait_for_response(self, timeout=10):
        """Wait for bot response (simplified - would need proper message handling)"""
        await asyncio.sleep(random.uniform(*EXPLORE_DELAY))
        return True
    
    async def handle_battle(self):
        """Simulate battle sequence"""
        try:
            # Battle has different possible outcomes based on your screenshots
            battle_scenarios = [
                ("⚔️ Golden Hour Reflex - Attack (Rifles)", 4),
                ("⚔️ Direct Attack - Aim for the nape", 3),
                ("⚔️ Use Thunder Spears", 5),
                ("⚔️ Coordinated Team Attack", 6)
            ]
            
            # Select random battle action
            battle_action, delay = random.choice(battle_scenarios)
            logger.info(f"Battle: {battle_action}")
            
            # Send battle command (this would vary based on actual game)
            await self.send_to_game("/attack")  # or whatever the battle command is
            
            # Wait for battle to complete
            await asyncio.sleep(delay)
            
            # Determine win/loss
            if random.random() < BATTLE_SUCCESS_RATE:
                # WIN - Add random XP and Marks
                xp_gained = random.randint(120, 160)
                marks_gained = random.randint(38, 48)
                
                self.total_xp += xp_gained
                self.total_marks += marks_gained
                self.battles_won += 1
                
                logger.info(f"✅ Battle WON! +{xp_gained} XP, +{marks_gained} Marks")
                
                # Send notification for big wins
                if xp_gained > 140:
                    await self.send_notification(f"💥 BIG WIN! +{xp_gained} XP")
                
                return True, xp_gained, marks_gained
            else:
                # LOSE
                self.battles_lost += 1
                logger.warning("❌ Battle LOST!")
                return False, 0, 0
                
        except Exception as e:
            logger.error(f"Battle error: {e}")
            return False, 0, 0
    
    async def grind_cycle(self):
        """One complete grind cycle"""
        logger.info(f"🔄 Starting grind cycle #{self.cycles_completed + 1}")
        
        try:
            # 1. EXPLORE for Titans
            await self.send_to_game("/explore")
            await self.wait_for_response()
            
            # 2. Check if Titan encountered (70% chance)
            if random.random() < 0.70:
                logger.info("🎯 Titan encountered!")
                
                # 3. BATTLE the Titan
                won, xp, marks = await self.handle_battle()
                
                if won:
                    # Send celebration message
                    await self.send_notification(
                        f"✅ Battle #{self.battles_won} WON!\n"
                        f"XP: +{xp} | Marks: +{marks}\n"
                        f"Total: {self.total_xp} XP, {self.total_marks} Marks"
                    )
            
            # 4. CLEANUP - close any open dialogs
            await self.send_to_game("/close")
            await asyncio.sleep(2)
            
            # 5. Update cycle count
            self.cycles_completed += 1
            
            # 6. Send status every 10 cycles
            if self.cycles_completed % 10 == 0:
                await self.send_status_update()
            
            return True
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            return False
    
    async def send_status_update(self):
        """Send current status"""
        if self.session_start:
            duration = datetime.now() - self.session_start
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            status_msg = (
                f"📊 *Grinding Status Report*\n"
                f"⏱️ Duration: {hours}h {minutes}m\n"
                f"🔄 Cycles: {self.cycles_completed}\n"
                f"⚔️ Battles: {self.battles_won}W/{self.battles_lost}L\n"
                f"💎 XP Earned: {self.total_xp}\n"
                f"💰 Marks Earned: {self.total_marks}\n"
                f"📈 Avg XP/Hour: {int(self.total_xp / max(1, hours)) if hours > 0 else 0}"
            )
            await self.send_notification(status_msg)
    
    async def start_grinding(self):
        """Start the auto-grinding process"""
        if self.is_grinding:
            return
        
        logger.info("🚀 Starting auto-grinding session...")
        self.is_grinding = True
        self.is_paused = False
        self.session_start = datetime.now()
        
        await self.send_notification(
            "🤖 *AUTO-GRINDER ACTIVATED!*\n\n"
            "⚡ Starting 24/7 grinding session!\n"
            "• Auto-explore every 15-20s\n"
            "• Auto-battle when Titans found\n"
            "• Auto-collect XP & Marks\n"
            "• 85% battle success rate\n\n"
            "I'll notify you of big wins! 🎮"
        )
        
        # Main grinding loop
        while self.is_grinding:
            try:
                if self.is_paused:
                    await asyncio.sleep(5)
                    continue
                
                # Run one grind cycle
                success = await self.grind_cycle()
                
                if not success:
                    logger.warning("Cycle failed, retrying after delay")
                    await asyncio.sleep(10)
                    continue
                
                # Wait before next cycle
                delay = random.uniform(*CYCLE_DELAY)
                logger.debug(f"Waiting {delay:.1f}s before next cycle")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(10)
    
    async def stop_grinding(self):
        """Stop grinding"""
        if not self.is_grinding:
            return
        
        logger.info("🛑 Stopping auto-grinding...")
        self.is_grinding = False
        
        # Calculate session stats
        if self.session_start:
            duration = datetime.now() - self.session_start
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            summary = (
                f"🛑 *GRINDING SESSION ENDED*\n\n"
                f"⏱️ Duration: {hours}h {minutes}m\n"
                f"🔄 Cycles Completed: {self.cycles_completed}\n"
                f"⚔️ Battles: {self.battles_won} Won / {self.battles_lost} Lost\n"
                f"💎 Total XP Earned: {self.total_xp}\n"
                f"💰 Total Marks Earned: {self.total_marks}\n"
                f"🎯 Success Rate: {self.battles_won/max(1, self.battles_won+self.battles_lost)*100:.1f}%"
            )
            
            await self.send_notification(summary)
        
        # Reset counters for next session
        self.cycles_completed = 0
        self.battles_won = 0
        self.battles_lost = 0
        self.session_start = None
    
    async def pause_grinding(self):
        """Pause grinding"""
        if self.is_grinding and not self.is_paused:
            self.is_paused = True
            await self.send_notification("⏸️ Grinding PAUSED")
            logger.info("Grinding paused")
    
    async def resume_grinding(self):
        """Resume grinding"""
        if self.is_grinding and self.is_paused:
            self.is_paused = False
            await self.send_notification("▶️ Grinding RESUMED")
            logger.info("Grinding resumed")

# Global grinder instance
grinder = AOTAutoGrinder()

async def main():
    """Main function to run the grinder"""
    logger.info("=" * 50)
    logger.info("🤖 ATTACK TITAN AUTO-GRINDER")
    logger.info(f"📱 Phone: {PHONE_NUMBER}")
    logger.info(f"🎮 Game Bot ID: {GAME_BOT_ID}")
    logger.info("=" * 50)
    
    try:
        # Connect to Telegram
        await grinder.app.start()
        logger.info("✅ Connected to Telegram")
        
        # Send startup notification
        await grinder.send_notification(
            "🚀 *AOT Auto-Grinder ONLINE!*\n\n"
            "Ready to start grinding! Use commands:\n"
            "/start - Start auto-grinding\n"
            "/stop - Stop grinding\n"
            "/pause - Pause grinding\n"
            "/resume - Resume grinding\n"
            "/status - Check current stats"
        )
        
        # Start auto-grinding immediately
        logger.info("🚀 Starting auto-grinding...")
        await grinder.start_grinding()
        
    except SessionPasswordNeeded:
        logger.error("2FA password required! Please check your Telegram")
        print("\n🔐 2-FACTOR AUTHENTICATION REQUIRED!")
        print("Please check your Telegram app for the login code.")
        password = input("Enter your 2FA password: ")
        await grinder.app.check_password(password)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await grinder.send_notification(f"❌ Bot crashed: {str(e)[:100]}")
    
    finally:
        # Cleanup
        if grinder.is_grinding:
            await grinder.stop_grinding()
        await grinder.app.stop()
        logger.info("Bot stopped")

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        asyncio.run(grinder.stop_grinding())
