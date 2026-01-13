#!/usr/bin/env python3
"""
Pac-Man GitHub Contributions Generator

Generates an animated SVG showing Pac-Man eating GitHub contribution dots
in the exact GitHub contribution calendar layout.
Pac-Man moves horizontally through rows in a serpentine pattern.
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

# Visual constants - Exact GitHub contribution calendar style
CELL_SIZE = 10
CELL_GAP = 3
CELL_RADIUS = 2
WEEKS_TO_SHOW = 53  # Full year (53 weeks)
DAYS_IN_WEEK = 7

# Layout
MARGIN_TOP = 55
MARGIN_LEFT = 35
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 25

# Colors - GitHub dark theme exact colors
BG_COLOR = "#0d1117"
EMPTY_CELL_COLOR = "#161b22"
LEVEL_COLORS = {
    0: "#161b22",  # No contributions
    1: "#0e4429",  # Low
    2: "#006d32",  # Medium-low  
    3: "#26a641",  # Medium-high
    4: "#39d353"   # High
}
PACMAN_COLOR = "#ffff00"
TEXT_COLOR = "#8b949e"
MONTH_TEXT_COLOR = "#8b949e"

# Animation - SLOW speed
ANIMATION_DURATION_PER_CELL = 0.25  # seconds per cell (slower = higher value)


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
    """Generate mock contribution data matching GitHub's calendar."""
    import random
    contributions = []
    
    # Generate data for the last year (53 weeks)
    end_date = datetime.now()
    # Align to the start of the week (Sunday)
    days_since_sunday = (end_date.weekday() + 1) % 7
    end_date = end_date - timedelta(days=days_since_sunday) + timedelta(days=6)
    start_date = end_date - timedelta(weeks=52)
    
    current = start_date
    while current <= end_date:
        # Generate realistic contribution patterns
        is_weekday = current.weekday() < 5
        
        if random.random() < (0.5 if is_weekday else 0.25):
            count = random.choices([1, 3, 6, 10, 15], weights=[0.35, 0.30, 0.20, 0.10, 0.05])[0]
            if count <= 2:
                level = 1
            elif count <= 5:
                level = 2
            elif count <= 9:
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


def build_calendar_grid(contributions: List[Dict]) -> List[List[Dict]]:
    """
    Build a 7 rows × 53 columns grid matching GitHub's contribution calendar.
    Returns grid[day_of_week][week_index] = contribution data
    """
    if not contributions:
        return [[None for _ in range(WEEKS_TO_SHOW)] for _ in range(DAYS_IN_WEEK)]
    
    # Sort by date and get last 53 weeks
    sorted_contribs = sorted(contributions, key=lambda x: x['date'])
    
    # Build week-based structure
    weeks_data = []
    current_week = [None] * 7
    
    for contrib in sorted_contribs:
        date = datetime.strptime(contrib['date'], '%Y-%m-%d')
        # GitHub uses Sunday = 0
        day_of_week = (date.weekday() + 1) % 7
        contrib['day_of_week'] = day_of_week
        contrib['x'] = 0  # Will be set later
        contrib['y'] = 0
        
        current_week[day_of_week] = contrib
        
        if day_of_week == 6:  # Saturday (end of week)
            weeks_data.append(current_week)
            current_week = [None] * 7
    
    if any(c is not None for c in current_week):
        weeks_data.append(current_week)
    
    # Take last 53 weeks
    weeks_data = weeks_data[-WEEKS_TO_SHOW:]
    
    # Convert to grid[row][col] format (row = day of week, col = week)
    grid = [[None for _ in range(len(weeks_data))] for _ in range(DAYS_IN_WEEK)]
    
    for week_idx, week in enumerate(weeks_data):
        for day_idx, day_data in enumerate(week):
            if day_data:
                grid[day_idx][week_idx] = day_data
    
    return grid, weeks_data


def get_month_labels(weeks_data: List[List[Dict]]) -> List[Tuple[int, str]]:
    """Get month labels for the calendar header."""
    months = []
    current_month = None
    
    for week_idx, week in enumerate(weeks_data):
        for day in week:
            if day:
                date = datetime.strptime(day['date'], '%Y-%m-%d')
                month_name = date.strftime('%b')
                if month_name != current_month:
                    months.append((week_idx, month_name))
                    current_month = month_name
                break
    
    return months


