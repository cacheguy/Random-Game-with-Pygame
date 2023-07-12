import pygame as pg

from constants import *

import time
import asyncio
from pathlib import Path

import os; os.chdir(os.path.dirname(__file__))


# Settings
target_fps = 60
target_dt = 1/target_fps
fixed_timestep_settings = {
    "enable": True,
    "interpolate": True,
    "snap_dt": True,
    "busy_loop": False
}


def load_image(filename: Path) -> pg.Surface:
    surface = pg.image.load(filename).convert()
    surface = pg.transform.scale_by(surface, SCALE)
    surface.set_colorkey((0,0,0))
    return surface

def relative_to_camera(pos, camera_position):
    return [pos[0] - camera_position[0], pos[1] - camera_position[1]]

def lerp(num1, num2, alpha):
    return num1 + (alpha * (num2 - num1))


class Sprite:
    engine = None
    def __init__(self, screen: pg.Surface, filename: Path=None):
        self.screen = screen
        self.draw_rect_offset = (0,0)
        self.shape_type = None

        self.change_x = 0
        self.change_y = 0

        self.opacity = 255
        self.angle = 0
        self.scale = 1

        self.pos = [0,0]  # Topleft

        if filename is not None:
            self.surface = load_image(filename)
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
        return pg.Rect(*self.pos, *self.size)
    
    @property
    def draw_rect(self) -> pg.Rect:
        """The rect of the surface that will be drawn."""
        rect = self.surface.get_rect()
        rect.topleft = self.pos
        rect.x += self.draw_rect_offset[0]
        rect.y += self.draw_rect_offset[1]
        return rect

    def on_screen(self, rect):
        return not (rect.right< 0 or rect.left > SCREEN_WIDTH or rect.bottom < 0 or rect.top > SCREEN_HEIGHT)
            
    def update(self): 
        pass

    def draw(self):
        draw_pos = relative_to_camera(self.pos, self.engine.camera_position)
        draw_pos[0] += self.draw_rect_offset[0]
        draw_pos[1] += self.draw_rect_offset[1]

        draw_rect_to_cam = self.draw_rect
        draw_rect_to_cam.topleft = relative_to_camera(draw_rect_to_cam.topleft, self.engine.camera_position)

        if self.on_screen(draw_rect_to_cam):
            self.screen.blit(self.surface, draw_pos)


class Player(Sprite):
    def __init__(self, screen: pg.Surface):
        super().__init__(screen=screen)
        self.surface = load_image(Path("assets/player/idle1.png"))
        self.surfaces = []
        self.surfaces.append(self.surface)
        self.surfaces.append(pg.transform.flip(self.surface, True, False))

        self.pos = [0,0]
        self.hitbox_rect = load_image(Path("assets/player/hitbox.png")).get_bounding_rect()
        self.size = list(self.hitbox_rect.size)
        self.draw_rect_offset = -self.hitbox_rect.topleft[0], -self.hitbox_rect.topleft[1]

        self.collisions = None
        self.face_direction = RIGHT_FACING

        self.old_pos = list(self.pos)

    def move_on_inputs(self):
        speed = 8
        if self.engine.keys["right"] and not self.engine.keys["left"]:
            self.change_x = speed
        elif self.engine.keys["left"] and not self.engine.keys["right"]:
            self.change_x = -speed
        else:
            self.change_x = 0

        if self.engine.keys["up"] and self.collisions["bottom"]:
            self.change_y = -18

    def get_collisions(self, tiles):
        hit_list = []
        for tile in tiles:
            if self.rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list

    def apply_physics(self):
        self.collisions = {"top": False, "left": False, "right": False, "bottom": False}

        self.pos[0] += self.change_x
        hit_list = self.get_collisions(self.engine.tiles)
        rect = self.rect
        for tile in hit_list:
            if not tile.shape_type in ("slope1", "slope2"):
                if self.change_x > 0:
                    rect.right = tile.rect.left
                    self.collisions["right"] = True
                elif self.change_x < 0:
                    rect.left = tile.rect.right
                    self.collisions["left"] = True
        self.pos = list(rect.topleft)

        self.pos[1] += self.change_y
        hit_list = self.get_collisions(self.engine.tiles)
        rect = self.rect
        for tile in hit_list:
            if not tile.shape_type in ("slope1", "slope2"):
                if self.change_y > 0:
                    rect.bottom = tile.rect.top
                    self.collisions["bottom"] = True
                elif self.change_y < 0:
                    rect.top = tile.rect.bottom
                    self.collisions["top"] = True
        self.pos = list(rect.topleft)

        hit_list = self.get_collisions(self.engine.tiles)
        rect = self.rect
        for tile in hit_list:
            if tile.shape_type in ("slope1", "slope2"):
                if tile.shape_type == "slope1":
                    pos_height = rect.right - tile.rect.left
                elif tile.shape_type == "slope2":
                    pos_height = tile.rect.right - rect.left
                
                # Add constraints
                pos_height = min(pos_height, tile.rect.width)
                pos_height = max(pos_height, 0)

                target_y = tile.rect.bottom - pos_height

                if rect.bottom > target_y:
                    rect.bottom = target_y
                    self.collisions["bottom"] = True
        self.pos = list(rect.topleft)
        
        if self.collisions["bottom"] or self.collisions["top"]:
            self.change_y = 0

    def update(self):
        self.old_pos = list(self.pos)
        self.move_on_inputs()

        self.change_y += 1
        if self.change_y > 30: self.change_y = 30

        # self.pos[0] += self.change_x
        self.apply_physics()
        # self.pos[1] += self.change_y
        # self.update_physics(False)

        if self.change_x > 0:
            self.face_direction = RIGHT_FACING
        elif self.change_x < 0:
            self.face_direction = LEFT_FACING

        self.surface = self.surfaces[self.face_direction]

    def draw(self):
        alpha = self.engine.accumulator/(1/60)
        old = self.pos
        self.pos = [
            lerp(self.old_pos[0], self.pos[0], alpha),
            lerp(self.old_pos[1], self.pos[1], alpha)
        ]
        super().draw()
        self.pos = old


