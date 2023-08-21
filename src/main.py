import pygame as pg
import pygplus as pgp

from sprites import Player
from tilemap import Tilemap

import asyncio
from pathlib import Path

import os; os.chdir(os.path.dirname(__file__))


class Engine(pgp.engine.Engine):
    def __init__(self):
        super().__init__(width=1600, 
                         height=900, 
                         title="Ninja Game", 
                         icon_path=Path("assets/icon.png"))

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
        self.scene["Projectiles"] = pgp.sprite.SpriteList()
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

    def position_camera(self, speed=0.17):
        self.old_camera_position = list(self.camera_position)
        self.camera_position[0] = pgp.lerp(self.camera_position[0]+self.screen_width/2, self.player.centerx, speed)
        self.camera_position[1] = pgp.lerp(self.camera_position[1]+self.screen_height/2, self.player.centery, speed)
        self.camera_position[0] -= self.screen_width / 2
        self.camera_position[1] -= self.screen_height / 2

    def rel_to_camera(self, pos): return [pos[0] - self.camera_position[0], pos[1] - self.camera_position[1]]

    def draw(self):
        alpha = self.accumulator/pgp.TARGET_DT
        old = self.camera_position
        self.camera_position = [
            pgp.lerp(self.old_camera_position[0], self.camera_position[0], alpha),
            pgp.lerp(self.old_camera_position[1], self.camera_position[1], alpha)
        ]

        self.screen.fill((119, 196, 236))

        for spritelist in self.scene.values():
            spritelist.draw()
        self.player.draw()

        # grid_pos = self.player.pos[0]//64*64, self.player.pos[1]//64*64
        # grid_pos = relative_to_camera(grid_pos, self.camera_position)
        # pg.draw.rect(self.screen, (0,0,255), pg.Rect(grid_pos, (64,64)), 2)
        # tiles = self.tilemap.get_nearby_tiles_at(self.player.pos)

        self.camera_position = old

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

    def update(self):
        self.handle_events()

        if self.player.pos[1] > 3200:
            self.reset()
        for spritelist in self.scene.values():
            spritelist.update()
        self.player.update()

        self.position_camera()


if __name__ == "__main__":
    game = Engine()
    game.gameloop()