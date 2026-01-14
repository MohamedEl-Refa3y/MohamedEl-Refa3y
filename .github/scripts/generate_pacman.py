#!/usr/bin/env python3
"""
Pac-Man GitHub Contributions Generator

Generates an animated SVG showing Pac-Man eating GitHub contribution dots
in the exact GitHub contribution calendar layout (last 12 months).
"""

import os
import json
import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'MohamedEl-Refa3y')
OUTPUT_PATH = 'dist/pacman.svg'

# Visual constants - Exact GitHub contribution calendar style
CELL_SIZE = 11
CELL_GAP = 3
CELL_RADIUS = 2
WEEKS_TO_SHOW = 53  # Full year (53 weeks)
DAYS_IN_WEEK = 7

# Layout - Match GitHub exactly
MARGIN_TOP = 40
MARGIN_LEFT = 40
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 35

# Colors - GitHub dark theme exact colors
BG_COLOR = "#0d1117"
EMPTY_CELL_COLOR = "#161b22"
LEVEL_COLORS = {
    0: "#161b22",  # No contributions (dark gray)
    1: "#0e4429",  # Low (dark green)
    2: "#006d32",  # Medium-low (green)
    3: "#26a641",  # Medium-high (bright green)
    4: "#39d353"   # High (brightest green)
}
PACMAN_COLOR = "#ffff00"
TEXT_COLOR = "#8b949e"
TITLE_COLOR = "#e6edf3"

# Animation - SLOW speed
ANIMATION_DURATION_PER_CELL = 0.20  # seconds per cell


def fetch_contributions_graphql() -> Dict:
    """Fetch contribution data for the last year from GitHub GraphQL API."""
    if not GITHUB_TOKEN:
        print("[WARN] No GITHUB_TOKEN found. Cannot fetch contributions via GraphQL.")
        return None
    
    print(f"[API] Using GraphQL API with token: {GITHUB_TOKEN[:8]}...")
    
    # Query for the last year's contributions (what GitHub shows by default)
    query = """
    query($username: String!) {
        user(login: $username) {
            contributionsCollection {
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
    
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': {'username': GITHUB_USERNAME}},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"[ERROR] GraphQL request failed: {response.status_code}")
        print(f"[ERROR] Response: {response.text[:500]}")
        return None
    
    data = response.json()
    
    if 'errors' in data:
        print(f"[ERROR] GraphQL errors: {data['errors']}")
        return None
    
    if not data.get('data', {}).get('user'):
        print(f"[ERROR] No user data returned. Response: {data}")
        return None
    
    calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
    total_contributions = calendar['totalContributions']
    
    contributions = []
    for week in calendar['weeks']:
        for day in week['contributionDays']:
            level = contribution_level_to_int(day['contributionLevel'])
            contributions.append({
                'date': day['date'],
                'count': day['contributionCount'],
                'level': level
            })
    
    print(f"[OK] Fetched {total_contributions} contributions in the last year")
    return {
        'contributions': contributions,
        'total': total_contributions
    }


def fetch_contributions() -> Dict:
    """Fetch contributions - GraphQL API only (requires PAT_TOKEN for private profiles)."""
    result = fetch_contributions_graphql()
    if result and result['contributions']:
        return result
    
    # Fall back to mock data
    print("[WARN] Could not fetch real contributions. Using mock data.")
    print("[HINT] Make sure PAT_TOKEN secret is set with 'read:user' permission")
    return generate_mock_data()


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
    """Generate mock contribution data matching GitHub's calendar (last year)."""
    import random
    contributions = []
    
    # Generate data for the last year (53 weeks) - exactly like GitHub
    end_date = datetime.now()
    # Align to Saturday (end of week in GitHub's calendar)
    days_until_saturday = (5 - end_date.weekday()) % 7
    end_date = end_date + timedelta(days=days_until_saturday)
    start_date = end_date - timedelta(weeks=52) + timedelta(days=1)
    
    current = start_date
    total = 0
    while current <= end_date:
        # Generate realistic contribution patterns
        is_weekday = current.weekday() < 5
        
        if random.random() < (0.4 if is_weekday else 0.2):
            count = random.choices([1, 2, 4, 7, 12], weights=[0.35, 0.30, 0.20, 0.10, 0.05])[0]
            if count <= 2:
                level = 1
            elif count <= 4:
                level = 2
            elif count <= 7:
                level = 3
            else:
                level = 4
            total += count
        else:
            count = 0
            level = 0
        
        contributions.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': count,
            'level': level
        })
        current += timedelta(days=1)
    
    return {'contributions': contributions, 'total': total}


