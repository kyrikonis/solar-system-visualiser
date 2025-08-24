"""
3D Solar System Visualiser

Controls:
    Mouse Drag: Rotate camera around solar system
    Scroll: Zoom in/out
    Arrow Keys: Step forward/backward by days
    [ or ]: Step by months  
    , or .: Step by hours
    Space: Pause/resume animation
    T: Jump to today
    R: Reset view
    F: Follow selected planet
    1-8: Quick select planets
    H: Toggle help
    Click: Select planet for details
"""

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
import numpy as np

import pygame

from planet_data import PLANETS, elements_to_xy, generate_orbit_points


# configuration
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1000
FPS = 60
STAR_COUNT = 600
DEFAULT_ZOOM = 140
MAX_TRAIL_LENGTH = 200

# colours
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


class Camera3D:
    """class handles all 3d camera projection and movement"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        
        # Camera position in spherical coordinates
        self.rotation_x = -25  # Tilt angle 
        self.rotation_z = 0    # horizontal rotation 
        self.distance = 800    # distance from origin
        
        # mouse control state
        self.dragging = False
        self.last_mouse = (0, 0)
        
        # Follow mode
        self.follow_planet = None
        
    def update_size(self, width: int, height: int):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
    
    def project_3d_to_2d(self, x: float, y: float, z: float, zoom: float) -> Tuple[int, int, float]:
        """
        converts 3D coordinates to 2D screen position.
        Returns (screen_x, screen_y, depth) where depth is used for sorting
        """
        # Apply camera rotations
        # First rotate around Z axis (horizontal)
        cos_z = math.cos(math.radians(self.rotation_z))
        sin_z = math.sin(math.radians(self.rotation_z))
        x_rot = x * cos_z - y * sin_z
        y_rot = x * sin_z + y * cos_z
        
        # Then rotate around X axis (vertical tilt)
        cos_x = math.cos(math.radians(self.rotation_x))
        sin_x = math.sin(math.radians(self.rotation_x))
        y_final = y_rot * cos_x - z * sin_x
        z_final = y_rot * sin_x + z * cos_x
        
        # Apply perspective projection
        perspective_scale = self.distance / (self.distance + z_final * zoom)
        
        # Convert to screen coordinates
        screen_x = int(self.center[0] + x_rot * zoom * perspective_scale)
        screen_y = int(self.center[1] - y_final * zoom * perspective_scale)
        
        # Return depth for sorting (further away = smaller value)
        depth = z_final
        
        return screen_x, screen_y, depth
    
    def handle_mouse_down(self, pos: Tuple[int, int]):
        """Start camera drag"""
        self.dragging = True
        self.last_mouse = pos
    
    def handle_mouse_up(self):
        """End camera drag"""
        self.dragging = False
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Update camera rotation based on mouse drag"""
        if self.dragging:
            dx = pos[0] - self.last_mouse[0]
            dy = pos[1] - self.last_mouse[1]
            
            # Update rotations (with some sensitivity scaling)
            self.rotation_z += dx * 0.5
            self.rotation_x = max(-89, min(89, self.rotation_x + dy * 0.3))
            
            self.last_mouse = pos
    
    def handle_scroll(self, direction: int):
        """Zoom camera in/out"""
        if direction > 0:
            self.distance = max(200, self.distance * 0.9)
        else:
            self.distance = min(3000, self.distance * 1.1)
    
    def reset(self):
        """Reset camera to default position"""
        self.rotation_x = -25
        self.rotation_z = 0
        self.distance = 800
        self.follow_planet = None


@dataclass
class PlanetStyle:
    """Visual properties for each celestial body"""
    radius: int
    color: Tuple[int, int, int]
    has_rings: bool = False
    ring_color: Optional[Tuple[int, int, int]] = None
    has_atmosphere: bool = False


