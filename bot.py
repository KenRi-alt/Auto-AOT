import logging
import random
import json
import os
import re
import asyncio
import html
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
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
    Poll
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

# ========== CONFIGURATION ==========
BOT_TOKEN = "8595078591:AAGvR4NQEhmNbphFGPcJFP2tDq1LYN5M66c"
OWNER_ID = 6108185460
BOT_USERNAME = "@Spam_protectBot"
LOG_CHANNEL = -1003662720845
ADMIN_PASSWORD = "admin2024"
# ===================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateEnterpriseBot:
    def __init__(self):
        self.groups = {}
        self.users = {}
        self.warnings = defaultdict(list)
        self.mutes = {}
        self.bans = set()
        self.reports = defaultdict(list)
        self.broadcasts = {}
        self.stats = {
            'total_messages': 0,
            'total_groups': 0,
            'total_users': 0,
            'total_warnings': 0,
            'total_mutes': 0,
            'total_bans': 0,
            'start_time': datetime.now()
        }
        
        # Anti-spam systems
        self.flood_data = {}
        self.spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'[0-9]{10,}',
            r'@[A-Za-z0-9_]{5,}',
            r'(?i)(buy|sell|deal|discount|offer|cheap|price)[\s\S]{0,50}(now|today|limited)',
            r'(?i)(free|money|cash|earn|profit|income|rich|wealth)[\s\S]{0,50}(fast|easy|quick|simple)',
            r'(?i)(click|link|website|url|visit|join|register|signup)[\s\S]{0,50}(here|now|today)',
        ]
        
        # Security settings
        self.security_settings = {
            'max_warnings': 3,
            'mute_duration': 300,
            'ban_duration': 86400,
            'flood_threshold': 5,
            'flood_timeframe': 5,
            'anti_link': True,
            'anti_spam': True,
            'anti_flood': True,
            'anti_caps': True,
            'anti_repetition': True
        }
        
        logger.info("Ultimate Enterprise Bot Initialized")
    
    # ========== LOGGING SYSTEM ==========
    
    async def log_to_channel(self, log_type: str, data: dict, level: str = "INFO"):
        """Log to the dedicated log channel"""
        try:
            emoji_map = {
                'INFO': '📝',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'SECURITY': '🔐',
                'BROADCAST': '📢',
                'JOIN': '👤',
                'LEAVE': '👋',
                'WARN': '⚠️',
                'MUTE': '🔇',
                'BAN': '🚫',
                'KICK': '👢',
                'SETTINGS': '⚙️',
                'BACKUP': '💾',
                'RESTORE': '🔄',
                'STATS': '📊'
            }
            
            emoji = emoji_map.get(level, '📝')
            
            log_message = f"{emoji} *{level} - {log_type}*\n"
            log_message += f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if 'chat' in data:
                log_message += f"💬 *Chat:* {data['chat']}\n"
            if 'user' in data:
                log_message += f"👤 *User:* {data['user']}\n"
            if 'action' in data:
                log_message += f"🎯 *Action:* {data['action']}\n"
            if 'reason' in data:
                log_message += f"📝 *Reason:* {data['reason']}\n"
            if 'details' in data:
                log_message += f"🔍 *Details:* {data['details']}\n"
            
            log_message += f"\n`{json.dumps(data, indent=2, default=str)}`"
            
            # Send to log channel
            await self.application.bot.send_message(
                chat_id=LOG_CHANNEL,
                text=log_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            logger.info(f"[{level}] {log_type}: {data}")
            
        except Exception as e:
            logger.error(f"Failed to log to channel: {e}")
    
    # ========== SECURITY TIGHTENING ==========
    
    async def security_check(self, chat_id: int, user_id: int, message_text: str) -> Dict:
        """Comprehensive security check"""
        threats = []
        
        # 1. Flood check
        flood_result = await self.check_flood(chat_id, user_id)
        if flood_result['detected']:
            threats.append(('FLOOD', flood_result))
        
        # 2. Spam pattern check
        spam_result = await self.check_spam_patterns(message_text)
        if spam_result['detected']:
            threats.append(('SPAM', spam_result))
        
        # 3. Link check
        link_result = await self.check_links(message_text)
        if link_result['detected']:
            threats.append(('LINK', link_result))
        
        # 4. Caps check
        caps_result = await self.check_caps(message_text)
        if caps_result['detected']:
            threats.append(('CAPS', caps_result))
        
        # 5. Repetition check
        rep_result = await self.check_repetition(chat_id, user_id, message_text)
        if rep_result['detected']:
            threats.append(('REPETITION', rep_result))
        
        return {
            'threats': threats,
            'total_score': sum(t[1]['score'] for t in threats),
            'threat_count': len(threats)
        }
    
    async def check_flood(self, chat_id: int, user_id: int) -> Dict:
        """Enhanced flood detection"""
        key = f"{chat_id}_{user_id}"
        
        if key not in self.flood_data:
            self.flood_data[key] = {
                'count': 0,
                'last_time': datetime.now(),
                'messages': [],
                'score': 0
            }
        
        data = self.flood_data[key]
        now = datetime.now()
        time_diff = (now - data['last_time']).seconds
        
        # Reset after configured timeframe
        if time_diff > self.security_settings['flood_timeframe']:
            data['count'] = 0
            data['score'] = max(0, data['score'] - 10)
            data['messages'] = []
        
        data['count'] += 1
        data['last_time'] = now
        data['messages'].append(now)
        
        # Keep only last 20 messages
        if len(data['messages']) > 20:
            data['messages'] = data['messages'][-20:]
        
        # Calculate flood score
        score = 0
        
        if data['count'] >= self.security_settings['flood_threshold'] * 2 and time_diff < self.security_settings['flood_timeframe']:
            score = 100
        elif data['count'] >= self.security_settings['flood_threshold'] + 2 and time_diff < self.security_settings['flood_timeframe']:
            score = 70
        elif data['count'] >= self.security_settings['flood_threshold'] and time_diff < self.security_settings['flood_timeframe']:
            score = 50
        
        data['score'] += score
        
        detected = score >= 50
        details = f"Flood: {data['count']} messages in {time_diff}s (Score: {data['score']})"
        
        return {'detected': detected, 'score': score, 'details': details}
    
    async def check_spam_patterns(self, text: str) -> Dict:
        """Enhanced spam pattern detection"""
        if not text:
            return {'detected': False, 'score': 0, 'details': ''}
        
        score = 0
        detected_patterns = []
        
        for i, pattern in enumerate(self.spam_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_patterns.append(f"Pattern_{i}")
                score += len(matches) * 25
        
        detected = score > 30
        details = f"Spam patterns: {', '.join(detected_patterns[:3])}" if detected_patterns else ""
        
        return {'detected': detected, 'score': score, 'details': details}
    
    async def check_links(self, text: str) -> Dict:
        """Enhanced link detection"""
        if not text or not self.security_settings['anti_link']:
            return {'detected': False, 'score': 0, 'details': ''}
        
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        if not urls:
            return {'detected': False, 'score': 0, 'details': ''}
        
        # Check for suspicious domains
        suspicious_domains = ['bit.ly', 'tinyurl.com', 'shortener', 'spam', 'malware', 'phishing']
        suspicious_count = 0
        
        for url in urls:
            if any(domain in url.lower() for domain in suspicious_domains):
                suspicious_count += 1
        
        score = len(urls) * 20 + suspicious_count * 30
        detected = score > 40
        details = f"Links: {len(urls)} total, {suspicious_count} suspicious"
        
        return {'detected': detected, 'score': score, 'details': details}
    
    async def check_caps(self, text: str) -> Dict:
        """Enhanced caps detection"""
        if not text or len(text) < 10 or not self.security_settings['anti_caps']:
            return {'detected': False, 'score': 0, 'details': ''}
        
        caps_count = sum(1 for c in text if c.isupper())
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return {'detected': False, 'score': 0, 'details': ''}
        
        caps_ratio = caps_count / total_chars
        score = int(caps_ratio * 100) if caps_ratio > 0.6 else 0
        detected = caps_ratio > 0.7
        details = f"Caps ratio: {caps_ratio:.1%} ({caps_count}/{total_chars})"
        
        return {'detected': detected, 'score': score, 'details': details}
    
    async def check_repetition(self, chat_id: int, user_id: int, text: str) -> Dict:
        """Enhanced repetition detection"""
        if not text or len(text) < 5 or not self.security_settings['anti_repetition']:
            return {'detected': False, 'score': 0, 'details': ''}
        
        key = f"recent_{chat_id}_{user_id}"
        if key not in self.flood_data:
            self.flood_data[key] = {'messages': []}
        
        recent_messages = self.flood_data[key]['messages']
        
        # Check for repetition
        score = 0
        repetition_count = 0
        
        for msg in recent_messages[-5:]:
            if text == msg or (len(text) > 10 and text in msg) or (len(msg) > 10 and msg in text):
                repetition_count += 1
                score += 40
        
        detected = repetition_count >= 2
        details = f"Repetition: {repetition_count} similar messages"
        
        # Store current message
        recent_messages.append(text)
        if len(recent_messages) > 10:
            recent_messages.pop(0)
        
        self.flood_data[key]['messages'] = recent_messages
        
        return {'detected': detected, 'score': score, 'details': details}
    
    async def handle_security_threat(self, chat: Chat, user: ChatMember, message: Message, security_result: Dict):
        """Handle security threats with graduated response"""
        if not security_result['threats']:
            return
        
        # Get user's warning history
        warning_key = (chat.id, user.id)
        warning_count = len(self.warnings.get(warning_key, []))
        
        # Determine action based on threat level
        total_score = security_result['total_score']
        
        if total_score >= 100 or warning_count >= self.security_settings['max_warnings']:
            # Severe threat - immediate mute
            await self.mute_user(chat, user.id, self.security_settings['mute_duration'], "Severe security threat")
            await self.delete_message(message)
            
            # Log action
            await self.log_to_channel(
                "AUTO_MUTE",
                {
                    'chat': chat.title,
                    'user': f"@{user.username}" if user.username else user.first_name,
                    'action': 'AUTO_MUTE',
                    'reason': 'Severe security threat',
                    'details': f"Score: {total_score}, Threats: {security_result['threat_count']}",
                    'duration': f"{self.security_settings['mute_duration']}s"
                },
                "SECURITY"
            )
            
        elif total_score >= 70:
            # High threat - warning and message deletion
            await self.issue_warning(chat, user, message, security_result)
            await self.delete_message(message)
            
        elif total_score >= 40:
            # Medium threat - warning only
            await self.issue_warning(chat, user, message, security_result)
    
    async def delete_message(self, message: Message):
        """Delete a message with error handling"""
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
    
    async def issue_warning(self, chat: Chat, user: ChatMember, message: Message, security_result: Dict):
        """Issue a warning to user"""
        warning_key = (chat.id, user.id)
        
        # Add warning to history
        warning_data = {
            'time': datetime.now(),
            'score': security_result['total_score'],
            'threats': [t[0] for t in security_result['threats']],
            'message': message.text[:100] if message.text else ""
        }
        
        self.warnings[warning_key].append(warning_data)
        warning_count = len(self.warnings[warning_key])
        
        # Send warning message
        warning_msg = await chat.send_message(
            f"⚠️ *SECURITY WARNING #{warning_count}*\n\n"
            f"*User:* {user.mention_html()}\n"
            f"*Threat Level:* {security_result['total_score']}/100\n"
            f"*Detected:* {', '.join([t[0] for t in security_result['threats'][:3]])}\n"
            f"*Status:* {warning_count}/{self.security_settings['max_warnings']} warnings\n\n"
            f"⚠️ *{self.security_settings['max_warnings'] - warning_count} warnings remaining*",
            parse_mode=ParseMode.HTML
        )
        
        # Auto-delete warning after 30 seconds
        await asyncio.sleep(30)
        try:
            await warning_msg.delete()
        except:
            pass
        
        # Log warning
        await self.log_to_channel(
            "WARNING_ISSUED",
            {
                'chat': chat.title,
                'user': f"@{user.username}" if user.username else user.first_name,
                'action': 'WARNING',
                'count': warning_count,
                'score': security_result['total_score'],
                'threats': [t[0] for t in security_result['threats']]
            },
            "WARNING"
        )
    
    async def mute_user(self, chat: Chat, user_id: int, duration: int, reason: str):
        """Mute a user with enhanced permissions"""
        try:
            mute_until = datetime.now() + timedelta(seconds=duration)
            
            await chat.restrict_member(
                user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                ),
                until_date=mute_until
            )
            
            # Store mute
            self.mutes[(chat.id, user_id)] = mute_until
            
            # Send notification
            duration_str = f"{duration//60} minutes" if duration >= 60 else f"{duration} seconds"
            
            mute_msg = await chat.send_message(
                f"🔇 *USER MUTED*\n\n"
                f"*Duration:* {duration_str}\n"
                f"*Reason:* {reason}\n"
                f"*Action:* Automated Security System",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Auto-delete notification
            await asyncio.sleep(20)
            try:
                await mute_msg.delete()
            except:
                pass
            
        except Exception as e:
            logger.error(f"Failed to mute user {user_id}: {e}")
    
    # ========== MESSAGE HANDLER ==========
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all messages with security checks"""
        message = update.message
        chat = update.effective_chat
        user = update.effective_user
        
        # Skip if not a group
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return
        
        # Initialize group if not exists
        if chat.id not in self.groups:
            self.groups[chat.id] = {
                'title': chat.title,
                'members': await chat.get_member_count(),
                'created': datetime.now(),
                'last_active': datetime.now(),
                'messages': 0
            }
        
        # Update stats
        self.groups[chat.id]['messages'] += 1
        self.groups[chat.id]['last_active'] = datetime.now()
        self.stats['total_messages'] += 1
        
        # Skip if user is admin
        try:
            member = await chat.get_member(user.id)
            if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return
        except:
            pass
        
        # Run security check
        security_result = await self.security_check(
            chat.id, 
            user.id, 
            message.text or ""
        )
        
        # Handle threats if any
        if security_result['threats']:
            await self.handle_security_threat(chat, user, message, security_result)
    
    # ========== COMMAND HANDLERS ==========
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user
        
        text = f"""
🔐 *ULTIMATE SECURITY BOT*

👤 *User:* {user.mention_html()}
🆔 *ID:* `{user.id}`
⚡ *Status:* Active & Secured

🛡️ *Security Features:*
• Multi-layer Anti-Spam
• Real-time Threat Detection
• Automated Moderation
• Smart Flood Protection
• Link & Pattern Filtering

📊 *System Stats:*
• Groups Protected: {len(self.groups)}
• Total Messages: {self.stats['total_messages']:,}
• Security Level: MAXIMUM

🚀 *Add me to your group for protection!*
        """
        
        keyboard = [[
            InlineKeyboardButton("➕ Add to Group", 
                url=f"http://t.me/{BOT_USERNAME.replace('@', '')}?startgroup=true"),
            InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")
        ]]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("🚫 Owner only!")
            return
        
        text = f"""
👑 *SECURITY ADMIN PANEL*

📊 *System Status:*
• Groups: {len(self.groups)}
• Total Messages: {self.stats['total_messages']:,}
• Warnings: {sum(len(w) for w in self.warnings.values())}
• Mutes Active: {len([m for m in self.mutes.values() if m > datetime.now()])}

🔐 *Security Settings:*
• Max Warnings: {self.security_settings['max_warnings']}
• Mute Duration: {self.security_settings['mute_duration']}s
• Flood Threshold: {self.security_settings['flood_threshold']}
• Anti-Link: {'✅ ON' if self.security_settings['anti_link'] else '❌ OFF'}
• Anti-Spam: {'✅ ON' if self.security_settings['anti_spam'] else '❌ OFF'}

⚡ *Quick Actions:*
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 View Stats", callback_data="view_stats"),
                InlineKeyboardButton("⚙️ Settings", callback_data="security_settings")
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
                InlineKeyboardButton("🔍 Logs", callback_data="view_logs")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_admin"),
                InlineKeyboardButton("❌ Close", callback_data="close_admin")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast command"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("🚫 Owner only!")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: `/broadcast message`\n\n"
                "*Example:*\n"
                "`/broadcast *Important:* Server maintenance at 10 PM`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        message = ' '.join(context.args)
        group_count = len(self.groups)
        
        # Send to log channel first
        await self.log_to_channel(
            "BROADCAST_START",
            {
                'action': 'BROADCAST_START',
                'groups': group_count,
                'message_preview': message[:100]
            },
            "BROADCAST"
        )
        
        # Send to groups
        sent = 0
        failed = 0
        
        for chat_id in self.groups.keys():
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                sent += 1
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send to {chat_id}: {e}")
        
        # Send completion report
        report = f"""
✅ *BROADCAST COMPLETED*

*Results:*
• ✅ Sent: {sent}
• ❌ Failed: {failed}
• 📊 Success Rate: {(sent/(sent+failed)*100):.1f}% ({sent}/{sent+failed})

*Details:*
• Target: All Groups ({group_count})
• Message Length: {len(message)} characters
• Time: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN)
        
        # Log completion
        await self.log_to_channel(
            "BROADCAST_COMPLETE",
            {
                'action': 'BROADCAST_COMPLETE',
                'sent': sent,
                'failed': failed,
                'success_rate': f"{(sent/(sent+failed)*100):.1f}%",
                'total_groups': group_count
            },
            "BROADCAST"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Statistics command"""
        uptime = datetime.now() - self.stats['start_time']
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"
        
        text = f"""
📊 *SYSTEM STATISTICS*

🤖 *Bot Information:*
• Username: {BOT_USERNAME}
• Uptime: {uptime_str}
• Status: 🟢 ONLINE

👥 *User Statistics:*
• Total Users: Calculating...
• Active Today: Calculating...

💬 *Group Statistics:*
• Total Groups: {len(self.groups)}
• Active Groups: {sum(1 for g in self.groups.values() if (datetime.now() - g['last_active']).seconds < 3600)}
• Total Messages: {self.stats['total_messages']:,}

🔐 *Security Statistics:*
• Total Warnings: {sum(len(w) for w in self.warnings.values())}
• Active Mutes: {len([m for m in self.mutes.values() if m > datetime.now()])}
• Threats Blocked: Calculating...

⚡ *Performance:*
• Response Time: <1s
• Security Level: MAXIMUM
• System Health: ✅ OPTIMAL
        """
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def security_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Security settings command"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("🚫 Owner only!")
            return
        
        text = f"""
🔐 *SECURITY SETTINGS*

*Current Configuration:*
• Max Warnings: {self.security_settings['max_warnings']}
• Mute Duration: {self.security_settings['mute_duration']} seconds
• Ban Duration: {self.security_settings['ban_duration']} seconds
• Flood Threshold: {self.security_settings['flood_threshold']} messages
• Flood Timeframe: {self.security_settings['flood_timeframe']} seconds

*Toggle Settings:*
• Anti-Link: {'✅ ON' if self.security_settings['anti_link'] else '❌ OFF'}
• Anti-Spam: {'✅ ON' if self.security_settings['anti_spam'] else '❌ OFF'}
• Anti-Flood: {'✅ ON' if self.security_settings['anti_flood'] else '❌ OFF'}
• Anti-Caps: {'✅ ON' if self.security_settings['anti_caps'] else '❌ OFF'}
• Anti-Repetition: {'✅ ON' if self.security_settings['anti_repetition'] else '❌ OFF'}

*Usage:* `/security setting value`
*Example:* `/security max_warnings 5`
        """
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Increase Security", callback_data="increase_security"),
                InlineKeyboardButton("➖ Decrease Security", callback_data="decrease_security")
            ],
            [
                InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_security"),
                InlineKeyboardButton("📊 View Logs", callback_data="security_logs")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        text = """
🤖 *SECURITY BOT - HELP*

🔐 *Admin Commands:*
• `/admin` - Owner admin panel
• `/security` - Security settings
• `/stats` - System statistics
• `/broadcast` - Broadcast to all groups
• `/logs` - View security logs

⚙️ *Group Commands:*
• `/settings` - Configure group (Admin only)
• `/warn @user` - Warn user (Admin)
• `/mute @user` - Mute user (Admin)
• `/ban @user` - Ban user (Admin)

📊 *User Commands:*
• `/report @user reason` - Report user
• `/rules` - Show group rules
• `/ping` - Check bot status

🛡️ *Security Features:*
• Multi-layer anti-spam protection
• Real-time threat detection
• Automated moderation
• Flood prevention
• Link filtering
• Pattern recognition

💼 *Support:* Contact @Admin
        """
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ========== BUTTON HANDLERS ==========
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "admin_panel":
            if query.from_user.id != OWNER_ID:
                await query.edit_message_text("🚫 Owner only!")
                return
            
            await self.admin_command(update, context)
            
        elif data == "view_stats":
            await self.stats_command(update, context)
            
        elif data == "security_settings":
            await self.security_command(update, context)
            
        elif data == "broadcast":
            if query.from_user.id != OWNER_ID:
                await query.edit_message_text("🚫 Owner only!")
                return
            
            await query.edit_message_text(
                "📢 *BROADCAST SYSTEM*\n\n"
                "Usage: `/broadcast message`\n\n"
                "*Example:*\n"
                "`/broadcast *Important Update:* New features added!`\n\n"
                "*Features:*\n"
                "• Send to all groups\n"
                "• Markdown formatting\n"
                "• Rate limited\n"
                "• Delivery reports",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif data == "increase_security":
            if query.from_user.id != OWNER_ID:
                await query.edit_message_text("🚫 Owner only!")
                return
            
            # Increase security settings
            self.security_settings['max_warnings'] = min(5, self.security_settings['max_warnings'] + 1)
            self.security_settings['mute_duration'] = min(600, self.security_settings['mute_duration'] + 60)
            self.security_settings['flood_threshold'] = max(3, self.security_settings['flood_threshold'] - 1)
            
            await query.edit_message_text(
                f"🔐 *SECURITY INCREASED*\n\n"
                f"*New Settings:*\n"
                f"• Max Warnings: {self.security_settings['max_warnings']}\n"
                f"• Mute Duration: {self.security_settings['mute_duration']}s\n"
                f"• Flood Threshold: {self.security_settings['flood_threshold']}\n\n"
                f"Security level increased!",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif data == "refresh_admin":
            await self.admin_command(update, context)
            
        elif data == "close_admin":
            await query.edit_message_text("Admin panel closed.")
    
    # ========== APPLICATION SETUP ==========
    
    async def setup_application(self, application: Application):
        """Setup application with all handlers"""
        self.application = application
        
        # Command handlers
        command_handlers = [
            ("start", self.start_command),
            ("admin", self.admin_command),
            ("stats", self.stats_command),
            ("broadcast", self.broadcast_command),
            ("security", self.security_command),
            ("help", self.help_command),
            ("ping", self.stats_command),
        ]
        
        for cmd, handler in command_handlers:
            application.add_handler(CommandHandler(cmd, handler))
        
        # Message handler
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.message_handler
        ))
        
        # Button handler
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Set bot commands
        bot_commands = [
            BotCommand("start", "Start bot"),
            BotCommand("admin", "Owner admin panel"),
            BotCommand("stats", "System statistics"),
            BotCommand("broadcast", "Broadcast to all groups"),
            BotCommand("security", "Security settings"),
            BotCommand("help", "Show help"),
            BotCommand("ping", "Check bot status"),
        ]
        
        await application.bot.set_my_commands(bot_commands)
        
        logger.info("Application setup complete")
        
        # Send startup log
        await self.log_to_channel(
            "BOT_STARTUP",
            {
                'action': 'STARTUP',
                'time': datetime.now().isoformat(),
                'version': '2.0',
                'owner': OWNER_ID
            },
            "INFO"
        )

def main():
    """Start the bot"""
    bot = UltimateEnterpriseBot()
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Setup post initialization
    async def post_init(application: Application):
        await bot.setup_application(application)
    
    # Assign the coroutine function
    app.post_init = post_init
    
    print("=" * 60)
    print("🔐 ULTIMATE SECURITY BOT STARTING...")
    print("=" * 60)
    print(f"🤖 Bot: {BOT_USERNAME}")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"📊 Log Channel: {LOG_CHANNEL}")
    print(f"🔐 Security Level: MAXIMUM")
    print(f"⚡ Anti-Spam Systems: ACTIVE")
    print("=" * 60)
    print("🚀 Bot is ready!")
    print("=" * 60)
    
    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main()
