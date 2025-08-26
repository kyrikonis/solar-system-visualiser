# 3D Solar System Visualizer

A real-time 3D visualisation/simulator of our Solar System using accurate NASA orbital elements. You can see the state of the solar system at any given time with full camera controls and detailed information for each planet.

## Features

### Real-time 3D Visualisation
- Full 3D camera system controlled via mouse
- Accurate planetary positions based on Keplerian orbital elements (J2000.0 epoch)
- Smooth orbital animations with configurable time steps
- Starry background for immersive space experience

### Planetary Details
- All 8 planets with realistic colours and sizes relative to each other
- Saturns rings with 3D perspective effects
- Atmospheric effects for Venus and Earth
- Orbital trails tracking each planets paths
- Individual planet information cells with facts on whatever one of your choosing

### Time Control
- Set any date from past to future
- Multiple time step controls (hours, days, months)
- Pause/resume
- Quick reset to current date

### Interactive Controls
- **Mouse Drag**: Rotate camera around solar system
- **Mouse Scroll**: Zoom in/out
- **Arrow Keys**: Step forward/backward by days
- **[ or ]**: Step by months
- **Comma/Period**: Step by hours
- **Space**: Pause/resume animation
- **1-8**: Quick select planets for detailed info
- **F**: Follow selected planet with camera
- **T**: Jump to today's date
- **R**: Reset camera view
- **H**: Toggle help display

## Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Setup
1. Clone the repository:
```bash
git clone https://github.com/kyrikonis/solar-system-visualiser.git
cd solar-system-visualiser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

### Starting the Application
When you run `main.py`, you'll be prompted to enter a start date:
```
🌟 3D Solar System Explorer 🌟
Enter date (YYYY-MM-DD) or press Enter for today:
```

Supported date formats:
- `2024-12-25` (YYYY-MM-DD)
- `2024-12-25 14:30` (YYYY-MM-DD HH:MM)
- `2024/12/25` (YYYY/MM/DD)
- Press Enter for current date

### Navigation
- **Rotate View**: Click and drag with mouse
- **Zoom**: Use mouse scroll wheel or + or - keys
- **Time Travel**: Use arrow keys or bracket keys to change date
- **Planet Selection**: Use number keys 1-8 to select planets
- **Follow Mode**: Press F while a planet is selected to track it

### Planet Information
Select any planet (keys 1-8) to view detailed information including:
- Distance from Sun and Earth
- Orbital speed
- Physical characteristics (mass, gravity, temperature)
- Day length and number of moons
- Interesting facts

## Technical Details

### Orbital Mechanics
The simulation uses accurate Keplerian orbital elements:
- **Semi-major axis (a)**: Size of orbit
- **Eccentricity (e)**: Orbital shape
- **Inclination (i)**: Tilt of orbital plane
- **Longitude of ascending node (Ω)**: Orbital orientation
- **Argument of perihelion (ω)**: Point of closest approach
- **Mean anomaly (M₀)**: Starting position at epoch

### Coordinate System
- **Epoch**: J2000.0 (January 1, 2000, 12:00 UTC)
- **Reference Frame**: Ecliptic coordinates
- **Units**: Astronomical Units (AU) for distance
- **Time**: UTC for all calculations

### 3D Rendering
- Custom 3D projection system
- Depth sorting for proper planet ordering
- Perspective scaling based on camera distance
- Spherical coordinate camera system

## File Structure

```
solar-system-visualizer/
├── main.py              # Main application and 3D rendering
├── planet_data.py       # orbital mechanics and calculations
├── requirements.txt     # dependencies / libraries used
└── README.md
```

### Core Modules

**`main.py`**
- 3D camera system and controls
- Pygame-based rendering engine
- User interface and interaction handling
- Animation and time management

**`planet_data.py`**
- Keplerian orbital element data for all planets
- Orbital mechanics calculations (Kepler's equation solving)
- Coordinate transformations (orbital to Cartesian)
- Orbit path generation for visualization

## Planetary Data

The simulator includes accurate orbital elements for all planets:

| Planet  | Semi-major Axis (AU) | Eccentricity | Orbital Period (days) |
|---------|---------------------|--------------|----------------------|
| Mercury | 0.387               | 0.206        | 88.0                 |
| Venus   | 0.723               | 0.007        | 224.7                |
| Earth   | 1.000               | 0.017        | 365.3                |
| Mars    | 1.524               | 0.093        | 687.0                |
| Jupiter | 5.203               | 0.048        | 4332.6               |
| Saturn  | 9.555               | 0.056        | 10759.2              |
| Uranus  | 19.218              | 0.046        | 30688.5              |
| Neptune | 30.110              | 0.009        | 60182.0              |

## Educational Applications

This visualiser is perfect for:
- **Astronomy Education**: Understanding orbital mechanics and planetary motion
- **Historical Events**: Viewing planetary positions during significant dates
- **Mission Planning**: Visualizing spacecraft launch windows
- **Astronomical Phenomena**: Exploring conjunctions and alignments

## Limitations

- Simplified two-body orbital mechanics (no perturbations)
- No moons or asteroids included
- Planetary sizes not to scale (enhanced for visibility)
- Long-term accuracy decreases for dates far from J2000.0 epoch

## Acknowledgments

- NASA JPL for orbital element data
- Pygame community for the graphics framework
- Astronomical community for orbital mechanics resources

---

**Explore the universe from your computer! 🚀**