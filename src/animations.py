from constants import RIGHT_FACING, LEFT_FACING

from math import floor


class Animation():
    def __init__(self, frames, speed: float=0.25, use_RL: bool=False):
        self.frames = frames
        self.speed = speed
        self.use_RL = use_RL
        self._frame_num = 0
        self.had_automatically_resetted = False  # Can be used to check if the animation had already run one loop.

    @property
    def frame_num(self):
        return self._frame_num

    @frame_num.setter
    def frame_num(self, value):
        self._frame_num = value
        if self.frame_num >= len(self.frames):
            self.reset()
            self.had_automatically_resetted = True
        else:
            self.had_automatically_resetted = False

    def reset(self):
        self._frame_num = 0
        
    def update(self):
        self.frame_num += self.speed

    def get_frame(self, direction=None):
        if self.use_RL:
            current_frame = self.frames[floor(self.frame_num)][direction]
        else:
            current_frame = self.frames[floor(self.frame_num)]
        return current_frame