"""Scene 2 — Vector's Fortress.

The overall structure follows the same pattern as the multi-level game we built
in the lab: each level is a self-contained function that runs its own loop and
returns a string telling the caller which scene comes next.

Bigger ideas in this file:
  - Parallax scrolling: three background layers scrolled at different speeds
  - Custom timer events (pygame.USEREVENT) to fire turrets on a fixed interval
  - Drone patrol paths built with cos/sin — from the transformation lab
  - Normalised direction vectors for enemy projectile aim
  - Unstable platform state machine (stable → cracking → falling)
"""

import os
import math
import random
import pygame
from settings import (
    ASSETS_DIR, WIDTH, HEIGHT, FPS, GRAVITY,
    GRU_MAX_HP, WHITE, RED, GREEN, YELLOW, DARK
)
from gru import Gru, PlasmaBolt, ExplosionVFX, MuzzleFlash
from pause import run_pause


# custom timer events, so turrets/platforms tick on a real-time interval
# rather than every frame. same USEREVENT pattern we used for the lab's
# countdown clock — pygame queues an event each interval and we react to it.
TURRET_FIRE_EVENT    = pygame.USEREVENT + 1
UNSTABLE_CRACK_EVENT = pygame.USEREVENT + 2

# placeholder colours used by the procedural-drawn fallbacks (when a sprite asset isn't there yet)
PLAT_COLOUR   = (70, 80, 100)
UNSTABLE_COL  = (130, 80, 50)
PART_COLOURS  = [(0, 200, 255), (255, 180, 0), (180, 0, 255)]
MINION_COLOUR = (240, 210, 50)
DRONE_COLOUR  = (200, 60, 60)
TURRET_COLOUR = (100, 100, 120)


class Drone(pygame.sprite.Sprite):
    """Vector's flying security drone.

    Movement uses cos and sin to trace a smooth oval patrol path — the same
    trig we used in the lab exercise about rotating and transforming shapes.
    The angle variable increases each tick, and cos/sin convert it into x/y
    offsets around the drone's home position.
    """

    def __init__(self, cx: int, cy: int, patrol_range: int = 160, speed: float = 1.8):
        super().__init__()
        self.cx = cx           # home position the drone orbits around
        self.cy = cy
        self.patrol_range = patrol_range
        self.speed = speed
        self.angle = random.uniform(0, math.pi * 2)  # start at a random point in the cycle

        self.frozen      = False
        self.freeze_timer = 0

        self.image = self._make_image()
        self.rect  = self.image.get_rect(center=(cx, cy))

        # if the real sprite file exists, use it instead of the procedural fallback.
        # the sheet is a horizontal strip — we just take the first frame for now.
        sprite_path = os.path.join(ASSETS_DIR, "sprites", "drones", "idle.png")
        if os.path.exists(sprite_path):
            sheet = pygame.image.load(sprite_path).convert_alpha()
            frame_w = sheet.get_height()  # frames are square; width of one = sheet height
            frame = sheet.subsurface(pygame.Rect(0, 0, frame_w, sheet.get_height()))
            self.image = pygame.transform.scale(frame, (48, 48))
            self.rect  = self.image.get_rect(center=(cx, cy))

    @staticmethod
    def _make_image() -> pygame.Surface:
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(surf, DRONE_COLOUR, (24, 24), 22)
        pygame.draw.circle(surf, (255, 80, 80), (24, 24), 8)  # red "eye" in the centre
        return surf

    def update(self):
        if self.frozen:
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.frozen = False
                self.image.set_alpha(255)
            return

        # advance the angle each tick and recompute (x, y) from cos/sin of it.
        # the y-component uses angle*0.5 so vertical bobbing is half-frequency
        # vs horizontal sweep — that's what gives the path an oval shape.
        self.angle += self.speed * 0.03
        self.rect.centerx = int(self.cx + math.cos(self.angle) * self.patrol_range)
        self.rect.centery  = int(self.cy + math.sin(self.angle * 0.5) * 30)

    def freeze(self):
        self.frozen = True
        self.freeze_timer = 10**9  # effectively permanent — once shot, the drone stays disabled
        self.image.set_alpha(120)  # fade out to show the frozen state visually

    def shoot_at(self, target_rect) -> "EnemyProjectile | None":
        if self.frozen:
            return None
        return EnemyProjectile(self.rect.centerx, self.rect.centery, target_rect)