# Planet styles
PLANET_STYLES = {
    "Sun": PlanetStyle(25, (255, 215, 0)),
    "Mercury": PlanetStyle(5, (169, 169, 169)),
    "Venus": PlanetStyle(7, (255, 198, 73), has_atmosphere=True),
    "Earth": PlanetStyle(8, (100, 149, 237), has_atmosphere=True),
    "Mars": PlanetStyle(6, (205, 92, 92)),
    "Jupiter": PlanetStyle(16, (218, 165, 32)),
    "Saturn": PlanetStyle(14, (250, 235, 215), has_rings=True, ring_color=(210, 180, 140)),
    "Uranus": PlanetStyle(10, (64, 224, 208), has_rings=True, ring_color=(100, 150, 200)),
    "Neptune": PlanetStyle(10, (65, 105, 225)),
}

# Planet info
PLANET_INFO = {
    "Mercury": {
        "mass_earth": 0.055, 
        "gravity": 3.7, 
        "temp_avg": 167,
        "day_hours": 1407.6, 
        "moons": 0,
        "fact": "One day on Mercury equals 176 Earth days"
    },
    "Venus": {
        "mass_earth": 0.815, 
        "gravity": 8.87, 
        "temp_avg": 464,
        "day_hours": -5832.5,
        "moons": 0,
        "fact": "Venus rotates backwards and its day is longer than its year"
    },
    "Earth": {
        "mass_earth": 1.0, 
        "gravity": 9.8, 
        "temp_avg": 15,
        "day_hours": 24, 
        "moons": 1,
        "fact": "The only known planet with life"
    },
    "Mars": {
        "mass_earth": 0.107, 
        "gravity": 3.71, 
        "temp_avg": -65,
        "day_hours": 24.6, 
        "moons": 2,
        "fact": "Home to Olympus Mons, the largest volcano in the solar system"
    },
    "Jupiter": {
        "mass_earth": 317.8, 
        "gravity": 24.79, 
        "temp_avg": -110,
        "day_hours": 9.9, 
        "moons": 95,
        "fact": "The Great Red Spot is a storm larger than Earth"
    },
    "Saturn": {
        "mass_earth": 95.2, 
        "gravity": 10.44, 
        "temp_avg": -140,
        "day_hours": 10.7, 
        "moons": 146,
        "fact": "Saturn's rings are made of ice and rock, some pieces as large as houses"
    },
    "Uranus": {
        "mass_earth": 14.5, 
        "gravity": 8.69, 
        "temp_avg": -195,
        "day_hours": -17.2,
        "moons": 28,
        "fact": "Tilted on its side with vertical rings"
    },
    "Neptune": {
        "mass_earth": 17.1, 
        "gravity": 11.15, 
        "temp_avg": -200,
        "day_hours": 16.1, 
        "moons": 16,
        "fact": "Has the fastest winds in the solar system at 2100 km/h"
    }
}


# Utility functions
def clamp(value: float, min_val: float, max_val: float) -> float:
    """Keep value in bounds"""
    return max(min_val, min(max_val, value))


