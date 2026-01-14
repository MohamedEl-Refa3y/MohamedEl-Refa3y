#!/usr/bin/env python3
"""
Terminal Typing Animation Generator

Generates an animated SVG that simulates terminal typing effect
with light green text, blinking cursor, and persistent final message.
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
FADE_IN_DURATION = 1.0  # Final message fade in duration

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
]

FINAL_MSG = "Feel free to reach out through any of the channels below , I am pleased to help"
STATUS_LINE = "> Status: turning_innovation_into_reality..."

def generate_svg() -> str:
    """Generate the terminal typing animation SVG."""
    
    # Calculate dimensions - add extra space for final message and status
    max_chars = max(len(line) for line in LINES + [FINAL_MSG, STATUS_LINE])
    width = max(max_chars * 11 + 60, 800)  # Approximate character width
    height = (len(LINES) + 4) * LINE_HEIGHT + 60  # Extra space for final message and status
    
    # Build character animations
    animations = []
    current_time = 0.5  # Start after 0.5s
    
    for line_idx, line in enumerate(LINES):
        y_pos = 40 + line_idx * LINE_HEIGHT
        
        if not line:  # Empty line
            current_time += LINE_PAUSE
            continue
        
        for char_idx, char in enumerate(line):
            x_pos = 30 + char_idx * 10.5  # Approximate monospace width
            char_time = current_time + char_idx * CHAR_DURATION
            
            # Escape special characters for SVG
            if char == '<':
                char = '&lt;'
            elif char == '>':
                char = '&gt;'
            elif char == '&':
                char = '&amp;'
            elif char == '"':
                char = '&quot;'
            
            animations.append({
                'char': char,
                'x': x_pos,
                'y': y_pos,
                'begin': char_time,
                'line_idx': line_idx,
                'char_idx': char_idx
            })
        
        current_time += len(line) * CHAR_DURATION + LINE_PAUSE
    
    typing_end_time = current_time
    cursor_fade_time = typing_end_time + 0.5
    final_msg_start = typing_end_time + 1.0
    
    # Calculate positions for final message and status (centered below the typed text)
    final_msg_y = 40 + (len(LINES) + 2) * LINE_HEIGHT
    status_y = final_msg_y + LINE_HEIGHT + 5
    
    # Build SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
    <style>
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0; }}
        }}
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        @keyframes fadeOut {{
            0% {{ opacity: 0.8; }}
            100% {{ opacity: 0; }}
        }}
        .cursor {{
            animation: blink 1s infinite;
        }}
        .cursor-fade {{
            animation: fadeOut 0.5s ease-in-out {cursor_fade_time}s forwards;
        }}
        .final-msg {{
            opacity: 0;
            animation: fadeIn {FADE_IN_DURATION}s ease-in-out {final_msg_start}s forwards;
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
    
    <g class="text-container" transform="translate(10, 25)">
'''

    # Add each character with its animation
    for anim in animations:
        char = anim['char']
        if char.strip() == '':
            char = '&#160;'  # Non-breaking space
        
        svg += f'''        <text x="{anim['x']}" y="{anim['y']}" 
              fill="{TEXT_COLOR}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}"
              opacity="0">
            {char}
            <animate attributeName="opacity" from="0" to="1" 
                     begin="{anim['begin']:.2f}s" dur="0.01s" fill="freeze"/>
        </text>
'''

    # Add blinking cursor that follows the typing
    cursor_keyframes = []
    cursor_time = 0.5
    
    for line_idx, line in enumerate(LINES):
        if not line:
            cursor_time += LINE_PAUSE
            continue
            
        y_pos = 40 + line_idx * LINE_HEIGHT
        
        for char_idx in range(len(line) + 1):
            x_pos = 30 + char_idx * 10.5
            cursor_keyframes.append({
                'x': x_pos,
                'y': y_pos,
                'time': cursor_time
            })
            if char_idx < len(line):
                cursor_time += CHAR_DURATION
        
        cursor_time += LINE_PAUSE
        
    # Keep cursor at the end until it fades
    cursor_keyframes.append({
        'x': cursor_keyframes[-1]['x'],
        'y': cursor_keyframes[-1]['y'],
        'time': typing_end_time
    })

    # Build cursor position animations
    cursor_x_values = ";".join([str(kf['x']) for kf in cursor_keyframes])
    cursor_y_values = ";".join([str(kf['y']) for kf in cursor_keyframes])
    cursor_times = ";".join([f"{kf['time'] / typing_end_time:.4f}" for kf in cursor_keyframes])
    
    svg += f'''
        <!-- Blinking cursor -->
        <rect class="cursor cursor-fade" width="10" height="{FONT_SIZE + 2}" fill="{CURSOR_COLOR}" opacity="0.8">
            <animate attributeName="x" values="{cursor_x_values}" 
                     keyTimes="{cursor_times}" dur="{typing_end_time}s" fill="freeze"/>
            <animate attributeName="y" values="{cursor_y_values}" 
                     keyTimes="{cursor_times}" dur="{typing_end_time}s" fill="freeze"/>
            <animate attributeName="opacity" from="0" to="0.8" begin="0.5s" dur="0.01s" fill="freeze"/>
        </rect>
        
        <!-- Final Message -->
        <text class="final-msg" x="30" y="{final_msg_y}"
              fill="{TEXT_COLOR}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">
            {FINAL_MSG}
        </text>
        
        <!-- Status Line -->
        <text class="final-msg" x="30" y="{status_y}"
              fill="{TEXT_COLOR}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">
            {STATUS_LINE}
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
