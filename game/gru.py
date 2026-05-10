import os
import pygame
from settings import (
    ASSETS_DIR, GRAVITY, MAX_FALL_SPEED, GRU_SPEED, GRU_JUMP,
    FREEZE_RAY_SPEED, GRU_MAX_HP, INVINCIBILITY_FRAMES, FRAME_DURATION,
    WIDTH, WHITE, RED, GREEN
)


# loads a numbered PNG sequence from a folder — e.g. idle0.png, idle1.png, idle2.png...
def _load_frames(folder: str, prefix: str, count: int) -> list:
    frames = []
    for i in range(count):
        path = os.path.join(folder, f"{prefix}{i}.png")
        img = pygame.image.load(path).convert_alpha()
        frames.append(img)
    return frames


class PlasmaBolt(pygame.sprite.Sprite):
    """Single plasma-blaster bolt. Travels horizontally until it hits something
    or has flown roughly one screen's width — using travel distance rather than
    an absolute world-x bound, since scrolling levels can be several screens wide.
    """

    MAX_TRAVEL = WIDTH  # roughly one screen worth of horizontal travel before the bolt fizzles out

    def __init__(self, x: int, y: int, facing_right: bool):
        super().__init__()
        sheet_path = os.path.join(ASSETS_DIR, "sprites", "vfx", "bullets_projectiles.png")
        # the sheet's "transparent" background is actually opaque black
        # (alpha=255 everywhere). loading with .convert() + a colorkey on
        # pure black drops the surrounds so only the sprite shows.
        sheet = pygame.image.load(sheet_path).convert()
        sheet.set_colorkey((0, 0, 0))
        self.image = sheet.subsurface(pygame.Rect(0, 0, 32, 16)).copy()
        self.image = pygame.transform.scale(self.image, (40, 16))
        if not facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect()
        self.rect.centery = y
        self.rect.x = x if facing_right else x - self.rect.width
        self.dx = FREEZE_RAY_SPEED if facing_right else -FREEZE_RAY_SPEED
        self._travelled = 0

    def update(self):
        self.rect.x += self.dx
        self._travelled += abs(self.dx)
        if self._travelled >= self.MAX_TRAVEL:
            self.kill()


