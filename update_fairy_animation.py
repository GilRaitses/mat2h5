import re
import os

BASE_DIR = '/Users/gilraitses/INDYsim/scripts/2025-12-04/mat2h5'

def main():
    # Read the fairy frames
    with open(os.path.join(BASE_DIR, 'docs/fairy.yaml'), 'r') as f:
        lines = f.readlines()

    # Extract frames (using 1-based line numbers from earlier analysis, converting to 0-based)
    # Frame 1: Lines 1-75 -> indices 0-75
    frame1 = "".join(lines[0:75])
    
    # Frame 2: Lines 79-153 -> indices 78-153
    frame2 = "".join(lines[78:153])
    
    # Frame 3: Lines 155-229 -> indices 154-229
    frame3 = "".join(lines[154:229])
    
    # Frame 4: Lines 236-310 -> indices 235-310
    frame4 = "".join(lines[235:310])

    frames = [frame1, frame2, frame3, frame4]
    
    # Construct the JS array string
    js_frames = "const fairyFrames = [\n"
    for i, frame in enumerate(frames):
        # Escape backticks and backslashes if any
        safe_frame = frame.replace('\\', '\\\\').replace('`', '\\`')
        js_frames += f"    `{safe_frame}`,\n"
    js_frames += "];"

    # Read index.html
    with open(os.path.join(BASE_DIR, 'index.html'), 'r') as f:
        content = f.read()

    # 1. Update the HTML hardcoded content (Frame 1)
    html_pattern = r'(<div id="global-fairy-background">[\s\S]*?<div class="fairy-art">)([\s\S]*?)(</div>)'
    
    def replace_html_art(match):
        return match.group(1) + frame1 + match.group(3)
        
    new_content = re.sub(html_pattern, replace_html_art, content, count=1)

    # 2. Replace JS logic
    # Find the const fairyASCII = `...`; block and subsequent logic
    # We match from "const fairyASCII =" to the end of the else block or similar structure.
    # In previous steps, we had:
    # if (fairyArt) { fairyArt.textContent = fairyASCII; }
    # if (mainFairyArt) { ... } else { ... }
    
    # But wait, in the last edit I consolidated it to:
    # const fairyASCII = `...`;
    # if (fairyArt) { fairyArt.textContent = fairyASCII; }
    # if (mainFairyArt) { ... } 
    
    # Actually, I consolidated IDs too. There is only one fairy-art now in the JS (though the var name might be different).
    # Let's look at the file content from my last read (which I don't have fully fresh).
    # I'll use a broader regex to catch the variable definition and the immediate usage.
    
    # "const fairyASCII = `.*?`;" (dotall)
    
    new_js_logic = f"""        // Fairy animation frames
        {js_frames}
        
        const fairyArt = document.querySelector('#global-fairy-background .fairy-art');
        
        // Initial frame
        if (fairyArt) {{
            fairyArt.textContent = fairyFrames[0];
        }}
        
        // Animation loop
        let currentFrame = 0;
        setInterval(() => {{
            currentFrame = (currentFrame + 1) % fairyFrames.length;
            if (fairyArt) {{
                fairyArt.textContent = fairyFrames[currentFrame];
            }}
        }}, 150); // 150ms for gif-like animation
"""

    # Remove the old variable and usage
    # We'll search for "const fairyASCII =" and the following block.
    # Since the string is huge, regex might be slow or hit limits if we aren't careful.
    # Instead of regex for the huge string, let's find the start and end lines.
    
    lines_html = new_content.split('\n')
    start_line = -1
    end_line = -1
    
    for i, line in enumerate(lines_html):
        if 'const fairyASCII = `' in line:
            start_line = i
        if start_line != -1 and 'console.log(\'Main fairy art element not found\');' in line:
            # This captures the end of the logic block roughly
            # The closing brace } for the else block is on the next line usually
            end_line = i + 2 # Grab the closing brace
            break
            
    if start_line != -1 and end_line != -1:
        # Replace lines
        new_lines = lines_html[:start_line] + [new_js_logic] + lines_html[end_line+1:]
        new_content = '\n'.join(new_lines)
    else:
        print("Could not find JS start/end lines via simple search. Trying regex fallback.")
        # Fallback regex
        pattern = r"const fairyASCII = `[\s\S]*?console\.log\('Main fairy art element not found'\);\s+}"
        if re.search(pattern, new_content):
             new_content = re.sub(pattern, new_js_logic, new_content)
        else:
             print("Regex failed too.")

    # Write back
    with open(os.path.join(BASE_DIR, 'index.html'), 'w') as f:
        f.write(new_content)

if __name__ == '__main__':
    main()
