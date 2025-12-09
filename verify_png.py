
from PIL import Image
import os

def check_image_content(filename):
    try:
        img = Image.open(filename)
        img = img.convert("RGBA")
        width, height = img.size
        print(f"Checking {filename} ({width}x{height})...")
        
        non_transparent_count = 0
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    non_transparent_count += 1
                    
        print(f"  Non-transparent pixels: {non_transparent_count}")
        if non_transparent_count == 0:
            print("  WARNING: Image is fully transparent!")
        elif non_transparent_count == width * height:
            print("  WARNING: Image is fully OPAQUE (Solid block?)")
            # Check center pixel
            print(f"  Center pixel: {pixels[width//2, height//2]}")
            print(f"  Top-left pixel: {pixels[0, 0]}")
        else:
            print(f"  Image has content ({non_transparent_count} / {width*height} pixels).")
            print(f"  Center pixel: {pixels[width//2, height//2]}")
            
    except Exception as e:
        print(f"  Error reading {filename}: {e}")

check_image_content("favicon.png")
check_image_content("cursor.png")
