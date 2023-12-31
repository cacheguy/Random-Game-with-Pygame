import pygame as pg
import pygplus as pgp

from .constants import *
from .utils import get_offsets_from_rect, load_spritesheet, lerp

from typing import List
from pathlib import Path


def init_nodes(engine):
    Node.engine = engine

class Node:
    engine = None

class Sprite(Node):
    _loaded_resources = False
    _rotate_cache = {}
    def __init__(self, surface: pg.Surface=None):
        self.screen = self.engine.screen
        self.draw_rect_offset = (0,0)
        self.shape_type = None

        self.movement = pg.Vector2(0,0)

        self.opacity = 255
        self.angle = 0
        self.scale = 1

        self.pos = [0,0]  # Topleft
        self.old_pos = list(self.pos)

        if surface is not None:
            self.surface = surface
            self.set_size_from_surface(self.surface)
        else:
            self.surface = None
            self.size = [0,0]

        self.spritelists = []

        self.use_rotate_cache = False

        if not self.__class__._loaded_resources:
            self.__class__._loaded_resources = True
            self.load_resources()

    def set_size_from_surface(self, surface):
        hitbox_rect = surface.get_bounding_rect()
        self.size = list(hitbox_rect.size)
        self.draw_rect_offset = -hitbox_rect.topleft[0], -hitbox_rect.topleft[1]

    def load_resources(self):
        pass

    @property
    def left(self):
        return self.rect().left
    @left.setter
    def left(self, value):
        rect = self.rect()
        rect.left = value
        self.pos = list(rect.topleft)

    @property
    def right(self):
        return self.rect().right
    @right.setter
    def right(self, value):
        rect = self.rect()
        rect.right = value
        self.pos = list(rect.topleft)

    @property
    def top(self):
        return self.rect().top
    @top.setter
    def top(self, value):
        rect = self.rect()
        rect.top = value
        self.pos = list(rect.topleft)

    @property
    def bottom(self):
        return self.rect().bottom
    @bottom.setter
    def bottom(self, value):
        rect = self.rect()
        rect.bottom = value
        self.pos = list(rect.topleft)

    @property
    def centerx(self):
        return self.rect().centerx
    @centerx.setter
    def centerx(self, value):
        rect = self.rect()
        rect.centerx = value
        self.pos = list(rect.topleft)

    @property
    def centery(self):
        return self.rect().centery
    @centery.setter
    def centery(self, value):
        rect = self.rect()
        rect.centery = value
        self.pos = list(rect.topleft)

    @property
    def angle(self):
        return self._angle
    
    @angle.setter
    def angle(self, value):
        self._angle = value%360

    def rect(self) -> pg.Rect:
        """The actual rect of the sprite. Useful for collision detection and more."""
        return pg.Rect(round(self.pos[0]), round(self.pos[1]), round(self.size[0]), round(self.size[1]))
    
    def draw_rect(self) -> pg.Rect:
        """The rect of the surface that will be drawn."""
        rect = self.surface.get_rect()
        rect.topleft = [round(self.pos[0]), round(self.pos[1])]
        rect.x += self.draw_rect_offset[0]
        rect.y += self.draw_rect_offset[1]
        return rect

    def on_screen(self, rect):
        return not (rect.right< 0 or rect.left > self.engine.screen_width or 
                    rect.bottom < 0 or rect.top > self.engine.screen_height)
            
    def update(self): 
        self.reset_old_pos()

    def raw_draw(self):
        draw_rect_to_cam = self.draw_rect()
        draw_rect_to_cam.topleft = self.engine.rel_to_camera(draw_rect_to_cam.topleft)

        if not self.angle == 0:
            if self.use_rotate_cache:
                # Cache the rotated surfaces for faster rotations
                r_angle = round(self.angle)%360
                if (info := (self.surface, r_angle)) in self._rotate_cache:
                    surface = self.__class__._rotate_cache[info]
                else:
                    surface = pg.transform.rotate(self.surface, r_angle)
                    self.__class__._rotate_cache[info] = surface
            else:
                surface = pg.transform.rotate(self.surface, self.angle)
            rect = surface.get_rect()
            rect.center = draw_rect_to_cam.center
            pos = rect.topleft
        else:
            surface = self.surface
            rect = draw_rect_to_cam
            pos = draw_rect_to_cam.topleft
        if self.opacity == 0:
            return
        elif not self.opacity == 255:
            surface = surface.copy()
            surface.set_alpha(self.opacity)

        if self.on_screen(rect):
            self.screen.blit(surface, pos)

    def draw(self):
        alpha = self.engine.accumulator/pgp.TARGET_DT
        old = self.pos
        if pgp.FIXED_TIMESTEP_SETTINGS["interpolate"]:
            self.pos = [
                lerp(self.old_pos[0], self.pos[0], alpha),
                lerp(self.old_pos[1], self.pos[1], alpha)
            ]
        self.raw_draw()
        self.pos = old

    def kill(self):
        for spritelist in self.spritelists.copy():
            spritelist.remove(self)

    def add_spritelist(self, spritelist):
        self.spritelists.append(spritelist)

    def remove_spritelist(self, spritelist):
        self.spritelists.remove(spritelist)

    def reset_old_pos(self):
        self.old_pos = list(self.pos)


