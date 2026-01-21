import asyncio
from telethon import TelegramClient, events
from telethon.errors import MessageIdInvalidError

# ========== YOUR CREDENTIALS ==========
api_id = 23222481
api_hash = 'e1774d41d4630957a8a9f3711c9b8a19'
phone = '+256772313853'
GAME_BOT_ID = 7876606523  # Attack Titan bot
YOUR_ID = 6108185460  # Your Telegram ID
# ======================================

async def main():
    client = TelegramClient('attack_titan_session', api_id, api_hash)
    
    await client.start(phone=phone)
    print("✅ Logged in!")
    print("🤖 Bot is now running...")
    
    # Send notification to yourself
    await client.send_message(YOUR_ID, "🤖 Attack Titan Auto-Grinder is ONLINE! Starting...")
    
    # ========== AUTO-EXPLORE ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_explore(event):
        # Auto explore when idle
        if "use /explore" in event.raw_text.lower() or "encounter expired" in event.raw_text.lower():
            await asyncio.sleep(1)
            await event.client.send_message(GAME_BOT_ID, "/explore")
    
    # ========== AUTO-BATTLE ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_battle(event):
        # Battle when Titan appears
        if any(word in event.raw_text.lower() for word in ['titan', 'battle', 'fight', 'combat']):
            await asyncio.sleep(1.5)
            
            # Click attack button if available
            if event.buttons:
                try:
                    await event.click(0)  # Click first button (usually Attack)
                except:
                    await event.client.send_message(GAME_BOT_ID, "/attack")
    
    # ========== AUTO-CLOSE ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_close(event):
        # Close after battle results
        if "defeated" in event.raw_text.lower() or "won" in event.raw_text.lower() or "victory" in event.raw_text.lower():
            await asyncio.sleep(2)
            await event.client.send_message(GAME_BOT_ID, "/close")
    
    # ========== AUTO-REVIVE ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_revive(event):
        # Auto revive if dead
        if "dead" in event.raw_text.lower() or "revive" in event.raw_text.lower():
            await asyncio.sleep(1)
            await event.client.send_message(GAME_BOT_ID, "/revive")
            await asyncio.sleep(1)
            await event.client.send_message(GAME_BOT_ID, "/explore")
    
    # ========== CAPTCHA HANDLING ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_captcha(event):
        # Notify for captcha
        if "captcha" in event.raw_text.lower() or "verify" in event.raw_text.lower():
            await event.client.send_message(YOUR_ID, "🚨 CAPTCHA REQUIRED! Please check!")
    
    # ========== XP/MARKS NOTIFICATION ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_rewards(event):
        # Notify big rewards
        if "xp:" in event.raw_text.lower() or "marks:" in event.raw_text.lower():
            if "+" in event.raw_text:
                await asyncio.sleep(1)
                await event.client.send_message(YOUR_ID, f"🎉 Reward received!\n{event.raw_text[:100]}")
    
    # ========== ERROR HANDLING ==========
    @client.on(events.NewMessage(from_users=GAME_BOT_ID))
    async def handle_errors(event):
        # Handle cooldowns
        if "wait" in event.raw_text.lower() or "cooldown" in event.raw_text.lower():
            await asyncio.sleep(5)
            await event.client.send_message(GAME_BOT_ID, "/explore")
    
    # ========== START AUTO-GRINDING ==========
    await asyncio.sleep(2)
    await client.send_message(GAME_BOT_ID, "/start")
    await asyncio.sleep(1)
    await client.send_message(GAME_BOT_ID, "/explore")
    
    print("⚡ Auto-grinding started!")
    
    # Keep bot running forever
    await client.run_until_disconnected()

# Run the bot
if __name__ == "__main__":
    print("🤖 Starting Attack Titan Auto-Grinder...")
    print(f"📱 Phone: {phone}")
    print(f"🎮 Game Bot: {GAME_BOT_ID}")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
