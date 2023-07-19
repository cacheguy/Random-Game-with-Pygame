import pygame as pg

from pathlib import Path

from constants import *

def load_image(filename: Path) -> pg.Surface:
    surface = pg.image.load(filename).convert()
    surface = pg.transform.scale_by(surface, SCALE)
    surface.set_colorkey((0,0,0))
    return surface

def load_spritesheet(filename: Path, count: int = -1):
    tile_size = 16
    spritesheet = pg.image.load(filename).convert()
    spritesheet.set_colorkey((0,0,0))

    rows = spritesheet.get_height()//tile_size
    columns = spritesheet.get_width()//tile_size
    surfaces = []

    i = 0
    for row in range(rows):
        for column in range(columns):
            pos = column*tile_size, row*tile_size
            surface = spritesheet.subsurface(pos, (tile_size, tile_size))
            surface = pg.transform.scale_by(surface, SCALE)
            surfaces.append(surface)
            i += 1
            if i >= count and not count==-1: break
        if i >= count and not count==-1: break

    return surfaces


def relative_to_camera(pos, camera_position):
    return [pos[0] - camera_position[0], pos[1] - camera_position[1]]

def lerp(num1, num2, alpha):
    return num1 + (alpha * (num2 - num1))