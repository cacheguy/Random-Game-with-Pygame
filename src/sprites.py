import pygame as pg

from constants import *
from utils import *
from animations import AnimationStates
from spritelists import Sprite, SpriteList

from pathlib import Path
import math
import random
import sys
import time

# TODO Add interpolation
class Enemy(Sprite):
    def __init__(self, boundary_left, boundary_right, surface: pg.Surface=None):
        super().__init__(surface)
        s = load_spritesheet(Path("assets/enemy/enemy_idle.png"), size=24, count=4)
        idle_surfaces = [s[0], s[0], s[1], s[2], s[3], s[3], s[2], s[1]]
        self.idle_anim = AnimationStates(frames_dict={"default": idle_surfaces}, speed=0.135, use_RL=True)

        walk_surfaces = load_spritesheet(Path("assets/enemy/enemy_walk.png"), size=24, count=10)
        self.walk_anim = AnimationStates(frames_dict={"default": walk_surfaces}, speed=0.21, use_RL=True)

        fall_surfaces = load_spritesheet(Path("assets/enemy/enemy_fall.png"), size=24, count=3)
        self.fall_anim = AnimationStates(frames_dict={"default": fall_surfaces}, speed=0.35, use_RL=True)

        self.change_x = 3
        self.boundary_left = boundary_left
        self.boundary_right = boundary_right

        self.walking = random.choice([True, False])
        self.flip_timer = 0

    def update(self):
        super().update()
        self.flip_timer -= 1
        switched = False
        if self.right >= self.boundary_right or self.left <= self.boundary_left:
            self.change_x *= -1
            switched = True  # Make sure enemy doesn't flip direction twice
        if self.flip_timer <= 0 and not switched:
            self.flip_timer = 0
            self.walking = not self.walking
            self.flip_timer = random.randint(50, 300)
            if self.walking:
                if random.choice([True, False]):
                    self.change_x *= -1
        
        if self.walking:
            self.pos[0] += self.change_x
        self.pos[1] += self.change_y

        if self.change_x > 0:
            self.face_direction = RIGHT_FACING
        elif self.change_x < 0:
            self.face_direction = LEFT_FACING

        if self.walking:
            self.surface = self.walk_anim.update(direction=self.face_direction)
        else:
            self.surface = self.idle_anim.update(direction=self.face_direction)
        

class Tile(Sprite):
    def __init__(self, surface: pg.Surface, pos=[0,0], properties={}, animated=False):
        super().__init__()
        self.surface = surface
        self.size = [64,64]
        self.draw_rect_offset = [0,0]
        self.properties = properties
        self.tile_type = self.properties.get("tile_type")
        self.animated = animated
        self.pos = pos

    def point_in_tile(self, point):
        """This method can calculate collisions with shape types like slopes."""
        if self.rect().collidepoint(*point):
            rel_to_tile = point[0] - self.left, point[1] - self.top
            if self.shape_type == "slope1":
                if rel_to_tile[1] > self.size[0]-rel_to_tile[0]:
                    return True
                else:
                    return False
            elif self.shape_type == "slope2":
                if rel_to_tile[1] >= rel_to_tile[0]:
                    return True
                else:
                    return False
            else:
                return True
        return False

    def update(self):
        super().update()
        self.opacity = 255


class MovingTile(Sprite): pass


