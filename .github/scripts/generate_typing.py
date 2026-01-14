#!/usr/bin/env python3
"""
Terminal Typing Animation Generator

Generates an animated SVG that simulates terminal typing effect
with light green text, blinking cursor, and loop with clear screen.
"""

import os

OUTPUT_PATH = 'dist/typing.svg'

# Colors - Terminal style
BG_COLOR = "#0d1117"
TEXT_COLOR = "#39d353"  # Light green (GitHub's bright green)
CURSOR_COLOR = "#39d353"

# Animation timing
CHAR_DURATION = 0.05  # 50ms per character
LINE_PAUSE = 0.75  # 0.75 seconds pause after each line
CLEAR_DURATION = 0.5  # Clear screen fade duration

# Font settings
FONT_FAMILY = "'Courier New', Consolas, 'Liberation Mono', monospace"
FONT_SIZE = 18
LINE_HEIGHT = 28

# Lines to type
LINES = [
    "> Initializing Profile: Mohamed Elrefaay_",
    "> Role: AI Developer @ Hail Emirate (Innovation & AI Dept)",
    "",
    "> Loading Production Modules...",
    "  [+] Advanced RAG & Vector Search Architectures",
    "  [+] Orchestrating Multi-Agent Workflows",
    "  [+] GenAI System Design & Optimization",
    "  [+] Deep Learning Research & Development",
    "",
    "> Status: turning_innovation_into_reality..."
]

FINAL_MSG = "Feel free to reach out through any of the channels below , I am pleased to help"

