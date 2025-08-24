
"""
Consists of all orbital mechanics calculations.

Inclused conversion from Keplerian orbital elements to  Cartesian coordinates for planetary positions. 
Elements are based on J2000.0 epoch values suitable for educational visualisation.

"""

import math
from datetime import datetime
from typing import Tuple, List, Dict

J2000_EPOCH = datetime(2000, 1, 1, 12, 0, 0)

# Planetary orbital elements at J2000.0
# a: semi-major axis (AU)
# e: eccentricity 
# i: inclination (degrees)
# Omega: longitude of ascending node (degrees)
# omega: argument of perihelion (degrees)
# M0: mean anomaly at epoch (degrees)
# period: orbital period (days)
PLANETS = {
    "Mercury": {
        "a": 0.387098, "e": 0.205630, "i": 7.0049,
        "Omega": 48.331, "omega": 29.124, "M0": 174.796, 
        "period": 87.969
    },
    "Venus": {
        "a": 0.723332, "e": 0.006772, "i": 3.3947,
        "Omega": 76.680, "omega": 54.884, "M0": 50.115,
        "period": 224.701
    },
    "Earth": {
        "a": 1.000000, "e": 0.016710, "i": 0.0000,
        "Omega": -11.260, "omega": 114.207, "M0": 357.517,
        "period": 365.256
    },
    "Mars": {
        "a": 1.523679, "e": 0.093400, "i": 1.8506,
        "Omega": 49.558, "omega": 286.503, "M0": 19.373,
        "period": 686.980
    },
    "Jupiter": {
        "a": 5.20260, "e": 0.048498, "i": 1.3033,
        "Omega": 100.464, "omega": 273.867, "M0": 20.020,
        "period": 4332.589
    },
    "Saturn": {
        "a": 9.55491, "e": 0.055508, "i": 2.4852,
        "Omega": 113.665, "omega": 339.392, "M0": 317.020,
        "period": 10759.22
    },
    "Uranus": {
        "a": 19.2184, "e": 0.046295, "i": 0.7730,
        "Omega": 74.006, "omega": 96.998, "M0": 142.238,
        "period": 30688.5
    },
    "Neptune": {
        "a": 30.1104, "e": 0.008988, "i": 1.7700,
        "Omega": 131.784, "omega": 272.846, "M0": 256.228,
        "period": 60182.0
    },
}


def days_since_j2000(date: datetime) -> float:
    """Calculate days elapsed since J2000.0 epoch"""
    delta = date - J2000_EPOCH
    return delta.days + delta.seconds / 86400.0


def mean_anomaly(elements: Dict, date: datetime) -> float:
    """
    Calculate mean anomaly at given date.
    
    The mean anomaly increases linearly with time, representing
    where the planet would be if it moved at constant speed.
    """
    M0 = elements["M0"]
    period = elements["period"]
    days = days_since_j2000(date)
    
    # Mean motion (degrees per day)
    n = 360.0 / period
    
    # Current mean anomaly
    M = (M0 + n * days) % 360.0
    return M


def solve_kepler(M_deg: float, eccentricity: float) -> float:
    """
    Solve Kepler's equation: M = E - e*sin(E)
    
    Uses Newton-Raphson iteration to find eccentric anomaly E
    given mean anomaly M and eccentricity e.
    
    Returns E in radians.
    """
    # Convert to radians and normalize to [-pi, pi]
    M = math.radians(M_deg % 360.0)
    M = (M + math.pi) % (2 * math.pi) - math.pi
    
    # Initial guess - use M for low eccentricity, pi for high
    E = M if eccentricity < 0.8 else math.pi
    
    # Newton-Raphson iteration
    for _ in range(10):  # Usually converges in 3-5 iterations
        f = E - eccentricity * math.sin(E) - M
        f_prime = 1.0 - eccentricity * math.cos(E)
        
        correction = f / f_prime
        E -= correction
        
        if abs(correction) < 1e-10:
            break
    
    return E


def true_anomaly(E: float, eccentricity: float) -> float:
    """
    Calculate true anomaly from eccentric anomaly.
    
    The true anomaly is the actual angle from perihelion
    to the planet's current position.
    """
    # Use half-angle formula for better numerical stability
    half_E = E / 2.0
    sqrt_ratio = math.sqrt((1 + eccentricity) / (1 - eccentricity))
    
    nu = 2.0 * math.atan2(
        sqrt_ratio * math.sin(half_E),
        math.cos(half_E)
    )
    
    return nu


def elements_to_xyz(elements: Dict, date: datetime) -> Tuple[float, float, float]:
    """
    Convert orbital elements to 3D position.
    
    Returns (x, y, z) in AU, with the Sun at origin.
    Coordinate system is J2000 ecliptic.
    """
    # Unpack elements
    a = elements["a"]  # semi-major axis
    e = elements["e"]  # eccentricity
    i = math.radians(elements["i"])  # inclination
    Omega = math.radians(elements["Omega"])  # ascending node
    omega = math.radians(elements["omega"])  # perihelion argument
    
    # Calculate anomalies
    M = mean_anomaly(elements, date)
    E = solve_kepler(M, e)
    nu = true_anomaly(E, e)
    
    # Distance from Sun
    r = a * (1 - e * math.cos(E))
    
    # Position in orbital plane
    x_orbital = r * math.cos(nu)
    y_orbital = r * math.sin(nu)
    
    # Rotate to ecliptic coordinates
    # This is a 3-1-3 Euler rotation: Omega, i, omega
    u = omega + nu  # argument of latitude
    
    cos_u = math.cos(u)
    sin_u = math.sin(u)
    cos_Omega = math.cos(Omega)
    sin_Omega = math.sin(Omega)
    cos_i = math.cos(i)
    sin_i = math.sin(i)
    
    # Apply rotation matrix
    x = r * (cos_Omega * cos_u - sin_Omega * sin_u * cos_i)
    y = r * (sin_Omega * cos_u + cos_Omega * sin_u * cos_i)
    z = r * (sin_u * sin_i)
    
    return x, y, z


def elements_to_xy(elements: Dict, date: datetime) -> Tuple[float, float, float]:
    """
    Convenience function for 2D visualization.
    Returns same as elements_to_xyz but named for clarity.
    """
    return elements_to_xyz(elements, date)


def generate_orbit_points(elements: Dict, num_points: int = 200) -> List[Tuple[float, float, float]]:
    """
    Generate points along a complete orbit.
    
    Creates a smooth orbital path by sampling positions
    at regular true anomaly intervals.
    """
    a = elements["a"]
    e = elements["e"]
    i = math.radians(elements["i"])
    Omega = math.radians(elements["Omega"])
    omega = math.radians(elements["omega"])
    
    points = []
    
    # Sample the orbit uniformly in true anomaly
    for j in range(num_points + 1):
        # True anomaly from 0 to 2π
        nu = 2 * math.pi * j / num_points
        
        # Distance using orbit equation
        r = a * (1 - e * e) / (1 + e * math.cos(nu))
        
        # Convert to ecliptic coordinates
        u = omega + nu
        
        cos_u = math.cos(u)
        sin_u = math.sin(u)
        cos_Omega = math.cos(Omega)
        sin_Omega = math.sin(Omega)
        cos_i = math.cos(i)
        sin_i = math.sin(i)
        
        x = r * (cos_Omega * cos_u - sin_Omega * sin_u * cos_i)
        y = r * (sin_Omega * cos_u + cos_Omega * sin_u * cos_i)
        z = r * (sin_u * sin_i)
        
        points.append((x, y, z))
    
    return points