
import re
from PIL import Image, ImageDraw, ImageFont
import os

def render_ascii_to_image(lines, color, output_file, max_size=None, crop=True):
    # Font settings
    # Try multiple fonts
    font_paths = [
        "C:\\Windows\\Fonts\\consola.ttf",
        "C:\\Windows\\Fonts\\lucon.ttf", # Lucida Console
        "C:\\Windows\\Fonts\\cour.ttf",   # Courier New
    ]
    
    font = None
    font_size = 40 # Large size for high res render before downscaling
    
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                print(f"Using font: {fp}")
                break
            except:
                continue
    
    if not font:
        print("Warning: Could not load any monospace font, using default")
        font = ImageFont.load_default()

    # Measure size
    try:
        char_width = font.getlength("A")
        left, top, right, bottom = font.getbbox("A")
        char_height = bottom - top
    except:
        # Fallback for default font if getlength fails (older PILLOW)
        char_width = 10
        char_height = 15
        
    line_height = int(char_height * 1.2)
    
    # Calculate canvas size
    max_line_len = max((len(line) for line in lines), default=0)
    img_width = int(max_line_len * char_width) + 40
    img_height = int(len(lines) * line_height) + 40

    # Create image
    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw text
    y = 20
    for line in lines:
        if line.strip():
            draw.text((20, y), line, font=font, fill=color)
        y += line_height

    # Crop to content
    if crop:
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
            print(f"Cropped to {img.size}")
        else:
            print(f"Warning: Empty image bbox for {output_file}")
            # If empty, maybe the font didn't render braille chars?
            # Braille: U+2800 - U+28FF
            # If standard fonts fail, we might be in trouble.
            # But Consolas usually has them.
            pass

    # Resize if needed
    if max_size:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

    img.save(output_file)
    print(f"Generated {output_file} at size {img.size}")

def main():
    print("Starting asset generation...")
    
    # 1. Favicon (Fairy)
    try:
        with open('docs/assets/fairy-frames.js', 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'`(.*?)`', content, re.DOTALL)
        if match:
            text = match.group(1)
            lines = text.splitlines()
            # Trim
            while lines and not lines[0].strip(): lines.pop(0)
            while lines and not lines[-1].strip(): lines.pop()
            
            print(f"Fairy lines: {len(lines)}")
            # Chartreuse #7fff00 is (127, 255, 0)
            render_ascii_to_image(lines, (127, 255, 0, 255), "favicon.png", max_size=(64, 64))
        else:
            print("No fairy match found")
    except Exception as e:
        print(f"Error fairy: {e}")

    # 2. Cursor (Maggot)
    try:
        with open('docs/assets/maggot-frame.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_lines = content.splitlines()
        all_lines = [l for l in all_lines if l.strip() not in ['[', ']']]
        
        # Take first ~40 lines 
        frame_lines = all_lines[:40]
        
        # Remove completely empty lines at start/end
        while frame_lines and not frame_lines[0].strip(): frame_lines.pop(0)
        while frame_lines and not frame_lines[-1].strip(): frame_lines.pop()

        print(f"Maggot lines: {len(frame_lines)}")
        
        # Cursor Black (0, 0, 0)
        render_ascii_to_image(frame_lines, (0, 0, 0, 255), "cursor.png", max_size=(64, 64))

    except Exception as e:
        print(f"Error maggot: {e}")

if __name__ == "__main__":
    main()