class Engine:
    def __init__(self):
        pg.init()

        Sprite.set_engine(self)
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("calibri", size=32)

        self.camera_position = [0,0]
        self.old_camera_position = list(self.camera_position)

        self.enable_debug_text = True
        self.reset_debug_text()

        self.dt = 1/60
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
        }
        self.player = Player(self.screen)
        self.camera_position = list(self.player.rect.center)

        tilemap = [
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,3,4,0,0,0,2,2,0,
            0,0,0,0,0,0,0,0,3,2,2,4,0,0,0,0,0,
            0,0,0,0,0,0,3,2,2,2,2,2,2,2,2,2,2,
            1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
            1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
        ]
        tilemap_width = 17
        tilemap_height = 7
        tile_size = 16
        self.tiles = []
        i = 0
        for y in range(tilemap_height):
            for x in range(tilemap_width):
                if not tilemap[i] == 0:
                    if tilemap[i] == 1: 
                        tile_object = Sprite(self.screen, Path("assets/tiles/brick.png"))
                    elif tilemap[i] == 2: 
                        tile_object = Sprite(self.screen, Path("assets/tiles/stone.png"))
                    elif tilemap[i] == 3: 
                        tile_object = Sprite(self.screen, Path("assets/tiles/wood_slope1.png"))
                        tile_object.shape_type = "slope1"
                    elif tilemap[i] == 4: 
                        tile_object = Sprite(self.screen, Path("assets/tiles/wood_slope2.png"))
                        tile_object.shape_type = "slope2"
                    else: 
                        raise Exception("Invalid tile ID")

                    tile_object.pos = x*tile_size*SCALE, y*tile_size*SCALE

                    self.tiles.append(tile_object)
                i += 1

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
                    case pg.K_f: self.enable_debug_text = not self.enable_debug_text
            elif event.type == pg.KEYUP:
                match event.key:
                    case pg.K_w | pg.K_UP | pg.K_SPACE: self.keys["up"] = False
                    case pg.K_s | pg.K_DOWN: self.keys["down"] = False
                    case pg.K_a | pg.K_LEFT: self.keys["left"] = False
                    case pg.K_d | pg.K_RIGHT: self.keys["right"] = False

    def quit(self):
        self.running = False

    def position_camera(self):
        self.old_camera_position = list(self.camera_position)
        self.camera_position[0] = lerp(self.camera_position[0]+SCREEN_WIDTH/2, self.player.rect.centerx, 0.17)
        self.camera_position[1] = lerp(self.camera_position[1]+SCREEN_HEIGHT/2, self.player.rect.centery, 0.17)
        self.camera_position[0] -= SCREEN_WIDTH / 2
        self.camera_position[1] -= SCREEN_HEIGHT / 2

    def draw(self):
        self.screen.fill((119, 196, 236))
        for tile in self.tiles:
            tile.draw()
        self.player.draw()
        # rect = self.player.rect
        # rect.topleft = relative_to_camera(rect.topleft, self.camera_position)
        # pg.draw.rect(self.screen, (0,255,0), rect, 2)
        # rect = self.player.draw_rect
        # rect.topleft = relative_to_camera(rect.topleft, self.camera_position)
        # pg.draw.rect(self.screen, (255,0,0), rect, 2)

        self.reset_debug_text()
        self.debug_text("FPS", self.fps)
        self.debug_text("Updates per frame", self.updates_per_frame)
        self.debug_text("Change x", self.player.change_x)
        self.debug_text("Change y", self.player.change_y)

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
            if fixed_timestep_settings["enable"]:
                if fixed_timestep_settings["busy_loop"]:
                    self.dt = self.clock.tick_busy_loop()/1000
                else:
                    self.dt = self.clock.tick()/1000
                if self.dt == 0:
                    self.fps = "infinite"
                else:
                    self.fps = 1/self.dt

                self.accumulator += self.dt
                self.updates_per_frame = 0
                while self.accumulator >= 1/60:
                    self.update()
                    self.accumulator -= 1/60
                    self.updates_per_frame += 1
                    self.position_camera()

                alpha = self.accumulator / (1/60)
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
                dt = self.clock.tick(60)/1000
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
        self.player.update()
        


if __name__ == "__main__":
    game = Engine()
    asyncio.run(game.gameloop())