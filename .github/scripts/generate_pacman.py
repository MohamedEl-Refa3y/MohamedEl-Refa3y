#!/usr/bin/env python3
"""
Pac-Man GitHub Contributions Generator

Generates an animated SVG showing Pac-Man eating GitHub contribution dots
in a calendar-style maze layout matching GitHub's contribution graph.
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

# Visual constants - Calendar style like GitHub
CELL_SIZE = 11
CELL_GAP = 3
CELL_TOTAL = CELL_SIZE + CELL_GAP
WEEKS_TO_SHOW = 53  # Full year
DAYS_IN_WEEK = 7
MARGIN_TOP = 50
MARGIN_LEFT = 40
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 30

# Colors
BG_COLOR = "#0d1117"  # GitHub dark theme background
EMPTY_CELL_COLOR = "#161b22"  # Empty contribution cell
LEVEL_COLORS = {
    0: "#161b22",  # No contributions
    1: "#0e4429",  # Low
    2: "#006d32",  # Medium-low
    3: "#26a641",  # Medium-high
    4: "#39d353"   # High
}
PACMAN_COLOR = "#ffff00"
WALL_COLOR = "#30363d"
TEXT_COLOR = "#8b949e"


def fetch_contributions() -> Dict:
    """Fetch all contribution data from GitHub GraphQL API."""
    if not GITHUB_TOKEN:
        print("Warning: No GITHUB_TOKEN found. Using mock data.")
        return generate_mock_data()
    
    # First, get the contribution years
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
    
    # Fetch contributions for each year
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
                        level = contribution_level_to_int(day['contributionLevel'])
                        all_contributions.append({
                            'date': day['date'],
                            'count': day['contributionCount'],
                            'level': level
                        })
    
    return {'contributions': all_contributions, 'years': years}


def contribution_level_to_int(level_str: str) -> int:
    """Convert GitHub contribution level string to integer."""
    level_map = {
        'NONE': 0,
        'FIRST_QUARTILE': 1,
        'SECOND_QUARTILE': 2,
        'THIRD_QUARTILE': 3,
        'FOURTH_QUARTILE': 4
    }
    return level_map.get(level_str, 0)


def generate_mock_data() -> Dict:
    """Generate mock contribution data for testing."""
    import random
    contributions = []
    
    # Generate data for the last 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*2)
    
    current = start_date
    while current <= end_date:
        # Generate realistic contribution patterns
        # More contributions on weekdays
        is_weekday = current.weekday() < 5
        
        if random.random() < (0.6 if is_weekday else 0.3):
            count = random.choices([1, 2, 5, 10, 20], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
            if count == 1:
                level = 1
            elif count <= 3:
                level = 2
            elif count <= 8:
                level = 3
            else:
                level = 4
        else:
            count = 0
            level = 0
        
        contributions.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': count,
            'level': level
        })
        current += timedelta(days=1)
    
    years = list(set(int(c['date'][:4]) for c in contributions))
    return {'contributions': contributions, 'years': sorted(years)}


def organize_by_weeks(contributions: List[Dict]) -> List[List[Dict]]:
    """Organize contributions into weeks (columns) for calendar view."""
    if not contributions:
        return []
    
    # Sort by date
    sorted_contribs = sorted(contributions, key=lambda x: x['date'])
    
    # Group into weeks
    weeks = []
    current_week = []
    
    for contrib in sorted_contribs:
        date = datetime.strptime(contrib['date'], '%Y-%m-%d')
        day_of_week = date.weekday()  # Monday = 0, Sunday = 6
        # GitHub uses Sunday = 0, so adjust
        github_day = (day_of_week + 1) % 7
        
        contrib['day_of_week'] = github_day
        current_week.append(contrib)
        
        if github_day == 6:  # Saturday (end of GitHub week)
            weeks.append(current_week)
            current_week = []
    
    if current_week:
        weeks.append(current_week)
    
    return weeks


def generate_svg(contributions_data: Dict) -> str:
    """Generate the Pac-Man SVG with calendar-style grid."""
    contributions = contributions_data['contributions']
    years = contributions_data.get('years', [])
    
    if not contributions:
        return generate_empty_svg()
    
    # Get last 53 weeks of contributions
    weeks = organize_by_weeks(contributions)
    weeks = weeks[-WEEKS_TO_SHOW:] if len(weeks) > WEEKS_TO_SHOW else weeks
    
    # Calculate dimensions
    width = MARGIN_LEFT + (len(weeks) * CELL_TOTAL) + MARGIN_RIGHT
    height = MARGIN_TOP + (DAYS_IN_WEEK * CELL_TOTAL) + MARGIN_BOTTOM
    
    # Build path for Pac-Man animation (serpentine through the grid)
    path_points = []
    all_cells = []
    
    for week_idx, week in enumerate(weeks):
        for day in week:
            x = MARGIN_LEFT + (week_idx * CELL_TOTAL) + CELL_SIZE // 2
            y = MARGIN_TOP + (day['day_of_week'] * CELL_TOTAL) + CELL_SIZE // 2
            all_cells.append({
                'x': x,
                'y': y,
                'level': day['level'],
                'count': day['count'],
                'date': day['date']
            })
    
    # Create serpentine path for Pac-Man
    for week_idx in range(len(weeks)):
        for day_idx in range(DAYS_IN_WEEK):
            # Serpentine: go down on even weeks, up on odd weeks
            actual_day = day_idx if week_idx % 2 == 0 else (DAYS_IN_WEEK - 1 - day_idx)
            x = MARGIN_LEFT + (week_idx * CELL_TOTAL) + CELL_SIZE // 2
            y = MARGIN_TOP + (actual_day * CELL_TOTAL) + CELL_SIZE // 2
            path_points.append((x, y))
    
    # Animation duration based on number of cells
    animation_duration = max(20, len(path_points) * 0.08)
    
    # Calculate stats
    total_contributions = sum(c['count'] for c in contributions)
    active_days = sum(1 for c in contributions if c['count'] > 0)
    
    # Build SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" 
     style="background-color: {BG_COLOR};">
    
    <defs>
        <!-- Pac-Man gradient -->
        <radialGradient id="pacmanGradient">
            <stop offset="0%" stop-color="#ffff66"/>
            <stop offset="100%" stop-color="{PACMAN_COLOR}"/>
        </radialGradient>
        
        <!-- Glow effect -->
        <filter id="glow">
            <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        
        <!-- Drop shadow -->
        <filter id="shadow">
            <feDropShadow dx="0" dy="1" stdDeviation="1" flood-opacity="0.3"/>
        </filter>
    </defs>
    
    <!-- Title -->
    <text x="{width // 2}" y="20" fill="{TEXT_COLOR}" text-anchor="middle" 
          font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="600">
        {GITHUB_USERNAME}'s Contribution Chomper
    </text>
    
    <!-- Stats -->
    <text x="{width // 2}" y="38" fill="{TEXT_COLOR}" text-anchor="middle" 
          font-family="'Segoe UI', Arial, sans-serif" font-size="11">
        {total_contributions:,} contributions | {active_days} active days | {min(years) if years else 'N/A'}-{max(years) if years else 'N/A'}
    </text>
    
    <!-- Day labels -->
    <g fill="{TEXT_COLOR}" font-family="'Segoe UI', Arial, sans-serif" font-size="9">
        <text x="{MARGIN_LEFT - 8}" y="{MARGIN_TOP + CELL_TOTAL * 1 + 3}" text-anchor="end">Mon</text>
        <text x="{MARGIN_LEFT - 8}" y="{MARGIN_TOP + CELL_TOTAL * 3 + 3}" text-anchor="end">Wed</text>
        <text x="{MARGIN_LEFT - 8}" y="{MARGIN_TOP + CELL_TOTAL * 5 + 3}" text-anchor="end">Fri</text>
    </g>
    
    <!-- Contribution cells -->
    <g id="cells">'''
    
    # Add contribution cells
    for cell in all_cells:
        color = LEVEL_COLORS.get(cell['level'], LEVEL_COLORS[0])
        cell_x = cell['x'] - CELL_SIZE // 2
        cell_y = cell['y'] - CELL_SIZE // 2
        
        # Calculate delay for when Pac-Man reaches this cell
        cell_idx = all_cells.index(cell)
        delay = cell_idx * (animation_duration / len(all_cells))
        
        if cell['level'] > 0:
            # Active contribution cell - will be "eaten"
            svg += f'''
        <g>
            <rect x="{cell_x}" y="{cell_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" 
                  rx="2" fill="{color}" opacity="1">
                <animate attributeName="opacity" begin="{delay:.2f}s" dur="0.3s" 
                         from="1" to="0.2" fill="freeze"/>
            </rect>
            <!-- Contribution dot that gets eaten -->
            <circle cx="{cell['x']}" cy="{cell['y']}" r="{2 + cell['level']}" 
                    fill="{PACMAN_COLOR}" opacity="0.9" filter="url(#glow)">
                <animate attributeName="r" begin="{delay:.2f}s" dur="0.2s" 
                         from="{2 + cell['level']}" to="0" fill="freeze"/>
                <animate attributeName="opacity" begin="{delay:.2f}s" dur="0.2s" 
                         from="0.9" to="0" fill="freeze"/>
            </circle>
        </g>'''
        else:
            # Empty cell
            svg += f'''
        <rect x="{cell_x}" y="{cell_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" 
              rx="2" fill="{color}"/>'''
    
    svg += '''
    </g>'''
    
    # Add Pac-Man with animation
    if path_points:
        path_d = f"M {path_points[0][0]},{path_points[0][1]}"
        for px, py in path_points[1:]:
            path_d += f" L {px},{py}"
        
        svg += f'''
    
    <!-- Motion path (invisible) -->
    <path id="motionPath" d="{path_d}" fill="none" stroke="none"/>
    
    <!-- Pac-Man -->
    <g id="pacman" filter="url(#shadow)">
        <animateMotion dur="{animation_duration}s" repeatCount="indefinite" rotate="auto">
            <mpath href="#motionPath"/>
        </animateMotion>
        
        <!-- Body -->
        <circle cx="0" cy="0" r="8" fill="url(#pacmanGradient)"/>
        
        <!-- Animated mouth -->
        <g>
            <path fill="{BG_COLOR}">
                <animate attributeName="d" dur="0.15s" repeatCount="indefinite"
                    values="M 0,0 L 8,3 L 8,-3 Z;
                            M 0,0 L 8,1 L 8,-1 Z;
                            M 0,0 L 8,3 L 8,-3 Z"/>
            </path>
        </g>
        
        <!-- Eye -->
        <circle cx="-1" cy="-4" r="1.5" fill="{BG_COLOR}"/>
    </g>
    
    <!-- Score display -->
    <g id="score">
        <rect x="{width - 120}" y="5" width="110" height="25" rx="5" fill="{WALL_COLOR}" opacity="0.8"/>
        <text x="{width - 65}" y="22" fill="{PACMAN_COLOR}" text-anchor="middle" 
              font-family="'Courier New', monospace" font-size="12" font-weight="bold">
            SCORE: {total_contributions}
        </text>
    </g>
    
    <!-- Legend -->
    <g transform="translate({width - 140}, {height - 20})">
        <text x="0" y="0" fill="{TEXT_COLOR}" font-family="'Segoe UI', Arial, sans-serif" font-size="9">Less</text>'''
        
        for i, (level, color) in enumerate(LEVEL_COLORS.items()):
            svg += f'''
        <rect x="{30 + i * 14}" y="-9" width="10" height="10" rx="2" fill="{color}"/>'''
        
        svg += f'''
        <text x="{30 + 5 * 14 + 5}" y="0" fill="{TEXT_COLOR}" font-family="'Segoe UI', Arial, sans-serif" font-size="9">More</text>
    </g>'''
    
    svg += '''
</svg>'''
    
    return svg


def generate_empty_svg() -> str:
    """Generate a placeholder SVG when no contributions are found."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200">
    <rect width="800" height="200" fill="#0d1117"/>
    <text x="400" y="100" fill="#8b949e" text-anchor="middle" 
          font-family="'Segoe UI', Arial, sans-serif" font-size="16">
        No contributions yet - Start coding! 
    </text>
</svg>'''


def main():
    """Main entry point."""
    print(f"[PACMAN] Generating Pac-Man contributions for {GITHUB_USERNAME}...")
    
    # Fetch contributions
    print("[INFO] Fetching contribution data...")
    contributions_data = fetch_contributions()
    
    total = len(contributions_data['contributions'])
    active = sum(1 for c in contributions_data['contributions'] if c['count'] > 0)
    total_contribs = sum(c['count'] for c in contributions_data['contributions'])
    years = contributions_data.get('years', [])
    
    print(f"[OK] Found {total} total days, {active} active days, {total_contribs} contributions")
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
