"""
Solar System Data Visualiser core code.

Interactive Visualiser (2D) of planet's positions for a chosen date.
Uses NASA/JPL-style Keplerian elements reference to J2000.0.
--------

Controls:

Left / Right : step ±1 day
[ / ] : step ±30 days
, / . : step ±1 hour
- / = : zoom out / zoom in
T : jump to today
Space : pause/resume auto-advance
H : toggle help overlay
R : reset camera & time step
Esc / Q : quit
---------
"""

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple


import pygame

