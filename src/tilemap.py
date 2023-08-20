import pygame as pg
import pytiled_parser
import pytiled_parser.tiled_object

from constants import *
from utils import load_spritesheet, load_image
from sprites import Tile, CoinTile, Sprite, Enemy, RopeTile
from spritelists import SpriteList

from pathlib import Path
import time

DEFAULT_CLASS = Tile
TYPES_TO_TILES = {
    "coin": {
        "class": CoinTile
    },
    "rope": {
        "class": RopeTile
    }
}


class Tilemap:
    def __init__(self, filename: Path):
        tilemap = pytiled_parser.parse_map(filename)
        tile_size = 16
        id_to_tile_info = {}
        for firstgid, tileset in tilemap.tilesets.items():
            if tileset.image is None:
                # Collection of images
                for tileid, tile in tileset.tiles.items():
                    id_to_tile_info[tileid+firstgid] = {
                        "surface": load_image(tile.image),  # TODO: Add caching
                        "properties": tile.properties,
                    }
            else:
                # Spritesheet image
                surfaces = load_spritesheet(tileset.image)
                for index, surface in enumerate(surfaces):
                    id_to_tile_info[index+firstgid] = {"surface": surface, "properties": {}}
                    for tileid, tile in tileset.tiles.items():
                        if index == tileid:
                            id_to_tile_info[index+firstgid]["properties"] = tile.properties
        self.layers = {}
        for layer in tilemap.layers:
            self.layers[layer.name] = SpriteList()
            if isinstance(layer, pytiled_parser.TileLayer):
                tiles_data = layer.data
                for y, row in enumerate(tiles_data):
                    for x, num in enumerate(row):
                        if num == 0: continue
                        tile_info = id_to_tile_info[num]
                        properties = tile_info["properties"]
                        if properties is None:
                            properties = {}

                        custom_class = Tile
                        if properties:
                            tile_type = properties.get("tile_type")
                            if TYPES_TO_TILES.get(tile_type):
                                custom_class = TYPES_TO_TILES.get(tile_type)["class"]
                        pos = [x*tile_size*SCALE, 
                               y*tile_size*SCALE-(tile_info["surface"].get_height()-tile_size*SCALE)]
                        tile_object = custom_class(surface=tile_info["surface"], 
                                                   pos=pos, 
                                                   properties=properties)

                        if properties.get("shape_type") == "slope1":
                            tile_object.shape_type = "slope1"
                        elif properties.get("shape_type") == "slope2":
                            tile_object.shape_type = "slope2"
                        self.layers[layer.name].append(tile_object)

            elif isinstance(layer, pytiled_parser.ObjectLayer):
                for obj in layer.tiled_objects:
                   if isinstance(obj, pytiled_parser.tiled_object.Tile):
                        properties = {**id_to_tile_info[obj.gid]["properties"], **obj.properties}
                        if properties.get("tile_type") == "green_ninja":
                            b_left_id = properties["boundary_left"]
                            b_left_obj = [obj for obj in layer.tiled_objects if obj.id == b_left_id][0]
                            b_left_x = b_left_obj.coordinates[0] * SCALE
                            
                            b_right_id = properties["boundary_right"]
                            b_right_obj = [obj for obj in layer.tiled_objects if obj.id == b_right_id][0]
                            b_right_x = b_right_obj.coordinates[0] * SCALE

                            sprite = Enemy(b_left_x, b_right_x, id_to_tile_info[obj.gid]["surface"])
                            sprite.left, sprite.bottom = list(obj.coordinates)
                            sprite.left *= SCALE
                            sprite.bottom *= SCALE
                            self.layers[layer.name].append(sprite)
                   elif isinstance(obj, pytiled_parser.tiled_object.Point):
                       if "spawn" in obj.properties:
                           self.spawn_point = list(obj.coordinates)
                           self.spawn_point[0] *= SCALE
                           self.spawn_point[1] *= SCALE