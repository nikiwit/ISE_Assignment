import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

WIDTH, HEIGHT = 1280, 720
FPS = 60

GRAVITY = 0.6
MAX_FALL_SPEED = 18
GRU_SPEED = 4
GRU_JUMP = -17
FREEZE_RAY_SPEED = 10
GRU_MAX_HP = 3
INVINCIBILITY_FRAMES = 90

FRAME_DURATION = 6  # ticks per animation frame

BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
RED    = (200, 30, 30)
GREEN  = (30, 200, 30)
YELLOW = (240, 220, 50)
DARK   = (20, 20, 30)
