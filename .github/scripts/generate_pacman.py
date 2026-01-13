#!/usr/bin/env python3
"""
Pac-Man GitHub Contributions Generator

Generates an animated SVG showing Pac-Man eating GitHub contribution dots
in a maze-style layout. Fetches all contributions from all years.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'MohamedEl-Refa3y')
OUTPUT_PATH = 'dist/pacman.svg'

# Visual constants
CELL_SIZE = 12
DOT_RADIUS_MIN = 2
DOT_RADIUS_MAX = 5
PACMAN_SIZE = 20
MAZE_PADDING = 30
COLS_PER_ROW = 53  # 53 weeks per year
ROW_HEIGHT = CELL_SIZE * 8  # 7 days + spacing
WALL_COLOR = "#1a1a4e"
BG_COLOR = "#000000"
DOT_COLOR = "#ffff00"
PACMAN_COLOR = "#ffff00"
GHOST_COLORS = ["#ff0000", "#00ffff", "#ffb8ff", "#ffb852"]


def fetch_contributions() -> Dict:
    """Fetch all contribution data from GitHub GraphQL API."""
    if not GITHUB_TOKEN:
        print("Warning: No GITHUB_TOKEN found. Using mock data.")
        return generate_mock_data()
    
    # First, get the user's account creation date
    user_query = """
    query($username: String!) {
        user(login: $username) {
            createdAt
            contributionsCollection {
                contributionYears
            }
        }
    }
    """
    
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': user_query, 'variables': {'username': GITHUB_USERNAME}},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error fetching user data: {response.status_code}")
        return generate_mock_data()
    
    user_data = response.json()
    
    if 'errors' in user_data:
        print(f"GraphQL errors: {user_data['errors']}")
        return generate_mock_data()
    
    years = user_data['data']['user']['contributionsCollection']['contributionYears']
    
    # Now fetch contributions for each year
    all_contributions = []
    
    for year in sorted(years):
        year_query = """
        query($username: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $username) {
                contributionsCollection(from: $from, to: $to) {
                    contributionCalendar {
                        totalContributions
                        weeks {
                            contributionDays {
                                date
                                contributionCount
                                contributionLevel
                            }
                        }
                    }
                }
            }
        }
        """
        
        from_date = f"{year}-01-01T00:00:00Z"
        to_date = f"{year}-12-31T23:59:59Z"
        
        response = requests.post(
            'https://api.github.com/graphql',
            json={
                'query': year_query,
                'variables': {
                    'username': GITHUB_USERNAME,
                    'from': from_date,
                    'to': to_date
                }
            },
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['user']:
                calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
                for week in calendar['weeks']:
                    for day in week['contributionDays']:
                        all_contributions.append({
                            'date': day['date'],
                            'count': day['contributionCount'],
                            'level': day['contributionLevel']
                        })
    
    return {'contributions': all_contributions, 'years': years}


def generate_mock_data() -> Dict:
    """Generate mock contribution data for testing."""
    import random
    contributions = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()
    
    current = start_date
    while current <= end_date:
        # Generate random contribution level
        count = random.choices(
            [0, 1, 3, 6, 10],
            weights=[0.3, 0.3, 0.2, 0.15, 0.05]
        )[0]
        
        level_map = {0: 'NONE', 1: 'FIRST_QUARTILE', 3: 'SECOND_QUARTILE', 
                     6: 'THIRD_QUARTILE', 10: 'FOURTH_QUARTILE'}
        
        contributions.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': count,
            'level': level_map.get(count, 'FIRST_QUARTILE')
        })
        current += timedelta(days=1)
    
    years = list(set(int(c['date'][:4]) for c in contributions))
    return {'contributions': contributions, 'years': sorted(years)}


def level_to_radius(level: str) -> float:
    """Convert contribution level to dot radius."""
    level_map = {
        'NONE': 0,
        'FIRST_QUARTILE': DOT_RADIUS_MIN,
        'SECOND_QUARTILE': DOT_RADIUS_MIN + 1,
        'THIRD_QUARTILE': DOT_RADIUS_MAX - 1,
        'FOURTH_QUARTILE': DOT_RADIUS_MAX
    }
    return level_map.get(level, DOT_RADIUS_MIN)


def generate_maze_path(contributions: List[Dict]) -> List[Tuple[float, float, float, str]]:
    """
    Generate positions for contribution dots in a maze-like path.
    Returns list of (x, y, radius, date) tuples.
    """
    dots = []
    
    # Filter out days with no contributions for cleaner visualization
    active_contributions = [c for c in contributions if c['count'] > 0]
    
    if not active_contributions:
        return dots
    
    # Calculate grid dimensions
    total_dots = len(active_contributions)
    cols = min(COLS_PER_ROW, total_dots)
    rows = math.ceil(total_dots / cols)
    
    # Generate serpentine path through the maze
    for i, contrib in enumerate(active_contributions):
        row = i // cols
        col = i % cols
        
        # Serpentine pattern: reverse direction on odd rows
        if row % 2 == 1:
            col = cols - 1 - col
        
        x = MAZE_PADDING + col * CELL_SIZE + CELL_SIZE // 2
        y = MAZE_PADDING + row * ROW_HEIGHT + CELL_SIZE // 2
        
        radius = level_to_radius(contrib['level'])
        
        dots.append((x, y, radius, contrib['date']))
    
    return dots


def generate_svg(contributions_data: Dict) -> str:
    """Generate the complete Pac-Man SVG animation."""
    contributions = contributions_data['contributions']
    years = contributions_data.get('years', [])
    
    dots = generate_maze_path(contributions)
    
    if not dots:
        # Return a simple placeholder if no contributions
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200">
            <rect width="800" height="200" fill="#000"/>
            <text x="400" y="100" fill="#fff" text-anchor="middle" font-family="Arial" font-size="20">
                No contributions yet - Start coding! 🎮
            </text>
        </svg>'''
    
    # Calculate SVG dimensions
    max_x = max(d[0] for d in dots) + MAZE_PADDING + PACMAN_SIZE
    max_y = max(d[1] for d in dots) + MAZE_PADDING + PACMAN_SIZE
    
    width = max(800, max_x + 50)
    height = max(200, max_y + 50)
    
    # Animation duration based on number of dots
    animation_duration = max(10, len(dots) * 0.15)
    
    # Build SVG
    svg_parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" 
     style="background-color: {BG_COLOR};">
    
    <defs>
        <!-- Pac-Man gradient -->
        <radialGradient id="pacmanGradient">
            <stop offset="0%" stop-color="#ffff66"/>
            <stop offset="100%" stop-color="{PACMAN_COLOR}"/>
        </radialGradient>
        
        <!-- Glow effect for dots -->
        <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        
        <!-- Pac-Man clip path for mouth animation -->
        <clipPath id="pacmanMouth">
            <path id="mouthPath">
                <animate attributeName="d" 
                    dur="0.3s" 
                    repeatCount="indefinite"
                    values="M 0,0 L 20,0 L 20,20 L 0,20 Z;
                            M 10,10 L 20,5 L 20,15 Z M 0,0 L 10,0 L 10,20 L 0,20 Z;
                            M 0,0 L 20,0 L 20,20 L 0,20 Z"/>
            </path>
        </clipPath>
    </defs>
    
    <!-- Maze walls background pattern -->
    <pattern id="mazePattern" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
        <rect width="24" height="24" fill="{BG_COLOR}"/>
        <rect x="0" y="0" width="2" height="24" fill="{WALL_COLOR}" opacity="0.3"/>
        <rect x="0" y="0" width="24" height="2" fill="{WALL_COLOR}" opacity="0.3"/>
    </pattern>
    <rect width="100%" height="100%" fill="url(#mazePattern)"/>
    
    <!-- Title -->
    <text x="{width/2}" y="20" fill="#ffffff" text-anchor="middle" 
          font-family="'Press Start 2P', 'Courier New', monospace" font-size="12">
        🎮 CONTRIBUTION CHOMPER 🎮
    </text>
    
    <!-- Year labels -->''']
    
    # Add year labels
    if years:
        year_label_y = 35
        svg_parts.append(f'''
    <text x="{width/2}" y="{year_label_y}" fill="#888888" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="10">
        {min(years)} - {max(years)} ({len([c for c in contributions if c["count"] > 0])} active days)
    </text>''')
    
    # Add contribution dots
    svg_parts.append('\n    <!-- Contribution dots -->')
    svg_parts.append('    <g id="dots">')
    
    for i, (x, y, radius, date) in enumerate(dots):
        if radius > 0:
            # Dots will fade out when Pac-Man "eats" them
            delay = i * (animation_duration / len(dots))
            svg_parts.append(f'''
        <circle cx="{x}" cy="{y}" r="{radius}" fill="{DOT_COLOR}" filter="url(#glow)" opacity="1">
            <animate attributeName="opacity" 
                     begin="{delay:.2f}s" 
                     dur="0.2s" 
                     from="1" to="0" 
                     fill="freeze"/>
            <animate attributeName="r" 
                     begin="{delay:.2f}s" 
                     dur="0.2s" 
                     from="{radius}" to="0" 
                     fill="freeze"/>
        </circle>''')
    
    svg_parts.append('    </g>')
    
    # Generate Pac-Man path
    if len(dots) > 1:
        path_points = ' '.join([f"{d[0]},{d[1]}" for d in dots])
        
        # Pac-Man character with animation
        svg_parts.append(f'''
    <!-- Pac-Man -->
    <g id="pacman">
        <!-- Body -->
        <circle cx="0" cy="0" r="{PACMAN_SIZE//2}" fill="url(#pacmanGradient)">
        </circle>
        <!-- Mouth (chomping animation) -->
        <g>
            <path fill="{BG_COLOR}">
                <animate attributeName="d" 
                    dur="0.2s" 
                    repeatCount="indefinite"
                    values="M 0,0 L {PACMAN_SIZE//2},0 L {PACMAN_SIZE//2},{PACMAN_SIZE//4} L 0,0 
                            L {PACMAN_SIZE//2},-{PACMAN_SIZE//4} L {PACMAN_SIZE//2},0 Z;
                            M 0,0 L {PACMAN_SIZE//2},{PACMAN_SIZE//6} L {PACMAN_SIZE//2},{PACMAN_SIZE//4} L 0,0 
                            L {PACMAN_SIZE//2},-{PACMAN_SIZE//4} L {PACMAN_SIZE//2},-{PACMAN_SIZE//6} Z;
                            M 0,0 L {PACMAN_SIZE//2},0 L {PACMAN_SIZE//2},{PACMAN_SIZE//4} L 0,0 
                            L {PACMAN_SIZE//2},-{PACMAN_SIZE//4} L {PACMAN_SIZE//2},0 Z"/>
            </path>
        </g>
        <!-- Eye -->
        <circle cx="-2" cy="-{PACMAN_SIZE//4}" r="2" fill="{BG_COLOR}"/>
        
        <!-- Movement animation -->
        <animateMotion dur="{animation_duration}s" repeatCount="indefinite" rotate="auto">
            <mpath href="#motionPath"/>
        </animateMotion>
    </g>
    
    <!-- Motion path (invisible) -->
    <path id="motionPath" d="M {dots[0][0]},{dots[0][1]} L {' L '.join([f'{d[0]},{d[1]}' for d in dots])}" 
          fill="none" stroke="none"/>''')
    
    # Add score counter
    total_contributions = sum(1 for c in contributions if c['count'] > 0)
    svg_parts.append(f'''
    <!-- Score -->
    <g id="score">
        <text x="{width - 20}" y="25" fill="#ffffff" text-anchor="end" 
              font-family="'Press Start 2P', 'Courier New', monospace" font-size="10">
            SCORE: {total_contributions:,}
        </text>
    </g>
    
    <!-- Power pellets (high contribution days) -->
    <g id="powerPellets">''')
    
    # Add power pellets for high-contribution days
    high_contrib_days = [(i, d) for i, d in enumerate(dots) if d[2] >= DOT_RADIUS_MAX]
    for i, (idx, (x, y, radius, date)) in enumerate(high_contrib_days[:4]):  # Max 4 power pellets
        svg_parts.append(f'''
        <circle cx="{x}" cy="{y + 15}" r="6" fill="{GHOST_COLORS[i % len(GHOST_COLORS)]}" opacity="0.7">
            <animate attributeName="opacity" dur="0.5s" values="0.7;1;0.7" repeatCount="indefinite"/>
        </circle>''')
    
    svg_parts.append('    </g>')
    
    # Close SVG
    svg_parts.append('\n</svg>')
    
    return ''.join(svg_parts)


def main():
    """Main entry point."""
    print(f"[PACMAN] Generating Pac-Man contributions for {GITHUB_USERNAME}...")
    
    # Fetch contributions
    print("[INFO] Fetching contribution data...")
    contributions_data = fetch_contributions()
    
    total = len(contributions_data['contributions'])
    active = sum(1 for c in contributions_data['contributions'] if c['count'] > 0)
    years = contributions_data.get('years', [])
    
    print(f"[OK] Found {total} total days, {active} active contribution days")
    print(f"[YEARS] Years covered: {', '.join(map(str, years)) if years else 'N/A'}")
    
    # Generate SVG
    print("[ART] Generating Pac-Man SVG animation...")
    svg_content = generate_svg(contributions_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Write SVG file
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"[OK] SVG saved to {OUTPUT_PATH}")
    print("[PACMAN] GAME ON! Your Pac-Man contributions are ready!")


if __name__ == '__main__':
    main()
