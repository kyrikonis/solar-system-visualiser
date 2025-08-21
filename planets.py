"""
Orbital elements and maths stay here

Elements are referenced to the J2000.0 epoch and are approximate mean 

Symbols / fields:
- a (AU): semi-major axis
- e: eccentricity
- i (deg): inclination to ecliptic
- Ω (deg): longitude of ascending node
- ω (deg): argument of perihelion
- M0 (deg): mean anomaly at epoch (J2000.0)
- period (days): sidereal orbital period

Rotation to heliocentric ecliptic coordinates (x,y,z) uses the standard
3-1-3 Euler sequence: Ω, i, ω.
"""


import math
from datetime import datetime, timedelta
from typing import Tuple


# J2000.0 epoch (UTC-compatible representation)
EPOCH_J2000 = datetime(2000, 1, 1, 12, 0, 0)


# approx mean orbital elements at J2000.0 and AU
# values from JPL/NASA sources
# for serious work, query JPL Horizons for osculating elements per date
PLANETS = {
"Mercury": {"a": 0.387098, "e": 0.205630, "i": 7.0049, "Ω": 48.331, "ω": 29.124, "M0": 174.796, "period": 87.969},
"Venus": {"a": 0.723332, "e": 0.006772, "i": 3.3947, "Ω": 76.680, "ω": 54.884, "M0": 50.115, "period": 224.701},
"Earth": {"a": 1.000000, "e": 0.016710, "i": 0.0000, "Ω": -11.260, "ω": 114.207, "M0": 357.517, "period": 365.256},
"Mars": {"a": 1.523679, "e": 0.093400, "i": 1.8506, "Ω": 49.558, "ω": 286.503, "M0": 19.373, "period": 686.980},
"Jupiter": {"a": 5.20260, "e": 0.048498, "i": 1.3033, "Ω": 100.464, "ω": 273.867, "M0": 20.020, "period": 4332.589},
"Saturn": {"a": 9.55491, "e": 0.055508, "i": 2.4852, "Ω": 113.665, "ω": 339.392, "M0": 317.020, "period": 10759.22},
"Uranus": {"a": 19.2184, "e": 0.046295, "i": 0.7730, "Ω": 74.006, "ω": 96.998, "M0": 142.238, "period": 30688.5},
"Neptune": {"a": 30.1104, "e": 0.008988, "i": 1.7700, "Ω": 131.784, "ω": 272.846, "M0": 256.228, "period": 60182.0},
}

def days_since_epoch(date: datetime) -> float:
#  days elapsed since J2000.0
    delta = date - EPOCH_J2000
    return delta.days + delta.seconds / 86400 + delta.microseconds / 86400e6

def mean_anomaly_at(elements: dict, date: datetime) -> float:
# mean anomaly at given date
    M0 = elements["M0"]
    T = elements["period"]