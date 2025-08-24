"""
Solar System Visualiser
An interactive visualisation of planetary positions using Keplerian orbital mechanics.
Navigate through time to see how planets move in their orbits around the Sun.

Controls:
    Arrow Keys: Step forward/backward by days
    [ or ]: Step by months  
    , or .: Step by hours
    - or =: Zoom in/out
    Space: Pause/resume animation
    T: Jump to today
    R: Reset view
    H: Toggle help
    Click: Select planet for details
"""

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional

import pygame

from planet_data import PLANETS, elements_to_xy, generate_orbit_points


# Configutation

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1000
FPS = 60
STAR_COUNT = 400
DEFAULT_ZOOM = 140 
MAX_TRAIL_LENGTH = 300

# Colour defining for the universe
COLORS = {
    'background': (5, 5, 15),
    'white': (245, 245, 245),
    'sun': (255, 215, 0),
    'hud_bg': (15, 15, 25, 200),
    'hud_text': (220, 220, 240),
    'hud_accent': (100, 149, 237),
    'orbit': (80, 80, 120, 150),
    'grid': (40, 40, 60, 100),
}


# detail/design for the planets

@dataclass
class PlanetStyle:
    """Visual properties for each celestial body"""
    radius: int
    color: Tuple[int, int, int]
    has_rings: bool = False
    ring_color: Optional[Tuple[int, int, int]] = None
    has_atmosphere: bool = False


# visual details for each planet
PLANET_STYLES = {
    "Sun": PlanetStyle(25, (255, 215, 0)),
    "Mercury": PlanetStyle(5, (169, 169, 169)),
    "Venus": PlanetStyle(7, (255, 198, 73), has_atmosphere=True),
    "Earth": PlanetStyle(8, (100, 149, 237), has_atmosphere=True),
    "Mars": PlanetStyle(6, (205, 92, 92)),
    "Jupiter": PlanetStyle(16, (218, 165, 32)),
    "Saturn": PlanetStyle(14, (250, 235, 215), has_rings=True, ring_color=(210, 180, 140)),
    "Uranus": PlanetStyle(10, (64, 224, 208)),
    "Neptune": PlanetStyle(10, (65, 105, 225)),
}

# characteristics of each planet
PLANET_INFO = {
    "Mercury": {
        "mass_earth": 0.055, 
        "gravity": 3.7, 
        "temp_avg": 167,
        "day_hours": 1407.6, 
        "moons": 0,
        "fact": "One day on Mercury is equal to 176 days on Earth"
    },
    "Venus": {
        "mass_earth": 0.815, 
        "gravity": 8.87, 
        "temp_avg": 464,
        "day_hours": -5832.5,  # negative = retrograde
        "moons": 0,
        "fact": "Venus rotates backwards and its day is longer than its year"
    },
    "Earth": {
        "mass_earth": 1.0, 
        "gravity": 9.8, 
        "temp_avg": 15,
        "day_hours": 24, 
        "moons": 1,
        "fact": "Where we call home"
    },
    "Mars": {
        "mass_earth": 0.107, 
        "gravity": 3.71, 
        "temp_avg": -65,
        "day_hours": 24.6, 
        "moons": 2,
        "fact": "Home to the largest Mountain/Volcano in the Universe: Olympus Mons"
    },
    "Jupiter": {
        "mass_earth": 317.8, 
        "gravity": 24.79, 
        "temp_avg": -110,
        "day_hours": 9.9, 
        "moons": 95,
        "fact": "It's famous Great Red Spot is a storm larger than Earth itself"
    },
    "Saturn": {
        "mass_earth": 95.2, 
        "gravity": 10.44, 
        "temp_avg": -140,
        "day_hours": 10.7, 
        "moons": 146,
        "fact": "Saturn's famous rings are made of ice and rock particles, some as large as your house"
    },
    "Uranus": {
        "mass_earth": 14.5, 
        "gravity": 8.69, 
        "temp_avg": -195,
        "day_hours": -17.2,
        "moons": 28,
        "fact": "Uranus is tilted on its side, and even has a ring around it vertically"
    },
    "Neptune": {
        "mass_earth": 17.1, 
        "gravity": 11.15, 
        "temp_avg": -200,
        "day_hours": 16.1, 
        "moons": 16,
        "fact": "Has the fastest winds in the solar system going up to 2,100 km/h"
    }
}