class CoinTile(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surface = load_image(Path("assets/tiles/gold_coin/gold_coin.png"))
        surfaces = load_spritesheet(Path("assets/tiles/gold_coin/gold_coin_collect.png"))
        self.collect_anim = AnimationStates({"default": surfaces}, speed=0.1)
        self.original_y = self.pos[1]
        self.frames_passed = 0
        self.collected = False

    def collect(self):
        self.collected = True

    def update(self):
        super().update()
        if self.collected:
            self.surface = self.collect_anim.update()
            if self.collect_anim.finished:
                self.kill()
            self.pos[1] = self.original_y
        else:
            self.frames_passed += 1
            self.pos[1] = self.original_y + (math.sin(self.frames_passed/21) * 7)


class RopeTile(Tile):
    """Doesn't do much now... will work on later"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surface = load_image(Path("assets/tiles/rope.png"))
        self.change_angle = 2

    def update(self):
        super().update()
        self.angle += self.change_angle
        if self.angle >= 35 or self.angle <= -35:
            self.change_angle *= -1

MAX_JUMP_COUNT = 10
JUMP_SPEED = 14

ACCELERATION = 1.15
DEACCELERATION = 1.15
MAX_WALK_SPEED = 8.25

class Player(Sprite):
    def __init__(self, spawn_centerx, spawn_bottom):
        super().__init__()
        
        self.collisions = {"top": False, "left": False, "right": False, "bottom": False}
        self.face_direction = RIGHT_FACING

        self.can_jump = True
        self.stop_jump = False
        self.jump_count = 0
        self.gravity = 1.1

        self.sounds = {}
        self.sounds["jump"] = pg.mixer.Sound(Path("assets/sounds/jump.wav"))
        self.sounds["spring"] = pg.mixer.Sound(Path("assets/sounds/spring.wav"))
        self.sounds["coin"] = pg.mixer.Sound(Path("assets/sounds/coin.wav"))
        self.sounds["shuriken_throw"] = pg.mixer.Sound(Path("assets/sounds/shuriken_throw.wav"))
        self.god_mode = False
        self.on_slope = False
        self.blink = 0
        self.walking = False
        self.anim_state = "idle"

        self.can_shoot_shuriken = True
        self.shuriken_refresh_time = 0

        self.use_rotate_cache = True

        hitbox_rect = load_image(Path("assets/player/hitbox.png")).get_bounding_rect()
        self.size = list(hitbox_rect.size)
        self.draw_rect_offset = -hitbox_rect.topleft[0], -hitbox_rect.topleft[1]

        self.centerx = spawn_centerx
        self.bottom = spawn_bottom
        self.time = 0

    @classmethod
    def load_resources(cls):
        s = load_spritesheet(Path("assets/player/player_idle.png"), size=24, count=4)
        idle_surfaces = [s[0], s[0], s[1], s[2], s[3], s[3], s[2], s[1]]
        idle_surfaces_dict = {
            "default": idle_surfaces, 
            "blink": cls.blinkify_surfaces(idle_surfaces)
        }
        cls.idle_anim = AnimationStates(frames_dict=idle_surfaces_dict, speed=0.15, use_RL=True)

        walk_surfaces = load_spritesheet(Path("assets/player/player_walk.png"), size=24, count=10)
        walk_surfaces_dict = {
            "default": walk_surfaces, 
            "blink": cls.blinkify_surfaces(walk_surfaces)
        }
        cls.walk_anim = AnimationStates(frames_dict=walk_surfaces_dict, speed=0.29, use_RL=True)

        fall_surfaces = load_spritesheet(Path("assets/player/player_fall.png"), size=24, count=3)
        fall_surfaces_dict = {
            "default": fall_surfaces,
            "blink": cls.blinkify_surfaces(fall_surfaces)
        }
        cls.fall_anim = AnimationStates(frames_dict=fall_surfaces_dict, speed=0.35, use_RL=True)

    
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
            self.walking = True
        elif self.engine.keys["left"] and not self.engine.keys["right"]:
            self.change_x -= ACCELERATION
            self.walking = True
        else:
            self.walking = False
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
            if self.rect().colliderect(tile):
                hit_list.append(tile)
        return hit_list

    @staticmethod
    def blinkify_surfaces(surfaces):
        return [pallete_swap(surface, (21,12,69,255), (232,187,121,255)) for surface in surfaces]
    
    def do_collisions(self):
        if self.on_slope and not self.change_y < 0:
            self.change_y += 10
        if not self.god_mode: self.change_y += self.gravity
        if self.change_y > 30: self.change_y = 30
        self.collisions = {"top": False, "left": False, "right": False, "bottom": False}
        walls = self.engine.scene["Walls"]

        self.pos[0] += self.change_x
        hit_list = self.get_collisions(walls.get_nearby_tiles_at(self.rect()))
        for tile in hit_list:
            if not tile.shape_type in ("slope1", "slope2"):
                if self.change_x > 0 and self.right>=tile.left and self.left<=tile.left:
                    self.right = tile.left
                    self.collisions["right"] = True
                elif self.change_x < 0 and tile.right>=self.left and tile.left<=self.left:
                    self.left = tile.right
                    self.collisions["left"] = True
            else: 
                pass
                # TODO This code prevents player from glitching up slopes when going in the opposite direction of the 
                # slope. e.g. player moves right into a slope2 tile. It currently causes some glitches when you slowly 
                # walk off slope1 tiles. Will fix later. For now, make sure there is a normal tile next to a slope tile

                # if tile.shape_type == "slope1":
                #     if self.change_x < 0 and tile.rect().right>=rect.left and tile.rect().left<=rect.left:
                #         rect.left = tile.rect().right
                #         self.collisions["left"] = True
                # elif tile.shape_type == "slope2":
                #     if self.change_x > 0 and rect.right>=tile.rect().left and rect.left<=tile.rect().left:
                #         rect.right = tile.rect().left
                #         self.collisions["right"] = True

        self.pos[1] += self.change_y
        hit_list = self.get_collisions(walls.get_nearby_tiles_at(self.rect()))
        for tile in hit_list:
            if not tile.shape_type in ("slope1", "slope2"):
                if self.change_y > 0 and tile.top<=self.bottom and tile.bottom>=self.bottom:
                    self.bottom = tile.top
                    self.collisions["bottom"] = True
                elif self.change_y < 0 and self.top<=tile.bottom and self.bottom>=tile.bottom:
                    self.top = tile.bottom
                    self.collisions["top"] = True
            else:
                if tile.shape_type in ("slope1", "slope2"):
                    if self.change_y < 0 and self.top<=tile.bottom and self.bottom>=tile.bottom:
                        self.top = tile.bottom
                        self.collisions["top"] = True
        
        self.on_slope = False
        hit_list = self.get_collisions(walls.get_nearby_tiles_at(self.rect()))
        for tile in hit_list:
            if tile.shape_type in ("slope1", "slope2"):
                if tile.shape_type == "slope1":
                    pos_height = self.right - tile.left
                elif tile.shape_type == "slope2":
                    pos_height = tile.right - self.left
                
                # Add constraints
                pos_height = min(pos_height, tile.rect().height)
                pos_height = max(pos_height, 0)

                target_y = tile.bottom - pos_height

                if self.bottom > target_y:
                    self.bottom = target_y
                    self.collisions["bottom"] = True
                    self.on_slope = True

        if self.collisions["bottom"] or self.collisions["top"]:
            self.change_y = 0

    def update(self):
        super().update()
        self.god_mode = self.engine.keys["g"]
        self.move_on_inputs()

        if self.shuriken_refresh_time > 0:
            self.shuriken_refresh_time -= 1
            if self.shuriken_refresh_time < 0:
                self.shuriken_refresh_time = 0
        if not self.engine.keys["e"]:
            self.can_shoot_shuriken = True

        if self.engine.keys["e"] and self.can_shoot_shuriken and self.shuriken_refresh_time == 0:
            shuriken = Shuriken(self, self.face_direction)
            shuriken.reset_old_pos()
            self.engine.scene["Projectiles"].append(shuriken)
            self.can_shoot_shuriken = False
            self.shuriken_refresh_time = 22
            self.sounds["shuriken_throw"].play()
            self.shuriken_refresh_time

        hit_list = self.get_collisions(self.engine.scene["Objects"]) 
        for obj in hit_list:
            if obj.tile_type == "spring":
                self.bottom = obj.top
                self.change_y = -32
                self.jump_count = MAX_JUMP_COUNT
                self.sounds["spring"].play()
            elif obj.tile_type == "coin":
                if not obj.collected:
                    obj.collect()
                    self.sounds["coin"].play()

        self.do_collisions()
        self.update_animation()

    def update_animation(self):
        if self.change_x > 0:
            self.face_direction = RIGHT_FACING
        elif self.change_x < 0:
            self.face_direction = LEFT_FACING

        self.blink += 1
        if self.blink > 8:
            self.blink = random.randint(-400, -250)

        if self.blink > 0:
            state = "blink"
        else:
            state = "default"

        if self.god_mode:
            self.anim_state = "god"
            self.surface = self.fall_anim.frames_dict[self.face_direction][state][-1]

        elif not self.can_jump:
            if not self.anim_state in ("in_fall", "fall"):
                self.anim_state = "in_fall"
                self.fall_anim.reset()

            if self.anim_state == "in_fall":
                self.surface = self.fall_anim.update(state=state, direction=self.face_direction)
                if self.fall_anim.finished:
                    self.anim_state = "fall"

            elif self.anim_state == "fall":
                self.surface = self.fall_anim.frames_dict[self.face_direction][state][-1]

        elif self.anim_state in ("in_fall", "fall", "out_fall"):
            if self.anim_state in ("in_fall", "fall"):
                self.anim_state = "out_fall"
                self.fall_anim.reset()
            self.surface = self.fall_anim.update(state=state, direction=self.face_direction, 
                                                 reverse=True, speed_alpha=3)
            if self.fall_anim.finished:
                self.anim_state = "exit_fall"


        elif self.walking or not self.change_x == 0:
            if not self.anim_state == "walk":
                self.walk_anim.reset()
            self.anim_state = "walk"
            self.surface = self.walk_anim.update(state=state, 
                                                 direction=self.face_direction, 
                                                 speed_alpha=abs(self.change_x/MAX_WALK_SPEED))

        else:
            if not self.anim_state == "idle":
                self.idle_anim.reset()
            self.anim_state = "idle"
            self.surface = self.idle_anim.update(state=state, direction=self.face_direction)

    def draw(self):
        old = time.perf_counter_ns()
        super().draw()
        self.time = time.perf_counter_ns()-old


class Shuriken(Sprite):
    speed = 14
    def __init__(self, player, direction):
        super().__init__()
        if direction == RIGHT_FACING:
            self.pos = [player.centerx+10, player.centery-24]
            self.change_x = 22
            self.surface = self.idle_surface
            self.set_size_from_surface(self.surface)
        elif direction == LEFT_FACING:
            self.pos = [player.centerx-10, player.centery-24]
            self.change_x = -22
            self.surface = self.idle_surface_flipped
            self.set_size_from_surface(self.surface)
        else:
            raise ValueError(f"Invalid direction: {direction}")
            
        self.distance_traveled = 0
        self.angle = random.randint(0, 359)
        self.time_on_wall = None

        self.use_rotate_cache = True

    @classmethod
    def load_resources(cls):
        cls.idle_surface = load_image(Path("assets/projectiles/shuriken.png"))
        cls.idle_surface_flipped = pg.transform.flip(cls.idle_surface, True, False)
        
    def update(self):
        super().update()
        walls = self.engine.scene["Walls"]
        if not self.time_on_wall is None:
            self.time_on_wall -= 1
            if self.time_on_wall < 0:
                if self.opacity - 10 < 0: self.kill()
                else: self.opacity -= 10
        else:

            if self.change_x < 0:
                self.change_x += 1
                if self.change_x > -self.speed:
                    self.change_x = -self.speed
            elif self.change_x > 0:
                self.change_x -= 1
                if self.change_x < self.speed:
                    self.change_x = self.speed
            if self.change_x > 0: points = ((self.right, self.bottom), (self.right, self.top))
            elif self.change_x < 0: points = ((self.left, self.bottom), (self.left, self.top))
            else: points = ()
            for point in points:
                if tile := walls.hash_tilemap.get(walls.hash_point(point)):
                    if tile.point_in_tile(point):
                        self.change_x = 0
                        self.time_on_wall = 280
        self.angle += self.change_x*-0.7
        self.pos[0] += self.change_x
        self.pos[1] += self.change_y
        self.distance_traveled += abs(self.change_x)
        if self.distance_traveled > 3200:
            self.kill()

    def draw(self):
        old = time.perf_counter_ns()
        super().draw()