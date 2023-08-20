import pygame as pg

from constants import RIGHT_FACING, LEFT_FACING

from math import floor, ceil


#TODO Add finished
class AnimationStates:
    def __init__(self, frames_dict, speed: float=0.25, use_RL: bool=False):
        # frames_dict = {
        #     "default": [pg.Surface, ...], 
        #     "blink": [pg.Surface, ...], 
        # }
        if use_RL:
            new_dict = {}
            new_dict[RIGHT_FACING] = frames_dict
            new_dict[LEFT_FACING] = {}
            for key, value in frames_dict.items():
                new_dict[LEFT_FACING][key] = [pg.transform.flip(surface, True, False) for surface in value]
            
            self.frames_dict = new_dict
        else:
            self.frames_dict = frames_dict

        # Check all lists are same length
        lengths = set()
        for value in self.frames_dict.values():
            if isinstance(value, list):
                lengths.add(len(value))
            elif isinstance(value, dict):
                for value2 in value.values():
                    lengths.add(len(value2))
        if not len(lengths) == 1:
            raise ValueError("All lists of Surfaces must have the same length")
        
        self.frame_list_len = list(lengths)[0]
        self.use_RL = use_RL
        self.speed = speed
        self._frame_num = 0
        self.finished = False  # Can be used to check if the animation had already run one loop.

    @property
    def frame_num(self):
        return self._frame_num

    @frame_num.setter
    def frame_num(self, value):
        self._frame_num = value
        if self.frame_num >= self.frame_list_len:
            self.reset()
            self.finished = True
        else:
            self.finished = False

    def reset(self, reverse=False):
        self._frame_num = 0
        
    def update(self, state="default", direction=None, speed_alpha=1, reverse=False):
        if self.use_RL:
            frame_list = self.frames_dict[direction][state]
        else:
            frame_list = self.frames_dict[state]
        if reverse:
            frame_list = list(reversed(frame_list))

        # We return current surface, THEN update frame num. That way, we don't skip the first frame.
        frame = frame_list[floor(self.frame_num)]
        self.frame_num += self.speed * speed_alpha
        return frame
        