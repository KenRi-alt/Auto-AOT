"""
🖼️ IMAGE GENERATION SYSTEM
Enhanced image creation with fallbacks
"""

import io
import logging
import random
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    logging.warning("Pillow not installed. Image generation disabled.")

from config import Config

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Professional image generator with fallbacks"""
    
    def __init__(self):
        self.fonts = {}
        if HAS_PILLOW:
            self.load_fonts()
    
    def load_fonts(self):
        """Load fonts with fallbacks"""
        try:
            # Try different font paths
            font_paths = [
                "arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf"
            ]
            
            font_found = False
            for path in font_paths:
                try:
                    self.fonts['small'] = ImageFont.truetype(path, 14)
                    self.fonts['medium'] = ImageFont.truetype(path, 18)
                    self.fonts['large'] = ImageFont.truetype(path, 24)
                    self.fonts['title'] = ImageFont.truetype(path, 32)
                    font_found = True
                    break
                except:
                    continue
            
            if not font_found:
                raise Exception("No fonts found")
                
        except Exception as e:
            logger.warning(f"Font loading failed: {e}. Using default fonts.")
            self.fonts['small'] = ImageFont.load_default()
            self.fonts['medium'] = ImageFont.load_default()
            self.fonts['large'] = ImageFont.load_default()
            self.fonts['title'] = ImageFont.load_default()
    
    def create_profile_card(self, user_data: Dict, achievements: List[Dict]) -> Optional[bytes]:
        """Create profile card image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 600, 500
            img = Image.new('RGB', (width, height), color='#0d1b2a')
            draw = ImageDraw.Draw(img)
            
            # Background pattern
            for i in range(0, width, 20):
                for j in range(0, height, 20):
                    if (i + j) % 40 == 0:
                        draw.rectangle([i, j, i+10, j+10], fill='#1b263b')
            
            # Title
            name = user_data.get('first_name', 'User')
            title = f"👤 {name}'s Profile"
            draw.text((width//2 - 120, 20), title, fill='#4CC9F0', font=self.fonts['title'])
            
            # Stats grid
            stats = [
                ("💰 Cash", f"${user_data.get('cash', 0):,}", "#00b894"),
                ("🏦 Bank", f"${user_data.get('bank_balance', 0):,}", "#0984e3"),
                ("⭐ Level", str(user_data.get('level', 1)), "#fd79a8"),
                ("🔥 Streak", f"{user_data.get('daily_streak', 0)} days", "#fdcb6e"),
                ("👥 Family", f"{len(user_data.get('family', []))} members", "#6c5ce7"),
                ("🌾 Garden", f"{len(user_data.get('plants', []))} crops", "#00cec9")
            ]
            
            for i, (label, value, color) in enumerate(stats):
                x = 50 + (i % 2) * 250
                y = 80 + (i // 2) * 70
                
                # Stat box
                draw.rounded_rectangle([x, y, x + 220, y + 50], radius=10, fill='#1b263b', outline=color, width=2)
                
                # Label
                draw.text((x + 10, y + 8), label, fill='#CCCCCC', font=self.fonts['small'])
                
                # Value
                draw.text((x + 10, y + 25), value, fill='white', font=self.fonts['medium'])
            
            # Achievements section
            unlocked = sum(1 for a in achievements if a.get('unlocked', False))
            total = len(achievements)
            
            achievements_text = f"🏆 Achievements: {unlocked}/{total}"
            draw.text((50, 250), achievements_text, fill='#ffba08', font=self.fonts['medium'])
            
            # Progress bar for achievements
            bar_width = 500
            bar_height = 20
            progress = (unlocked / total * 100) if total > 0 else 0
            
            # Bar background
            draw.rounded_rectangle([50, 280, 50 + bar_width, 280 + bar_height], 
                                 radius=10, fill='#2d3436')
            
            # Progress fill
            progress_width = int(bar_width * progress / 100)
            draw.rounded_rectangle([50, 280, 50 + progress_width, 280 + bar_height], 
                                 radius=10, fill='#00b894')
            
            # Progress text
            progress_text = f"{int(progress)}%"
            draw.text((50 + bar_width//2 - 20, 280), progress_text, 
                     fill='white', font=self.fonts['small'])
            
            # Recent achievements
            y_offset = 320
            for i, achievement in enumerate(achievements[:3]):
                status = "✅" if achievement.get('unlocked') else "🔒"
                name = achievement.get('name', '')[:20]
                draw.text((70, y_offset + i * 25), 
                         f"{status} {name}", 
                         fill='#90be6d' if achievement.get('unlocked') else '#777777',
                         font=self.fonts['small'])
            
            # Footer
            footer = f"Family Tree Bot v{Config.VERSION}"
            draw.text((width//2 - 100, height - 30), 
                     footer, fill='#636e72', font=self.fonts['small'])
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Profile card error: {e}")
            return None
    
    def create_garden_image(self, username: str, plants: List[Dict], garden_info: Dict) -> Optional[bytes]:
        """Create garden layout image"""
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
            
            # Title
            title = f"🌾 {username}'s Garden"
            draw.text((width//2 - 140, 20), title, fill='#4CAF50', font=self.fonts['title'])
            
            # Garden grid (3x3)
            grid_size = 3
            cell_size = 100
            padding = 20
            start_x = (width - (grid_size * cell_size + (grid_size - 1) * padding)) // 2
            start_y = 70
            
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
                        draw.text((x1 + 30, y1 + 20), emoji, fill='white', font=self.fonts['large'])
                        
                        # Progress circle
                        self._draw_progress_circle(draw, x1 + 50, y2 - 30, 20, progress)
                        
                        # Crop name
                        crop_name = plant.get('crop_type', 'Unknown').title()[:6]
                        draw.text((x1 + 10, y1 + 5), crop_name, fill='#CCCCCC', font=self.fonts['small'])
                    
                    else:
                        # Empty slot
                        draw.text((x1 + 40, y1 + 40), "➕", fill='#666666', font=self.fonts['large'])
                        draw.text((x1 + 20, y2 - 20), "Empty", fill='#888888', font=self.fonts['small'])
            
            # Stats section
            stats_y = start_y + grid_size * (cell_size + padding) + 20
            
            # Slots
            total_slots = garden_info.get('slots', 9)
            used_slots = len(plants)
            slots_text = f"📊 Slots: {used_slots}/{total_slots}"
            draw.text((50, stats_y), slots_text, fill='#FFC107', font=self.fonts['medium'])
            
            # Greenhouse
            greenhouse_level = garden_info.get('greenhouse_level', 0)
            greenhouse_text = f"🏠 Greenhouse: Level {greenhouse_level}"
            draw.text((width - 250, stats_y), greenhouse_text, fill='#4CAF50', font=self.fonts['medium'])
            
            # Ready crops
            ready_count = sum(1 for p in plants if p.get('current_progress', 0) >= 100)
            if ready_count > 0:
                ready_text = f"✅ Ready: {ready_count}"
                draw.text((50, stats_y + 30), ready_text, fill='#00b894', font=self.fonts['medium'])
            
            # Footer
            footer = "Use /harvest to collect ready crops"
            draw.text((width//2 - 150, height - 30), footer, fill='#CCCCCC', font=self.fonts['small'])
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Garden image error: {e}")
            return None
    
    def create_scratch_card(self, ticket_id: str, numbers: str) -> Optional[bytes]:
        """Create lottery scratch card"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 400, 250
            img = Image.new('RGB', (width, height), color='#2a9d8f')
            draw = ImageDraw.Draw(img)
            
            # Decorative border
            draw.rectangle([0, 0, width, height], outline='#264653', width=8)
            draw.rectangle([10, 10, width-10, height-10], outline='#e9c46a', width=4)
            
            # Title with shadow
            draw.text((width//2 - 85, 25), "🎰 LOTTERY", fill='#264653', font=self.fonts['title'])
            draw.text((width//2 - 83, 23), "🎰 LOTTERY", fill='white', font=self.fonts['title'])
            
            # Ticket ID
            draw.text((width//2 - 70, 70), f"Ticket #{ticket_id}", fill='#ffd166', font=self.fonts['large'])
            
            # Scratch area
            scratch_area = self._create_scratch_pattern(width//2 - 150, 110, 300, 80)
            img.paste(scratch_area, (width//2 - 150, 110))
            
            # Hidden numbers (peek)
            if len(numbers) >= 6:
                hidden = f"🎫 {numbers[0]} • • • • {numbers[-1]}"
                draw.text((width//2 - 90, 135), hidden, fill='#264653', font=self.fonts['medium'])
            
            # Instructions
            draw.text((width//2 - 180, height - 40), 
                     "Use /scratch to reveal numbers!", 
                     fill='#e9f5db', font=self.fonts['small'])
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Scratch card error: {e}")
            return None
    
    def _draw_progress_circle(self, draw, x: int, y: int, radius: int, progress: float):
        """Draw progress circle"""
        if not HAS_PILLOW:
            return
        
        try:
            # Background circle
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                        fill='#2d3436', outline='#636e72', width=2)
            
            # Progress arc
            if progress > 0:
                # Convert progress to angle (360° = 100%)
                angle = int(360 * progress / 100)
                
                # Create mask for arc
                mask = Image.new('L', (radius*4, radius*4), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.pieslice([0, 0, radius*4, radius*4], 
                                  -90, angle-90, fill=255)
                mask = mask.resize((radius*2, radius*2), Image.Resampling.LANCZOS)
                
                # Create colored circle
                color_img = Image.new('RGB', (radius*2, radius*2), 
                                    '#00b894' if progress >= 100 else '#0984e3')
                
                # Apply mask
                color_img.putalpha(mask)
                
                # Paste onto main image
                # Note: This requires the main image reference
                pass  # Simplified for now
                
            # Percentage text
            text = f"{int(progress)}%"
            draw.text((x-10, y-8), text, fill='white', font=self.fonts['small'])
            
        except Exception as e:
            logger.error(f"Progress circle error: {e}")
    
    def _create_scratch_pattern(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """Create scratch-off pattern"""
        if not HAS_PILLOW:
            return Image.new('RGB', (width, height), color='#e9c46a')
        
        pattern = Image.new('RGB', (width, height), color='#e9c46a')
        draw = ImageDraw.Draw(pattern)
        
        # Create scratch texture
        for i in range(0, width, 5):
            for j in range(0, height, 5):
                if random.random() > 0.7:
                    color = random.choice(['#f4a261', '#e76f51', '#e9c46a'])
                    draw.rectangle([i, j, i+3, j+3], fill=color)
        
        return pattern
    
    def create_business_card(self, business_data: Dict) -> Optional[bytes]:
        """Create business card image"""
        if not HAS_PILLOW:
            return None
        
        try:
            width, height = 500, 300
            img = Image.new('RGB', (width, height), color='#2d3436')
            draw = ImageDraw.Draw(img)
            
            # Business header
            business_type = business_data.get('type', '').upper()
            business_name = business_data.get('name', 'Business')
            
            # Background stripe
            draw.rectangle([0, 0, width, 80], fill='#0984e3')
            
            # Business icon
            icons = {
                'farm': '🌾', 'store': '🏪', 'restaurant': '🍽️',
                'hotel': '🏨', 'casino': '🎰'
            }
            icon = icons.get(business_data.get('type', ''), '🏢')
            
            draw.text((30, 20), icon, fill='white', font=self.fonts['title'])
            
            # Business name
            draw.text((80, 25), business_name, fill='white', font=self.fonts['title'])
            
            # Business type
            draw.text((80, 60), business_type, fill='#dfe6e9', font=self.fonts['small'])
            
            # Stats
            stats = [
                ("Level", str(business_data.get('level', 1))),
                ("Income", f"${business_data.get('income', 0):,}/day"),
                ("Total Earned", f"${business_data.get('total_earned', 0):,}"),
                ("Next Collection", "Ready" if business_data.get('ready', False) else "Waiting")
            ]
            
            y_offset = 100
            for label, value in stats:
                # Label
                draw.text((50, y_offset), f"{label}:", fill='#CCCCCC', font=self.fonts['medium'])
                
                # Value
                draw.text((200, y_offset), value, fill='#00b894', font=self.fonts['medium'])
                
                y_offset += 40
            
            # Border
            draw.rectangle([0, 0, width, height], outline='#636e72', width=2)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Business card error: {e}")
            return None
    
    def create_stock_chart(self, symbol: str, history: List[float]) -> Optional[bytes]:
        """Create simple stock chart"""
        if not HAS_PILLOW or len(history) < 2:
            return None
        
        try:
            width, height = 400, 200
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((10, 10), f"📈 {symbol} Price History", fill='white', font=self.fonts['medium'])
            
            # Calculate chart dimensions
            chart_width = width - 40
            chart_height = height - 60
            chart_x = 20
            chart_y = 40
            
            # Find min and max values
            min_price = min(history)
            max_price = max(history)
            price_range = max_price - min_price if max_price > min_price else 1
            
            # Draw grid
            for i in range(0, chart_width + 1, 40):
                draw.line([(chart_x + i, chart_y), (chart_x + i, chart_y + chart_height)], 
                         fill='#2d3436', width=1)
            
            for i in range(0, chart_height + 1, 40):
                draw.line([(chart_x, chart_y + i), (chart_x + chart_width, chart_y + i)], 
                         fill='#2d3436', width=1)
            
            # Draw price line
            points = []
            for i, price in enumerate(history):
                x = chart_x + (i * chart_width / (len(history) - 1))
                y = chart_y + chart_height - ((price - min_price) / price_range * chart_height)
                points.append((x, y))
            
            # Draw line
            if len(points) > 1:
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i+1]], fill='#00b894', width=2)
            
            # Draw points
            for x, y in points:
                draw.ellipse([x-3, y-3, x+3, y+3], fill='#fd79a8')
            
            # Price labels
            current_price = history[-1]
            previous_price = history[-2] if len(history) > 1 else current_price
            change = current_price - previous_price
            change_percent = (change / previous_price * 100) if previous_price > 0 else 0
            
            price_text = f"${current_price:.2f}"
            change_text = f"{change:+.2f} ({change_percent:+.1f}%)"
            change_color = '#00b894' if change >= 0 else '#d63031'
            
            draw.text((chart_x, chart_y + chart_height + 10), 
                     price_text, fill='white', font=self.fonts['medium'])
            draw.text((chart_x + 100, chart_y + chart_height + 10), 
                     change_text, fill=change_color, font=self.fonts['medium'])
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Stock chart error: {e}")
            return None

# Global instance
image_gen = ImageGenerator()
