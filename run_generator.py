#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our generator
from cat_video_generator import OpenSourceCatVideoGenerator

def main():
    """Run the generator once for GitHub Actions."""
    try:
        print("🐱 Starting Cat Video Generator...")
        generator = OpenSourceCatVideoGenerator()
        
        # Generate a single video
        video_path = generator.generate_daily_video()
        
        if video_path:
            print(f"✅ Success! Video created: {video_path}")
            # Print video info for GitHub Actions log
            if Path(video_path).exists():
                size = Path(video_path).stat().st_size / 1024 / 1024  # MB
                print(f"📹 Video size: {size:.2f} MB")
            return 0
        else:
            print("❌ Failed to generate video")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())