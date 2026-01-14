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
LINE_PAUSE = 2.0  # 2 seconds pause after each line
CLEAR_DURATION = 0.5  # Clear screen fade duration

# Font settings
FONT_FAMILY = "'Courier New', Consolas, 'Liberation Mono', monospace"
FONT_SIZE = 18
LINE_HEIGHT = 28

# Lines to type
LINES = [
    "> Hi, I'm Mohamed Elrefaay",
    "> AI Developer | Automation Enthusiast",
    "",
    "> About Me",
    "  - Currently working on Driven LLM Automation & RAG systems",
    "  - Learning Mathematics for ML/DL",
    "  - Open to collaborate on private or enterprise AI projects",
    "  - Ask me about RAG systems, Agentic workflows, and ML deployment",
]


def generate_svg() -> str:
    """Generate the terminal typing animation SVG."""
    
    # Calculate dimensions
    max_chars = max(len(line) for line in LINES)
    width = max(max_chars * 11 + 60, 700)  # Approximate character width
    height = len(LINES) * LINE_HEIGHT + 60
    
    # Calculate total animation duration
    total_chars = sum(len(line) for line in LINES)
    typing_time = total_chars * CHAR_DURATION
    pause_time = len(LINES) * LINE_PAUSE
    total_duration = typing_time + pause_time + CLEAR_DURATION + 1  # +1 for buffer
    
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
        .cursor {{
            animation: blink 1s infinite;
        }}
        .text-container {{
            animation: fadeOut 0.5s ease-in-out {total_duration - 0.5}s forwards;
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

    # Build cursor position animations
    cursor_x_values = ";".join([str(kf['x']) for kf in cursor_keyframes])
    cursor_y_values = ";".join([str(kf['y']) for kf in cursor_keyframes])
    cursor_times = ";".join([f"{kf['time'] / total_duration:.4f}" for kf in cursor_keyframes])
    
    svg += f'''
        <!-- Blinking cursor -->
        <rect class="cursor" width="10" height="{FONT_SIZE + 2}" fill="{CURSOR_COLOR}" opacity="0.8">
            <animate attributeName="x" values="{cursor_x_values}" 
                     keyTimes="{cursor_times}" dur="{total_duration}s" fill="freeze"/>
            <animate attributeName="y" values="{cursor_y_values}" 
                     keyTimes="{cursor_times}" dur="{total_duration}s" fill="freeze"/>
            <animate attributeName="opacity" from="0" to="0.8" begin="0.5s" dur="0.01s" fill="freeze"/>
        </rect>
    </g>
    
    <!-- Restart animation by refreshing the SVG -->
    <animate attributeName="visibility" begin="{total_duration}s" dur="0.01s" 
             values="visible;visible" repeatCount="indefinite"/>
             
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
