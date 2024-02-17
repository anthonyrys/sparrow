import inspect
import pygame
import math
import sys

# General
def generate_import_dict(*excludes):
    if not excludes:
        excludes = ()

    defaults = (
        'PolygonParticle',
        'Sfx', 'Fonts', 'Sprite'
    )

    name = sys.modules[inspect.getmodule(inspect.stack()[1][0]).__name__]

    return {
        k: v for k, v in (c for c in inspect.getmembers(name, inspect.isclass) if c[0] not in excludes and c[0] not in defaults)
    }

# Pygame
def scale(image, sx, sy=None):
    if not sy: sy = sx
    return pygame.transform.scale(image, (image.get_width() * sx, image.get_height() * sy)).convert_alpha()

# Math
def clamp(v, mi, mx):
    return max(mi, min(v, mx))

def get_distance(p1, p2):
    rx = abs(p1[0] - p2[0])
    ry = abs(p1[1] - p2[1])

    return math.sqrt(((rx **2) + (ry **2)))
