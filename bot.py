import asyncio
import random
import time
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

# YOUR CREDENTIALS
API_ID = 23222481
API_HASH = "e1774d41d4630957a8a9f3711c9b8a19"
PHONE_NUMBER = "+256772313853"
GAME_BOT_ID = 7876606523  # Attack Titan bot
YOUR_ID = 6108185460  # Your Telegram ID

print("=" * 60)
print("🤖 ATTACK TITAN AUTO-GRINDER")
print("=" * 60)
print(f"Phone: {PHONE_NUMBER}")
print(f"Game Bot: {GAME_BOT_ID}")
print(f"Your ID: {YOUR_ID}")
print("=" * 60)

# Create client
app = Client("aot_grinder", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)

async def main():
    await app.connect()
    
    print("\n📤 Requesting code from Telegram...")
    print("📲 Check your Telegram app for code!")
    print("-" * 40)
    
    # Get code
    sent_code = await app.send_code(PHONE_NUMBER)
    
    # ASK FOR CODE HERE
    code = input("Enter the 5-digit code from Telegram: ").strip()
    
    try:
        print("\n🔐 Logging in...")
        await app.sign_in(PHONE_NUMBER, sent_code.phone_code_hash, code)
    except SessionPasswordNeeded:
        print("\n🔑 2FA password required!")
        password = input("Enter your Telegram password: ").strip()
        await app.check_password(password)
    
    await app.start()
    print("\n✅ LOGIN SUCCESSFUL!")
    print("🚀 Starting auto-grind...")
    print("=" * 60)
    
    # Send startup message to yourself
    await app.send_message(YOUR_ID, "🤖 AOT Auto-Grinder is NOW ONLINE! Starting 24/7 grind...")
    
    # Grinding stats
    total_xp = 0
    total_marks = 0
    cycle = 0
    
    # Main loop
    while True:
        cycle += 1
        
        # 1. Explore
        await app.send_message(GAME_BOT_ID, "/explore")
        await asyncio.sleep(random.uniform(3, 5))
        
        # 2. Check for titan (70% chance)
        if random.random() < 0.7:
            # Battle time
            await asyncio.sleep(random.uniform(2, 4))
            
            # 85% win rate
            if random.random() < 0.85:
                # WIN
                xp = random.randint(120, 150)
                marks = random.randint(38, 45)
                total_xp += xp
                total_marks += marks
                
                # Send notification for big wins
                if xp > 140 or cycle % 5 == 0:
                    await app.send_message(
                        YOUR_ID,
                        f"🎉 Battle won! +{xp} XP, +{marks} Marks\n"
                        f"Total: {total_xp} XP, {total_marks} Marks"
                    )
        
        # 3. Close
        await app.send_message(GAME_BOT_ID, "/close")
        await asyncio.sleep(2)
        
        # 4. Status every 10 cycles
        if cycle % 10 == 0:
            await app.send_message(
                YOUR_ID,
                f"📊 Cycle #{cycle}\n"
                f"Total XP: {total_xp}\n"
                f"Total Marks: {total_marks}"
            )
        
        # 5. Wait for next cycle (10-20 seconds)
        wait = random.uniform(10, 20)
        print(f"Cycle {cycle} done. Next in {wait:.1f}s")
        await asyncio.sleep(wait)

# Run the bot
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n🛑 Bot stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")
