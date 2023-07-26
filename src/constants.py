SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
TITLE = "Random Pygame game"

SCALE = 4
RIGHT_FACING = 0
LEFT_FACING = 1

# Settings
MAX_FPS = 0  # Put 0 for no fps limit
TARGET_FPS = 60
TARGET_DT = 1/TARGET_FPS
FIXED_TIMESTEP_SETTINGS = {
    "enable": True,
    "interpolate": True,  # TODO Make this work
    "snap_dt": True,
    "busy_loop": False
}