def format_date(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def format_distance(au: float) -> str:
    """Convert AU to readable distance"""
    if au < 0.1:
        return f"{au * 149.6:.1f} million km"
    return f"{au:.3f} AU"


def calculate_planet_distance(planet_name: str, date: datetime) -> Dict[str, float]:
    """Get planet distances and speed"""
    x, y, z = elements_to_xy(PLANETS[planet_name], date)
    distance_from_sun = math.sqrt(x*x + y*y + z*z)
    
    earth_x, earth_y, earth_z = elements_to_xy(PLANETS["Earth"], date)
    distance_from_earth = math.sqrt(
        (x - earth_x)**2 + (y - earth_y)**2 + (z - earth_z)**2
    )
    
    orbital_speed = math.sqrt(1.0 / distance_from_sun) * 29.78
    
    return {
        "sun_distance": distance_from_sun,
        "earth_distance": distance_from_earth,
        "orbital_speed": orbital_speed
    }


def auto_zoom_level(date: datetime) -> float:
    """Calculate initial zoom"""
    max_dist = 0
    for planet_data in PLANETS.values():
        x, y, _ = elements_to_xy(planet_data, date)
        dist = math.sqrt(x*x + y*y)
        max_dist = max(max_dist, dist)
    
    screen_radius = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 2
    return max(20, int(screen_radius * 0.8 / max_dist))


# 3D Drawing functions
def draw_3d_starfield(screen: pygame.Surface, camera: Camera3D):
    """Draw stars that appear to be at infinity"""
    random.seed(42)  # Fixed seed for consistent stars
    
    for _ in range(STAR_COUNT):
        # Generate stars in a sphere around the viewer
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(-math.pi/2, math.pi/2)
        
        # Convert to cartesian at "infinite" distance
        x = 1000 * math.cos(phi) * math.cos(theta)
        y = 1000 * math.cos(phi) * math.sin(theta)
        z = 1000 * math.sin(phi)
        
        # Project to screen
        screen_x, screen_y, _ = camera.project_3d_to_2d(x, y, z, 1)
        
        # Only draw if on screen
        if 0 <= screen_x < screen.get_width() and 0 <= screen_y < screen.get_height():
            brightness = random.randint(100, 255)
            size = 2 if random.random() < 0.02 else 1
            
            if size == 2:
                pygame.draw.circle(screen, (brightness, brightness, brightness), 
                                 (screen_x, screen_y), size)
            else:
                screen.set_at((screen_x, screen_y), (brightness, brightness, brightness))


def draw_3d_grid(screen: pygame.Surface, camera: Camera3D, zoom: float):
    """Draw a 3D reference grid in the orbital plane"""
    # Draw concentric circles at different AU distances
    for au in range(5, 35, 5):
        points = []
        for angle in range(0, 361, 10):
            x = au * math.cos(math.radians(angle))
            y = au * math.sin(math.radians(angle))
            z = 0
            
            screen_x, screen_y, depth = camera.project_3d_to_2d(x, y, z, zoom)
            points.append((screen_x, screen_y))
        
        # Draw the circle
        if len(points) > 2:
            try:
                pygame.draw.lines(screen, COLORS['grid'], False, points, 1)
            except:
                pass


def draw_3d_sun(screen: pygame.Surface, camera: Camera3D, zoom: float):
    """Draw sun with 3D positioning"""
    screen_x, screen_y, depth = camera.project_3d_to_2d(0, 0, 0, zoom)
    style = PLANET_STYLES["Sun"]
    
    # Scale based on distance
    scale = camera.distance / (camera.distance + depth * zoom)
    radius = int(style.radius * scale)
    
    # Glow effect
    for r in range(radius + 15, radius, -2):
        alpha = int(30 * (radius + 15 - r) / 15)
        glow_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLORS['sun'], alpha), (r, r), r)
        screen.blit(glow_surf, (screen_x - r, screen_y - r))
    
    # Main sun
    pygame.draw.circle(screen, style.color, (screen_x, screen_y), radius)
    pygame.draw.circle(screen, (255, 255, 200), (screen_x, screen_y), max(1, radius - 5))


def draw_3d_orbit(screen: pygame.Surface, points: List, camera: Camera3D, 
                  zoom: float, highlighted: bool = False):
    """Draw orbit in 3D space"""
    screen_points = []
    
    for x, y, z in points:
        screen_x, screen_y, depth = camera.project_3d_to_2d(x, y, z, zoom)
        
        # Check if point is reasonably on screen
        margin = 200
        if (-margin < screen_x < screen.get_width() + margin and 
            -margin < screen_y < screen.get_height() + margin):
            screen_points.append((screen_x, screen_y, depth))
    
    if len(screen_points) > 2:
        # Sort by depth and draw back to front
        color = COLORS['hud_accent'] if highlighted else COLORS['orbit']
        width = 2 if highlighted else 1
        
        # Draw the orbit line
        points_2d = [(x, y) for x, y, _ in screen_points]
        try:
            orbit_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            pygame.draw.lines(orbit_surf, color, False, points_2d, width)
            screen.blit(orbit_surf, (0, 0))
        except:
            pass