DYNAMIC_TEMPLATE = [
    "top_left", "top", "top_right", "top_left_right", "slope2",
    "left", "none", "right", "left_right", "slope2_bottom", 
    "bottom_left", "bottom", "bottom_right", "bottom_left_right", "slope1",
    "left_top_bottom", "top_bottom", "right_top_bottom", "top_bottom_left_right", "slope1_bottom"
]


loaded_dynamics = False
def load_dynamic_surfaces():
    global loaded_dynamics, DYNAMIC_NAME_TO_SURFACES
    if not loaded_dynamics:
        loaded_dynamics = True
        DYNAMIC_NAME_TO_SURFACES = {
            "grass": load_spritesheet(Path("assets/tiles/grass.png"))
        }


class SpriteList(Node):
    def __init__(self):
        self.tile_size = 16*pgp.SCALE
        self.hash_tilemap = None
        self.sprites: List[Sprite] = []

    def hash_point(self, point):
        return point[0]//self.tile_size, point[1]//self.tile_size

    def load_hash_tilemap(self):
        self.hash_tilemap = {}
        for tile in self.sprites:
            grid_pos = self.hash_point(tile.pos)
            self.hash_tilemap[grid_pos] = tile

    def append(self, sprite):
        if not isinstance(sprite, Sprite):
            raise TypeError("Argument is not an instance of Sprite")
        self.sprites.append(sprite)
        sprite.add_spritelist(self)

    def remove(self, sprite):
        if not isinstance(sprite, Sprite):
            raise TypeError("Argument is not an instance of Sprite")
        self.sprites.remove(sprite)
        sprite.remove_spritelist(self)

    def empty(self):
        for sprite in self.sprites.copy():
            self.sprites.remove(sprite)
            sprite.remove_spritelist(self)

    def has(self, sprite):
        return sprite in self.sprites
    
    def __iter__(self):
        return iter(self.sprites)
    
    def __contains__(self, sprite):
        return self.has(sprite)
    
    def __bool__(self):
        return bool(self.sprites)

    def __len__(self):
        return len(self.sprites)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def get_nearby_tiles_at(self, rect):
        if self.hash_tilemap is None:
            raise Exception("Hash tilemap has not been loaded yet")
        grid_pos = self.hash_point(rect.topleft)
        offsets = get_offsets_from_rect(rect, self.tile_size)
        tiles = []
        for offset in offsets:
            grid_offsetted = grid_pos[0]+offset[0], grid_pos[1]+offset[1]
            if self.hash_tilemap.get(grid_offsetted):
                tiles.append(self.hash_tilemap[grid_offsetted])
        return tiles
    
    def get_surrounding_directions(self, grid_pos):
        if self.hash_tilemap is None:
            raise Exception("Hash tilemap has not been loaded yet")
        return {
            "top": not (grid_pos[0], grid_pos[1]-1) in self.hash_tilemap, 
            "bottom": not (grid_pos[0], grid_pos[1]+1) in self.hash_tilemap, 
            "left": not (grid_pos[0]-1, grid_pos[1]) in self.hash_tilemap, 
            "right": not (grid_pos[0]+1, grid_pos[1]) in self.hash_tilemap
        }

    def draw(self):
        if not self.hash_tilemap is None:
            cam_x, cam_y = self.engine.camera_position
            r_cam_pos = round(cam_x), round(cam_y)
            for x in range(r_cam_pos[0]//self.tile_size, (r_cam_pos[0]+Node.engine.screen_width)//self.tile_size+1):
                for y in range(r_cam_pos[1]//self.tile_size, (r_cam_pos[1]+Node.engine.screen_height)//
                               self.tile_size+1):
                    grid_pos = x,y
                    if grid_pos in self.hash_tilemap:
                        self.hash_tilemap[grid_pos].draw()
        else:
            for sprite in self.sprites:
                sprite.draw()

    def set_dynamic_surfaces(self):
        if self.hash_tilemap is None:
            raise Exception("Hash tilemap has not been loaded yet")
        if not loaded_dynamics:
            load_dynamic_surfaces()
        for grid_pos, tile in self.hash_tilemap.items():
            if not "dynamic_type" in tile.properties:
                continue

            dynamic_type = None
            if tile.shape_type == "slope1":
                dynamic_type = "slope1"

            elif tile.shape_type == "slope2":
                dynamic_type = "slope2"
            
            elif (pos := (grid_pos[0], grid_pos[1]-1)) in self.hash_tilemap:
                if self.hash_tilemap[pos].shape_type == "slope1":
                    dynamic_type = "slope1_bottom"

                elif self.hash_tilemap[pos].shape_type == "slope2":
                    dynamic_type = "slope2_bottom"

            if dynamic_type is None:
                directions = sorted([key for key, value in self.get_surrounding_directions(grid_pos).items() if value])
                if len(directions) == 0:
                    dynamic_type = "none"
                for dynamic_dir in DYNAMIC_TEMPLATE:
                    if directions == sorted(dynamic_dir.split("_")):
                        dynamic_type = dynamic_dir

            if dynamic_type is None:
                raise Exception("Uknown dynamic type")
            
            surfaces = DYNAMIC_NAME_TO_SURFACES[tile.properties["dynamic_type"]]
            tile.surface = surfaces[DYNAMIC_TEMPLATE.index(dynamic_type)]


    def update(self):
        for sprite in self.sprites:
            sprite.update()