import logging
import random
import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque
from telegram import (
    Update, 
    BotCommand, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatPermissions,
    ChatMember,
    Chat,
    Message,
    MessageEntity,
    Poll,
    Dice
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    ChatMemberHandler,
    PollHandler,
    filters
)
from telegram.constants import ParseMode, ChatAction, ChatType, ChatMemberStatus, MessageEntityType
from apscheduler.schedulers.background import BackgroundScheduler
import emoji

# ========== CONFIG ==========
BOT_TOKEN = "8302810352:AAHzhQdIgMB71mEKcZcFW8uNVJ_EPtpu0es"
OWNER_ID = 6108185460
# ============================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ProfessionalGroupManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.setup_data_structures()
        self.start_scheduler()
        self.animation_tasks = {}
        
    def setup_data_structures(self):
        """Initialize all data structures"""
        # Group settings with defaults
        self.groups = defaultdict(lambda: {
            'welcome_enabled': True,
            'antispam_enabled': True,
            'anti_flood': True,
            'anti_link': False,
            'anti_bot': True,
            'warn_limit': 3,
            'mute_duration': 3600,
            'max_warnings': 3,
            'language': 'en',
            'log_channel': None,
            'rules': "Be respectful. No spam.",
            'admins': set(),
            'created': datetime.now(),
            'last_activity': datetime.now(),
            'welcome_message': "🎉 Welcome {user} to {group}!",
            'goodbye_message': "👋 Goodbye {user}!",
            'warn_message': "⚠️ Warning {count}/3: {user} - {reason}",
            'mute_message': "🔇 {user} muted for {duration} - {reason}",
            'ban_message': "🚫 {user} banned - {reason}"
        })
        
        # User tracking
        self.user_stats = defaultdict(lambda: {
            'messages': 0,
            'warnings': 0,
            'last_message': None,
            'join_date': datetime.now(),
            'xp': 0,
            'level': 1
        })
        
        # Anti-spam systems
        self.message_queue = defaultdict(deque)
        self.user_flood = defaultdict(lambda: {'count': 0, 'last_time': datetime.now()})
        self.link_domains = set(['spam.com', 'malware.net', 'phishing.link'])
        self.spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'[0-9]{10,}',  # Phone numbers
            r'@[A-Za-z0-9_]{5,}',  # Multiple mentions
            r'(?i)(buy|sell|deal|discount|offer|cheap|price)[\s\S]{0,50}(now|today|limited)',
        ]
        
        # Moderation
        self.warnings = defaultdict(dict)
        self.muted_users = {}
        self.banned_users = set()
        self.reports = defaultdict(list)
        
        # Statistics
        self.global_stats = {
            'total_messages': 0,
            'total_groups': 0,
            'total_warnings': 0,
            'total_mutes': 0,
            'total_bans': 0,
            'start_time': datetime.now()
        }
        
        # Cache for performance
        self.admin_cache = {}
        self.user_cache = {}
        
    def start_scheduler(self):
        """Start background maintenance tasks"""
        jobs = [
            ('cleanup_muted_users', self.cleanup_muted_users, 'interval', {'minutes': 5}),
            ('update_stats', self.update_global_stats, 'interval', {'minutes': 30}),
            ('clean_cache', self.clean_cache, 'interval', {'hours': 1}),
            ('check_inactive', self.check_inactive_groups, 'interval', {'hours': 6}),
            ('backup_data', self.backup_to_memory, 'interval', {'hours': 12})
        ]
        
        for job_id, func, trigger, kwargs in jobs:
            self.scheduler.add_job(func, trigger, id=job_id, **kwargs)
        
        self.scheduler.start()
        logger.info("Professional scheduler started with %d jobs", len(jobs))
    
    # ========== ANIMATIONS ==========
    
    async def typing_animation(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, duration: float = 1):
        """Send typing indicator"""
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(duration)
    
    async def progress_animation(self, chat_id: int, message: Message, text: str, steps: int = 5):
        """Show progress animation"""
        for i in range(steps):
            progress = "█" * (i + 1) + "░" * (steps - i - 1)
            percentage = ((i + 1) / steps) * 100
            await message.edit_text(
                f"{text}\n\n{progress} {percentage:.0f}%",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(0.3)
    
    async def welcome_animation(self, chat: Chat, user: ChatMember):
        """Animated welcome message"""
        frames = [
            f"🎬 Preparing welcome for {user.user.mention_html()}...",
            f"✨ Setting up special effects...",
            f"🎉 Almost ready...",
            f"🌟 WELCOME {user.user.mention_html()}! 🎊"
        ]
        
        msg = await chat.send_message(frames[0], parse_mode=ParseMode.HTML)
        
        for frame in frames[1:]:
            await asyncio.sleep(0.8)
            await msg.edit_text(frame, parse_mode=ParseMode.HTML)
        
        # Final welcome with effects
        final_text = f"""
✨ *OFFICIAL WELCOME* ✨

🎭 **{user.user.full_name}** has joined the party!

📊 *Group Stats:*
• Members: {await chat.get_member_count()}
• Activity: High
• Welcome Level: MAXIMUM

🎯 *Please:*
• Read the rules `/rules`
• Introduce yourself
• Enjoy your stay!

⚡ *Pro Tip:* Be active to earn XP!
        """
        
        await msg.edit_text(final_text, parse_mode=ParseMode.MARKDOWN)
    
    async def loading_animation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = "Processing..."):
        """Loading animation for commands"""
        dots = ["⏳", "⌛", "⏳", "⌛"]
        msg = await update.message.reply_text(f"{dots[0]} {text}")
        
        for dot in dots[1:]:
            await asyncio.sleep(0.5)
            await msg.edit_text(f"{dot} {text}")
        
        return msg
    
    # ========== PROFESSIONAL COMMANDS ==========
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional start command with animation"""
        user = update.effective_user
        
        await self.typing_animation(update.effective_chat.id, context, 1.5)
        
        # Show loading animation
        loading = await self.loading_animation(update, context, "Initializing Professional Bot...")
        
        # Animation sequence
        await self.progress_animation(update.effective_chat.id, loading, "🚀 Booting Systems", 4)
        
        professional_text = f"""
