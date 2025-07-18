import os
import json
import random
import requests
from datetime import datetime
from pathlib import Path
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import textwrap
import schedule
import time
import pyttsx3
import threading
import hashlib

class OpenSourceCatVideoGenerator:
    def __init__(self, config_file='config.json'):
        """Initialize the cat video generator with open source configuration."""
        self.config = self.load_config(config_file)
        self.output_dir = Path(self.config['output_directory'])
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize offline TTS engine
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # Content types for variety
        self.content_types = ['fun_fact', 'care_tip', 'quote', 'meme_fact']
        
        # Used content tracker to avoid repetition
        self.used_content_file = 'used_content.json'
        self.used_content = self.load_used_content()
        
        # Pre-written cat content database
        self.cat_content_db = self.load_cat_content_database()
    
    def load_config(self, config_file):
        """Load configuration from JSON file."""
        default_config = {
            "output_directory": "./cat_videos",
            "video_duration": 15,
            "video_resolution": [1080, 1920],  # TikTok format
            "font_path": None,  # Will auto-detect system fonts
            "tts_rate": 150,
            "tts_volume": 0.8,
            "background_colors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return {**default_config, **config}
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Creating default config.")
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def load_used_content(self):
        """Load previously used content to avoid repetition."""
        try:
            with open(self.used_content_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_used_content(self):
        """Save used content to file."""
        with open(self.used_content_file, 'w') as f:
            json.dump(self.used_content, f, indent=2)
    
    def setup_tts(self):
        """Setup text-to-speech engine."""
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a female voice
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
            
            self.tts_engine.setProperty('rate', self.config['tts_rate'])
            self.tts_engine.setProperty('volume', self.config['tts_volume'])
            
        except Exception as e:
            print(f"TTS setup warning: {e}")
    
    def load_cat_content_database(self):
        """Load pre-written cat content database."""
        return {
            'fun_fact': [
                "Cats have a third eyelid called a nictitating membrane that protects their eyes during fights or hunting.",
                "A cat's purr vibrates at frequencies between 25-50 Hz, which can help heal bones and reduce pain in humans.",
                "Cats can rotate their ears 180 degrees and have 32 muscles controlling each ear, compared to humans who have only 6.",
                "The world's longest cat measured 48.5 inches from nose to tail tip. That's longer than a baseball bat!",
                "Cats have scent glands on their paws, which is why they knead soft surfaces to mark their territory.",
                "A cat's brain is 90% similar to a human brain, and they have nearly twice as many neurons as dogs.",
                "Cats can see in just one-sixth the light that humans need and have a 200-degree field of vision.",
                "The average cat sleeps 12-16 hours per day, which means they're awake for only 6-8 hours daily.",
                "Cats have a special scent organ called the Jacobson's organ that lets them 'taste' smells.",
                "A group of cats is called a 'clowder' and a group of kittens is called a 'kindle'."
            ],
            'care_tip': [
                "Brush your cat daily to prevent hairballs and reduce shedding. Long-haired cats need even more frequent brushing.",
                "Keep your cat's litter box clean by scooping daily. Cats are very particular about cleanliness.",
                "Provide fresh water daily in a clean bowl. Many cats prefer running water, so consider a pet fountain.",
                "Schedule regular vet checkups every 6-12 months to catch health issues early.",
                "Keep your cat mentally stimulated with puzzle toys and rotate toys weekly to maintain interest.",
                "Trim your cat's nails every 2-3 weeks to prevent them from getting too sharp or long.",
                "Create vertical spaces with cat trees or shelves. Cats love to climb and observe from high places.",
                "Feed your cat at the same times daily to establish a routine and prevent overeating.",
                "Provide multiple litter boxes if you have multiple cats - one per cat plus one extra.",
                "Keep toxic plants like lilies, azaleas, and poinsettias away from your curious cat."
            ],
            'quote': [
                "A cat is a puzzle for which there is no solution. - Hazel Nicholson",
                "Time spent with cats is never wasted. - Sigmund Freud",
                "Cats choose us; we don't own them. - Kristin Cast",
                "In ancient times cats were worshipped as gods; they have not forgotten this. - Terry Pratchett",
                "A cat has absolute emotional honesty: human beings may hide their feelings, but a cat does not.",
                "Cats are connoisseurs of comfort. - James Herriot",
                "There are few things in life more heartwarming than to be welcomed by a cat. - Tay Hohoff",
                "A cat is a lion in a jungle of small bushes. - English Proverb",
                "Cats are intended to teach us that not everything in nature has a function. - Garrison Keillor",
                "The cat does not offer services. The cat offers itself. - William S. Burroughs"
            ],
            'meme_fact': [
                "Your cat isn't ignoring you - they're just pretending you don't exist until dinner time.",
                "Cats knock things off tables not out of spite, but because they're testing gravity... constantly.",
                "That 3 AM zoomies session? Your cat is practicing for their invisible marathon competition.",
                "When your cat brings you dead mice, they're not being mean - they think you're a terrible hunter.",
                "Cats sleep 16 hours a day and still act exhausted when you ask them to do literally anything.",
                "Your cat's favorite box cost $0, but they'll ignore the $50 cat bed you bought them.",
                "Cats have perfected the art of looking completely innocent while plotting your demise.",
                "Every cat owner knows the struggle of trying to use a computer while your cat demands attention.",
                "Cats can hear a can opener from three rooms away but mysteriously go deaf when you call their name.",
                "Your cat judges your life choices, especially when you're eating cereal for dinner again."
            ]
        }
    
    def generate_script(self, content_type):
        """Generate script from pre-written content database."""
        available_content = [
            content for content in self.cat_content_db[content_type]
            if content not in self.used_content
        ]
        
        if not available_content:
            # Reset used content if we've used everything
            self.used_content = []
            available_content = self.cat_content_db[content_type]
        
        script = random.choice(available_content)
        self.used_content.append(script)
        self.save_used_content()
        
        return script
    
    def generate_voiceover(self, script, output_path):
        """Generate voiceover using pyttsx3 (offline TTS)."""
        try:
            def save_audio():
                self.tts_engine.save_to_file(script, str(output_path))
                self.tts_engine.runAndWait()
            
            # Run TTS in a separate thread to avoid blocking
            audio_thread = threading.Thread(target=save_audio)
            audio_thread.start()
            audio_thread.join(timeout=30)  # 30 second timeout
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"Error generating voiceover: {e}")
            return False
    
    def get_free_cat_images(self):
        """Get free cat images from multiple sources."""
        try:
            # Try Lorem Picsum with seed for consistency
            seed = random.randint(1, 1000)
            images = [
                f"https://picsum.photos/seed/{seed + i}/1080/1920?random" for i in range(3)
            ]
            
            # Add some PlaceKitten images
            kitten_images = [
                "https://placekitten.com/1080/1920",
                "https://placekitten.com/1080/1920?random=1",
                "https://placekitten.com/1080/1920?random=2"
            ]
            
            return images + kitten_images
            
        except Exception as e:
            print(f"Error getting images: {e}")
            return ["https://placekitten.com/1080/1920"] * 3
    
    def create_gradient_background(self, size=(1080, 1920), color1=None, color2=None):
        """Create a gradient background image."""
        if not color1:
            color1 = random.choice(self.config['background_colors'])
        if not color2:
            color2 = random.choice(self.config['background_colors'])
        
        # Convert hex to RGB
        color1_rgb = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        color2_rgb = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        
        img = Image.new('RGB', size, color1_rgb)
        draw = ImageDraw.Draw(img)
        
        # Create gradient
        for i in range(size[1]):
            ratio = i / size[1]
            r = int(color1_rgb[0] * (1 - ratio) + color2_rgb[0] * ratio)
            g = int(color1_rgb[1] * (1 - ratio) + color2_rgb[1] * ratio)
            b = int(color1_rgb[2] * (1 - ratio) + color2_rgb[2] * ratio)
            draw.line([(0, i), (size[0], i)], fill=(r, g, b))
        
        return img
    
    def download_image(self, url, output_path):
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False
    
    def get_system_font(self):
        """Get available system font."""
        font_paths = [
            # Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            # macOS
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        return None  # Will use default font
    
    def create_text_overlay(self, text, size=(1080, 1920)):
        """Create text overlay image with better styling."""
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Get font
        font_path = self.config['font_path'] or self.get_system_font()
        try:
            if font_path:
                font = ImageFont.truetype(font_path, 70)
                small_font = ImageFont.truetype(font_path, 40)
            else:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Wrap text
        wrapped_text = textwrap.fill(text, width=25)
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        # Draw background rectangle
        padding = 40
        rect_coords = [x - padding, y - padding, x + text_width + padding, y + text_height + padding]
        draw.rounded_rectangle(rect_coords, radius=20, fill=(0, 0, 0, 150))
        
        # Draw text with outline
        outline_color = (255, 255, 255, 255)
        text_color = (255, 255, 255, 255)
        
        for adj in range(-2, 3):
            for adj2 in range(-2, 3):
                if adj != 0 or adj2 != 0:
                    draw.text((x + adj, y + adj2), wrapped_text, font=font, fill=(0, 0, 0, 255))
        
        draw.text((x, y), wrapped_text, font=font, fill=text_color, align='center')
        
        return img
    
    def create_video(self, script, content_type):
        """Create the final video using open source tools."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = f"cat_video_{content_type}_{timestamp}.mp4"
        video_path = self.output_dir / video_name
        
        # Generate voiceover
        audio_path = self.output_dir / f"audio_{timestamp}.wav"
        audio_success = self.generate_voiceover(script, audio_path)
        
        # Create gradient backgrounds instead of downloading images
        clips = []
        num_clips = 3
        duration_per_clip = self.config['video_duration'] / num_clips
        
        for i in range(num_clips):
            # Create gradient background
            bg_img = self.create_gradient_background()
            bg_path = self.output_dir / f"bg_{i}_{timestamp}.png"
            bg_img.save(bg_path)
            
            # Create video clip
            clip = ImageClip(str(bg_path)).set_duration(duration_per_clip)
            clips.append(clip)
        
        try:
            # Concatenate clips
            video = concatenate_videoclips(clips)
            
            # Create text overlay
            text_overlay = self.create_text_overlay(script)
            text_overlay_path = self.output_dir / f"text_overlay_{timestamp}.png"
            text_overlay.save(text_overlay_path)
            
            # Add text overlay
            text_clip = ImageClip(str(text_overlay_path)).set_duration(video.duration)
            video = CompositeVideoClip([video, text_clip])
            
            # Add audio if available
            if audio_success and os.path.exists(audio_path):
                try:
                    audio = AudioFileClip(str(audio_path))
                    video = video.set_audio(audio)
                except Exception as e:
                    print(f"Could not add audio: {e}")
            
            # Write final video
            video.write_videofile(
                str(video_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Cleanup temporary files
            for i in range(num_clips):
                bg_path = self.output_dir / f"bg_{i}_{timestamp}.png"
                if bg_path.exists():
                    bg_path.unlink()
            
            if audio_path.exists():
                audio_path.unlink()
            text_overlay_path.unlink()
            
            print(f"Video created successfully: {video_path}")
            return video_path
            
        except Exception as e:
            print(f"Error creating video: {e}")
            return None
    
    def generate_daily_video(self):
        """Generate a daily cat video."""
        content_type = random.choice(self.content_types)
        print(f"Generating {content_type} video...")
        
        script = self.generate_script(content_type)
        print(f"Script: {script}")
        
        video_path = self.create_video(script, content_type)
        
        if video_path:
            print(f"Daily cat video generated: {video_path}")
            return video_path
        else:
            print("Failed to generate daily video")
            return None
    
    def schedule_daily_videos(self):
        """Schedule daily video generation."""
        schedule.every().day.at("09:00").do(self.generate_daily_video)
        
        print("Scheduled daily cat videos at 9:00 AM")
        print("Press Ctrl+C to stop the scheduler")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main function to run the cat video generator."""
    generator = OpenSourceCatVideoGenerator()
    
    print("🐱 Open Source Cat Video Generator 🐱")
    print("=" * 40)
    print("1. Generate video now")
    print("2. Start daily scheduler")
    print("3. Test TTS system")
    print("4. Exit")
    
    choice = input("Enter your choice (1-4): ")
    
    if choice == '1':
        generator.generate_daily_video()
    elif choice == '2':
        try:
            generator.schedule_daily_videos()
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
    elif choice == '3':
        print("Testing TTS system...")
        test_path = Path("test_audio.wav")
        if generator.generate_voiceover("Testing text to speech system", test_path):
            print("TTS test successful!")
            if test_path.exists():
                test_path.unlink()
        else:
            print("TTS test failed.")
    elif choice == '4':
        print("Goodbye! 🐱")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