# function defining

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Keep a value within bounds"""
    return max(min_val, min(max_val, value))


def format_date(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def format_distance(au: float) -> str:
    """Convert AU to human-readable distance"""
    if au < 0.1:
        return f"{au * 149.6:.1f} million km"
    return f"{au:.3f} AU"


def calculate_planet_distance(planet_name: str, date: datetime) -> Dict[str, float]:
    """Calculate current distances and speeds for a planet"""
    x, y, z = elements_to_xy(PLANETS[planet_name], date)
    distance_from_sun = math.sqrt(x*x + y*y + z*z)
    
    # Get Earth's position for relative distance
    earth_x, earth_y, earth_z = elements_to_xy(PLANETS["Earth"], date)
    distance_from_earth = math.sqrt(
        (x - earth_x)**2 + (y - earth_y)**2 + (z - earth_z)**2
    )
    
    # Rough orbital speed calculation (simplified)
    orbital_speed = math.sqrt(1.0 / distance_from_sun) * 29.78
    
    return {
        "sun_distance": distance_from_sun,
        "earth_distance": distance_from_earth,
        "orbital_speed": orbital_speed
    }


def auto_zoom_level(date: datetime) -> float:
    """Initial zoom amount to fit all planets on screen"""
    max_dist = 0
    for planet_data in PLANETS.values():
        x, y, _ = elements_to_xy(planet_data, date)
        dist = math.sqrt(x*x + y*y)
        max_dist = max(max_dist, dist)
    
    screen_radius = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 2
    return max(20, int(screen_radius * 0.8 / max_dist))


# Visual 'drawing' functions

def draw_starfield(screen: pygame.Surface):
    """Create a background of 'stars' """
    for _ in range(STAR_COUNT):
        x = random.randrange(screen.get_width())
        y = random.randrange(screen.get_height())
        brightness = random.randint(100, 255)
        
        # Occasional bright star
        if random.random() < 0.02: 
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 2)
        else:
            screen.set_at((x, y), (brightness, brightness, brightness))


def draw_grid(screen: pygame.Surface, center: Tuple[int, int], zoom: float):
    """Draw distance grid circles"""
    for au in range(5, 35, 5):
        radius = int(au * zoom)
        if radius < max(screen.get_width(), screen.get_height()):
            pygame.draw.circle(screen, COLORS['grid'], center, radius, 1)


def draw_sun(screen: pygame.Surface, center: Tuple[int, int]):
    """Draw the sun with a simple glow effect"""
    style = PLANET_STYLES["Sun"]
    
    # Outer glow
    for r in range(35, style.radius, -3):
        alpha = int(30 * (35 - r) / 15)
        glow_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLORS['sun'], alpha), (r, r), r)
        screen.blit(glow_surf, (center[0] - r, center[1] - r))
    
    # Main sun
    pygame.draw.circle(screen, style.color, center, style.radius)
    
    # Bright core
    pygame.draw.circle(screen, (255, 255, 200), center, style.radius - 5)


def draw_orbit(screen: pygame.Surface, points: List[Tuple[float, float, float]], 
               center: Tuple[int, int], zoom: float, highlighted: bool = False):
    """Draw an orbital path"""
    screen_points = []
    
    for x, y, _ in points:
        screen_x = int(center[0] + x * zoom)
        screen_y = int(center[1] + y * zoom)
        
        # Only include points that are reasonably on screen
        margin = 200
        if (-margin < screen_x < screen.get_width() + margin and 
            -margin < screen_y < screen.get_height() + margin):
            screen_points.append((screen_x, screen_y))
    
    if len(screen_points) > 2:
        color = COLORS['hud_accent'] if highlighted else COLORS['orbit']
        width = 2 if highlighted else 1
        
        try:
            orbit_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            pygame.draw.lines(orbit_surf, color, False, screen_points, width)
            screen.blit(orbit_surf, (0, 0))
        except:
            pass  # Skip if drawing fails


def draw_planet(screen: pygame.Surface, font: pygame.font.Font, 
                name: str, position: Tuple[float, float], 
                center: Tuple[int, int], zoom: float, 
                trails: List, selected: bool = False) -> Tuple[int, int]:
    """Draw a planet at its current position"""
    style = PLANET_STYLES[name]
    x = int(center[0] + position[0] * zoom)
    y = int(center[1] + position[1] * zoom)
    
    # Selection indicator
    if selected:
        pygame.draw.circle(screen, COLORS['hud_accent'], (x, y), style.radius + 8, 3)
    
    # Atmosphere effect
    if style.has_atmosphere:
        atmo_surf = pygame.Surface((style.radius*4, style.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(atmo_surf, (*style.color, 30), 
                         (style.radius*2, style.radius*2), style.radius + 4)
        screen.blit(atmo_surf, (x - style.radius*2, y - style.radius*2))
    
    # Main planet body
    pygame.draw.circle(screen, style.color, (x, y), style.radius)
    
    # Simple 3D effect with highlight
    highlight = tuple(min(255, c + 50) for c in style.color)
    pygame.draw.circle(screen, highlight, 
                      (x - style.radius//3, y - style.radius//3), 
                      style.radius//3)
    
    # Saturn's rings
    if style.has_rings and style.ring_color:
        ring_rect = pygame.Rect(x - style.radius - 10, y - 3, 
                               2 * (style.radius + 10), 6)
        pygame.draw.ellipse(screen, style.ring_color, ring_rect, 2)
    
    # Planet label
    label = font.render(name, True, COLORS['white'])
    label_x = x + style.radius + 5
    label_y = y - style.radius
    
    # Label background for readability
    label_bg = pygame.Surface((label.get_width() + 4, label.get_height() + 2), pygame.SRCALPHA)
    label_bg.fill((0, 0, 0, 150))
    screen.blit(label_bg, (label_x - 2, label_y - 1))
    screen.blit(label, (label_x, label_y))
    
    # Update trail
    trails.append((x, y))
    if len(trails) > MAX_TRAIL_LENGTH:
        trails.pop(0)
    
    # Draw trail
    if len(trails) > 2:
        for i in range(1, len(trails)):
            alpha = int(150 * i / len(trails))
            color = (*style.color, alpha)
            
            trail_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
            trail_surf.fill(color)
            screen.blit(trail_surf, (trails[i][0] - 2, trails[i][1] - 2))
    
    return (x, y)


def draw_hud(screen: pygame.Surface, fonts: Dict, date: datetime, 
             zoom: float, paused: bool, time_step: timedelta, 
             selected_planet: Optional[str] = None):
    """Draw the heads-up display with current information"""
    font = fonts['normal']
    font_title = fonts['title']
    
    # Build info lines
    lines = [
        ("Solar System Explorer", font_title, COLORS['hud_accent']),
        (f"Date: {format_date(date)}", font, COLORS['hud_text']),
        (f"Zoom: {100 * zoom / DEFAULT_ZOOM:.0f}%", font, COLORS['hud_text']),
        (f"{'PAUSED' if paused else 'RUNNING'}", font, 
         (255, 100, 100) if paused else (100, 255, 100)),
    ]
    
    if selected_planet:
        distances = calculate_planet_distance(selected_planet, date)
        lines.append(
            (f"{selected_planet}: {format_distance(distances['sun_distance'])} from Sun", 
             font, COLORS['hud_accent'])
        )
    
    # Calculate panel size
    max_width = max(f.size(text)[0] for text, f, _ in lines)
    panel_height = len(lines) * 25 + 20
    
    # Draw panel
    panel = pygame.Surface((max_width + 40, panel_height), pygame.SRCALPHA)
    panel.fill(COLORS['hud_bg'])
    screen.blit(panel, (10, 10))
    
    # Draw text
    y = 20
    for text, font_to_use, color in lines:
        rendered = font_to_use.render(text, True, color)
        screen.blit(rendered, (20, y))
        y += 25


def draw_controls(screen: pygame.Surface, font: pygame.font.Font):
    """Draw control hints"""
    controls = [
        "CONTROLS",
        "Left or Right arrow keys  Day ±1",
        "[ or ]  Month ±30",
        ", or .  Hour ±1",
        "- or =  Zoom",
        "Space  Pause",
        "T  Today",
        "R  Reset",
        "Click  Select",
    ]
    
    # Position in bottom right
    y = screen.get_height() - len(controls) * 18 - 20
    x = screen.get_width() - 150
    
    # Background
    panel = pygame.Surface((140, len(controls) * 18 + 10), pygame.SRCALPHA)
    panel.fill(COLORS['hud_bg'])
    screen.blit(panel, (x - 5, y - 5))
    
    # Draw each line
    for i, line in enumerate(controls):
        color = COLORS['hud_accent'] if i == 0 else COLORS['hud_text']
        text = font.render(line, True, color)
        screen.blit(text, (x, y + i * 18))


def draw_planet_info(screen: pygame.Surface, fonts: Dict, 
                     planet_name: str, date: datetime):
    """Draw detailed planet information panel"""
    if planet_name not in PLANET_INFO:
        return
    
    info = PLANET_INFO[planet_name]
    distances = calculate_planet_distance(planet_name, date)
    
    # Build info text
    lines = [
        f"{planet_name.upper()}",
        "",
        f"Distance from Sun: {format_distance(distances['sun_distance'])}",
        f"Distance from Earth: {format_distance(distances['earth_distance'])}",
        f"Orbital Speed: {distances['orbital_speed']:.1f} km/s",
        "",
        f"Mass: {info['mass_earth']:.2f} Earth masses",
        f"Gravity: {info['gravity']:.1f} m/s²",
        f"Day Length: {abs(info['day_hours']):.1f} hours",
        f"Moons: {info['moons']}",
        f"Avg Temperature: {info['temp_avg']}°C",
        "",
        info['fact']
    ]
    
    # Word wrap long fact if needed
    if len(info['fact']) > 40:
        words = info['fact'].split()
        wrapped = []
        current = ""
        for word in words:
            if len(current + word) < 40:
                current += word + " "
            else:
                wrapped.append(current.strip())
                current = word + " "
        if current:
            wrapped.append(current.strip())
        lines[-1:] = wrapped
    
    # Calculate panel size
    font = fonts['small']
    max_width = max(font.size(line)[0] for line in lines if line)
    panel_height = len(lines) * 18 + 20
    
    # Position on left side
    x = 20
    y = (screen.get_height() - panel_height) // 2
    
    # Draw panel
    panel = pygame.Surface((max_width + 30, panel_height), pygame.SRCALPHA)
    panel.fill(COLORS['hud_bg'])
    screen.blit(panel, (x, y))
    
    # Border in planet color
    pygame.draw.rect(screen, PLANET_STYLES[planet_name].color, 
                    (x, y, max_width + 30, panel_height), 2)
    
    # Draw text
    text_y = y + 10
    for i, line in enumerate(lines):
        if not line:
            text_y += 18
            continue
        
        # Title in planet color, rest in white
        if i == 0:
            color = PLANET_STYLES[planet_name].color
            text = fonts['normal'].render(line, True, color)
        else:
            text = font.render(line, True, COLORS['hud_text'])
        
        screen.blit(text, (x + 10, text_y))
        text_y += 18


# logic for the main functions

def get_start_date() -> datetime:
    """Get starting date from user input"""
    try:
        user_input = input(
            "\n🌟 Solar System Explorer 🌟\n"
            "Enter date (YYYY-MM-DD) or press Enter for today: "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return datetime.utcnow()
    
    if not user_input:
        return datetime.utcnow()
    
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y/%m/%d"]:
        try:
            return datetime.strptime(user_input, fmt)
        except ValueError:
            continue
    
    print("Invalid date format. Using today's date.")
    return datetime.utcnow()


def handle_click(mouse_pos: Tuple[int, int], planet_positions: Dict, 
                 current_selection: Optional[str]) -> Optional[str]:
    """Check if click hits a planet"""
    mouse_x, mouse_y = mouse_pos
    
    for name, (px, py) in planet_positions.items():
        distance = math.sqrt((mouse_x - px)**2 + (mouse_y - py)**2)
        if distance <= PLANET_STYLES[name].radius + 5:
            # Toggle selection
            return None if current_selection == name else name
    
    return current_selection


def main():
    """Main game loop"""
    # Get starting date
    current_date = get_start_date()
    print(f"Starting at: {format_date(current_date)}")
    
    # Initialise Pygame
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Solar System Explorer")
    clock = pygame.time.Clock()
    
    # Load fonts
    fonts = {
        'title': pygame.font.Font(None, 20),
        'normal': pygame.font.Font(None, 16),
        'small': pygame.font.Font(None, 14)
    }
    
    # Game state
    center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    zoom = auto_zoom_level(current_date)
    paused = False
    show_help = True
    selected_planet = None
    
    # Time controls
    time_step = timedelta(hours=1)
    
    # Planet trails
    trails = {name: [] for name in PLANETS.keys()}
    
    # Pre-calculate orbits
    orbits = {name: generate_orbit_points(data) 
              for name, data in PLANETS.items()}
    
    print("Controls: Arrow keys for time, -/= for zoom, Space to pause, H for help")
    
    # Main loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_h:
                    show_help = not show_help
                elif event.key == pygame.K_t:
                    current_date = datetime.utcnow()
                elif event.key == pygame.K_r:
                    zoom = auto_zoom_level(current_date)
                    selected_planet = None
                    
                # Time controls
                elif event.key == pygame.K_LEFT:
                    current_date -= timedelta(days=1)
                elif event.key == pygame.K_RIGHT:
                    current_date += timedelta(days=1)
                elif event.key == pygame.K_LEFTBRACKET:
                    current_date -= timedelta(days=30)
                elif event.key == pygame.K_RIGHTBRACKET:
                    current_date += timedelta(days=30)
                elif event.key == pygame.K_COMMA:
                    current_date -= timedelta(hours=1)
                elif event.key == pygame.K_PERIOD:
                    current_date += timedelta(hours=1)
                    
                # Zoom
                elif event.key == pygame.K_MINUS:
                    zoom = clamp(zoom * 0.9, 20, 800)
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    zoom = clamp(zoom * 1.1, 20, 800)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    planet_positions = {}
                    for name in PLANETS:
                        x, y, _ = elements_to_xy(PLANETS[name], current_date)
                        px = int(center[0] + x * zoom)
                        py = int(center[1] + y * zoom)
                        planet_positions[name] = (px, py)
                    selected_planet = handle_click(event.pos, planet_positions, selected_planet)
                    
            elif event.type == pygame.VIDEORESIZE:
                center = (event.w // 2, event.h // 2)
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        
        # Auto-advance time when not paused
        if not paused:
            current_date += time_step / FPS
        
        # Clear screen
        screen.fill(COLORS['background'])
        
        # Draw background elements
        draw_starfield(screen)
        draw_grid(screen, center, zoom)
        draw_sun(screen, center)
        
        # Draw orbits
        for name, orbit_points in orbits.items():
            is_selected = (name == selected_planet)
            draw_orbit(screen, orbit_points, center, zoom, is_selected)
        
        # Draw planets and collect positions
        planet_positions = {}
        for name in PLANETS:
            x, y, _ = elements_to_xy(PLANETS[name], current_date)
            is_selected = (name == selected_planet)
            pos = draw_planet(screen, fonts['small'], name, (x, y), 
                            center, zoom, trails[name], is_selected)
            planet_positions[name] = pos
        
        # Draw UI elements
        if show_help:
            draw_hud(screen, fonts, current_date, zoom, paused, time_step, selected_planet)
            draw_controls(screen, fonts['small'])
        
        if selected_planet:
            draw_planet_info(screen, fonts, selected_planet, current_date)
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()


if __name__ == "__main__":
    main()