class ExplosionVFX(pygame.sprite.Sprite):
    """A fireball that scales from small to full-size over a duration, then
    disappears. Used as the kill flash on enemies — visually reads as 'BOOM'
    rather than 'cloud of particles'.

    Source sprite is the peak-fireball frame from explosion_sheet_1.png
    (row 3, col 0), cached at class level so it's only loaded once.
    """

    _BASE_FRAME = None  # peak-fireball source surface — loaded once, shared across all instances

    def __init__(self, cx: int, cy: int, sheet_index: int = 1,
                 duration_ticks: int = 48, max_size: int = 96):
        super().__init__()
        self._load_base(sheet_index)
        self._cx, self._cy = cx, cy
        self._duration = duration_ticks
        self._max_size = max_size
        self._tick = 0
        self.image = pygame.transform.scale(self._BASE_FRAME, (max(1, max_size // 5),
                                                               max(1, max_size // 5)))
        self.rect = self.image.get_rect(center=(cx, cy))

    @classmethod
    def _load_base(cls, sheet_index: int):
        if cls._BASE_FRAME is not None:
            return
        path = os.path.join(
            ASSETS_DIR, "sprites", "vfx", f"explosion_sheet_{sheet_index}.png"
        )
        sheet = pygame.image.load(path).convert_alpha()
        # the sheet is an 8x8 grid; row 3 col 0 happens to be the peak fireball frame we want
        frame_size = sheet.get_width() // 8
        cls._BASE_FRAME = sheet.subsurface(
            pygame.Rect(0, 3 * frame_size, frame_size, frame_size)
        ).copy()

    def update(self):
        self._tick += 1
        if self._tick >= self._duration:
            self.kill()
            return
        # ease-out curve: fast growth early, slowing as it nears full size.
        # we start at 30% (not 0%) so the explosion is visible from frame 1 —
        # otherwise the visual lags behind the boom of the sound.
        progress = self._tick / self._duration
        eased = 1 - (1 - progress) ** 2
        size = int(self._max_size * (0.3 + 0.7 * eased))
        self.image = pygame.transform.scale(self._BASE_FRAME, (size, size))
        self.rect = self.image.get_rect(center=(self._cx, self._cy))


class MuzzleFlash(pygame.sprite.Sprite):
    """Short-lived plasma-blaster muzzle flash — plays shot0..shot3 once at the gun tip.

    The shot/*.png frames are particle effects, not character frames, so they
    can't be used as Gru's animation directly (it makes him disappear). Instead
    they live as a separate VFX sprite anchored at the firing position.
    """

    def __init__(self, x: int, y: int, facing_right: bool):
        super().__init__()
        folder = os.path.join(ASSETS_DIR, "sprites", "gru", "shot")
        self.frames = _load_frames(folder, "shot", 4)
        if not facing_right:
            self.frames = [pygame.transform.flip(f, True, False) for f in self.frames]
        self.frame_index = 0
        self.frame_timer = 0
        self.image = self.frames[0]
        # anchor flush against the gun tip so the flash sits right at Gru's hand
        anchor_kwargs = {"midleft": (x, y)} if facing_right else {"midright": (x, y)}
        self.rect = self.image.get_rect(**anchor_kwargs)

    def update(self):
        self.frame_timer += 1
        if self.frame_timer >= FRAME_DURATION:
            self.frame_timer = 0
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.kill()
                return
            self.image = self.frames[self.frame_index]


class Gru(pygame.sprite.Sprite):
    """Playable character — R1 responsibility.

    Controls:
      Left / Right arrows  — walk
      Up arrow or W        — jump (only while on the ground)
      Down arrow or S      — crouch
      SPACE                — shoot plasma blaster
    """

    STATES = ("idle", "walk", "jump", "crouch", "hurt", "dead")

    def __init__(self, x: int, y: int):
        super().__init__()
        self.vx = 0.0
        self.vy = 0.0
        self.hp = GRU_MAX_HP
        self.facing_right = True
        self.on_ground = False
        self.state = "idle"
        self.frame_index = 0
        self.frame_timer = 0       # tick counter for animation frame stepping (same pattern as the lab's countdown timer)
        self.iframes = 0           # invincibility frames remaining after a hit
        self.shoot_cooldown = 0    # gates SPACE so we don't fire every single tick
        self._state_lock = 0       # blocks state changes until the current animation has played out (hurt, etc.)
        self.jump_buffer = 0       # ticks left to honour a queued jump press — forgives slightly-early jump inputs

        self.animations = self._load_animations()
        self.image = self.animations["idle"][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        # standing vs crouching hitbox heights — width is fixed for both.
        # draw() bottom-aligns the sprite to the rect, so when we shrink the
        # rect for a crouch, Gru's feet stay on the floor (he doesn't levitate).
        self.standing_height = self.rect.height
        self.crouch_height   = self.rect.height // 2
        self.is_crouched     = False

        bar_dir = os.path.join(ASSETS_DIR, "sprites", "gru", "hp_bar")
        self._bar_img    = pygame.image.load(os.path.join(bar_dir, "bar.png")).convert_alpha()
        self._border_img = pygame.image.load(os.path.join(bar_dir, "border.png")).convert_alpha()

    def _load_animations(self) -> dict:
        gru_dir = os.path.join(ASSETS_DIR, "sprites", "gru")
        anims = {}

        iceray = os.path.join(gru_dir, "iceray")
        anims["idle"]   = _load_frames(os.path.join(iceray, "idle"),  "idle",  4)
        anims["walk"]   = _load_frames(os.path.join(iceray, "walk"),  "walk",  6)
        anims["jump"]   = _load_frames(os.path.join(iceray, "jump"),  "jump",  1)
        anims["crouch"] = _load_frames(os.path.join(iceray, "crouch"), "crouch", 1)
        anims["hurt"]   = _load_frames(os.path.join(iceray, "electrified"), "electrified", 2)

        # note: the shot/*.png frames are muzzle-flash particles, NOT character frames.
        # they're handled by the MuzzleFlash sprite separately, not as a Gru animation.

        # we don't have a dedicated death animation, so I reuse the "knock" frames
        anims["dead"] = _load_frames(
            os.path.join(gru_dir, "unequipped", "knock"), "knock", 5
        )

        return anims

    def handle_input(self, keys, events) -> "PlasmaBolt | None":
        """Read player input and return a PlasmaBolt if the player fired, else None.

        I split input into two types: held keys (key.get_pressed) for walking
        and crouching, and KEYDOWN events for jumping and shooting so those
        actions only trigger once per press rather than every tick.
        """
        fired = None

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    # buffer the jump press — update() actually triggers it once on_ground is true
                    self.jump_buffer = 6
                if event.key == pygame.K_SPACE and self.shoot_cooldown == 0:
                    fired = self.shoot()

        # block movement while a locked animation is playing (e.g. hurt) so the player can't override it
        if self._state_lock == 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx = -GRU_SPEED
                self.facing_right = False
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx = GRU_SPEED
                self.facing_right = True
            else:
                self.vx = 0

        return fired

    def apply_gravity(self):
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

    def move_and_collide(self, platforms: list):
        """Move Gru and push him out of any platform he overlaps.

        I handle horizontal and vertical movement in separate passes so that
        corner collisions resolve cleanly — if you do both axes at once you
        get stuck on walls when landing.
        """
        # horizontal pass
        self.rect.x += int(self.vx)
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vx > 0:
                    self.rect.right = plat.left
                elif self.vx < 0:
                    self.rect.left = plat.right
                self.vx = 0

        # vertical pass. we decide on_ground AFTER the move using a 1-px down probe.
        # why: at low vy (e.g. 0.6 right after landing) int() truncates to 0, so
        # the rect doesn't overlap the platform this frame. if we relied on
        # "did we collide this frame?" alone, on_ground would flicker every
        # other frame — making Gru jitter and freezing his animation on frame 0.
        landed = False
        self.rect.y += int(self.vy)
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vy > 0:
                    self.rect.bottom = plat.top
                    landed = True
                elif self.vy < 0:
                    self.rect.top = plat.bottom
                self.vy = 0

        if landed:
            self.on_ground = True
        elif self.vy < 0:
            self.on_ground = False  # mid-jump (rising)
        else:
            probe = self.rect.move(0, 1)
            self.on_ground = any(probe.colliderect(p) for p in platforms)

    def shoot(self):
        """Spawn a plasma bolt and a muzzle-flash VFX. Returns (bolt, flash).

        Walk/idle/jump animations continue normally during fire — no state lock,
        because the muzzle flash is rendered as a separate sprite rather than
        replacing Gru's body for the shoot duration.
        """
        self.shoot_cooldown = 20
        tip_x = self.rect.right if self.facing_right else self.rect.left
        ray   = PlasmaBolt(tip_x, self.rect.centery, self.facing_right)
        flash = MuzzleFlash(tip_x, self.rect.centery, self.facing_right)
        return ray, flash

    def take_damage(self) -> bool:
        """Apply 1 HP of damage. Returns True if damage was applied, False if
        the hit was absorbed by invincibility frames (caller can use this to
        avoid e.g. retriggering the hit sfx on every bullet during iframes)."""
        if self.iframes > 0:
            return False
        self.hp -= 1
        self.iframes = INVINCIBILITY_FRAMES
        self._set_state("hurt")
        self._state_lock = len(self.animations["hurt"]) * FRAME_DURATION * 2
        return True

    def _set_state(self, new_state: str):
        # only reset the frame counter when the state actually changes — otherwise
        # walk/idle would restart from frame 0 every tick and look stuttery
        if self.state != new_state:
            self.state = new_state
            self.frame_index = 0
            self.frame_timer = 0

    def _update_crouch_rect(self, keys, platforms):
        """Resize the collision rect based on whether Gru is ducking.

        When standing up under a low ceiling, the rect would re-grow into a
        platform — so we probe with the full-height rect first and stay crouched
        if it would collide. This is the standard 'low ceiling' pattern from
        platformers like Mario / Mega Man.
        """
        wants_crouch = (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.on_ground

        if wants_crouch and not self.is_crouched:
            bottom = self.rect.bottom
            self.rect.height = self.crouch_height
            self.rect.bottom = bottom
            self.is_crouched = True
        elif not wants_crouch and self.is_crouched:
            bottom = self.rect.bottom
            candidate = pygame.Rect(self.rect.x, bottom - self.standing_height,
                                    self.rect.width, self.standing_height)
            if not any(candidate.colliderect(p) for p in platforms):
                self.rect = candidate
                self.is_crouched = False
            # else: there's a ceiling above us — stay crouched until it clears

    def _update_state(self, keys):
        if self._state_lock > 0:
            return  # don't interrupt — let the locked animation play out

        if not self.on_ground:
            self._set_state("jump")
        elif self.is_crouched:
            # use the physical crouch flag (not the key) so the crouch pose
            # holds even after the player releases DOWN under a low ceiling.
            self._set_state("crouch")
        elif self.vx != 0:
            self._set_state("walk")
        else:
            self._set_state("idle")

    def _advance_frame(self):
        """Step to the next animation frame every FRAME_DURATION ticks.

        I count ticks with frame_timer rather than using real time — this is
        the same approach we used for the countdown timer in the lab, just
        applied to animation instead of a clock.
        """
        frames = self.animations[self.state]
        self.frame_timer += 1
        if self.frame_timer >= FRAME_DURATION:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames)

    def update(self, keys, events, platforms: list):
        fired = self.handle_input(keys, events)

        self.apply_gravity()
        self.move_and_collide(platforms)

        # consume any buffered jump now that on_ground has been computed for this frame
        if self.jump_buffer > 0:
            if self.on_ground and self._state_lock == 0:
                self.vy = GRU_JUMP
                self.on_ground = False
            self.jump_buffer -= 1

        self._update_crouch_rect(keys, platforms)
        self._update_state(keys)
        self._advance_frame()

        if self._state_lock > 0:
            self._state_lock -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.iframes > 0:
            self.iframes -= 1

        # flip the sprite horizontally so Gru faces whichever direction he last moved
        frame = self.animations[self.state][self.frame_index]
        self.image = pygame.transform.flip(frame, not self.facing_right, False)

        return fired  # the caller adds this to the plasma_bolts group (see scene2)

    def draw(self, surface: pygame.Surface):
        # blink Gru during iframes: skip every other 6-tick window. dividing
        # iframes by 6 then checking even/odd gives a steady, non-distracting blink.
        if self.iframes > 0 and (self.iframes // 6) % 2 == 0:
            return

        # we anchor the image by midbottom so Gru's feet stay on the floor when
        # the collision rect shrinks for a crouch — otherwise the sprite would
        # appear to float / clip up.
        img_rect = self.image.get_rect(midbottom=self.rect.midbottom)
        surface.blit(self.image, img_rect)
        self._draw_hp_bar(surface)

    def _draw_hp_bar(self, surface: pygame.Surface):
        # one pip per max HP — filled bar for remaining health, empty border for lost
        bar_x, bar_y = 20, 20
        pip_w = self._bar_img.get_width()
        for i in range(GRU_MAX_HP):
            blit_img = self._bar_img if i < self.hp else self._border_img
            surface.blit(blit_img, (bar_x + i * (pip_w + 4), bar_y))
