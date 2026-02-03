"""
🖼️ IMAGE GENERATION SYSTEM
With profile pictures and font fallbacks for Railway
"""

import io
import logging
import random
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import aiohttp

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    logging.warning("Pillow not installed. Image generation disabled.")

from config import Config

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Professional image generator with profile pictures"""
    
    def __init__(self):
        self.fonts = {}
        if HAS_PILLOW:
            self.load_fonts()
    
    def load_fonts(self):
        """Load fonts with fallbacks - FIXED FOR RAILWAY"""
        try:
            # Always available in Python
            self.fonts['small'] = ImageFont.load_default()
            self.fonts['medium'] = ImageFont.load_default()
            self.fonts['large'] = ImageFont.load_default()
            self.fonts['title'] = ImageFont.load_default()
            logger.info("✅ Using default fonts (Railway compatible)")
            
        except Exception as e:
            logger.warning(f"Font loading: {e}")
            # Ultimate fallback
            self.fonts['small'] = None
            self.fonts['medium'] = None
            self.fonts['large'] = None
            self.fonts['title'] = None
    
    async def download_profile_pic(self, bot, user_id: int) -> Optional[bytes]:
        """Download user's profile picture"""
        try:
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                # Get the largest photo
                photo = photos.photos[0][-1]
                file = await bot.get_file(photo.file_id)
                file_path = file.file_path
                
                # Download photo
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file_path}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.read()
            return None
        except Exception as e:
            logger.error(f"Profile pic download error: {e}")
            return None
    
    def create_circular_mask(self, size: int) -> Image.Image:
        """Create circular mask for profile pictures"""
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        return mask
    
    def create_profile_card(self, bot, user_data: Dict, achievements: List[Dict], 
                          family: List[Dict] = None) -> Optional[bytes]:
        """Create profile card with profile picture"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 700  # Increased height for family
            img = Image.new('RGB', (width, height), color='#0d1b2a')
            draw = ImageDraw.Draw(img)
            
            # Background
            draw.rectangle([0, 0, width, height], fill='#0d1b2a')
            
            # Header with gradient
            for i in range(150):
                alpha = i / 150
                color = (
                    int(9 * (1 - alpha) + 13 * alpha),
                    int(132 * (1 - alpha) + 148 * alpha),
                    int(227 * (1 - alpha) + 199 * alpha)
                )
                draw.line([(0, i), (width, i)], fill=color)
            
            # Try to get profile picture
            profile_pic = None
            try:
                import asyncio
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                profile_pic_data = loop.run_until_complete(
                    self.download_profile_pic(bot, user_data['user_id'])
                )
                if profile_pic_data:
                    profile_pic = Image.open(io.BytesIO(profile_pic_data))
                    profile_pic = profile_pic.resize((100, 100))
                    
                    # Create circular mask
                    mask = self.create_circular_mask(100)
                    
                    # Create circular profile picture
                    circular_pic = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
                    circular_pic.paste(profile_pic, (0, 0), mask)
                    
                    # Paste on image
                    img.paste(circular_pic, (width//2 - 50, 40), circular_pic)
                    
                    # Add border
                    draw.ellipse([width//2 - 52, 38, width//2 + 52, 142], 
                               outline='white', width=3)
            except:
                # Fallback: Draw circle with initial
                draw.ellipse([width//2 - 50, 40, width//2 + 50, 140], 
                           fill='#0984e3', outline='white', width=3)
                initial = user_data.get('first_name', 'U')[0].upper()
                draw.text((width//2 - 15, 75), initial, 
                         fill='white', font=self.fonts['title'])
            
            # User name
            name = user_data.get('first_name', 'User')
            draw.text((width//2 - 100, 160), f"👤 {name}", 
                     fill='white', font=self.fonts['title'] if self.fonts['title'] else None)
            
            # Stats grid
            stats = [
                ("💰 Cash", f"${user_data.get('cash', 0):,}", "#00b894"),
                ("🏦 Bank", f"${user_data.get('bank_balance', 0):,}", "#0984e3"),
                ("⭐ Level", str(user_data.get('level', 1)), "#fd79a8"),
                ("🔥 Streak", f"{user_data.get('daily_streak', 0)}d", "#fdcb6e")
            ]
            
            y_offset = 210
            for i, (label, value, color) in enumerate(stats):
                x = 30 + (i % 2) * 270
                y = y_offset + (i // 2) * 60
                
                # Stat box
                draw.rounded_rectangle([x, y, x + 240, y + 50], 
                                     radius=10, fill=color)
                
                # Label
                draw.text((x + 10, y + 8), label, 
                         fill='white', font=self.fonts['small'] if self.fonts['small'] else None)
                
                # Value
                draw.text((x + 10, y + 25), value, 
                         fill='white', font=self.fonts['medium'] if self.fonts['medium'] else None)
            
            # Family section (if provided)
            if family:
                y_offset += 140
                draw.text((30, y_offset), "👨‍👩‍👧‍👦 Family Members:", 
                         fill='#FFC107', font=self.fonts['medium'] if self.fonts['medium'] else None)
                
                # Show first 4 family members
                for i, member in enumerate(family[:4]):
                    x = 30 + (i % 2) * 270
                    y = y_offset + 30 + (i // 2) * 50
                    
                    # Family member box
                    draw.rounded_rectangle([x, y, x + 240, y + 40], 
                                         radius=8, fill='#1b263b', outline='#6c5ce7', width=2)
                    
                    # Member name and relation
                    relation_emoji = "💑" if member.get('relation') == 'spouse' else "👶"
                    name = member.get('first_name', 'Unknown')[:12]
                    text = f"{relation_emoji} {name}"
                    draw.text((x + 10, y + 10), text, 
                             fill='white', font=self.fonts['small'] if self.fonts['small'] else None)
            
            # Footer
            footer = f"Family Tree Bot • v{Config.VERSION}"
            draw.text((width//2 - 100, height - 30), footer, 
                     fill='#636e72', font=self.fonts['small'] if self.fonts['small'] else None)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True, quality=85)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Profile card error: {e}")
            return None
    
    def create_family_tree_image(self, main_user: Dict, family: List[Dict]) -> Optional[bytes]:
        """Create visual family tree"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='#f8f9fa')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((width//2 - 150, 20), "🌳 FAMILY TREE", 
                     fill='#2d3436', font=self.fonts['title'] if self.fonts['title'] else None)
            
            # Main user in center
            center_x, center_y = width//2, height//2
            draw.ellipse([center_x - 60, center_y - 60, center_x + 60, center_y + 60], 
                       fill='#0984e3', outline='#2d3436', width=3)
            
            main_name = main_user.get('first_name', 'You')[:8]
            draw.text((center_x - 40, center_y - 10), f"👑 {main_name}", 
                     fill='white', font=self.fonts['medium'] if self.fonts['medium'] else None)
            
            # Draw family members around
            angles = [0, 45, 90, 135, 180, 225, 270, 315]
            radius = 200
            
            for i, member in enumerate(family[:8]):
                angle = angles[i] if i < len(angles) else angles[i % len(angles)]
                rad = angle * 3.14159 / 180
                
                x = center_x + int(radius * (i+1)/len(family) * (1 if i % 2 == 0 else -1))
                y = center_y + int(radius * (i+1)/len(family) * (1 if i < 4 else -1))
                
                # Draw connection line
                draw.line([center_x, center_y, x, y], fill='#636e72', width=2)
                
                # Draw member circle
                relation_color = '#e17055' if member.get('relation') == 'spouse' else '#00b894'
                draw.ellipse([x - 40, y - 40, x + 40, y + 40], 
                           fill=relation_color, outline='#2d3436', width=2)
                
                # Member name
                name = member.get('first_name', 'Unknown')[:6]
                relation = "💑" if member.get('relation') == 'spouse' else "👶"
                draw.text((x - 30, y - 10), f"{relation} {name}", 
                         fill='white', font=self.fonts['small'] if self.fonts['small'] else None)
            
            # Stats
            stats_text = f"Total Family: {len(family)} members"
            draw.text((width//2 - 100, height - 50), stats_text, 
                     fill='#2d3436', font=self.fonts['medium'] if self.fonts['medium'] else None)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Family tree image error: {e}")
            return None
    
    def create_garden_image(self, username: str, plants: List[Dict], garden_info: Dict) -> Optional[bytes]:
        """Create garden layout - minimal text"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 500
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Background gradient
            for i in range(height):
                r = int(26 * (1 - i/height) + 10)
                g = int(26 * (1 - i/height) + 20)
                b = int(46 * (1 - i/height) + 30)
                draw.line([(0, i), (width, i)], fill=(r, g, b))
            
            # Title with emoji
            draw.text((width//2 - 50, 20), "🌾 GARDEN", 
                     fill='#4CAF50', font=self.fonts['title'] if self.fonts['title'] else None)
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 100
            padding = 20
            start_x = (width - (grid_size * cell_size + (grid_size - 1) * padding)) // 2
            start_y = 80
            
            for row in range(grid_size):
                for col in range(grid_size):
                    idx = row * grid_size + col
                    x1 = start_x + col * (cell_size + padding)
                    y1 = start_y + row * (cell_size + padding)
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    # Cell background
                    draw.rounded_rectangle([x1, y1, x2, y2], radius=15, 
                                         fill='#2d3436', outline='#636e72', width=2)
                    
                    if idx < len(plants):
                        plant = plants[idx]
                        progress = plant.get('current_progress', 0)
                        
                        # Crop emoji
                        crop_emojis = {
                            "carrot": "🥕", "tomato": "🍅", "potato": "🥔",
                            "eggplant": "🍆", "corn": "🌽", "pepper": "🫑",
                            "watermelon": "🍉", "pumpkin": "🎃"
                        }
                        emoji = crop_emojis.get(plant.get('crop_type', ''), '🌱')
                        
                        # Draw emoji
                        draw.text((x1 + 35, y1 + 20), emoji, 
                                 fill='white', font=self.fonts['large'] if self.fonts['large'] else None)
                        
                        # Progress circle
                        circle_x, circle_y = x1 + 50, y2 - 30
                        radius = 20
                        
                        # Background circle
                        draw.ellipse([circle_x-radius, circle_y-radius, 
                                    circle_x+radius, circle_y+radius], 
                                   fill='#2d3436', outline='#636e72', width=2)
                        
                        # Progress text
                        progress_text = f"{int(progress)}%"
                        draw.text((circle_x - 10, circle_y - 8), progress_text, 
                                 fill='white', font=self.fonts['small'] if self.fonts['small'] else None)
                    
                    else:
                        # Empty slot
                        draw.text((x1 + 40, y1 + 40), "➕", 
                                 fill='#666666', font=self.fonts['large'] if self.fonts['large'] else None)
            
            # Stats at bottom
            ready_count = sum(1 for p in plants if p.get('current_progress', 0) >= 100)
            total_slots = garden_info.get('slots', 9)
            
            stats_text = f"📊 {len(plants)}/{total_slots} slots • ✅ {ready_count} ready"
            draw.text((width//2 - 150, height - 40), stats_text, 
                     fill='#CCCCCC', font=self.fonts['medium'] if self.fonts['medium'] else None)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None
    
    def create_scratch_card(self, ticket_id: str, numbers: str) -> Optional[bytes]:
        """Create lottery scratch card - minimal text"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 400, 250
            img = Image.new('RGB', (width, height), color='#2a9d8f')
            draw = ImageDraw.Draw(img)
            
            # Decorative border
            draw.rectangle([0, 0, width, height], outline='#264653', width=8)
            
            # Title with emoji
            draw.text((width//2 - 80, 20), "🎰 LOTTERY", 
                     fill='white', font=self.fonts['title'] if self.fonts['title'] else None)
            
            # Ticket ID
            draw.text((width//2 - 60, 60), f"#{ticket_id}", 
                     fill='#ffd166', font=self.fonts['large'] if self.fonts['large'] else None)
            
            # Scratch area
            scratch_x, scratch_y = width//2 - 150, 110
            scratch_width, scratch_height = 300, 80
            
            # Create scratch texture
            for i in range(scratch_y, scratch_y + scratch_height, 5):
                for j in range(scratch_x, scratch_x + scratch_width, 5):
                    color = random.choice(['#e9c46a', '#f4a261', '#e76f51'])
                    draw.rectangle([j, i, j+3, i+3], fill=color)
            
            # Hidden numbers hint
            if len(numbers) >= 6:
                hint = f"🎫 {numbers[0]} • • • • {numbers[-1]}"
                draw.text((scratch_x + 80, scratch_y + 30), hint, 
                         fill='#264653', font=self.fonts['medium'] if self.fonts['medium'] else None)
            
            # Instructions with emoji
            draw.text((width//2 - 120, height - 40), "🔓 Use /scratch to reveal", 
                     fill='#e9f5db', font=self.fonts['small'] if self.fonts['small'] else None)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Scratch card error: {e}")
            return None

# Global instance
image_gen = ImageGenerator()
