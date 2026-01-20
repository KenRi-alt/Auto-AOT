🤖 Attack Titan Auto-Grind Bot

https://img.shields.io/badge/python-3.8+-blue
https://img.shields.io/badge/Telegram-Bot-blue
https://img.shields.io/badge/license-MIT-green

An automated grinding bot for Attack Titan game that farms XP and Marks 24/7 while you're away. Perfect for lazy gamers who want to progress without manual grinding.

✨ Features

· 🤖 Fully Automated: Auto-explore, auto-battle, auto-collect resources
· 📊 Smart Logic: Realistic gameplay simulation with proper delays
· 🛡️ Battle System: 90% success rate with XP/Marks calculation
· 🔔 Notifications: Get notified when bot starts/stops/pauses
· 📈 Statistics: Track sessions, XP, Marks earned
· ⏸️ Control: Pause/Resume/Stop anytime
· 🛡️ Security: Only responds to authorized user
· ☁️ Cloud Ready: Optimized for Railway deployment

🚀 Quick Deploy

https://railway.app/button.svg

Or manually deploy:

1. Fork/Clone this repository
2. Deploy on Railway:
   · Go to Railway.app
   · Click "New Project" → "Deploy from GitHub repo"
   · Select your repository
   · Railway will automatically deploy

⚙️ Setup Instructions

1. Prerequisites

· Telegram account with Attack Titan bot access
· Your User ID: 6108185460 (already configured)
· Your Bot Token: 8302810352:AAHzhQdIgMB71mEKcZcFW8uNVJ_EPtpu0es (already in code)

2. Local Setup (Optional)

```bash
# Clone the repository
git clone https://github.com/yourusername/attack-titan-bot.git
cd attack-titan-bot

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

📋 Commands

Command Description Example
/start Initialize bot & show welcome /start
/grind Start/Stop auto-grinding /grind
/status Check current stats /status
/pause Pause grinding /pause
/resume Resume grinding /resume
/reset Reset statistics /reset

🎮 How It Works

1. Exploration Phase: Bot sends /explore command
2. Encounter Check: 65% chance of finding Titan
3. Battle Phase: Auto-battle with 90% success rate
4. Rewards: Collects XP (120-160) and Marks (38-48)
5. Cleanup: Closes dialogs with /close
6. Repeat: Every 15-20 seconds

📊 Sample Output

```
🎉 Titan Defeated!
XP: +142
Marks: +42

💎 Session Total
XP: 284
Marks: 84
```

🛠️ Configuration

Edit bot.py to customize:

```python
# Timing settings
CHECK_INTERVAL = 15  # Seconds between cycles
BATTLE_COOLDOWN = 8  # Seconds after battle

# Game settings
ENCOUNTER_RATE = 0.65  # 65% chance of finding Titan
SUCCESS_RATE = 0.90    # 90% battle success rate

# Rewards range
XP_MIN = 120
XP_MAX = 160
MARKS_MIN = 38
MARKS_MAX = 48
```

🌐 Railway Deployment

Environment Variables

The bot already has your credentials hardcoded, but you can set these in Railway dashboard:

Variable Value Required
BOT_TOKEN 8302810352:AAHzhQdIgMB71mEKcZcFW8uNVJ_EPtpu0es ✅
USER_ID 6108185460 ✅

Railway Specifics

· Build Command: Automatic (detects Python)
· Start Command: python bot.py
· Health Check: None needed (polling bot)
· Restart Policy: Auto-restart on failure

📁 Project Structure

```
attack-titan-bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── Procfile           # Railway process file
├── railway.json       # Railway configuration
├── Dockerfile         # Docker container (optional)
└── README.md          # This file
```

🔧 Troubleshooting

Common Issues

1. Bot not responding
   · Check if your User ID is correct
   · Verify bot token is valid
   · Ensure bot is running on Railway
2. No XP/Marks being earned
   · Increase CHECK_INTERVAL if too fast
   · Check Telegram bot is responsive
   · Verify game mechanics haven't changed
3. Railway deployment failing
   · Check requirements.txt format
   · Verify Procfile exists
   · Check Railway logs for errors

Logs

· Railway: Dashboard → Project → Logs
· Local: Check console output
· Bot status: Use /status command

⚠️ Disclaimer

⚠️ Use at your own risk!

· This bot is for educational purposes
· May violate game Terms of Service
· Use responsibly and moderately
· I'm not responsible for any bans or issues

📄 License

MIT License - see LICENSE file

🤝 Contributing

Feel free to fork and improve:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

📞 Support

For issues/questions:

1. Check Troubleshooting section
2. Open a GitHub Issue
3. Contact via Telegram

---

Made with ❤️ for lazy gamers everywhere

Happy Auto-Grinding! 🎮⚡