def build_calendar_grid(contributions: List[Dict]) -> Tuple[List[List[Dict]], List[List[Dict]]]:
    """
    Build a 7 rows x 53 columns grid matching GitHub's contribution calendar.
    GitHub's calendar: rows are days (Sun=0 to Sat=6), columns are weeks.
    """
    if not contributions:
        return [[None for _ in range(WEEKS_TO_SHOW)] for _ in range(DAYS_IN_WEEK)], []
    
    # Sort by date
    sorted_contribs = sorted(contributions, key=lambda x: x['date'])
    
    # Build weeks structure (like GitHub)
    weeks_data = []
    current_week = [None] * 7
    
    for contrib in sorted_contribs:
        date = datetime.strptime(contrib['date'], '%Y-%m-%d')
        # GitHub uses Sunday = 0
        day_of_week = (date.weekday() + 1) % 7
        
        current_week[day_of_week] = {
            **contrib,
            'day_of_week': day_of_week,
            'date_obj': date
        }
        
        if day_of_week == 6:  # Saturday (end of week)
            weeks_data.append(current_week)
            current_week = [None] * 7
    
    # Add last incomplete week if exists
    if any(c is not None for c in current_week):
        weeks_data.append(current_week)
    
    # Take last 53 weeks
    weeks_data = weeks_data[-WEEKS_TO_SHOW:]
    
    # Convert to grid[row][col] format
    grid = [[None for _ in range(len(weeks_data))] for _ in range(DAYS_IN_WEEK)]
    
    for week_idx, week in enumerate(weeks_data):
        for day_idx, day_data in enumerate(week):
            if day_data:
                grid[day_idx][week_idx] = day_data
    
    return grid, weeks_data


def get_month_labels(weeks_data: List[List[Dict]]) -> List[Tuple[int, str]]:
    """Get month labels for the calendar header (like GitHub)."""
    months = []
    last_month = None
    
    for week_idx, week in enumerate(weeks_data):
        # Check the first day of the week that has data
        for day in week:
            if day and day.get('date_obj'):
                month = day['date_obj'].month
                month_name = day['date_obj'].strftime('%b')
                if month != last_month:
                    months.append((week_idx, month_name))
                    last_month = month
                break
    
    return months


