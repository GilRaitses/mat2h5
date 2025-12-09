
import re
import html

def enc(s):
    return html.escape(s)

def text_to_svg(text_lines, color="#7fff00", filename="output.svg", font_size=10, char_width=6, char_height=10):
    lines = [l for l in text_lines]
    if not lines:
        return
    
    # Calculate dimensions
    max_len = max(len(l) for l in lines)
    width = max_len * char_width
    height = len(lines) * char_height
    
    # SVG Content
    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    svg_content += f'<style>text {{ font-family: monospace; font-size: {font_size}px; fill: {color}; white-space: pre; }}</style>'
    
    for i, line in enumerate(lines):
        y = (i + 1) * char_height - 2 # adjustment for baseline
        if line.strip(): # Optimization: don't print empty lines
             svg_content += f'<text x="0" y="{y}">{enc(line)}</text>'
    
    svg_content += '</svg>'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Generated {filename}")

def main():
    # 1. Fairy Favicon
    try:
        with open('docs/assets/fairy-frames.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find the first frame in the array
        # const fairyFrames = [`...`, `...`]
        # We want content inside first backticks
        match = re.search(r'`(.*?)`', content, re.DOTALL)
        if match:
            fairy_text = match.group(1)
            # Remove first newline if it starts with one due to backtick formatting
            if fairy_text.startswith('\n'):
                fairy_text = fairy_text[1:]
            
            lines = fairy_text.splitlines()
            while lines and not lines[0].strip(): lines.pop(0)
            
            # Favicon: keep current size, Chartreuse
            text_to_svg(lines, color="#7fff00", filename="favicon.svg", font_size=10, char_width=6, char_height=10)
        else:
            print("Could not find fairy frames")
            
    except Exception as e:
        print(f"Error processing fairy: {e}")

    # 2. Maggot Cursor
    try:
        with open('docs/assets/maggot-frame.js', 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.splitlines()
        lines = [l for l in lines if l.strip() not in ['[', ']']]
        
        # Take first 84 lines (approx one frame)
        frame_lines = lines[:84]
        
        while frame_lines and not frame_lines[0].strip(): frame_lines.pop(0)
        while frame_lines and not frame_lines[-1].strip(): frame_lines.pop()

        # Cursor: Black color (visible on chartreuse body), Scaled down via viewBox/width
        # We'll use a smaller font size effectively or set width attribute.
        # Let's try font_size=10 but override width in text_to_svg? 
        # Actually I can just call text_to_svg with a wrapper or modify the function.
        # I'll verify text_to_svg definition. It takes filename.
        
        # Let's modify text_to_svg call for cursor to write manually or I need to modify the function to accept width override if I want it to scale.
        # EASIER: Just use small font size. 2px.
        # 100 chars * 1.2px (char_width 0.6?) -> 60px.
        # Let's say font_size=4, char_width=2.4, char_height=4.
        # That keeps aspect ratio roughly 0.6.
        
        text_to_svg(frame_lines, color="#000000", filename="cursor.svg", font_size=4, char_width=2.4, char_height=4)

    except Exception as e:
        print(f"Error processing maggot: {e}")

if __name__ == "__main__":
    main()
