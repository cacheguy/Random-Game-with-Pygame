import pygame as pg
import pygplus as pgp

import asyncio

import os; os.chdir(os.path.dirname(__file__))


class Engine:
    def __init__(self, width, height, title="Pygame game", icon_path=None, icon_size=32):
        pg.init()

        pgp.init_nodes(engine=self)
        self.screen_width = width
        self.screen_height = height
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height), vsync=False)
        pg.display.set_caption(title)
        if icon_path:
            icon = pg.transform.scale(pg.image.load(icon_path).convert_alpha(), (icon_size, icon_size))
            pg.display.set_icon(icon)
        self.clock = pg.time.Clock()

        self.debug_font = pg.font.SysFont("calibri", size=32)
        self.enable_debug_text = True
        self.reset_debug_text()

        self.dt = pgp.TARGET_DT
        self.fps = 0
        self.updates_per_frame = 0

        self.running = True

    def reset(self):
        pass

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()

    def quit(self):
        self.running = False

    def draw(self):
        self.draw_background()

    def draw_background(self):
        self.screen.fill((119, 196, 236))

    def debug_text(self, item, value, round_floats=True):
        if isinstance(value, float) and round_floats:
            text = f"{item}: {round(value, 2)}"
        else:
            text = f"{item}: {value}"
        surface = self.debug_font.render(text, True, (255, 255, 255))
        rect = surface.get_rect()
        rect.bottomleft = (10, self.debug_text_y)
        self.screen.blit(surface, rect)
        self.debug_text_y -= self.debug_font.get_height() + 5

    def reset_debug_text(self):
        self.debug_text_y = self.screen_height - 4

    def gameloop(self):
        self.reset()
        self.running = True
        while self.running:
            if pgp.FIXED_TIMESTEP_SETTINGS["enable"]:
                if pgp.FIXED_TIMESTEP_SETTINGS["busy_loop"]:
                    self.dt = self.clock.tick_busy_loop(pgp.MAX_FPS)/1000
                else:
                    self.dt = self.clock.tick(pgp.MAX_FPS)/1000
                if self.dt == 0:
                    self.fps = "infinite"
                else:
                    self.fps = 1/self.dt

                self.accumulator += self.dt
                self.updates_per_frame = 0
                while self.accumulator >= pgp.TARGET_DT:
                    self.handle_events()
                    self.update()
                    self.accumulator -= pgp.TARGET_DT
                    self.updates_per_frame += 1
                
                self.draw()
                pg.display.flip()
            else:
                raise NotImplementedError("Not finished yet. Just use fixed timestep for now.")
                self.dt = self.clock.tick(pgp.MAX_FPS)/1000
                if self.dt == 0:
                    self.fps = "infinite"
                else:
                    self.fps = 1/self.dt
                self.handle_events()
                self.update()
                self.draw()
                pg.display.flip()

        pg.quit()

    def update(self):
        pass