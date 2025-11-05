#!/usr/bin/env python3
"""
Image Optimization Script for Lighthouse Performance
Automatically creates responsive versions of hero images

Run: python optimize_images.py
"""

import os
from pathlib import Path

try:
    from PIL import Image
    print("✅ Pillow is installed")
except ImportError:
    print("❌ Pillow not installed. Installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'Pillow'])
    from PIL import Image
    print("✅ Pillow installed successfully")

def optimize_image(input_path, output_path, width, quality=85):
    """
    Resize and optimize an image

    Args:
        input_path: Path to original image
        output_path: Path for optimized image
        width: Target width in pixels
        quality: JPEG quality (1-100)
    """
    try:
        with Image.open(input_path) as img:
            # Get original dimensions
            original_width, original_height = img.size

            # Calculate new height maintaining aspect ratio
            aspect_ratio = original_height / original_width
            height = int(width * aspect_ratio)

            print(f"📸 Processing: {os.path.basename(input_path)}")
            print(f"   Original: {original_width}x{original_height}")
            print(f"   Target: {width}x{height}")

            # Resize using high-quality Lanczos filter
            resized = img.resize((width, height), Image.Resampling.LANCZOS)

            # Save with compression
            resized.save(output_path, 'JPEG', quality=quality, optimize=True)

            # Get file sizes
            original_size = os.path.getsize(input_path) / 1024
            new_size = os.path.getsize(output_path) / 1024
            savings = ((original_size - new_size) / original_size) * 100

            print(f"   ✅ Saved: {output_path}")
            print(f"   💾 Size: {original_size:.1f}KB → {new_size:.1f}KB (saved {savings:.1f}%)")
            print()

            return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🚀 Image Optimization for Lighthouse Performance")
    print("=" * 60)
    print()

    # Get the base directory
    base_dir = Path(__file__).parent
    images_dir = base_dir / "main" / "static" / "images"

    if not images_dir.exists():
        print(f"❌ Images directory not found: {images_dir}")
        print("Please make sure you're running this from the project root")
        return

    print(f"📁 Images directory: {images_dir}")
    print()

    # Images to optimize
    images_to_optimize = [
        {
            'name': 'FRI BACKGROUND.jpg',
            'mobile': 'FRI BACKGROUND-mobile.jpg',
            'tablet': 'FRI BACKGROUND-tablet.jpg',
        },
        {
            'name': '2.jpg',
            'mobile': '2-mobile.jpg',
            'tablet': '2-tablet.jpg',
        }
    ]

    total_saved = 0
    success_count = 0

    for img_config in images_to_optimize:
        original_path = images_dir / img_config['name']

        if not original_path.exists():
            print(f"⚠️  Skipping {img_config['name']} - file not found")
            print()
            continue

        print(f"🎨 Optimizing: {img_config['name']}")
        print("-" * 60)

        # Create mobile version (640px, quality 80)
        mobile_path = images_dir / img_config['mobile']
        if optimize_image(original_path, mobile_path, width=640, quality=80):
            success_count += 1

        # Create tablet version (1024px, quality 85)
        tablet_path = images_dir / img_config['tablet']
        if optimize_image(original_path, tablet_path, width=1024, quality=85):
            success_count += 1

    print("=" * 60)
    print(f"✅ Optimization complete!")
    print(f"   Created {success_count} optimized images")
    print()
    print("📊 Expected Performance Impact:")
    print("   • Mobile LCP: 5.4s → 2.0-2.5s (-60%)")
    print("   • Mobile Score: 78 → 85-92 (+7-14 points)")
    print("   • Image delivery: ~366KB savings")
    print()
    print("🔄 Next Steps:")
    print("   1. Restart your Django server")
    print("   2. Clear browser cache (Ctrl+Shift+Del)")
    print("   3. Run Lighthouse again")
    print("=" * 60)

if __name__ == "__main__":
    main()
