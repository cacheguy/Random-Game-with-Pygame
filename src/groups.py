import pygame as pg

from sprites import Sprite
from constants import *
from utils import get_offsets_from_rect

from typing import List


class SpriteList:
    def __init__(self):
        self.tile_size = 16*SCALE
        self.hash_tilemap = None
        self.sprites: List[Sprite] = []

    def load_hash_tilemap(self):
        self.hash_tilemap = {}
        for tile in self.sprites:
            grid_pos = tile.pos[0]//self.tile_size, tile.pos[1]//self.tile_size
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
        grid_pos = rect.topleft[0]//self.tile_size, rect.topleft[1]//self.tile_size
        offsets = get_offsets_from_rect(rect, self.tile_size)
        tiles = []
        for offset in offsets:
            grid_offsetted = grid_pos[0]+offset[0], grid_pos[1]+offset[1]
            if self.hash_tilemap.get(grid_offsetted):
                tiles.append(self.hash_tilemap[grid_offsetted])
        return tiles

    def draw(self, camera_pos=None):
        if not self.hash_tilemap is None:
            if camera_pos is None:
                raise TypeError("camera_pos argument required for tile grid rendering")
            r_camera_pos = round(camera_pos[0]), round(camera_pos[1])
            for x in range(r_camera_pos[0]//self.tile_size, (r_camera_pos[0]+SCREEN_WIDTH)//self.tile_size+1):
                for y in range(r_camera_pos[1]//self.tile_size, (r_camera_pos[1]+SCREEN_HEIGHT)//self.tile_size+1):
                    grid_pos = x,y
                    if grid_pos in self.hash_tilemap:
                        self.hash_tilemap[grid_pos].draw()
        else:
            for sprite in self.sprites:
                sprite.draw()

    def update(self):
        for sprite in self.sprites:
            sprite.update()