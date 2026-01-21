import asyncio
from telethon import TelegramClient, events
import os
import sys

# ========== CORRECT CREDENTIALS ==========
API_ID = 23222481
API_HASH = 'e1774d41d4630957a8a9f3711c9b8a19'  # FIXED!
PHONE = '+256772313853'
GAME_BOT_ID = 7876606523
YOUR_ID = 6108185460
# =========================================

print("=" * 60)
print("🤖 ATTACK TITAN AUTO-GRINDER")
print("=" * 60)
print(f"API ID: {API_ID}")
print(f"API Hash: {API_HASH[:10]}...")
print(f"Phone: {PHONE}")
print(f"Game Bot: {GAME_BOT_ID}")
print("=" * 60)

# Delete old session to force new login
session_file = 'attack_titan.session'
if os.path.exists(session_file):
    print("🗑️ Removing old session file...")
    os.remove(session_file)

async def main():
    client = TelegramClient('attack_titan', API_ID, API_HASH)
    
    print("\n📱 Attempting to connect to Telegram...")
    print("📲 You will receive a code on your Telegram app!")
    
    try:
        # This will ask for phone number and code
        await client.start(phone=PHONE)
        
        print("\n" + "=" * 60)
        print("✅ LOGIN SUCCESSFUL!")
        print("=" * 60)
        
        # Get user info
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} (@{me.username})")
        
        # Send notification to yourself
        await client.send_message(YOUR_ID, 
            f"🤖 Attack Titan Auto-Grinder is ONLINE!\n"
            f"👤 Account: {me.first_name}\n"
            f"⏰ Started at: {asyncio.get_event_loop().time()}"
        )
        
        # ========== BOT LOGIC ==========
        
        # Auto-explore when idle
        @client.on(events.NewMessage(from_users=GAME_BOT_ID))
        async def auto_explore(event):
            text = event.raw_text.lower()
            
            if any(x in text for x in ['explore', 'expired', 'idle', 'waiting']):
                await asyncio.sleep(1)
                await client.send_message(GAME_BOT_ID, "/explore")
                print("🔍 Sent /explore")
        
        # Auto-battle
        @client.on(events.NewMessage(from_users=GAME_BOT_ID))
        async def auto_battle(event):
            text = event.raw_text.lower()
            
            if any(x in text for x in ['titan', 'battle', 'fight']):
                await asyncio.sleep(1)
                if event.buttons:
                    await event.click(0)  # Attack button
                else:
                    await client.send_message(GAME_BOT_ID, "/attack")
                print("⚔️ Started battle")
        
        # Auto-close
        @client.on(events.NewMessage(from_users=GAME_BOT_ID))
        async def auto_close(event):
            text = event.raw_text.lower()
            
            if any(x in text for x in ['defeated', 'victory', 'won', 'lost']):
                await asyncio.sleep(2)
                await client.send_message(GAME_BOT_ID, "/close")
                print("📭 Closed dialog")
                
                # Auto explore after battle
                await asyncio.sleep(1)
                await client.send_message(GAME_BOT_ID, "/explore")
        
        # Start auto-grinding
        print("\n⚡ Starting auto-grinding...")
        await client.send_message(GAME_BOT_ID, "/start")
        await asyncio.sleep(1)
        await client.send_message(GAME_BOT_ID, "/explore")
        
        print("\n" + "=" * 60)
        print("✅ BOT IS NOW RUNNING!")
        print("📱 Check your Telegram for game notifications")
        print("💤 Press Ctrl+C to stop the bot")
        print("=" * 60)
        
        # Keep running
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n💡 Possible solutions:")
        print("1. Check your API hash is correct")
        print("2. Make sure Telegram app is open")
        print("3. Try again in 1 minute")
        sys.exit(1)

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