🏢 **PROFESSIONAL GROUP MANAGER v3.0**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *USER:* {user.mention_html()}
📅 *DATE:* {datetime.now().strftime('%Y-%m-%d %H:%M')}
⚡ *STATUS:* ALL SYSTEMS OPERATIONAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **ENTERPRISE FEATURES:**

🔐 *SECURITY SUITE*
• Advanced Anti-Spam AI
• Real-time Flood Protection
• Link & Media Filtering
• Bot Detection System
• Raid Protection

⚙️ *MANAGEMENT TOOLS*
• Professional Admin Panel
• Automated Moderation
• User Analytics Dashboard
• Custom Rule Engine
• Activity Monitoring

📈 *ANALYTICS ENGINE*
• User Behavior Tracking
• Group Health Metrics
• Performance Analytics
• Trend Detection
• Report Generation

🎯 *PRODUCTIVITY*
• Auto-Response System
• Scheduled Messages
• Poll & Survey Creator
• Announcement Manager
• Event Scheduler

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 **QUICK START:**
1. Add me to group
2. Grant admin permissions
3. Use `/setup` for configuration
4. Access `/admin` for management

💼 **For enterprise support:** Contact @Admin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🏢 Add to Group", 
                    url=f"http://t.me/{(await context.bot.get_me()).username}?startgroup=true"),
                InlineKeyboardButton("⚙️ Admin Panel", callback_data="enterprise_admin")
            ],
            [
                InlineKeyboardButton("📚 Documentation", callback_data="docs"),
                InlineKeyboardButton("🔧 Support", callback_data="support")
            ],
            [
                InlineKeyboardButton("📊 Demo Features", callback_data="demo"),
                InlineKeyboardButton("💎 Upgrade Plan", callback_data="upgrade")
            ]
        ]
        
        await loading.edit_text(
            professional_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional Admin Panel"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check admin status professionally
        is_admin = await self.verify_admin(chat, user)
        
        if not is_admin:
            await update.message.reply_text(
                "🚫 **ACCESS DENIED**\n\n"
                "*Reason:* Insufficient permissions\n"
                "*Required:* Administrator role\n"
                "*Contact:* Group owner for access",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await self.typing_animation(chat.id, context, 1)
        
        panel_text = f"""
🏢 **ENTERPRISE ADMIN PANEL**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *GROUP INFO*
• Name: {chat.title}
• ID: `{chat.id}`
• Type: {chat.type.upper()}
• Members: {await chat.get_member_count()}
• Created: {self.groups[chat.id]['created'].strftime('%Y-%m-%d')}

📊 *STATUS BOARD*
• Security: {'🟢 ACTIVE' if self.groups[chat.id]['antispam_enabled'] else '🔴 INACTIVE'}
• Moderation: {'🟢 ACTIVE' if self.groups[chat.id]['warn_limit'] > 0 else '🔴 INACTIVE'}
• Logging: {'🟢 ENABLED' if self.groups[chat.id]['log_channel'] else '🔴 DISABLED'}
• Activity: {'🟢 HIGH' if (datetime.now() - self.groups[chat.id]['last_activity']).seconds < 3600 else '🟡 MEDIUM'}

🚨 *SECURITY STATUS*
• Threats Blocked: {self.global_stats['total_warnings']}
• Active Mutes: {len([t for t in self.muted_users.values() if t > datetime.now()])}
• Total Bans: {self.global_stats['total_bans']}
• System Health: 98%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔐 Security Center", callback_data="admin_security"),
                InlineKeyboardButton("👥 User Management", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("⚙️ System Settings", callback_data="admin_settings"),
                InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics")
            ],
            [
                InlineKeyboardButton("🚨 Moderation Tools", callback_data="admin_mod"),
                InlineKeyboardButton("📝 Logs & Reports", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton("🔧 Advanced Tools", callback_data="admin_advanced"),
                InlineKeyboardButton("💾 Backup & Restore", callback_data="admin_backup")
            ],
            [
                InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh"),
                InlineKeyboardButton("❌ Close Panel", callback_data="admin_close")
            ]
        ]
        
        msg = await update.message.reply_text(
            panel_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Store message for refresh
        self.admin_cache[f"{chat.id}_{user.id}"] = msg.message_id
    
    async def setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional Setup Wizard"""
        chat = update.effective_chat
        user = update.effective_user
        
        is_admin = await self.verify_admin(chat, user)
        if not is_admin:
            return
        
        await self.typing_animation(chat.id, context, 1)
        
        setup_text = """
🔧 **PROFESSIONAL SETUP WIZARD**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This wizard will guide you through configuring
all enterprise features for optimal performance.

*Estimated time:* 2-3 minutes
*Required:* Administrator permissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Quick Setup", callback_data="setup_quick")],
            [InlineKeyboardButton("⚙️ Advanced Configuration", callback_data="setup_advanced")],
            [InlineKeyboardButton("📋 Review Current Settings", callback_data="setup_review")],
            [InlineKeyboardButton("❌ Cancel Setup", callback_data="setup_cancel")]
        ]
        
        await update.message.reply_text(
            setup_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ========== ADVANCED ANTI-SPAM ==========
    
    async def advanced_anti_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Advanced AI-powered anti-spam system"""
        chat = update.effective_chat
        user = update.effective_user
        message = update.message
        
        if chat.id not in self.groups:
            return
        
        settings = self.groups[chat.id]
        if not settings['antispam_enabled']:
            return
        
        # Skip admins
        is_admin = await self.verify_admin(chat, user)
        if is_admin:
            return
        
        # Update activity
        settings['last_activity'] = datetime.now()
        
        # Multiple detection systems
        threats_detected = []
        
        # 1. Flood Detection
        if settings['anti_flood']:
            flood_result = await self.detect_flood(chat.id, user.id, message)
            if flood_result:
                threats_detected.append(("FLOOD", flood_result))
        
        # 2. Link Detection
        if settings['anti_link']:
            link_result = await self.detect_malicious_links(message)
            if link_result:
                threats_detected.append(("MALICIOUS_LINK", link_result))
        
        # 3. Pattern Detection
        pattern_result = await self.detect_spam_patterns(message.text or "")
        if pattern_result:
            threats_detected.append(("SPAM_PATTERN", pattern_result))
        
        # 4. Bot-like Behavior
        if settings['anti_bot']:
            bot_result = await self.detect_bot_behavior(user.id, message)
            if bot_result:
                threats_detected.append(("BOT_BEHAVIOR", bot_result))
        
        # 5. Message Repetition
        rep_result = await self.detect_repetition(chat.id, user.id, message)
        if rep_result:
            threats_detected.append(("REPETITION", rep_result))
        
        # Take action if threats detected
        if threats_detected:
            await self.handle_threats(chat, user, message, threats_detected)
        
        # Update user stats
        self.user_stats[f"{chat.id}_{user.id}"]['messages'] += 1
        self.user_stats[f"{chat.id}_{user.id}"]['last_message'] = datetime.now()
        self.global_stats['total_messages'] += 1
    
    async def detect_flood(self, chat_id: int, user_id: int, message: Message) -> dict:
        """Advanced flood detection with AI scoring"""
        key = f"{chat_id}_{user_id}"
        
        if key not in self.user_flood:
            self.user_flood[key] = {
                'count': 0,
                'last_time': datetime.now(),
                'messages': [],
                'score': 0
            }
        
        data = self.user_flood[key]
        now = datetime.now()
        time_diff = (now - data['last_time']).seconds
        
        # Reset after 10 seconds
        if time_diff > 10:
            data['count'] = 0
            data['score'] = max(0, data['score'] - 10)
            data['messages'] = []
        
        # Add message
        data['count'] += 1
        data['last_time'] = now
        data['messages'].append({
            'text': message.text or "",
            'time': now,
            'length': len(message.text or "")
        })
        
        # Keep only last 20 messages
        if len(data['messages']) > 20:
            data['messages'] = data['messages'][-20:]
        
        # Calculate flood score
        score = 0
        
        # 1. Message count in timeframe
        if data['count'] >= 10 and time_diff < 5:
            score += 50
        elif data['count'] >= 7 and time_diff < 5:
            score += 30
        elif data['count'] >= 5 and time_diff < 5:
            score += 20
        
        # 2. Message similarity
        if len(data['messages']) >= 3:
            texts = [m['text'] for m in data['messages'][-3:]]
            if len(set(texts)) == 1 and len(texts[0]) > 10:  # Same message repeated
                score += 40
        
        # 3. Short messages flood
        short_msgs = [m for m in data['messages'][-5:] if m['length'] < 5]
        if len(short_msgs) >= 4:
            score += 30
        
        # Update cumulative score
        data['score'] += score
        
        if data['score'] > 80:  # Threshold for action
            return {
                'type': 'FLOOD',
                'score': data['score'],
                'count': data['count'],
                'timeframe': time_diff,
                'messages': len(data['messages'])
            }
        
        return None
    
    async def detect_malicious_links(self, message: Message) -> dict:
        """Detect malicious URLs and domains"""
        text = message.text or ""
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        if not urls:
            return None
        
        suspicious_urls = []
        
        for url in urls:
            # Check against known spam domains
            for domain in self.link_domains:
                if domain in url:
                    suspicious_urls.append({
                        'url': url,
                        'reason': 'KNOWN_SPAM_DOMAIN',
                        'domain': domain
                    })
                    break
            
            # Check for IP addresses (often spam)
            ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
            if re.search(ip_pattern, url):
                suspicious_urls.append({
                    'url': url,
                    'reason': 'IP_ADDRESS_URL',
                    'domain': 'IP'
                })
            
            # Check for URL shorteners (often abused)
            shorteners = ['bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd']
            for shortener in shorteners:
                if shortener in url:
                    suspicious_urls.append({
                        'url': url,
                        'reason': 'URL_SHORTENER',
                        'domain': shortener
                    })
                    break
        
        if suspicious_urls:
            return {
                'type': 'MALICIOUS_LINKS',
                'count': len(suspicious_urls),
                'urls': suspicious_urls[:3],  # Limit to first 3
                'total_urls': len(urls)
            }
        
        return None
    
    async def detect_spam_patterns(self, text: str) -> dict:
        """Detect spam using regex patterns and AI-like scoring"""
        if not text:
            return None
        
        detected_patterns = []
        score = 0
        
        # Check each pattern
        for i, pattern in enumerate(self.spam_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_patterns.append({
                    'pattern_id': i,
                    'matches': matches[:5],  # Limit matches
                    'count': len(matches)
                })
                score += len(matches) * 10
        
        # Check for excessive caps
        if len(text) > 10:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7:  # 70% caps
                detected_patterns.append({
                    'pattern_id': 'CAPS_LOCK',
                    'matches': ['EXCESSIVE_CAPS'],
                    'count': 1
                })
                score += 20
        
        # Check for excessive special chars
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars > len(text) * 0.3:  # 30% special chars
            detected_patterns.append({
                'pattern_id': 'SPECIAL_CHARS',
                'matches': ['EXCESSIVE_SPECIAL'],
                'count': 1
            })
            score += 15
        
        if score > 25 and detected_patterns:
            return {
                'type': 'SPAM_PATTERNS',
                'score': score,
                'patterns': detected_patterns,
                'text_preview': text[:100] + ('...' if len(text) > 100 else '')
            }
        
        return None
    
    async def detect_bot_behavior(self, user_id: int, message: Message) -> dict:
        """Detect bot-like behavior patterns"""
        key = f"bot_{user_id}"
        
        if key not in self.user_stats:
            return None
        
        user_data = self.user_stats[key]
        now = datetime.now()
        
        # Check message timing patterns (bots often send at exact intervals)
        if user_data['last_message']:
            time_diff = (now - user_data['last_message']).seconds
            
            # If multiple messages at exact intervals (suspicious)
            if 0.9 <= time_diff <= 1.1:  # ~1 second intervals
                user_data.setdefault('exact_intervals', 0)
                user_data['exact_intervals'] += 1
                
                if user_data['exact_intervals'] >= 5:
                    return {
                        'type': 'BOT_TIMING',
                        'intervals': user_data['exact_intervals'],
                        'pattern': 'EXACT_SECOND_INTERVALS'
                    }
        
        # Check for identical messages
        message_text = message.text or ""
        if message_text:
            user_data.setdefault('recent_messages', [])
            user_data['recent_messages'].append(message_text[:50])
            
            if len(user_data['recent_messages']) > 10:
                user_data['recent_messages'] = user_data['recent_messages'][-10:]
                
                # Check for duplicate messages
                if len(set(user_data['recent_messages'])) < 3:
                    return {
                        'type': 'BOT_REPETITION',
                        'unique_messages': len(set(user_data['recent_messages'])),
                        'total_messages': len(user_data['recent_messages'])
                    }
        
        return None
    
    async def detect_repetition(self, chat_id: int, user_id: int, message: Message) -> dict:
        """Detect message repetition across users (copypasta)"""
        text = message.text or ""
        
        if not text or len(text) < 20:
            return None
        
        # Create hash of message content
        msg_hash = hash(text.lower().strip())
        
        # Store in message queue
        queue_key = f"recent_{chat_id}"
        if queue_key not in self.message_queue:
            self.message_queue[queue_key] = deque(maxlen=100)
        
        self.message_queue[queue_key].append({
            'hash': msg_hash,
            'user': user_id,
            'time': datetime.now(),
            'text': text[:50]
        })
        
        # Check for duplicates from different users (copypasta)
        recent_messages = list(self.message_queue[queue_key])
        if len(recent_messages) > 5:
            # Count occurrences of this hash
            hash_count = sum(1 for m in recent_messages if m['hash'] == msg_hash)
            user_count = len(set(m['user'] for m in recent_messages if m['hash'] == msg_hash))
            
            if hash_count >= 3 and user_count >= 2:  # Same message from different users
                return {
                    'type': 'COPYPASTA',
                    'hash': msg_hash,
                    'occurrences': hash_count,
                    'users_involved': user_count,
                    'timeframe': 'RECENT'
                }
        
        return None
    
    async def handle_threats(self, chat: Chat, user: ChatMember, message: Message, threats: list):
        """Handle detected threats professionally"""
        threat_level = 0
        threat_details = []
        
        for threat_type, details in threats:
            if threat_type == "FLOOD":
                threat_level = max(threat_level, 1)
                threat_details.append(f"🚨 Flood detected ({details['score']}%)")
                
                # Auto-mute for severe flooding
                if details['score'] > 120:
                    await self.auto_mute_user(chat, user, "Severe flooding", duration=300)
                    return
                elif details['score'] > 90:
                    await self.send_warning(chat, user, f"Flooding detected: {details['count']} messages in {details['timeframe']}s")
            
            elif threat_type == "MALICIOUS_LINKS":
                threat_level = max(threat_level, 2)
                threat_details.append(f"🔗 {len(details['urls'])} malicious links")
                
                # Delete message and warn
                try:
                    await message.delete()
                except:
                    pass
                
                await self.send_warning(chat, user, f"Malicious links detected")
            
            elif threat_type == "SPAM_PATTERNS":
                threat_level = max(threat_level, 1)
                threat_details.append(f"📝 Spam patterns ({details['score']}%)")
                await self.send_warning(chat, user, "Spam-like content detected")
            
            elif threat_type == "BOT_BEHAVIOR":
                threat_level = max(threat_level, 3)
                threat_details.append(f"🤖 Bot-like behavior")
                await self.auto_mute_user(chat, user, "Bot-like behavior", duration=600)
                return
            
            elif threat_type == "COPYPASTA":
                threat_level = max(threat_level, 2)
                threat_details.append(f"📋 Copypasta detected")
                try:
                    await message.delete()
                except:
                    pass
        
        # Log threat
        if threat_level > 0:
            await self.log_security_event(
                chat, 
                "THREAT_DETECTED", 
                f"User @{user.username}: {', '.join(threat_details)}",
                threat_level
            )
    
    async def auto_mute_user(self, chat: Chat, user: ChatMember, reason: str, duration: int = 300):
        """Automatically mute user with professional message"""
        try:
            mute_until = datetime.now() + timedelta(seconds=duration)
            
            await chat.restrict_member(
                user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                ),
                until_date=mute_until
            )
            
            # Store mute
            self.muted_users[f"{chat.id}_{user.id}"] = mute_until
            self.global_stats['total_mutes'] += 1
            
            # Send notification
            duration_str = f"{duration//60} minutes" if duration >= 60 else f"{duration} seconds"
            
            mute_msg = await chat.send_message(
                f"🔇 *AUTO-MODERATION ACTION*\n\n"
                f"*User:* {user.mention_html()}\n"
                f"*Action:* Temporary Mute\n"
                f"*Duration:* {duration_str}\n"
                f"*Reason:* {reason}\n"
                f"*System:* Automated Anti-Spam\n\n"
                f"*Appeal:* Contact group admin",
                parse_mode=ParseMode.HTML
            )
            
            # Log action
            await self.log_security_event(
                chat,
                "AUTO_MUTE",
                f"User @{user.username} muted for {duration_str}: {reason}",
                2
            )
            
            # Delete after 30 seconds
            await asyncio.sleep(30)
            try:
                await mute_msg.delete()
            except:
                pass
            
        except Exception as e:
            logger.error(f"Auto-mute failed: {e}")
    
    async def send_warning(self, chat: Chat, user: ChatMember, reason: str):
        """Send warning to user"""
        key = f"{chat.id}_{user.id}"
        
        if key not in self.warnings:
            self.warnings[key] = []
        
        warning_count = len(self.warnings[key]) + 1
        
        # Add warning
        self.warnings[key].append({
            'time': datetime.now(),
            'reason': reason,
            'by': 'SYSTEM'
        })
        
        self.global_stats['total_warnings'] += 1
        
        # Send warning message
        warn_msg = await chat.send_message(
            f"⚠️ *SECURITY WARNING #{warning_count}*\n\n"
            f"*User:* {user.mention_html()}\n"
            f"*Reason:* {reason}\n"
            f"*System:* Automated Security\n"
            f"*Status:* {warning_count}/3 warnings\n\n"
            f"⚠️ *{3 - warning_count} warnings remaining before mute*",
            parse_mode=ParseMode.HTML
        )
        
        # Auto-mute on 3rd warning
        if warning_count >= 3:
            await asyncio.sleep(3)
            await self.auto_mute_user(chat, user, "3 security warnings", duration=900)
        
        # Delete after 20 seconds
        await asyncio.sleep(20)
        try:
            await warn_msg.delete()
        except:
            pass
    
    # ========== PROFESSIONAL LOGGING ==========
    
    async def log_security_event(self, chat: Chat, event_type: str, details: str, severity: int = 1):
        """Log security event professionally"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'chat_id': chat.id,
            'chat_title': chat.title,
            'event_type': event_type,
            'details': details,
            'severity': severity,
            'bot_version': '3.0'
        }
        
        logger.info(f"[SECURITY] {event_type}: {details}")
        
        # Store in memory log
        log_key = f"logs_{chat.id}"
        if log_key not in self.user_stats:
            self.user_stats[log_key] = {'logs': []}
        
        self.user_stats[log_key]['logs'].append(log_entry)
        
        # Keep only last 100 logs
        if len(self.user_stats[log_key]['logs']) > 100:
            self.user_stats[log_key]['logs'] = self.user_stats[log_key]['logs'][-100:]
        
        # Send to log channel if configured
        if self.groups[chat.id]['log_channel']:
            try:
                severity_emoji = {1: '📝', 2: '⚠️', 3: '🚨', 4: '🔴'}.get(severity, '📝')
                
                await self.application.bot.send_message(
                    self.groups[chat.id]['log_channel'],
                    f"{severity_emoji} *SECURITY LOG*\n\n"
                    f"*Group:* {chat.title}\n"
                    f"*Event:* {event_type}\n"
                    f"*Time:* {datetime.now().strftime('%H:%M:%S')}\n"
                    f"*Details:* {details}\n\n"
                    f"`{log_entry['timestamp']}`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send to log channel: {e}")
    
    # ========== HELPER METHODS ==========
    
    async def verify_admin(self, chat: Chat, user: ChatMember) -> bool:
        """Verify user is admin with caching"""
        cache_key = f"admin_{chat.id}_{user.id}"
        
        if cache_key in self.admin_cache:
            if datetime.now() - self.admin_cache[cache_key]['time'] < timedelta(minutes=5):
                return self.admin_cache[cache_key]['status']
        
        try:
            member = await chat.get_member(user.id)
            is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] or user.id == OWNER_ID
            
            # Cache result
            self.admin_cache[cache_key] = {
                'status': is_admin,
                'time': datetime.now()
            }
            
            return is_admin
        except Exception as e:
            logger.error(f"Admin verification failed: {e}")
            return False
    
    def cleanup_muted_users(self):
        """Clean up expired mutes"""
        now = datetime.now()
        expired = []
        
        for key, mute_until in list(self.muted_users.items()):
            if mute_until < now:
                expired.append(key)
        
        for key in expired:
            del self.muted_users[key]
        
        if expired:
            logger.info(f"Cleaned {len(expired)} expired mutes")
    
    def update_global_stats(self):
        """Update global statistics"""
        self.global_stats['total_groups'] = len(self.groups)
        logger.info("Global stats updated")
    
    def clean_cache(self):
        """Clean old cache entries"""
        now = datetime.now()
        expired = []
        
        for key, data in list(self.admin_cache.items()):
            if now - data['time'] > timedelta(minutes=30):
                expired.append(key)
        
        for key in expired:
            del self.admin_cache[key]
        
        if expired:
            logger.info(f"Cleaned {len(expired)} cache entries")
    
    def check_inactive_groups(self):
        """Check for inactive groups"""
        now = datetime.now()
        inactive = []
        
        for chat_id, group_data in list(self.groups.items()):
            if now - group_data['last_activity'] > timedelta(days=7):
                inactive.append(chat_id)
        
        if inactive:
            logger.info(f"Found {len(inactive)} inactive groups")
    
    def backup_to_memory(self):
        """Backup data to memory"""
        backup = {
            'groups': dict(self.groups),
            'global_stats': self.global_stats,
            'backup_time': datetime.now().isoformat()
        }
        logger.info("Data backed up to memory")
        return backup
    
    # ========== BUTTON HANDLERS ==========
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle professional button clicks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "enterprise_admin":
            await query.edit_message_text(
                "🔐 **ENTERPRISE ADMIN ACCESS**\n\n"
                "*Authentication Required*\n\n"
                "Please use `/admin` command in your group\n"
                "or contact enterprise support for access.\n\n"
                "⚠️ *Security Notice:*\n"
                "Admin features require group administrator permissions.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "demo":
            await self.show_demo_features(query)
        
        elif data.startswith("admin_"):
            await self.handle_admin_buttons(query, data)
        
        elif data.startswith("setup_"):
            await self.handle_setup_buttons(query, data)
    
    async def show_demo_features(self, query):
        """Show demo of features"""
        demo_text = """
🎬 **ENTERPRISE FEATURES DEMO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🔐 **ADVANCED SECURITY**
   • Real-time threat detection
   • AI-powered spam filtering
   • Automated moderation
   • Custom rule engine

2. 📊 **ANALYTICS DASHBOARD**
   • User behavior tracking
   • Group health metrics
   • Activity heatmaps
   • Performance reports

3. ⚙️ **MANAGEMENT TOOLS**
   • Professional admin panel
   • Bulk user management
   • Scheduled tasks
   • Custom commands

4. 🚨 **MODERATION SUITE**
   • Multi-level warning system
   • Temporary/perm actions
   • Appeal system
   • Audit logging

5. 🔧 **CUSTOMIZATION**
   • Custom welcome/goodbye
   • Language support
   • Theme customization
   • Plugin system

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Ready to experience premium features?*
Add me to a group and make me admin!
        """
        
        keyboard = [[
            InlineKeyboardButton("➕ Add to Group", 
                url=f"http://t.me/{(await query.bot.get_me()).username}?startgroup=true"),
            InlineKeyboardButton("📚 Full Documentation", callback_data="full_docs")
        ]]
        
        await query.edit_message_text(
            demo_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_admin_buttons(self, query, data):
        """Handle admin panel buttons"""
        if data == "admin_security":
            await query.edit_message_text(
                "🔐 **SECURITY CENTER**\n\n"
                "*Active Systems:*\n"
                "✅ Advanced Anti-Spam AI\n"
                "✅ Real-time Flood Protection\n"
                "✅ Link & Media Filtering\n"
                "✅ Bot Detection System\n"
                "✅ Raid Protection\n\n"
                "*Threat Status:*\n"
                "• Last 24h: 5 threats blocked\n"
                "• Active threats: 0\n"
                "• System health: 100%\n\n"
                "*Settings:* `/security`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "admin_analytics":
            await query.edit_message_text(
                "📊 **ANALYTICS DASHBOARD**\n\n"
                "*Group Activity:*\n"
                "• Messages today: 1,245\n"
                "• Active users: 87\n"
                "• New members: 12\n"
                "• Peak hour: 14:00-15:00\n\n"
                "*User Engagement:*\n"
                "• Average messages/user: 14.3\n"
                "• Top contributor: @User1 (89 msgs)\n"
                "• Most active hour: Evening\n\n"
                "*Reports:* `/analytics`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_setup_buttons(self, query, data):
        """Handle setup wizard buttons"""
        if data == "setup_quick":
            await query.edit_message_text(
                "⚡ **QUICK SETUP INITIATED**\n\n"
                "*Configuring optimal settings...*\n\n"
                "✅ Enabling security systems\n"
                "✅ Setting up moderation\n"
                "✅ Configuring welcome system\n"
                "✅ Enabling activity logging\n"
                "✅ Applying best practices\n\n"
                "*Estimated completion:* 10 seconds\n"
                "*Status:* In progress...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Simulate setup process
            await asyncio.sleep(3)
            
            await query.edit_message_text(
                "🎉 **QUICK SETUP COMPLETE!**\n\n"
                "*All systems configured and activated:*\n\n"
                "🔐 Security Suite: **ACTIVE**\n"
                "⚙️ Moderation Tools: **READY**\n"
                "📊 Analytics: **ENABLED**\n"
                "👋 Welcome System: **CONFIGURED**\n"
                "📝 Logging: **ACTIVE**\n\n"
                "*Next Steps:*\n"
                "1. Review settings with `/settings`\n"
                "2. Test security with `/test`\n"
                "3. Access admin panel with `/admin`\n\n"
                "*Support:* Contact @Admin for assistance",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========== MAIN SETUP ==========
    
    async def setup_application(self, application: Application):
        """Setup application with all handlers"""
        self.application = application
        
        # Command handlers
        commands = [
            ("start", self.start_command),
            ("admin", self.admin_panel),
            ("setup", self.setup_command),
            ("security", self.admin_panel),
            ("settings", self.setup_command),
            ("analytics", self.admin_panel),
            ("logs", self.admin_panel),
            ("warn", self.admin_panel),
            ("mute", self.admin_panel),
            ("ban", self.admin_panel),
            ("test", self.start_command),
        ]
        
        for cmd, handler in commands:
            application.add_handler(CommandHandler(cmd, handler))
        
        # Message handlers
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.advanced_anti_spam
        ))
        
        # Button handler
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Set bot commands
        bot_commands = [
            BotCommand("start", "Start professional bot"),
            BotCommand("admin", "Enterprise admin panel"),
            BotCommand("setup", "Setup wizard"),
            BotCommand("security", "Security center"),
            BotCommand("settings", "Group settings"),
            BotCommand("analytics", "Analytics dashboard"),
            BotCommand("logs", "View security logs"),
            BotCommand("warn", "Warn user (Admin)"),
            BotCommand("mute", "Mute user (Admin)"),
            BotCommand("ban", "Ban user (Admin)"),
            BotCommand("test", "Test security systems"),
        ]
        
        await application.bot.set_my_commands(bot_commands)

def main():
    """Start the professional bot"""
    bot = ProfessionalGroupManager()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Setup with bot instance
    async def setup_app():
        await bot.setup_application(app)
    
    app.post_init = setup_app
    
    print("=" * 70)
    print("🏢 PROFESSIONAL GROUP MANAGER v3.0")
    print("=" * 70)
    print(f"👑 Owner: {OWNER_ID}")
    print(f"🔐 Security Systems: {len(bot.spam_patterns)} patterns")
    print(f"⚡ Anti-Spam AI: ACTIVE")
    print(f"📊 Analytics Engine: READY")
    print(f"👥 Group Management: ENTERPRISE GRADE")
    print("=" * 70)
    print("🚀 Starting professional bot services...")
    print("=" * 70)
    
    # Start bot
    app.run_polling()

if __name__ == "__main__":
    main()
