import pygame as pg

from constants import *
from utils import *

from pathlib import Path
import math
import random
import time


# class Group(pg.sprite.Group):
#     def draw(self, surface, bgsurf=None, special_flags=0):
#         sprites = self.sprites()
#         for sprite in sprites:
#             sprite.draw()

class Sprite():
    engine = None
    def __init__(self, surface: pg.Surface=None):
        self.screen = self.engine.screen
        self.draw_rect_offset = (0,0)
        self.shape_type = None

        self.change_x = 0
        self.change_y = 0

        self.opacity = 255
        self.angle = 0
        self.scale = 1

        self.pos = [0,0]  # Topleft

        if surface is not None:
            self.surface = surface
            self.size = list(self.surface.get_rect().size)
        else:
            self.surface = None
            self.size = [0,0]

    @classmethod
    def set_engine(cls, engine):
        cls.engine = engine

    @property
    def rect(self):
        """The actual rect of the sprite. Useful for collision detection and more."""
        return pg.Rect(round(self.pos[0]), round(self.pos[1]), round(self.size[0]), round(self.size[1]))
    
    @property
    def draw_rect(self) -> pg.Rect:
        """The rect of the surface that will be drawn."""
        rect = self.surface.get_rect()
        rect.topleft = [round(self.pos[0]), round(self.pos[1])]
        rect.x += self.draw_rect_offset[0]
        rect.y += self.draw_rect_offset[1]
        return rect

    def on_screen(self, rect):
        return not (rect.right< 0 or rect.left > SCREEN_WIDTH or rect.bottom < 0 or rect.top > SCREEN_HEIGHT)
            
    def update(self): 
        pass

    def draw(self):
        draw_rect_to_cam = self.draw_rect
        draw_rect_to_cam.topleft = relative_to_camera(draw_rect_to_cam.topleft, self.engine.camera_position)

        if not self.angle == 0:
            surface = pg.transform.rotate(self.surface, self.angle)
            rect = surface.get_rect()
            rect.center = draw_rect_to_cam.center
            pos = rect.topleft
        else:
            surface = self.surface
            rect = draw_rect_to_cam
            pos = draw_rect_to_cam.topleft

        if self.on_screen(rect):
            self.screen.blit(surface, pos)


class Tile(Sprite):
    def __init__(self, layer, surface: pg.Surface, pos=[0,0], properties={}, animated=False):
        super().__init__(surface)
        self.layer = layer
        self.properties = properties
        self.tile_type = self.properties.get("tile_type")
        self.animated = animated
        self.pos = pos

    def get_surrounding_tiles(self):
        pass

    def kill(self):
        self.layer.remove(self)


class MovingTile(Sprite): pass