class EnemyProjectile(pygame.sprite.Sprite):
    """Energy ball that travels from an enemy toward Gru's position.

    I calculate direction using a normalised vector: subtract the target position
    from the origin, divide by the distance to get a unit vector, then multiply
    by the desired speed. This ensures the projectile always travels at the same
    speed regardless of the angle.
    """

    MAX_TRAVEL = WIDTH  # roughly one screen of travel before fizzling out

    def __init__(self, x: int, y: int, target_rect: pygame.Rect):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 120, 0), (6, 6), 6)
        self.rect = self.image.get_rect(center=(x, y))

        dx = target_rect.centerx - x
        dy = target_rect.centery - y
        dist = max(1, math.hypot(dx, dy))  # hypot gives the straight-line distance; max(1,...) avoids division by zero
        self.vx = dx / dist * 5
        self.vy = dy / dist * 5
        self._travelled = 0.0

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        # cap by distance travelled, NOT by absolute world x — turrets later
        # in the level spawn projectiles at world x > WIDTH (1280), and an
        # absolute-bound check would kill those on their very first frame.
        self._travelled += math.hypot(self.vx, self.vy)
        if self._travelled >= self.MAX_TRAVEL:
            self.kill()


class Turret(pygame.sprite.Sprite):
    """Hovering gunship turret. Doesn't move — fires on the global timer event.

    Visually a hovering ship from sprites/gunship/idle.png (4-frame animation).
    Mechanically still a stationary turret: fires on the timer, can be frozen.
    """

    _FRAMES_RIGHT = None
    _FRAMES_LEFT  = None
    _FRAMES_RIGHT_LP = None  # low-profile (small) frames for ground turrets
    _FRAMES_LEFT_LP  = None
    _FRAME_TICKS  = 8        # ticks per animation frame — slower than Gru for a calm hover
    # low-profile turrets sit on the floor. the trick: the visual is bigger
    # than the hit rect — only the bottom 27 px registers collisions.
    # a standing plasma bolt (rect spans y=617..633) flies right over them,
    # while a crouching bolt (rect y=634..650) overlaps and kills.
    LOW_PROFILE_VISUAL     = 36
    LOW_PROFILE_HIT_HEIGHT = 27

    def __init__(self, x: int, y: int, facing_right: bool = True, low_profile: bool = False):
        super().__init__()
        self.facing_right = facing_right
        self.low_profile  = low_profile
        self._load_frames()
        if low_profile:
            self._right = self._FRAMES_RIGHT_LP
            self._left  = self._FRAMES_LEFT_LP
            self.image = (self._right if facing_right else self._left)[0]
            img_w, img_h = self.image.get_size()
            # hit rect = bottom HIT_HEIGHT pixels of the visual area. the
            # image is then drawn offset upward so its bottom aligns with rect.bottom.
            self.rect = pygame.Rect(x, y, img_w, self.LOW_PROFILE_HIT_HEIGHT)
            self.draw_offset = (0, -(img_h - self.LOW_PROFILE_HIT_HEIGHT))
        else:
            self._right = self._FRAMES_RIGHT
            self._left  = self._FRAMES_LEFT
            self.image = (self._right if facing_right else self._left)[0]
            self.rect  = self.image.get_rect(topleft=(x, y))
        self._frame_index = 0
        self._frame_timer = 0
        self.frozen = False
        self.freeze_timer = 0

    @classmethod
    def _load_frames(cls):
        if cls._FRAMES_RIGHT is not None:
            return
        sheet = pygame.image.load(
            os.path.join(ASSETS_DIR, "sprites", "gunship", "idle.png")
        ).convert_alpha()
        # 4 frames laid out horizontally in the source PNG, each 48x48
        right = [sheet.subsurface(pygame.Rect(i * 48, 0, 48, 48)) for i in range(4)]
        left  = [pygame.transform.flip(f, True, False) for f in right]
        cls._FRAMES_RIGHT = right
        cls._FRAMES_LEFT  = left
        # low-profile mode: scaled-down visual frames for floor turrets.
        # the smaller hit rect (LOW_PROFILE_HIT_HEIGHT) is set up in __init__.
        sz = cls.LOW_PROFILE_VISUAL
        cls._FRAMES_RIGHT_LP = [pygame.transform.scale(f, (sz, sz)) for f in right]
        cls._FRAMES_LEFT_LP  = [pygame.transform.scale(f, (sz, sz)) for f in left]

    def update(self):
        if self.frozen:
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.frozen = False
            return  # don't animate while frozen — visually conveys the freeze

        frames = self._right if self.facing_right else self._left
        self._frame_timer += 1
        if self._frame_timer >= self._FRAME_TICKS:
            self._frame_timer = 0
            self._frame_index = (self._frame_index + 1) % len(frames)
            self.image = frames[self._frame_index]

    def freeze(self):
        self.frozen = True
        self.freeze_timer = 10**9  # effectively permanent

    def fire(self, target_rect: pygame.Rect) -> "EnemyProjectile | None":
        if self.frozen:
            return None
        return EnemyProjectile(self.rect.centerx, self.rect.centery, target_rect)