def draw_3d_planet(screen: pygame.Surface, font: pygame.font.Font,
                   name: str, position: Tuple[float, float, float],
                   camera: Camera3D, zoom: float, trails: List,
                   selected: bool = False) -> Tuple[int, int, float]:
    """Draw planet in 3D space"""
    x, y, z = position
    screen_x, screen_y, depth = camera.project_3d_to_2d(x, y, z, zoom)
    
    style = PLANET_STYLES[name]
    
    # Scale radius based on distance
    scale = camera.distance / (camera.distance + depth * zoom)
    radius = max(2, int(style.radius * scale))
    
    # Don't draw if behind camera
    if scale <= 0:
        return screen_x, screen_y, depth
    
    # Selection indicator
    if selected:
        pygame.draw.circle(screen, COLORS['hud_accent'], 
                         (screen_x, screen_y), radius + 8, 3)
    
    # Atmosphere
    if style.has_atmosphere:
        atmo_radius = radius + 4
        atmo_surf = pygame.Surface((atmo_radius*2, atmo_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(atmo_surf, (*style.color, 30), 
                         (atmo_radius, atmo_radius), atmo_radius)
        screen.blit(atmo_surf, (screen_x - atmo_radius, screen_y - atmo_radius))
    
    # Main planet
    pygame.draw.circle(screen, style.color, (screen_x, screen_y), radius)
    
    # Shading for 3D effect
    highlight = tuple(min(255, c + 50) for c in style.color)
    highlight_offset = radius // 3
    pygame.draw.circle(screen, highlight, 
                      (screen_x - highlight_offset, screen_y - highlight_offset), 
                      max(1, radius // 3))
    
    # Saturn's rings (now properly 3D!)
    if style.has_rings and style.ring_color:
        # Calculate ring ellipse based on viewing angle
        ring_width = int((radius + 10) * 2)
        ring_height = int(abs(6 * math.cos(math.radians(camera.rotation_x))))
        
        if ring_height > 1:  # Only draw if visible
            ring_surf = pygame.Surface((ring_width + 20, ring_height + 20), pygame.SRCALPHA)
            ring_rect = pygame.Rect(10, 10, ring_width, ring_height)
            pygame.draw.ellipse(ring_surf, style.ring_color, ring_rect, 2)
            screen.blit(ring_surf, (screen_x - ring_width//2 - 10, screen_y - ring_height//2 - 10))
    
    # Label with depth-based sizing
    label_size = max(10, int(14 * scale))
    label_font = pygame.font.Font(None, label_size)
    label = label_font.render(name, True, COLORS['white'])
    
    label_x = screen_x + radius + 5
    label_y = screen_y - radius
    
    # Background for readability
    label_bg = pygame.Surface((label.get_width() + 4, label.get_height() + 2), pygame.SRCALPHA)
    label_bg.fill((0, 0, 0, 150))
    screen.blit(label_bg, (label_x - 2, label_y - 1))
    screen.blit(label, (label_x, label_y))
    
    # Update trail (in 3D!)
    trails.append((x, y, z))
    if len(trails) > MAX_TRAIL_LENGTH:
        trails.pop(0)
    
    # Draw 3D trail
    if len(trails) > 2:
        for i in range(1, len(trails)):
            trail_x, trail_y, trail_z = trails[i]
            trail_screen_x, trail_screen_y, trail_depth = camera.project_3d_to_2d(
                trail_x, trail_y, trail_z, zoom)
            
            alpha = int(100 * i / len(trails))
            color = (*style.color, alpha)
            
            trail_scale = camera.distance / (camera.distance + trail_depth * zoom)
            trail_size = max(1, int(3 * trail_scale))
            
            trail_surf = pygame.Surface((trail_size*2, trail_size*2), pygame.SRCALPHA)
            trail_surf.fill(color)
            screen.blit(trail_surf, (trail_screen_x - trail_size, trail_screen_y - trail_size))
    
    return screen_x, screen_y, depth


def draw_3d_hud(screen: pygame.Surface, fonts: Dict, date: datetime, 
                camera: Camera3D, zoom: float, paused: bool,
                selected_planet: Optional[str] = None):
    """Draw HUD with 3D camera info"""
    font = fonts['normal']
    font_title = fonts['title']
    
    lines = [
        ("3D Solar System Explorer", font_title, COLORS['hud_accent']),
        (f"Date: {format_date(date)}", font, COLORS['hud_text']),
        (f"Camera: {camera.rotation_x:.0f}° tilt, {camera.rotation_z:.0f}° rotation", 
         font, COLORS['hud_text']),
        (f"Zoom: {100 * zoom / DEFAULT_ZOOM:.0f}%", font, COLORS['hud_text']),
        (f"{'PAUSED' if paused else 'RUNNING'}", font, 
         (255, 100, 100) if paused else (100, 255, 100)),
    ]
    
    if camera.follow_planet:
        lines.append((f"Following: {camera.follow_planet}", font, COLORS['hud_accent']))
    
    if selected_planet:
        distances = calculate_planet_distance(selected_planet, date)
        lines.append(
            (f"{selected_planet}: {format_distance(distances['sun_distance'])} from Sun", 
             font, COLORS['hud_accent'])
        )
    
    max_width = max(f.size(text)[0] for text, f, _ in lines)
    panel_height = len(lines) * 25 + 20
    
    panel = pygame.Surface((max_width + 40, panel_height), pygame.SRCALPHA)
    panel.fill(COLORS['hud_bg'])
    screen.blit(panel, (10, 10))
    
    y = 20
    for text, font_to_use, color in lines:
        rendered = font_to_use.render(text, True, color)
        screen.blit(rendered, (20, y))
        y += 25


def draw_3d_controls(screen: pygame.Surface, font: pygame.font.Font):
    """Draw 3D control hints"""
    controls = [
        "3D CONTROLS",
        "Mouse Drag: Rotate",
        "Scroll: Zoom",
        "←/→: Day ±1",
        "[/]: Month ±30",
        "Space: Pause",
        "F: Follow planet",
        "1-8: Quick select",
        "R: Reset camera",
        "T: Today",
    ]
    
    y = screen.get_height() - len(controls) * 18 - 20
    x = screen.get_width() - 160
    
    panel = pygame.Surface((150, len(controls) * 18 + 10), pygame.SRCALPHA)
    panel.fill(COLORS['hud_bg'])
    screen.blit(panel, (x - 5, y - 5))
    
    for i, line in enumerate(controls):
        color = COLORS['hud_accent'] if i == 0 else COLORS['hud_text']
        text = font.render(line, True, color)
        screen.blit(text, (x, y + i * 18))


def draw_planet_info(screen: pygame.Surface, fonts: Dict, 
                     planet_name: str, date: datetime):
    """Planet info panel (same as before)"""
    if planet_name not in PLANET_INFO:
        return
    
    info = PLANET_INFO[planet_name]
    distances = calculate_planet_distance(planet_name, date)
    
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
        f"Temperature: {info['temp_average']}°C",
        "",
        info['fact']
    ]
    
    # wrap words
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
    
    font = fonts['small']
    max_width = max(font.size(line)[0] for line in lines if line)
    panel_height = len(lines) * 18 + 20
    
    x = 20
    y = (screen.get_height() - panel_height) // 2
    
    panel = pygame.Surface((max_width + 30, panel_height), pygame.SRCALPHA)
    panel.fill(COLORS['hud_bg'])
    screen.blit(panel, (x, y))
    
    pygame.draw.rect(screen, PLANET_STYLES[planet_name].color, 
                    (x, y, max_width + 30, panel_height), 2)
    
    text_y = y + 10
    for i, line in enumerate(lines):
        if not line:
            text_y += 18
            continue
        
        if i == 0:
            color = PLANET_STYLES[planet_name].color
            text = fonts['normal'].render(line, True, color)
        else:
            text = font.render(line, True, COLORS['hud_text'])
        
        screen.blit(text, (x + 10, text_y))
        text_y += 18


def get_start_date() -> datetime:
    try:
        user_input = input(
            "\n🌟 3D Solar System Explorer 🌟\n"
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
    
    print("Invalid date. Using today.")
    return datetime.utcnow()


def main():
    """Main loop with 3D rendering"""
    current_date = get_start_date()
    print(f"Starting at: {format_date(current_date)}")
    
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("3D Solar System Explorer")
    clock = pygame.time.Clock()
    
    fonts = {
        'title': pygame.font.Font(None, 20),
        'normal': pygame.font.Font(None, 16),
        'small': pygame.font.Font(None, 14)
    }
    
    # initialise 3d camera
    camera = Camera3D(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # State
    zoom = auto_zoom_level(current_date)
    paused = False
    show_help = True
    selected_planet = None
    time_step = timedelta(hours=1)
    
    # Planet trails
    trails = {name: [] for name in PLANETS.keys()}
    
    # Pre-calculate orbits
    orbits = {name: generate_orbit_points(data) 
              for name, data in PLANETS.items()}
    
    planet_list = ["Mercury", "Venus", "Earth", "Mars", 
                   "Jupiter", "Saturn", "Uranus", "Neptune"]
    
    print("Drag mouse to rotate view, scroll to or use key controls to zoom.")
    
    running = True
    while running:
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
                    camera.reset()
                    zoom = auto_zoom_level(current_date)
                elif event.key == pygame.K_f:
                    # to toggle 'follow mode'
                    if selected_planet:
                        camera.follow_planet = selected_planet if not camera.follow_planet else None
                
                # use number keys to select planet for info
                elif pygame.K_1 <= event.key <= pygame.K_8:
                    idx = event.key - pygame.K_1
                    if idx < len(planet_list):
                        selected_planet = planet_list[idx]
                
                # controls for changing time
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
                
                # Zoom controls
                elif event.key == pygame.K_MINUS:
                    zoom = clamp(zoom * 0.9, 20, 800)
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    zoom = clamp(zoom * 1.1, 20, 800)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    camera.handle_mouse_down(event.pos)
                elif event.button == 4:  # Scroll up
                    camera.handle_scroll(1)
                elif event.button == 5:  # Scroll down
                    camera.handle_scroll(-1)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    camera.handle_mouse_up()
            
            elif event.type == pygame.MOUSEMOTION:
                camera.handle_mouse_motion(event.pos)
            
            elif event.type == pygame.VIDEORESIZE:
                camera.update_size(event.w, event.h)
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        
        # Update time
        if not paused:
            current_date += time_step / FPS
        
        # Follow mode - update camera to track planet
        if camera.follow_planet and camera.follow_planet in PLANETS:
            x, y, z = elements_to_xy(PLANETS[camera.follow_planet], current_date)
            # camera rotation following planet
            angle = math.degrees(math.atan2(y, x))
            camera.rotation_z += (angle - camera.rotation_z - 90) * 0.05
        
        # Clear screen
        screen.fill(COLORS['background'])
        
        # draw 3d elements
        draw_3d_starfield(screen, camera)
        draw_3d_grid(screen, camera, zoom)
        
        # Collect all planets with depths for proper ordering
        planet_draws = []
        
        # Add sun
        sun_x, sun_y, sun_depth = camera.project_3d_to_2d(0, 0, 0, zoom)
        planet_draws.append(('Sun', None, (0, 0, 0), sun_depth, False))
        
        # Add planets
        for name in PLANETS:
            x, y, z = elements_to_xy(PLANETS[name], current_date)
            _, _, depth = camera.project_3d_to_2d(x, y, z, zoom)
            is_selected = (name == selected_planet)
            planet_draws.append((name, PLANETS[name], (x, y, z), depth, is_selected))
        
        # sort planets by 'depth' , furtherst first
        planet_draws.sort(key=lambda p: p[3], reverse=True)
        
        # orbits drawn behind planets
        for name, orbit_points in orbits.items():
            is_selected = (name == selected_planet)
            draw_3d_orbit(screen, orbit_points, camera, zoom, is_selected)
        
        # plents drawn in order
        planet_positions = {}
        for name, planet_data, position, depth, is_selected in planet_draws:
            if name == 'Sun':
                draw_3d_sun(screen, camera, zoom)
            else:
                screen_pos = draw_3d_planet(screen, fonts['small'], name, position,
                                           camera, zoom, trails[name], is_selected)
                planet_positions[name] = screen_pos[:2]  # Just x n y for click detection
        
        # Draw UI
        if show_help:
            draw_3d_hud(screen, fonts, current_date, camera, zoom, paused, selected_planet)
            draw_3d_controls(screen, fonts['small'])
        
        if selected_planet:
            draw_planet_info(screen, fonts, selected_planet, current_date)
        
        # update display
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()


if __name__ == "__main__":
    main()