class CoinTile(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_y = self.pos[1]
        self.frames_passed = 0

    def update(self):
        self.frames_passed += 1
        self.pos[1] = self.original_y + (math.sin(self.frames_passed/21) * 7)


MAX_JUMP_COUNT = 10
JUMP_SPEED = 14

ACCELERATION = 1.15
DEACCELERATION = 1.15
MAX_WALK_SPEED = 8.25

class Player(Sprite):
    def __init__(self):
        super().__init__()
        self.surface = load_image(Path("assets/player/idle1.png"))
        self.surfaces = []
        self.surfaces.append(self.surface)
        self.surfaces.append(pg.transform.flip(self.surface, True, False))

        self.pos = [0,0]
        self.hitbox_rect = load_image(Path("assets/player/hitbox.png")).get_bounding_rect()
        self.size = list(self.hitbox_rect.size)
        self.draw_rect_offset = -self.hitbox_rect.topleft[0], -self.hitbox_rect.topleft[1]

        self.collisions = {"top": False, "left": False, "right": False, "bottom": False}
        self.face_direction = RIGHT_FACING

        self.can_jump = True
        self.stop_jump = False
        self.jump_count = 0
        self.gravity = 1.1

        self.old_pos = list(self.pos)
        self.sounds = {}
        self.sounds["jump"] = pg.mixer.Sound(Path("assets/sounds/jump.wav"))
        self.sounds["spring"] = pg.mixer.Sound(Path("assets/sounds/spring.wav"))
        self.sounds["coin"] = pg.mixer.Sound(Path("assets/sounds/coin.wav"))
        self.god_mode = False
        self.on_slope = False
    
    def move_on_god_mode(self):
        speed = 18
        if self.engine.keys["right"] and not self.engine.keys["left"]: self.change_x = speed
        elif self.engine.keys["left"] and not self.engine.keys["right"]: self.change_x = -speed
        else: self.change_x = 0
        if self.engine.keys["down"] and not self.engine.keys["up"]: self.change_y = speed
        elif self.engine.keys["up"] and not self.engine.keys["down"]: self.change_y = -speed
        else: self.change_y = 0

    def move_on_inputs(self):
        if self.god_mode:
            self.move_on_god_mode()
            return
        self.can_jump = self.collisions["bottom"]

        if not self.engine.keys["up"]:
            if self.can_jump:
                self.stop_jump = False
                self.jump_count = 0
            else:
                self.stop_jump = True

        if (self.can_jump or self.jump_count > 0) \
            and self.jump_count < MAX_JUMP_COUNT \
            and self.engine.keys["up"] \
            and not self.stop_jump:
            self.change_y = -JUMP_SPEED
            if self.jump_count == 0:
                self.sounds["jump"].play()
            self.jump_count += 1

        if self.engine.keys["right"] and not self.engine.keys["left"]:
            self.change_x += ACCELERATION
        elif self.engine.keys["left"] and not self.engine.keys["right"]:
            self.change_x -= ACCELERATION
        else:
            if self.change_x > 0:
                self.change_x -= DEACCELERATION
                if self.change_x < 0:
                    self.change_x = 0
            elif self.change_x < 0:
                self.change_x += DEACCELERATION
                if self.change_x > 0:
                    self.change_x = 0

        if self.change_x > MAX_WALK_SPEED:
            self.change_x = MAX_WALK_SPEED
        elif self.change_x < -MAX_WALK_SPEED:
            self.change_x = -MAX_WALK_SPEED

    def get_collisions(self, tiles):
        hit_list = []
        for tile in tiles:
            if self.rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list

    def apply_collisions(self):
        if self.on_slope and not self.change_y < 0:
            self.change_y += 10
        if not self.god_mode: self.change_y += self.gravity
        if self.change_y > 30: self.change_y = 30
        self.collisions = {"top": False, "left": False, "right": False, "bottom": False}
        walls = self.engine.tilemap.layers["Walls"]

        self.pos[0] += self.change_x
        hit_list = self.get_collisions(self.engine.tilemap.get_nearby_tiles_at(self.pos))
        rect = self.rect
        for tile in hit_list:
            if not tile.shape_type in ("slope1", "slope2"):
                if self.change_x > 0 and rect.right>=tile.rect.left and rect.left<=tile.rect.left:
                    rect.right = tile.rect.left
                    self.collisions["right"] = True
                elif self.change_x < 0 and tile.rect.right>=rect.left and tile.rect.left<=rect.left:
                    rect.left = tile.rect.right
                    self.collisions["left"] = True
            else: 
                pass
                # TODO This code prevents player from glitching up slopes when going in the opposite direction of the 
                # slope. e.g. player moves right into a slope2 tile. It currently causes some glitches when you slowly 
                # walk off slope1 tiles. Will fix later. For now, make sure there is a normal tile next to a slope tile

                # if tile.shape_type == "slope1":
                #     if self.change_x < 0 and tile.rect.right>=rect.left and tile.rect.left<=rect.left:
                #         rect.left = tile.rect.right
                #         self.collisions["left"] = True
                # elif tile.shape_type == "slope2":
                #     if self.change_x > 0 and rect.right>=tile.rect.left and rect.left<=tile.rect.left:
                #         rect.right = tile.rect.left
                #         self.collisions["right"] = True
        self.pos = list(rect.topleft)

        self.pos[1] += self.change_y
        hit_list = self.get_collisions(self.engine.tilemap.get_nearby_tiles_at(self.pos))
        rect = self.rect
        for tile in hit_list:
            if not tile.shape_type in ("slope1", "slope2"):
                if self.change_y > 0 and tile.rect.top<=rect.bottom and tile.rect.bottom>=rect.bottom:
                    rect.bottom = tile.rect.top
                    self.collisions["bottom"] = True
                elif self.change_y < 0 and rect.top<=tile.rect.bottom and rect.bottom>=tile.rect.bottom:
                    rect.top = tile.rect.bottom
                    self.collisions["top"] = True
            else:
                if tile.shape_type in ("slope1", "slope2"):
                    if self.change_y < 0 and rect.top<=tile.rect.bottom and rect.bottom>=tile.rect.bottom:
                        rect.top = tile.rect.bottom
                        self.collisions["top"] = True
        self.pos = list(rect.topleft)
        
        self.on_slope = False
        hit_list = self.get_collisions(self.engine.tilemap.get_nearby_tiles_at(self.pos))
        rect = self.rect 
        for tile in hit_list:
            if tile.shape_type in ("slope1", "slope2"):
                if tile.shape_type == "slope1":
                    pos_height = rect.right - tile.rect.left
                elif tile.shape_type == "slope2":
                    pos_height = tile.rect.right - rect.left
                
                # Add constraints
                pos_height = min(pos_height, tile.rect.height)
                pos_height = max(pos_height, 0)

                target_y = tile.rect.bottom - pos_height

                if rect.bottom > target_y:
                    rect.bottom = target_y
                    self.collisions["bottom"] = True
                    self.on_slope = True
        self.pos = list(rect.topleft)

        if self.collisions["bottom"] or self.collisions["top"]:
            self.change_y = 0

    def update(self):
        self.old_pos = list(self.pos)
        self.god_mode = self.engine.keys["g"]
        self.move_on_inputs()
        hit_list = self.get_collisions(self.engine.tilemap.layers["Objects"]) 
        for obj in hit_list:
            if obj.tile_type == "spring":
                rect = self.rect
                rect.bottom = obj.rect.top
                self.pos = list(rect.topleft)
                self.change_y = -32
                self.jump_count = MAX_JUMP_COUNT
                self.sounds["spring"].play()
            elif obj.tile_type == "coin":
                obj.kill()
                self.sounds["coin"].play()

        self.apply_collisions()

        if self.change_x > 0:
            self.face_direction = RIGHT_FACING
        elif self.change_x < 0:
            self.face_direction = LEFT_FACING

        self.surface = self.surfaces[self.face_direction]

    def draw(self):
        alpha = self.engine.accumulator/TARGET_DT
        old = self.pos
        self.pos = [
            lerp(self.old_pos[0], self.pos[0], alpha),
            lerp(self.old_pos[1], self.pos[1], alpha)
        ]
        super().draw()
        self.pos = old