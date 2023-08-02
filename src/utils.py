import pygame as pg

from pathlib import Path
import time

from constants import *

def load_image(filename: Path) -> pg.Surface:
    surface = pg.image.load(filename).convert()
    surface = pg.transform.scale_by(surface, SCALE)
    surface.set_colorkey((0,0,0))
    return surface

def rotate_surface(surface, angle, pivot, offset):
    raise NotImplementedError
    rotated_surface = pg.transform.rotate(surface, -angle)  # Rotate the image.
    rotated_offset = pg.Vector2(*offset).rotate(angle)  # Rotate the offset vector.
    # Add the offset vector to the center/pivot point to shift the rect.
    rect = rotated_surface.get_rect(center=pivot+rotated_offset)
    return rotated_surface, rect  # Return the rotated image and shifted rect.

def load_spritesheet(filename: Path, size=16, count: int = -1):
    tile_size = size
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

def get_offsets_from_rect(rect: pg.Rect, tile_size: int):
    grid_left = rect.left//tile_size-rect.topleft[0]//tile_size
    grid_right = rect.right//tile_size-rect.topleft[0]//tile_size+1
    grid_top = rect.top//tile_size-rect.topleft[1]//tile_size
    grid_bottom = rect.bottom//tile_size-rect.topleft[1]//tile_size+1
    offsets = []
    for x in range(grid_left, grid_right):
        for y in range(grid_top, grid_bottom):
            offsets.append((x,y))
    return offsets

def pallete_swap(surface: pg.Surface, old_color, new_color):
    new_surface = pg.Surface(surface.get_size())
    new_surface.fill(new_color)

    surface_copy = surface.copy()
    old_colorkey = surface_copy.get_colorkey()
    surface_copy.set_colorkey(old_color)
    new_surface.blit(surface_copy, (0,0))
    new_surface.set_colorkey(old_colorkey)

    return new_surface