def generate_svg() -> str:
    """Generate the terminal typing animation SVG."""
    
    # Calculate dimensions
    max_chars = max(len(line) for line in LINES)
    # Ensure width is enough for the final message (~80 chars)
    width = max(max_chars * 11 + 60, 900)  
    height = len(LINES) * LINE_HEIGHT + 60
    
    # Calculate animations
    current_time = 0.5  # Start after 0.5s
    
    # Separate animations for main text (fades out) and status line (stays)
    main_text_animations = []
    status_text_animations = []
    
    cursor_keyframes = []
    cursor_time = 0.5
    
    for line_idx, line in enumerate(LINES):
        y_pos = 40 + line_idx * LINE_HEIGHT
        is_last_line = (line_idx == len(LINES) - 1)
        
        if not line:  # Empty line
            current_time += LINE_PAUSE
            cursor_time += LINE_PAUSE
            continue
        
        # Character animations
        for char_idx, char in enumerate(line):
            x_pos = 30 + char_idx * 10.5  # Approximate monospace width
            char_time = current_time + char_idx * CHAR_DURATION
            
            # Escape special characters for SVG
            if char == '<':
                char_esc = '&lt;'
            elif char == '>':
                char_esc = '&gt;'
            elif char == '&':
                char_esc = '&amp;'
            elif char == '"':
                char_esc = '&quot;'
            else:
                char_esc = char
            
            anim = {
                'char': char_esc,
                'x': x_pos,
                'y': y_pos,
                'begin': char_time
            }
            
            if is_last_line:
                status_text_animations.append(anim)
            else:
                main_text_animations.append(anim)
            
            # Cursor keyframes matching character position
            cursor_keyframes.append({
                'x': x_pos + 10.5, # Cursor after character
                'y': y_pos,
                'time': char_time
            })
            
        current_time += len(line) * CHAR_DURATION + LINE_PAUSE
        cursor_time = current_time # Sync cursor time
        
        # Add a keyframe for cursor at the end of the line (during the pause)
        if cursor_keyframes:
             cursor_keyframes.append({
                'x': cursor_keyframes[-1]['x'],
                'y': cursor_keyframes[-1]['y'],
                'time': cursor_time
            })

    
    typing_end_time = current_time
    fade_out_start = typing_end_time
    fade_out_end = fade_out_start + CLEAR_DURATION
    final_msg_start = fade_out_end + 0.5
    
    # Total duration for the cursor animation definition
    # We extend it to cover the fade out/in transition so cursor stays in place
    total_duration = final_msg_start + 1.0 
    
    # Build SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
    <style>
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0; }}
        }}
        @keyframes fadeOut {{
            0% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        .cursor {{
            animation: blink 1s infinite;
        }}
        .main-text-container {{
            animation: fadeOut {CLEAR_DURATION}s ease-in-out {fade_out_start}s forwards;
        }}
        .final-msg {{
            opacity: 0;
            animation: fadeIn 1s ease-in-out {final_msg_start}s forwards;
        }}
    </style>
    
    <rect width="{width}" height="{height}" fill="{BG_COLOR}"/>
    
    <!-- Terminal window decoration -->
    <rect x="10" y="10" width="{width - 20}" height="{height - 20}" 
          fill="{BG_COLOR}" stroke="#30363d" stroke-width="1" rx="6"/>
    
    <!-- Terminal header dots -->
    <circle cx="28" cy="22" r="5" fill="#ff5f56"/>
    <circle cx="48" cy="22" r="5" fill="#ffbd2e"/>
    <circle cx="68" cy="22" r="5" fill="#27c93f"/>
    
    <!-- Main text (fades out) -->
    <g class="main-text-container" transform="translate(10, 25)">
'''

    # Add main text characters
    for anim in main_text_animations:
        char = anim['char']
        if char.strip() == '':
            char = '&#160;'
        
        svg += f'''        <text x="{anim['x']}" y="{anim['y']}" 
              fill="{TEXT_COLOR}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}"
              opacity="0">
            {char}
            <animate attributeName="opacity" from="0" to="1" 
                     begin="{anim['begin']:.2f}s" dur="0.01s" fill="freeze"/>
        </text>
'''
    svg += '    </g>\n'
    
    # Status text (persistent)
    svg += '    <g class="status-text-container" transform="translate(10, 25)">\n'
    for anim in status_text_animations:
        char = anim['char']
        if char.strip() == '':
            char = '&#160;'
        
        svg += f'''        <text x="{anim['x']}" y="{anim['y']}" 
              fill="{TEXT_COLOR}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}"
              opacity="0">
            {char}
            <animate attributeName="opacity" from="0" to="1" 
                     begin="{anim['begin']:.2f}s" dur="0.01s" fill="freeze"/>
        </text>
'''
    svg += '    </g>\n'

    # Cursor
    # Normalize cursor times to 0-1 range for keyTimes
    # We extend the last keyframe to total_duration to keep it visible
    if cursor_keyframes:
        last_kf = cursor_keyframes[-1]
        cursor_keyframes.append({
            'x': last_kf['x'],
            'y': last_kf['y'],
            'time': total_duration # Stay until end
        })
        
    cursor_x_values = ";".join([str(kf['x']) for kf in cursor_keyframes])
    cursor_y_values = ";".join([str(kf['y']) for kf in cursor_keyframes])
    cursor_times = ";".join([f"{kf['time'] / total_duration:.4f}" for kf in cursor_keyframes])
    
    svg += f'''
    <g transform="translate(10, 25)">
        <!-- Blinking cursor -->
        <rect class="cursor" width="10" height="{FONT_SIZE + 2}" fill="{CURSOR_COLOR}" opacity="0.8">
            <animate attributeName="x" values="{cursor_x_values}" 
                     keyTimes="{cursor_times}" dur="{total_duration}s" fill="freeze"/>
            <animate attributeName="y" values="{cursor_y_values}" 
                     keyTimes="{cursor_times}" dur="{total_duration}s" fill="freeze"/>
            <animate attributeName="opacity" from="0" to="0.8" begin="0.5s" dur="0.01s" fill="freeze"/>
        </rect>
    </g>
'''
    
    # Final Message Centered
    # We place it in the center of the available space (roughly)
    # Since main text faded out, we have the upper area free.
    # The status line is at the bottom.
    # Center Y approx: (height - status_line_height) / 2
    # But using 50% is easier, just need to make sure it doesn't overlap status line if screen is small.
    # With fixed height based on lines, 50% should be fine as status is at bottom.
    
    svg += f'''
    <!-- Final Message Centered -->
    <g class="final-msg">
        <text x="50%" y="40%" text-anchor="middle" dominant-baseline="middle"
              fill="{TEXT_COLOR}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">
            {FINAL_MSG}
        </text>
    </g>
             
</svg>'''

    return svg


def main():
    """Main entry point."""
    print("[TYPING] Generating terminal typing animation...")
    
    # Generate SVG
    svg_content = generate_svg()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Write SVG file
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"[OK] SVG saved to {OUTPUT_PATH}")
    print("[TYPING] Animation ready!")


if __name__ == '__main__':
    main()
