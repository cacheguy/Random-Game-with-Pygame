import pygame as pg
import pytiled_parser

from constants import *
from utils import load_spritesheet, load_image, relative_to_camera
from sprites import Tile, CoinTile

from pathlib import Path
import time

DEFAULT_CLASS = Tile
TYPES_TO_TILES = {
    "coin": {
        "class": CoinTile
    },
}


class Tilemap:
    def __init__(self, filename: Path):
        tilemap = pytiled_parser.parse_map(filename)
        tile_size = 16
        id_to_tile_info = {}
        for firstgid, tileset in tilemap.tilesets.items():
            if tileset.image is None:
                for tileid, tile in tileset.tiles.items():
                    id_to_tile_info[tileid+firstgid] = {
                        "surface": load_image(tile.image),  # TODO: Add caching
                        "properties": tile.properties
                    }
            else:
                surfaces = load_spritesheet(tileset.image)
                for index, surface in enumerate(surfaces):
                    id_to_tile_info[index+firstgid] = {"surface": surface, "properties": {}}
                    for tileid, tile in tileset.tiles.items():
                        if index == tileid:
                            id_to_tile_info[index+firstgid]["properties"] = tile.properties
        self.layers = {}
        for layer in tilemap.layers:
            tiles_data = layer.data
            self.layers[layer.name] = []
            for y, row in enumerate(tiles_data):
                for x, num in enumerate(row):
                    if num == 0: continue
                    tile_info = id_to_tile_info[num]
                    properties = tile_info["properties"]
                    if properties is None:
                        properties = {}

                    # tile_class = TYPES_TO_TILES[properties.get("tile_type")]

                    custom_class = Tile
                    if properties:
                        tile_type = properties.get("tile_type")
                        if TYPES_TO_TILES.get(tile_type):
                            custom_class = TYPES_TO_TILES.get(tile_type)["class"]

                    tile_object = custom_class(layer=self.layers[layer.name], 
                                               surface=tile_info["surface"], 
                                               pos=[x*tile_size*SCALE, y*tile_size*SCALE], 
                                               properties=properties)

                    if properties:
                        if properties.get("shape_type") == "slope1":
                            tile_object.shape_type = "slope1"
                        elif properties.get("shape_type") == "slope2":
                            tile_object.shape_type = "slope2"
                    self.layers[layer.name].append(tile_object)

        self.hash_tilemap = {}
        for tile in self.layers["Walls"]:
            grid_pos = tile.pos[0]//(tile_size*SCALE), tile.pos[1]//(tile_size*SCALE)
            self.hash_tilemap[grid_pos] = tile

    def get_nearby_tiles_at(self, pos):
        tile_size = 16
        grid_pos = pos[0]//(tile_size*SCALE), pos[1]//(tile_size*SCALE)
        offsets = [
            (0,0), (1,0),
            (0,1), (1,1),
            (0,2), (1,2)
        ]
        tiles = []
        for offset in offsets:
            grid_offsetted = grid_pos[0]+offset[0], grid_pos[1]+offset[1]
            if self.hash_tilemap.get(grid_offsetted):
                tiles.append(self.hash_tilemap[grid_offsetted])
        return tiles

    
    def update(self, *args, **kwargs):
        for layer in self.layers.values():
            for tile in layer:
                tile.update()

    def draw(self, camera_pos):
        for name, layer in self.layers.items():
            if name == "Walls": continue
            for tile in layer:
                tile.draw()
        
        tile_size = 16*SCALE
        r_camera_pos = round(camera_pos[0]), round(camera_pos[1])
        for x in range(r_camera_pos[0]//tile_size, (r_camera_pos[0]+SCREEN_WIDTH)//tile_size+1):
            for y in range(r_camera_pos[1]//tile_size, (r_camera_pos[1]+SCREEN_HEIGHT)//tile_size+1):
                grid_pos = x,y
                if grid_pos in self.hash_tilemap:
                    self.hash_tilemap[grid_pos].draw()