def generate_svg(contributions_data: Dict) -> str:
    """Generate the Pac-Man SVG with exact GitHub calendar layout."""
    contributions = contributions_data['contributions']
    total_contributions = contributions_data.get('total', sum(c['count'] for c in contributions))
    
    if not contributions:
        return generate_empty_svg()
    
    # Build calendar grid
    grid, weeks_data = build_calendar_grid(contributions)
    num_weeks = len(weeks_data)
    
    # Calculate dimensions (match GitHub's sizing)
    grid_width = num_weeks * (CELL_SIZE + CELL_GAP)
    width = MARGIN_LEFT + grid_width + MARGIN_RIGHT
    height = MARGIN_TOP + (DAYS_IN_WEEK * (CELL_SIZE + CELL_GAP)) + MARGIN_BOTTOM
    
    # Get month labels
    month_labels = get_month_labels(weeks_data)
    
    # Calculate cell positions and build path
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
    path_points = []
    for row in range(DAYS_IN_WEEK):
        row_cells = [c for c in cells if c['row'] == row]
        if row % 2 == 0:
            row_cells.sort(key=lambda c: c['col'])
        else:
            row_cells.sort(key=lambda c: c['col'], reverse=True)
        for cell in row_cells:
            path_points.append((cell['cx'], cell['cy'], cell))
    
    # Animation timing
    total_cells = len(path_points)
    forward_duration = total_cells * ANIMATION_DURATION_PER_CELL
    total_duration = forward_duration * 2
    
    # Build SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" 
     style="background-color: {BG_COLOR};">
    
    <defs>
        <radialGradient id="pacmanGradient">
            <stop offset="0%" stop-color="#ffff66"/>
            <stop offset="100%" stop-color="{PACMAN_COLOR}"/>
        </radialGradient>
        
        <filter id="glow">
            <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        
        <!-- Pac-Man facing right -->
        <g id="pacmanRight">
            <circle cx="0" cy="0" r="5" fill="url(#pacmanGradient)"/>
            <path fill="{BG_COLOR}">
                <animate attributeName="d" dur="0.15s" repeatCount="indefinite"
                    values="M 0,0 L 5,1.5 L 5,-1.5 Z;
                            M 0,0 L 5,0.3 L 5,-0.3 Z;
                            M 0,0 L 5,1.5 L 5,-1.5 Z"/>
            </path>
            <circle cx="0.5" cy="-2.5" r="0.8" fill="{BG_COLOR}"/>
        </g>
        
        <!-- Pac-Man facing left -->
        <g id="pacmanLeft">
            <circle cx="0" cy="0" r="5" fill="url(#pacmanGradient)"/>
            <path fill="{BG_COLOR}">
                <animate attributeName="d" dur="0.15s" repeatCount="indefinite"
                    values="M 0,0 L -5,1.5 L -5,-1.5 Z;
                            M 0,0 L -5,0.3 L -5,-0.3 Z;
                            M 0,0 L -5,1.5 L -5,-1.5 Z"/>
            </path>
            <circle cx="-0.5" cy="-2.5" r="0.8" fill="{BG_COLOR}"/>
        </g>
    </defs>
    
    <!-- Title: "X contributions in the last year" -->
    <text x="{MARGIN_LEFT}" y="18" fill="{TITLE_COLOR}" 
          font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" 
          font-size="14" font-weight="400">
        {total_contributions:,} contributions in the last year
    </text>
    
    <!-- Month labels -->
    <g fill="{TEXT_COLOR}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">'''
    
    for week_idx, month_name in month_labels:
        x = MARGIN_LEFT + week_idx * (CELL_SIZE + CELL_GAP)
        svg += f'''
        <text x="{x}" y="{MARGIN_TOP - 8}">{month_name}</text>'''
    
    svg += f'''
    </g>
    
    <!-- Day labels (Mon, Wed, Fri) - GitHub style -->
    <g fill="{TEXT_COLOR}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">
        <text x="{MARGIN_LEFT - 28}" y="{MARGIN_TOP + 1 * (CELL_SIZE + CELL_GAP) + 9}">Mon</text>
        <text x="{MARGIN_LEFT - 28}" y="{MARGIN_TOP + 3 * (CELL_SIZE + CELL_GAP) + 9}">Wed</text>
        <text x="{MARGIN_LEFT - 28}" y="{MARGIN_TOP + 5 * (CELL_SIZE + CELL_GAP) + 9}">Fri</text>
    </g>
    
    <!-- Contribution cells -->
    <g id="cells">'''
    
    # Add contribution cells
    for idx, (px, py, cell) in enumerate(path_points):
        cell_data = cell['data']
        level = cell_data['level'] if cell_data else 0
        color = LEVEL_COLORS.get(level, LEVEL_COLORS[0])
        
        cell_x = cell['x']
        cell_y = cell['y']
        delay = idx * ANIMATION_DURATION_PER_CELL
        
        # Draw cell rectangle
        svg += f'''
        <rect x="{cell_x}" y="{cell_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" 
              rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" fill="{color}"/>'''
        
        # Add glowing dot for cells with contributions (Pac-Man eats these)
        if level > 0:
            dot_radius = 1.5 + level * 0.4
            svg += f'''
        <circle cx="{px}" cy="{py}" r="{dot_radius}" fill="{PACMAN_COLOR}" 
                opacity="0.9" filter="url(#glow)">
            <animate attributeName="opacity" begin="{delay:.2f}s" dur="0.1s" 
                     from="0.9" to="0" fill="freeze"/>
            <animate attributeName="r" begin="{delay:.2f}s" dur="0.1s" 
                     from="{dot_radius}" to="0" fill="freeze"/>
        </circle>'''
    
    svg += '''
    </g>'''
    
    # Build Pac-Man animation
    if path_points:
        # Calculate directions
        directions = []
        for i, (px, py, cell) in enumerate(path_points):
            row = cell['row']
            directions.append(1 if row % 2 == 0 else -1)
        
        return_directions = [-d for d in reversed(directions)]
        all_directions = directions + return_directions
        
        forward_positions = [(px, py) for px, py, _ in path_points]
        return_positions = list(reversed(forward_positions))
        all_positions = forward_positions + return_positions
        
        total_points = len(all_positions)
        key_times = ";".join([f"{i/(total_points-1):.6f}" for i in range(total_points)])
        position_values = ";".join([f"{px},{py}" for px, py in all_positions])
        
        right_opacity = []
        left_opacity = []
        for d in all_directions:
            if d == 1:
                right_opacity.append("1")
                left_opacity.append("0")
            else:
                right_opacity.append("0")
                left_opacity.append("1")
        
        svg += f'''
    
    <!-- Pac-Man facing RIGHT -->
    <use href="#pacmanRight" opacity="1">
        <animateTransform attributeName="transform" type="translate"
            values="{position_values}"
            keyTimes="{key_times}"
            dur="{total_duration}s" repeatCount="indefinite" calcMode="linear"/>
        <animate attributeName="opacity"
            values="{';'.join(right_opacity)}"
            keyTimes="{key_times}"
            dur="{total_duration}s" repeatCount="indefinite" calcMode="discrete"/>
    </use>
    
    <!-- Pac-Man facing LEFT -->
    <use href="#pacmanLeft" opacity="0">
        <animateTransform attributeName="transform" type="translate"
            values="{position_values}"
            keyTimes="{key_times}"
            dur="{total_duration}s" repeatCount="indefinite" calcMode="linear"/>
        <animate attributeName="opacity"
            values="{';'.join(left_opacity)}"
            keyTimes="{key_times}"
            dur="{total_duration}s" repeatCount="indefinite" calcMode="discrete"/>
    </use>'''
    
    # Legend (Less -> More) - GitHub style
    legend_x = width - 140
    legend_y = height - 18
    svg += f'''
    
    <!-- Legend -->
    <g transform="translate({legend_x}, {legend_y})">
        <text x="0" y="9" fill="{TEXT_COLOR}" 
              font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" 
              font-size="10">Less</text>'''
    
    for i, (level, color) in enumerate(LEVEL_COLORS.items()):
        svg += f'''
        <rect x="{32 + i * 14}" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}" 
              rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" fill="{color}"/>'''
    
    svg += f'''
        <text x="{32 + 5 * 14 + 4}" y="9" fill="{TEXT_COLOR}" 
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
    print(f"[INFO] Token present: {'Yes' if GITHUB_TOKEN else 'No'}")
    
    # Fetch contributions
    print("[INFO] Fetching contribution data (last year)...")
    contributions_data = fetch_contributions()
    
    total = contributions_data.get('total', 0)
    active = sum(1 for c in contributions_data['contributions'] if c['count'] > 0)
    
    print(f"[OK] {total} contributions, {active} active days in the last year")
    
    # Generate SVG
    print("[ART] Generating Pac-Man SVG animation...")
    svg_content = generate_svg(contributions_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Write SVG file
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"[OK] SVG saved to {OUTPUT_PATH}")
    print("[PACMAN] GAME ON!")


if __name__ == '__main__':
    main()