def generate_svg(contributions_data: Dict) -> str:
    """Generate the Pac-Man SVG with exact GitHub calendar layout."""
    contributions = contributions_data['contributions']
    years = contributions_data.get('years', [])
    
    if not contributions:
        return generate_empty_svg()
    
    # Build calendar grid
    grid, weeks_data = build_calendar_grid(contributions)
    num_weeks = len(weeks_data)
    
    # Calculate dimensions
    width = MARGIN_LEFT + (num_weeks * (CELL_SIZE + CELL_GAP)) + MARGIN_RIGHT
    height = MARGIN_TOP + (DAYS_IN_WEEK * (CELL_SIZE + CELL_GAP)) + MARGIN_BOTTOM
    
    # Calculate cell positions
    cells = []
    for row in range(DAYS_IN_WEEK):
        for col in range(num_weeks):
            x = MARGIN_LEFT + col * (CELL_SIZE + CELL_GAP)
            y = MARGIN_TOP + row * (CELL_SIZE + CELL_GAP)
            cell_data = grid[row][col] if col < len(grid[row]) else None
            cells.append({
                'x': x,
                'y': y,
                'cx': x + CELL_SIZE // 2,
                'cy': y + CELL_SIZE // 2,
                'row': row,
                'col': col,
                'data': cell_data
            })
    
    # Build HORIZONTAL serpentine path for Pac-Man
    # Move through each ROW, alternating direction
    path_points = []
    for row in range(DAYS_IN_WEEK):
        row_cells = [c for c in cells if c['row'] == row]
        if row % 2 == 0:
            # Even rows: left to right
            row_cells.sort(key=lambda c: c['col'])
        else:
            # Odd rows: right to left
            row_cells.sort(key=lambda c: c['col'], reverse=True)
        
        for cell in row_cells:
            path_points.append((cell['cx'], cell['cy'], cell))
    
    # Calculate stats
    total_contributions = sum(c['count'] for c in contributions if c['count'] > 0)
    active_days = sum(1 for c in contributions if c['count'] > 0)
    
    # Animation duration - SLOW (0.25 seconds per cell)
    animation_duration = len(path_points) * ANIMATION_DURATION_PER_CELL
    
    # Get month labels
    month_labels = get_month_labels(weeks_data)
    
    # Build SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" 
     style="background-color: {BG_COLOR};">
    
    <defs>
        <!-- Pac-Man gradient -->
        <radialGradient id="pacmanGradient">
            <stop offset="0%" stop-color="#ffff66"/>
            <stop offset="100%" stop-color="{PACMAN_COLOR}"/>
        </radialGradient>
        
        <!-- Glow effect for contribution dots -->
        <filter id="glow">
            <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    
    <!-- Title -->
    <text x="{MARGIN_LEFT}" y="18" fill="#ffffff" 
          font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" 
          font-size="14" font-weight="600">
        {total_contributions:,} contributions in {min(years) if years else datetime.now().year}-{max(years) if years else datetime.now().year}
    </text>
    
    <!-- Month labels -->
    <g fill="{MONTH_TEXT_COLOR}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">'''
    
    for week_idx, month_name in month_labels:
        x = MARGIN_LEFT + week_idx * (CELL_SIZE + CELL_GAP)
        svg += f'''
        <text x="{x}" y="{MARGIN_TOP - 8}">{month_name}</text>'''
    
    svg += '''
    </g>
    
    <!-- Day labels (Sun, Mon, Tue, Wed, Thu, Fri, Sat) -->
    <g fill="''' + TEXT_COLOR + '''" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="9">
        <text x="''' + str(MARGIN_LEFT - 25) + '''" y="''' + str(MARGIN_TOP + 1 * (CELL_SIZE + CELL_GAP) + 7) + '''">Mon</text>
        <text x="''' + str(MARGIN_LEFT - 25) + '''" y="''' + str(MARGIN_TOP + 3 * (CELL_SIZE + CELL_GAP) + 7) + '''">Wed</text>
        <text x="''' + str(MARGIN_LEFT - 25) + '''" y="''' + str(MARGIN_TOP + 5 * (CELL_SIZE + CELL_GAP) + 7) + '''">Fri</text>
    </g>
    
    <!-- Contribution cells (GitHub calendar grid) -->
    <g id="cells">'''
    
    # Add contribution cells
    for idx, (px, py, cell) in enumerate(path_points):
        cell_data = cell['data']
        level = cell_data['level'] if cell_data else 0
        color = LEVEL_COLORS.get(level, LEVEL_COLORS[0])
        
        # Cell position
        cell_x = cell['x']
        cell_y = cell['y']
        
        # Calculate when Pac-Man reaches this cell
        delay = idx * ANIMATION_DURATION_PER_CELL
        
        # Base cell (always visible)
        svg += f'''
        <rect x="{cell_x}" y="{cell_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" 
              rx="{CELL_RADIUS}" fill="{color}" class="contrib-cell"/>'''
        
        # Add glowing dot for cells with contributions (will be eaten)
        if level > 0:
            dot_radius = 2 + level * 0.5
            svg += f'''
        <circle cx="{px}" cy="{py}" r="{dot_radius}" fill="{PACMAN_COLOR}" 
                opacity="0.8" filter="url(#glow)" class="contrib-dot">
            <animate attributeName="opacity" begin="{delay:.2f}s" dur="0.15s" 
                     from="0.8" to="0" fill="freeze"/>
            <animate attributeName="r" begin="{delay:.2f}s" dur="0.15s" 
                     from="{dot_radius}" to="0" fill="freeze"/>
        </circle>'''
    
    svg += '''
    </g>'''
    
    # Build the motion path for Pac-Man (horizontal serpentine)
    if path_points:
        path_d = f"M {path_points[0][0]},{path_points[0][1]}"
        for px, py, _ in path_points[1:]:
            path_d += f" L {px},{py}"
        # Return path (reverse to create loop)
        for px, py, _ in reversed(path_points[:-1]):
            path_d += f" L {px},{py}"
        
        svg += f'''
    
    <!-- Motion path (invisible) - horizontal serpentine with return -->
    <path id="motionPath" d="{path_d}" fill="none" stroke="none"/>
    
    <!-- Pac-Man character -->
    <g id="pacman">
        <animateMotion dur="{animation_duration * 2}s" repeatCount="indefinite" rotate="auto">
            <mpath href="#motionPath"/>
        </animateMotion>
        
        <!-- Pac-Man body -->
        <circle cx="0" cy="0" r="6" fill="url(#pacmanGradient)"/>
        
        <!-- Chomping mouth animation -->
        <path fill="{BG_COLOR}">
            <animate attributeName="d" dur="0.2s" repeatCount="indefinite"
                values="M 0,0 L 6,2 L 6,-2 Z;
                        M 0,0 L 6,0.5 L 6,-0.5 Z;
                        M 0,0 L 6,2 L 6,-2 Z"/>
        </path>
        
        <!-- Eye -->
        <circle cx="-1" cy="-3" r="1" fill="{BG_COLOR}"/>
    </g>'''
    
    # Legend
    svg += f'''
    
    <!-- Legend -->
    <g transform="translate({width - 130}, {height - 15})">
        <text x="0" y="0" fill="{TEXT_COLOR}" 
              font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" 
              font-size="10">Less</text>'''
    
    for i, (level, color) in enumerate(LEVEL_COLORS.items()):
        svg += f'''
        <rect x="{30 + i * 13}" y="-9" width="{CELL_SIZE}" height="{CELL_SIZE}" 
              rx="{CELL_RADIUS}" fill="{color}"/>'''
    
    svg += f'''
        <text x="{30 + 5 * 13 + 5}" y="0" fill="{TEXT_COLOR}" 
              font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" 
              font-size="10">More</text>
    </g>
    
</svg>'''
    
    return svg


def generate_empty_svg() -> str:
    """Generate a placeholder SVG when no contributions are found."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 150">
    <rect width="800" height="150" fill="#0d1117"/>
    <text x="400" y="75" fill="#8b949e" text-anchor="middle" 
          font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" 
          font-size="14">
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
