import pygame as pg

from constants import *
from utils import *
from sprites import Player
from tilemap import Tilemap
from spritelists import init_nodes, SpriteList

import time
import math
import asyncio
from pathlib import Path

import os; os.chdir(os.path.dirname(__file__))


class Engine:
    def __init__(self):
        pg.init()

        init_nodes(engine=self)
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), vsync=False)
        pg.display.set_caption(TITLE)
        pg.display.set_icon(pg.transform.scale(pg.image.load(Path("assets/icon.png")).convert_alpha(), (32,32)))
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("calibri", size=32)

        self.enable_debug_text = True
        self.reset_debug_text()

        self.dt = TARGET_DT
        self.fps = 0
        self.updates_per_frame = 0

        self.running = True

    def reset(self):
        self.accumulator = 0
        self.keys = {
            "right": False,
            "left": False,
            "up": False,
            "down": False,
            "e": False,
            "g": False
        }

        tilemap = Tilemap(Path("assets/tilemap_project/tilemaps/basic_tilemap3.json"))
        self.scene = {}
        l = tilemap.layers
        self.scene["Projectiles"] = SpriteList()
        self.scene["Objects"] = l["Objects"]
        self.scene["Walls"] = l["Walls"]
        self.scene["Offgrid"] = l["Offgrid"]
                   
        self.scene["Walls"].load_hash_tilemap()
        self.scene["Walls"].set_dynamic_surfaces()

        self.player = Player(*tilemap.spawn_point)
        self.camera_position = [0,0]
        self.old_camera_position = [0,0]
        self.position_camera(speed=1)  # Actual camera positions are set here

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            elif event.type == pg.KEYDOWN:
                match event.key:
                    case pg.K_w | pg.K_UP | pg.K_SPACE: self.keys["up"] = True
                    case pg.K_s | pg.K_DOWN: self.keys["down"] = True
                    case pg.K_a | pg.K_LEFT: self.keys["left"] = True
                    case pg.K_d | pg.K_RIGHT: self.keys["right"] = True
                    case pg.K_e: self.keys["e"] = True
                    case pg.K_f: self.enable_debug_text = not self.enable_debug_text
                    case pg.K_g: self.keys["g"] = not self.keys["g"]
                    case pg.K_r: self.reset()
            elif event.type == pg.KEYUP:
                match event.key:
                    case pg.K_w | pg.K_UP | pg.K_SPACE: self.keys["up"] = False
                    case pg.K_s | pg.K_DOWN: self.keys["down"] = False
                    case pg.K_a | pg.K_LEFT: self.keys["left"] = False
                    case pg.K_d | pg.K_RIGHT: self.keys["right"] = False
                    case pg.K_e: self.keys["e"] = False

    def quit(self):
        self.running = False

    def position_camera(self, speed=0.17):
        self.old_camera_position = list(self.camera_position)
        self.camera_position[0] = lerp(self.camera_position[0]+SCREEN_WIDTH/2, self.player.centerx, speed)
        self.camera_position[1] = lerp(self.camera_position[1]+SCREEN_HEIGHT/2, self.player.centery, speed)
        self.camera_position[0] -= SCREEN_WIDTH / 2
        self.camera_position[1] -= SCREEN_HEIGHT / 2

    def draw(self):
        self.screen.fill((119, 196, 236))

        # mouse_pos = pg.mouse.get_pos()
        # mouse_pos = mouse_pos[0] + self.camera_position[0], mouse_pos[1] + self.camera_position[1]
        # grid_mouse_pos = mouse_pos[0]//64, mouse_pos[1]//64
        # if self.tilemap.layers["Walls"].hash_tilemap is not None:
        #     if tile := self.tilemap.layers["Walls"].hash_tilemap.get(grid_mouse_pos):
        #         mouse_collide = tile.point_in_tile(mouse_pos)
        #         if mouse_collide:
        #             tile.opacity = 255*0.6
        for spritelist in self.scene.values():
            spritelist.draw()
        self.player.draw()

        # grid_pos = self.player.pos[0]//64*64, self.player.pos[1]//64*64
        # grid_pos = relative_to_camera(grid_pos, self.camera_position)
        # pg.draw.rect(self.screen, (0,0,255), pg.Rect(grid_pos, (64,64)), 2)
        # tiles = self.tilemap.get_nearby_tiles_at(self.player.pos)

        # for tile in tiles:
        #     grid_pos = relative_to_camera(tile.pos, self.camera_position)
        #     pg.draw.rect(self.screen, (0,255,0), pg.Rect(grid_pos, (64,64)), 2)

        # rect = self.player.draw_rect
        # rect.topleft = relative_to_camera(rect.topleft, self.camera_position)
        # pg.draw.rect(self.screen, (255,0,0), rect, 2)

        # offsets = get_offsets_from_rect(self.player.rect(), 16*SCALE)

        # for offset in offsets:
        #     pg.draw.rect(self.screen, (0,255,0), pg.Rect(relative_to_camera([self.player.pos[0]//64*64+offset[0]*64, self.player.pos[1]//64*64+offset[1]*64], self.camera_position), [64,64]), 2)
        # rect = self.player.rect()
        # rect.topleft = relative_to_camera(rect.topleft, self.camera_position)
        # pg.draw.rect(self.screen, (255,0,0), rect, 2)

        if self.enable_debug_text:
            self.reset_debug_text()
            self.debug_text("FPS", self.fps)
            self.debug_text("Updates per frame", self.updates_per_frame)
            # self.debug_text("Change x", self.player.change_x)
            # self.debug_text("Change y", self.player.change_y)
            self.debug_text("Y position", self.player.pos[1])
            self.debug_text("X position", self.player.pos[0])
            self.debug_text("Can jump", self.player.can_jump)
            self.debug_text("Collisions", self.player.collisions)
            self.debug_text("On Slope", self.player.on_slope)
            self.debug_text("Jump Count", self.player.jump_count)
            self.debug_text("Time", self.player.time)
    def debug_text(self, item, value, round_floats=True):
        if isinstance(value, float) and round_floats:
            text = f"{item}: {round(value, 2)}"
        else:
            text = f"{item}: {value}"
        surface = self.font.render(text, True, (255, 255, 255))
        rect = surface.get_rect()
        rect.bottomleft = (10, self.debug_text_y)
        self.screen.blit(surface, rect)
        self.debug_text_y -= self.font.get_height() + 5

    def reset_debug_text(self):
        self.debug_text_y = SCREEN_HEIGHT - 4

    async def gameloop(self):
        self.reset()
        self.running = True
        while self.running:
            if FIXED_TIMESTEP_SETTINGS["enable"]:
                if FIXED_TIMESTEP_SETTINGS["busy_loop"]:
                    self.dt = self.clock.tick_busy_loop(MAX_FPS)/1000
                else:
                    self.dt = self.clock.tick(MAX_FPS)/1000
                if self.dt == 0:
                    self.fps = "infinite"
                else:
                    self.fps = 1/self.dt

                self.accumulator += self.dt
                self.updates_per_frame = 0
                while self.accumulator >= TARGET_DT:
                    self.update()
                    self.accumulator -= TARGET_DT
                    self.updates_per_frame += 1
                    self.position_camera()

                alpha = self.accumulator/TARGET_DT
                old = self.camera_position
                self.camera_position = [
                    lerp(self.old_camera_position[0], self.camera_position[0], alpha),
                    lerp(self.old_camera_position[1], self.camera_position[1], alpha)
                ]
                
                self.draw()
                self.camera_position = old
                pg.display.flip()
                await asyncio.sleep(0)
            else:
                self.dt = self.clock.tick(MAX_FPS)/1000
                if self.dt == 0:
                    self.fps = "infinite"
                else:
                    self.fps = 1/self.dt
                self.update()
                self.draw()
                pg.display.flip()

        pg.quit()

    def update(self):
        self.handle_events()
        if self.player.pos[1] > 3200:
            self.reset()
        for spritelist in self.scene.values():
            spritelist.update()
        self.player.update()


if __name__ == "__main__":
    game = Engine()
    asyncio.run(game.gameloop())