class ShrinkRayPart(pygame.sprite.Sprite):
    """One of five shrink-ray components Gru needs to collect.

    Visually a static yellow 4-pointed sparkle from the projectiles sheet.
    """

    _IMAGE = None

    def __init__(self, x: int, y: int, index: int):
        super().__init__()
        self.image = self._load_image()
        self.rect = self.image.get_rect(center=(x, y))

    @classmethod
    def _load_image(cls):
        if cls._IMAGE is not None:
            return cls._IMAGE
        # the sheet's "transparent" background is actually opaque black
        # (alpha=255). loading with .convert() + a colorkey on black drops
        # the surrounds, so we don't render a black box around each sparkle.
        sheet = pygame.image.load(
            os.path.join(ASSETS_DIR, "sprites", "vfx", "bullets_projectiles.png")
        ).convert()
        sheet.set_colorkey((0, 0, 0))
        cell = sheet.subsurface(pygame.Rect(176, 64, 16, 16)).copy()
        cls._IMAGE = pygame.transform.scale(cell, (32, 32))
        return cls._IMAGE

    def update(self):
        # static pickup — nothing to animate or move
        pass


class MinionCollectible(pygame.sprite.Sprite):
    """A friendly minion hiding in the fortress. Collecting one restores 1 HP."""

    # the source sheet has TWO background colours: a teal cell-border (0,128,128)
    # and a bright green fill (0,248,0). minions don't contain either colour,
    # so we can blanket-wipe both to transparent on load. cached at class level
    # so the work only runs the first time a minion is spawned.
    _sheet = None
    _BG_COLOURS = ((0, 128, 128), (0, 248, 0))

    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = self._make_image()
        self.rect  = self.image.get_rect(center=(x, y))

        sheet = self._load_sheet()
        if sheet is not None:
            # the sheet uses 32x32 cells with a 2 px column separator and 4 px
            # row separator between them. row 3, col 0 is a front-facing minion
            # looking at the camera — that's our default idle pose.
            CELL = 32
            COL_STRIDE, ROW_STRIDE = 34, 36  # cell + separator
            ORIGIN = (2, 2)                  # first cell starts after the top-left border
            col, row = 0, 3
            cx = ORIGIN[0] + col * COL_STRIDE
            cy = ORIGIN[1] + row * ROW_STRIDE
            frame = sheet.subsurface(pygame.Rect(cx, cy, CELL, CELL))
            self.image = pygame.transform.scale(frame, (48, 48))
            self.rect  = self.image.get_rect(center=(x, y))

    @classmethod
    def _load_sheet(cls):
        if cls._sheet is not None:
            return cls._sheet
        sheet_path = os.path.join(ASSETS_DIR, "sprites", "minion", "carl_minion_spritesheet.png")
        if not os.path.exists(sheet_path):
            return None
        sheet = pygame.image.load(sheet_path).convert_alpha()
        # vectorised background-removal via surfarray (numpy under the hood) —
        # way faster than a Python set_at loop over 850k+ pixels.
        rgb   = pygame.surfarray.pixels3d(sheet)
        alpha = pygame.surfarray.pixels_alpha(sheet)
        mask = None
        for r, g, b in cls._BG_COLOURS:
            m = (rgb[..., 0] == r) & (rgb[..., 1] == g) & (rgb[..., 2] == b)
            mask = m if mask is None else (mask | m)
        alpha[mask] = 0
        del rgb, alpha  # release the surface lock so the sheet is usable again
        cls._sheet = sheet
        return sheet

    @staticmethod
    def _make_image() -> pygame.Surface:
        surf = pygame.Surface((32, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, MINION_COLOUR, (4, 8, 24, 36))
        pygame.draw.ellipse(surf, (50, 50, 50), (10, 12, 12, 10))  # goggle frame
        pygame.draw.ellipse(surf, WHITE, (11, 13, 10, 8))           # goggle lens
        return surf


class UnstablePlatform:
    """A platform that breaks when Gru stands on it.

    I used a three-state machine: stable → cracking → falling.
    Once cracking starts, a tick counter runs; when it reaches CRACK_TICKS
    the platform switches to falling and gravity pulls it off screen.
    While cracking, the platform is still solid so Gru can still stand on it
    briefly — that's the intended one-second warning window from the storyboard.
    """

    STABLE   = "stable"
    CRACKING = "cracking"
    FALLING  = "falling"

    CRACK_TICKS = 60  # ~1 second at 60 FPS

    def __init__(self, rect: pygame.Rect):
        self.rect   = rect.copy()
        self.status = self.STABLE
        self.timer  = 0
        self.vy     = 0.0

    @property
    def active(self) -> bool:
        # only relevant while the rect is still on or above the screen
        return self.status != self.FALLING or self.rect.top < HEIGHT + 50

    def on_stood_upon(self):
        if self.status == self.STABLE:
            self.status = self.CRACKING
            self.timer  = 0

    def update(self):
        if self.status == self.CRACKING:
            self.timer += 1
            if self.timer >= self.CRACK_TICKS:
                self.status = self.FALLING
        elif self.status == self.FALLING:
            self.vy += GRAVITY
            self.rect.y += int(self.vy)

    def draw(self, surface: pygame.Surface, scroll_x: int):
        draw_rect = pygame.Rect(
            self.rect.x - scroll_x, self.rect.y,
            self.rect.width, self.rect.height
        )
        if self.status == self.STABLE:
            pygame.draw.rect(surface, PLAT_COLOUR, draw_rect)
        elif self.status == self.CRACKING:
            pygame.draw.rect(surface, UNSTABLE_COL, draw_rect)
            # two diverging lines to telegraph that the platform is splitting apart
            cx = draw_rect.centerx
            pygame.draw.line(surface, (200, 140, 80),
                             (cx, draw_rect.top), (cx + 12, draw_rect.bottom), 2)
            pygame.draw.line(surface, (200, 140, 80),
                             (cx, draw_rect.top), (cx - 8, draw_rect.bottom), 2)
        elif self.status == self.FALLING:
            pygame.draw.rect(surface, (100, 60, 30), draw_rect)


def _load_bg_layer(filename: str) -> pygame.Surface:
    path = os.path.join(ASSETS_DIR, "backgrounds", "city_night", filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (WIDTH, HEIGHT))


def _build_level() -> dict:
    """Define all platform positions and enemy/collectible placements.

    Everything is in world coordinates. The scene's scroll_x offset is
    subtracted only at draw time, so collision logic stays simple.
    """
    FLOOR_Y = HEIGHT - 60

    platforms = [
        pygame.Rect(0,    FLOOR_Y, 3000, 60),
        # low overhang near the start — bottom is 65 px above the floor,
        # same clearance as the sky-level crouch tunnel. standing Gru (70 tall)
        # doesn't fit under it; crouched Gru (35) does. think of this as the
        # tutorial for the crouch mechanic before the main tunnel later on.
        pygame.Rect(220,  575,     90, 20),
        pygame.Rect(300,  450,     200, 20),
        pygame.Rect(600,  360,     180, 20),
        pygame.Rect(900,  280,     200, 20),
        pygame.Rect(1200, 360,     180, 20),
        # sky-level crouch tunnel. the longer lower platform sits HIGHER than
        # step 4, so the player has to jump up to land on it. the shorter
        # upper platform hovers 65 px above; standing pose collides with it,
        # crouched pose slips through. the lower extends past the upper on
        # both sides so there's safe landing room outside the crouch zone.
        pygame.Rect(1400, 300,     300, 20),  # longer lower base
        pygame.Rect(1500, 215,     120, 20),  # shorter upper — raised 5 px for visual head clearance
        pygame.Rect(1800, 380,     180, 20),
        pygame.Rect(2100, 300,     200, 20),
        pygame.Rect(2400, 380,     200, 20),
        # second low overhang right before the final platform. same 65 px
        # floor clearance as the start one — forces a quick crouch on the
        # approach to the last collectible.
        pygame.Rect(2580, 575,     110, 20),
        pygame.Rect(2700, FLOOR_Y - 100, 300, 20),  # raised platform where the last part sits
    ]

    unstable = [
        UnstablePlatform(pygame.Rect(750,  400, 160, 20)),
        UnstablePlatform(pygame.Rect(1350, 310, 160, 20)),
        UnstablePlatform(pygame.Rect(1950, 340, 160, 20)),
    ]

    drones = pygame.sprite.Group(
        Drone(500,  350, patrol_range=120),
        Drone(1000, 240, patrol_range=150),
        Drone(1600, 380, patrol_range=130),
        Drone(2200, 280, patrol_range=110),
        Drone(2600, 350, patrol_range=140),
    )

    turrets = pygame.sprite.Group(
        # floor-level turrets use low_profile: 36 px visual, but only the
        # bottom 27 px is the actual hit rect. that means a crouching plasma
        # bolt (rect top y=634) lands a hit, while a standing bolt
        # (rect bottom y=633) flies right over them. so: only crouch-shoot kills.
        # note: y here is the hit-rect top, not the image top.
        Turret(850,  FLOOR_Y - 27, low_profile=True),
        Turret(2050, FLOOR_Y - 27, low_profile=True),
        # platform-mounted turrets stay full-size (48x48) — killable normally
        # from the platform Gru is standing on.
        Turret(1400, 316),
        Turret(2500, 336),
    )

    # parts are spread across the level so the player has to explore — including
    # one tucked inside the sky-level crouch tunnel (you have to crouch to grab it)
    # and one on the floor between the unstable platforms and the final stretch.
    parts = pygame.sprite.Group(
        ShrinkRayPart(920,  260, 0),
        ShrinkRayPart(1820, 360, 1),
        ShrinkRayPart(2750, FLOOR_Y - 130, 2),
        ShrinkRayPart(1560, 267, 3),  # inside the crouch tunnel — only reachable while crouched on the lower platform
        ShrinkRayPart(2250, 640, 4),  # on the floor between the unstable platform and step 8
    )

    minions = pygame.sprite.Group(
        MinionCollectible(430,  420),
        MinionCollectible(1100, 250),
        MinionCollectible(2300, 270),
    )

    return dict(platforms=platforms, unstable=unstable, drones=drones,
                turrets=turrets, parts=parts, minions=minions)


def scene2(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """Run Scene 2 — Vector's Fortress.

    Returns "scene3" when all five parts are collected, or "scene2" if Gru dies
    (which restarts the level from main.py's state machine).
    """
    pygame.display.set_caption("Scene 2 — Vector's Fortress")

    level_music_path = os.path.join(ASSETS_DIR, "music", "level1_great_mission.mp3")
    pygame.mixer.music.load(level_music_path)
    pygame.mixer.music.set_volume(0.55)
    pygame.mixer.music.play(-1)

    sfx_laser  = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "laser_freeze_ray.ogg"))
    sfx_hit    = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "minion_hit_1.wav"))
    sfx_laugh  = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "minion_laugh_1.wav"))
    sfx_yahoo  = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "minion_yahoo_2.wav"))
    sfx_scream = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "character_scream.wav"))
    sfx_start  = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "level_start.wav"))
    sfx_explode = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "explosion.wav"))
    sfx_explode.set_volume(0.7)
    sfx_start.play()

    # the laser sound file is ~40 seconds long, so we play it on a dedicated
    # channel and cap each play with maxtime. effect: each new shot replaces
    # the previous one (no stacking) and we only hear the first 300 ms = a zap.
    laser_channel = pygame.mixer.Channel(1)
    LASER_MAX_MS  = 300

    # three parallax background layers from assets/backgrounds/city_night/
    bg_sky   = _load_bg_layer("bg_composed.png")
    bg_back  = _load_bg_layer("city_back.png")
    bg_front = _load_bg_layer("city_front.png")

    level = _build_level()
    platforms = level["platforms"]
    unstable  = level["unstable"]
    drones    = level["drones"]
    turrets   = level["turrets"]
    parts     = level["parts"]
    minions   = level["minions"]

    # spawn directly on the floor (Gru.rect.bottom == FLOOR_Y) instead of dropping in from above
    gru = Gru(x=60, y=HEIGHT - 130)

    plasma_bolts = pygame.sprite.Group()
    enemy_shots = pygame.sprite.Group()
    vfx_group   = pygame.sprite.Group()

    scroll_x          = 0
    collected_parts   = 0
    quit_to_menu      = False
    restart_requested = False
    font = pygame.font.Font(None, 32)

    # turret fire timer — pygame queues a TURRET_FIRE_EVENT every 3 seconds
    # (same approach we used for the lab's countdown clock)
    pygame.time.set_timer(TURRET_FIRE_EVENT,    3000)
    pygame.time.set_timer(UNSTABLE_CRACK_EVENT, 1000)

    drone_shoot_timer = 0  # I track this with a tick counter rather than a USEREVENT to keep it simpler

    running = True
    while running:
        clock.tick(FPS)
        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == TURRET_FIRE_EVENT:
                # only on-screen turrets fire — offscreen ones feel unfair
                # because the player can't see the shot leaving the muzzle.
                view_left, view_right = scroll_x, scroll_x + WIDTH
                for turret in turrets:
                    if turret.rect.right < view_left or turret.rect.left > view_right:
                        continue
                    proj = turret.fire(gru.rect)
                    if proj:
                        enemy_shots.add(proj)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_result = run_pause(screen, clock)
                if pause_result == "menu":
                    quit_to_menu = True
                    running = False
                elif pause_result == "restart":
                    # bail out of this run; main.py sees "restart" and re-enters scene2 fresh
                    restart_requested = True
                    running = False
                else:  # "resume"
                    # pause replaced our level music with the menu track — restore it on resume
                    pygame.mixer.music.load(level_music_path)
                    pygame.mixer.music.set_volume(0.55)
                    pygame.mixer.music.play(-1)

        fired = gru.update(keys, events, platforms)
        if fired:
            ray, flash = fired
            plasma_bolts.add(ray)
            vfx_group.add(flash)
            laser_channel.play(sfx_laser, maxtime=LASER_MAX_MS)

        # world walls — clamp Gru's x to [0, WORLD_WIDTH - rect.width] so he
        # can't walk off either edge into empty space
        WORLD_WIDTH = platforms[0].right
        gru.rect.x = max(0, min(gru.rect.x, WORLD_WIDTH - gru.rect.width))

        # fall pit — if Gru drops off the bottom of the screen, just zero out
        # his HP and let the existing death sequence (scream + scene restart) handle it
        if gru.rect.top > HEIGHT:
            gru.hp = 0

        # camera follows Gru at the left third of the screen in BOTH directions
        # (walking back actually scrolls the world back). clamped to the world
        # bounds so we never expose empty space past the edge.
        scroll_x = gru.rect.centerx - WIDTH // 3
        scroll_x = max(0, min(scroll_x, WORLD_WIDTH - WIDTH))

        # if Gru is standing on an unstable platform, start its crack timer
        for up in unstable:
            if up.status == UnstablePlatform.STABLE and gru.rect.colliderect(up.rect):
                up.on_stood_upon()
            up.update()

        # only pass still-solid platforms to Gru's collision — falling ones shouldn't catch him
        unstable_rects = [
            up.rect for up in unstable
            if up.status in (UnstablePlatform.STABLE, UnstablePlatform.CRACKING)
        ]
        all_platforms = platforms + unstable_rects

        drones.update()
        turrets.update()
        plasma_bolts.update()
        enemy_shots.update()
        vfx_group.update()
        parts.update()

        # kill enemy shots once they pass below the floor surface so they don't
        # cross into the HUD area. shots fly freely through other platforms.
        floor_top = platforms[0].top
        for shot in list(enemy_shots):
            if shot.rect.top > floor_top:
                shot.kill()

        # drone shooting uses a frame counter rather than a USEREVENT — drones
        # fire less often than turrets, and I didn't want to burn another
        # global USEREVENT slot just for that.
        drone_shoot_timer += 1
        if drone_shoot_timer >= 120:  # ~2 seconds at 60 FPS
            drone_shoot_timer = 0
            view_left, view_right = scroll_x, scroll_x + WIDTH
            for drone in drones:
                if drone.rect.right < view_left or drone.rect.left > view_right:
                    continue
                proj = drone.shoot_at(gru.rect)
                if proj:
                    enemy_shots.add(proj)

        # plasma bolt hits — destroy the enemy outright. once it's killed, it's
        # gone from the sprite group, so subsequent bolts pass through empty
        # space and don't keep re-triggering the burst VFX.
        for ray in list(plasma_bolts):
            for drone in pygame.sprite.spritecollide(ray, drones, False):
                vfx_group.add(ExplosionVFX(ray.rect.centerx, ray.rect.centery, 1))
                sfx_explode.play()
                drone.kill()
                ray.kill()

        for ray in list(plasma_bolts):
            for turret in pygame.sprite.spritecollide(ray, turrets, False):
                vfx_group.add(ExplosionVFX(ray.rect.centerx, ray.rect.centery, 2))
                sfx_explode.play()
                turret.kill()
                ray.kill()

        if pygame.sprite.spritecollide(gru, enemy_shots, True):
            if gru.take_damage():
                sfx_hit.play()

        # bumping into a live drone directly also hurts Gru
        if pygame.sprite.spritecollide(gru, drones, False):
            unfrozen = [d for d in drones if not d.frozen]
            if unfrozen and any(gru.rect.colliderect(d.rect) for d in unfrozen):
                if gru.take_damage():
                    sfx_hit.play()

        for _ in pygame.sprite.spritecollide(gru, parts, True):
            collected_parts += 1
            sfx_yahoo.play()

        if pygame.sprite.spritecollide(gru, minions, True):
            if gru.hp < GRU_MAX_HP:
                gru.hp += 1
            sfx_laugh.play()

        # parallax: each background layer scrolls at a different fraction of scroll_x.
        # sky stays put (looks infinitely far away), back layer at 20%, front at 50% —
        # farther objects appear to move more slowly, which sells the depth effect.
        screen.blit(bg_sky, (0, 0))
        screen.blit(bg_back,  (-scroll_x * 0.2, 0))
        screen.blit(bg_front, (-scroll_x * 0.5, 0))

        for plat in platforms:
            draw_r = pygame.Rect(plat.x - scroll_x, plat.y, plat.width, plat.height)
            pygame.draw.rect(screen, PLAT_COLOUR, draw_r)

        for up in unstable:
            up.draw(screen, scroll_x)

        # helper: draw any sprite group with the camera scroll applied.
        # sprites can carry an optional `draw_offset` attribute to render
        # their image at a position other than rect.topleft — used by the
        # low-profile turret, where the visible art is bigger than the hit rect.
        def _draw_group(group):
            for sprite in group:
                ox, oy = getattr(sprite, "draw_offset", (0, 0))
                screen.blit(sprite.image, sprite.rect.move(-scroll_x + ox, oy))

        _draw_group(parts)
        _draw_group(minions)
        _draw_group(turrets)
        _draw_group(drones)
        _draw_group(plasma_bolts)
        _draw_group(enemy_shots)

        # Gru.draw() blits at self.rect, but self.rect is in WORLD coords.
        # we temporarily swap it for the screen-space rect so the blit lands
        # in the right place, then restore the world rect after — otherwise
        # physics next frame would think Gru moved by -scroll_x.
        saved_rect = gru.rect.copy()
        gru.rect   = gru.rect.move(-scroll_x, 0)
        gru.draw(screen)
        gru.rect   = saved_rect

        # vfx (muzzle flash, kill explosions) draws AFTER Gru — that way the
        # flash sits in front of his hand rather than getting hidden behind him.
        _draw_group(vfx_group)

        _draw_hud(screen, font, collected_parts, gru.hp)

        pygame.display.flip()

        if collected_parts >= 5:
            pygame.time.set_timer(TURRET_FIRE_EVENT, 0)
            pygame.time.set_timer(UNSTABLE_CRACK_EVENT, 0)
            pygame.mixer.music.stop()
            pygame.mixer.stop()  # also stop any in-flight Sound channels
            return "scene3"

        if gru.hp <= 0:
            sfx_scream.play()
            pygame.time.delay(800)
            pygame.time.set_timer(TURRET_FIRE_EVENT, 0)
            pygame.time.set_timer(UNSTABLE_CRACK_EVENT, 0)
            pygame.mixer.music.stop()
            pygame.mixer.stop()
            return "scene2"  # returning our own state name causes main.py to restart us

    pygame.time.set_timer(TURRET_FIRE_EVENT, 0)
    pygame.time.set_timer(UNSTABLE_CRACK_EVENT, 0)
    pygame.mixer.music.stop()
    pygame.mixer.stop()
    # restart_requested wins over quit_to_menu (the player picked RESTART LEVEL) —
    # main.py sees "restart" and re-enters scene2.
    if restart_requested:
        return "restart"
    return "menu"


def _draw_hud(surface: pygame.Surface, font: pygame.font.Font,
              collected: int, hp: int):
    parts_text = font.render(f"Shrink Ray Parts: {collected} / 5", True, YELLOW)
    surface.blit(parts_text, (WIDTH - parts_text.get_width() - 20, 20))

    hint_font = pygame.font.Font(None, 22)
    controls  = "Arrow Keys: Move  |  Up: Jump  |  Down: Crouch  |  Space: Plasma Blaster  |  ESC: Menu"
    hint = hint_font.render(controls, True, (160, 160, 160))
    surface.blit(hint, (10, HEIGHT - 30))
