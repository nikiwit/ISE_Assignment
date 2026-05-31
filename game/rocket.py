import pygame
from settings import ASSETS_DIR, WIDTH, HEIGHT, WHITE
import os
import random
import math

DISTANCE_GOAL = 2400
FUEL_MAX = 100
FUEL_DRAIN = 0.08
BOOST_FUEL_COST = 0.14
DASH_FUEL_COST = 0.22
ASTEROID_INTERVAL = 48
COMET_INTERVAL = 160
FUEL_INTERVAL = 260
INVINCIBILITY_FRAMES = 90

BASE_SPEED = 4.8
BOOST_SPEED = 8.2
DASH_SPEED = 14
INVINCIBLE_SPEED = 3.5

ROCKET_SIZE = (96, 64)
ROCKET_MAX_HP = 3

def _load_image(path, fallback_size=None):
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    if fallback_size is None:
        fallback_size = (48, 48)
    fallback = pygame.Surface(fallback_size, pygame.SRCALPHA)
    pygame.draw.polygon(fallback, WHITE, [(0, 0), (fallback_size[0] - 2, fallback_size[1] // 2), (0, fallback_size[1])])
    return fallback


class Asteroid(pygame.sprite.Sprite):
    _IMAGES = None

    def __init__(self, speed_scale=1.0):
        super().__init__()
        self.image = self._choose_image()
        self.rect = self.image.get_rect()
        self.rect.right = WIDTH + random.randint(20, 120)
        self.rect.y = random.randint(40, HEIGHT - 80)
        self.speed = random.uniform(4.0, 7.2) * speed_scale
        self.speed_multiplier = 1.0
        self.mask = pygame.mask.from_surface(self.image)

    @classmethod
    def _choose_image(cls):
        if cls._IMAGES is None:
            cls._IMAGES = []
            folder = os.path.join(ASSETS_DIR, "sprites", "space_objects", "asteroid")
            if os.path.isdir(folder):
                for name in sorted(os.listdir(folder)):
                    lower = name.lower()
                    if lower in ("asteroid1.png", "asteroid2.png"):
                        cls._IMAGES.append(pygame.image.load(os.path.join(folder, name)).convert_alpha())
            if not cls._IMAGES:
                surf = pygame.Surface((48, 48), pygame.SRCALPHA)
                pygame.draw.circle(surf, (130, 110, 80), (24, 24), 22)
                cls._IMAGES.append(surf)
        base = random.choice(cls._IMAGES)
        scale = random.uniform(0.55, 1.45)
        size = (max(24, int(base.get_width() * scale)), max(24, int(base.get_height() * scale)))
        return pygame.transform.smoothscale(base, size)

    def update(self):
        self.rect.x -= int(self.speed * self.speed_multiplier)
        if self.rect.right < -40:
            self.kill()


class BrokenAsteroid(pygame.sprite.Sprite):
    _FRAMES = None

    def __init__(self, center):
        super().__init__()
        self.frames = self._load_frames()
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=center)
        self.timer = 0

    @classmethod
    def _load_frames(cls):
        if cls._FRAMES is not None:
            return cls._FRAMES
        cls._FRAMES = []
        folder = os.path.join(ASSETS_DIR, "sprites", "space_objects", "asteroid")
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                lower = name.lower()
                if lower in ("asteroid3.png", "asteroid4.png", "asteroid5.png", "asteroid6.png", "asteroid7.png"):
                    cls._FRAMES.append(pygame.image.load(os.path.join(folder, name)).convert_alpha())
        if not cls._FRAMES:
            surf = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 120, 60), (24, 24), 22)
            cls._FRAMES = [surf]
        return cls._FRAMES

    def update(self):
        self.timer += 1
        if self.timer >= 6:
            self.timer = 0
            self.index += 1
            if self.index >= len(self.frames):
                self.kill()
                return
            self.image = self.frames[self.index]


class Comet(pygame.sprite.Sprite):
    """Comet that enters from the top-right area and travels toward the bottom-left.

    Spawn: the comet starts fully *above* the screen so its bottom edge is at y=0
    (i.e. it is not yet visible). This prevents the "sudden pop" on entry.
    Kill: once the comet's *top* edge has passed below HEIGHT (fully off-screen at the
    bottom) or its *right* edge is off the left side, so it never vanishes mid-frame.
    """

    _IMAGE = None

    # Comet size is kept compact: scale between 0.30 and 0.46 of the source image.
    _SCALE_MIN = 0.30
    _SCALE_MAX = 0.46

    def __init__(self):
        super().__init__()
        base = self._load_image()
        scale = random.uniform(self._SCALE_MIN, self._SCALE_MAX)
        w = max(18, int(base.get_width() * scale))
        h = max(18, int(base.get_height() * scale))
        self.image = pygame.transform.smoothscale(base, (w, h))
        self.mask = pygame.mask.from_surface(self.image)

        # Horizontal spawn: right third of the screen so it always comes from
        # the top-right region.
        spawn_x = random.randint(int(WIDTH * 0.5), WIDTH +20)

        # Start fully above the screen: rect.bottom == 0 means the sprite is
        # just touching the top edge but not yet visible.
        self.rect = self.image.get_rect()
        self.rect.bottom = 0
        self.rect.left = spawn_x

        # Float position for sub-pixel accuracy (avoids jitter from int casting).
        self.fx = float(self.rect.x)
        self.fy = float(self.rect.y)

        # Travel direction: mostly downward with a leftward component.
        # Angle 200–230° in standard math coords → down-left.
        angle = random.uniform(120, 150)
        speed = random.uniform(5.5, 7.5)
        self.vx = math.cos(math.radians(angle)) * speed
        self.vy = math.sin(math.radians(angle)) * speed

        self.speed_multiplier = 1.0

    @classmethod
    def _load_image(cls):
        if cls._IMAGE is None:
            path = os.path.join(ASSETS_DIR, "sprites", "space_objects", "comet", "comet.png")
            cls._IMAGE = _load_image(path, fallback_size=(64, 24))
        return cls._IMAGE

    def update(self):
        self.fx += self.vx * self.speed_multiplier
        self.fy += self.vy * self.speed_multiplier
        self.rect.x = int(self.fx)
        self.rect.y = int(self.fy)

        # Kill only when the sprite is *completely* off-screen so there is no
        # sudden disappearance while part of it is still visible.
        fully_below = self.rect.top > HEIGHT + 20
        fully_left = self.rect.right < -20
        fully_right = self.rect.left > WIDTH + 20
        if fully_below or fully_left or fully_right:
            self.kill()


class FuelCanister(pygame.sprite.Sprite):
    _IMAGE = None

    def __init__(self):
        super().__init__()
        self.image = self._load_image()
        self.rect = self.image.get_rect()
        self.rect.right = WIDTH + 40
        self.rect.y = random.randint(60, HEIGHT - 70)
        self.speed = 5.0
        self.mask = pygame.mask.from_surface(self.image)

    @classmethod
    def _load_image(cls):
        if cls._IMAGE is None:
            path = os.path.join(ASSETS_DIR, "sprites", "fuel", "fuel.webp")
            loaded = _load_image(path, fallback_size=(64, 64))
            fuel_sprite = pygame.transform.smoothscale(loaded, (56, 56))

            # Enhanced glow: larger canvas, more glow layers with richer colours.
            canvas_size = 108
            half = canvas_size // 2
            glow = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)

            # Outer soft halo (yellow-orange)
            for radius, alpha in [
                (50, 10),
                (44, 22),
                (38, 38),
                (31, 58),
                (24, 85),
                (17, 118),
                (11, 150),
            ]:
                pygame.draw.circle(glow, (255, 210, 60, alpha), (half, half), radius)

            # Inner bright white-yellow core highlight
            pygame.draw.circle(glow, (255, 255, 200, 60), (half, half), 9)

            glow.blit(fuel_sprite, fuel_sprite.get_rect(center=(half, half)))
            cls._IMAGE = glow
        return cls._IMAGE

    def update(self):
        self.rect.x -= int(self.speed)
        if self.rect.right < -20:
            self.kill()


class Health_Display (pygame.sprite.Sprite):
    _FRAMES = None
    
    def __init__(self, number):
        super().__init__()
        self.frames = self._load_frames()
        self.index = 0
        self.timer = 15
        self.waiting = 3
        self.number = number
        
    def draw(self, surface, center, lighter_color = False):
        img = self.frames[self.index]
        if lighter_color:
            img = img.copy()
            img.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
        rect = img.get_rect(center=center)
        surface.blit(img, rect)
        
        self.timer -= 1
        if self.timer <= 0:
            self.timer = 15
            if self.waiting > 0:
                self.waiting -= 1
            else:
                self.index = (self.index + 1) % len(self.frames)
                if self.index == 0:
                    self.waiting = 3
    
    @classmethod
    def _load_frames(cls):
        if cls._FRAMES is not None:
            return cls._FRAMES
        cls._FRAMES = []
        folder = os.path.join(ASSETS_DIR, "sprites", "rocket", "heart")
        if os.path.isdir(folder):
            sortedFiles = sorted(os.listdir(folder))
            for i in range(len(sortedFiles)):
                img = pygame.image.load(os.path.join(folder, sortedFiles[i])).convert_alpha()
                img = pygame.transform.smoothscale(img, (32, 32))
                cls._FRAMES.append(img)
                
            for i in range(0, len(sortedFiles)-1):
                img = pygame.image.load(os.path.join(folder, sortedFiles[i])).convert_alpha()
                img = pygame.transform.smoothscale(img, (32, 32))
                img = pygame.transform.flip(img, True, False)
                cls._FRAMES.append(img)
                    
        if not cls._FRAMES:
            surf = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 120, 60), (24, 24), 22)
            cls._FRAMES = [surf]
        return cls._FRAMES

class Rocket(pygame.sprite.Sprite):
    _IMAGE = None
    _TURBO_FRAMES = None

    def __init__(self, boost_sound, dash_sound, posthit_sound, explosion_sound):
        super().__init__()
        self.image = self._load_image()
        self.rect = self.image.get_rect(center=(WIDTH * 0.18, HEIGHT // 2))
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = pygame.Vector2(self.rect.center)
        self.health_sprites = [Health_Display(i) for i in range(ROCKET_MAX_HP)]
        self.health = ROCKET_MAX_HP
        self.fuel = FUEL_MAX
        self.distance = 0.0
        self.invincible = False
        self.inv_timer = 0
        self.blink_timer = 0
        self.boost_sound = boost_sound
        self.dash_sound = dash_sound
        self.posthit_sound = posthit_sound
        self.explosion_sound = explosion_sound
        self._turbo_index = 0
        self._turbo_timer = 0
        self._shift = False
        self._space = False
        self._boosting = False
        self._blast_loop_pending = False
        self._blast_channel = None
        self._boost_channel = None
        self.empty_fuel_active = False

        # --- Explosion animation state ---
        self.exploding = False
        self.explosion_timer = 0
        self.explosion_done = False
        # Particle list: each entry is [x, y, vx, vy, radius, colour, life, max_life]
        self._explosion_particles = []

        self.turbo_stage = self._get_turbo_stage()

        # Boost spark particles: [x, y, vx, vy, radius, life, max_life]
        self._sparks = []
        
        # Screen Border Flash States
        self.damage_alpha = 0.0
        
        # Mouse control states
        self.mouse_left = False
        self.mouse_right = False
        self.mouse_up = False
        self.mouse_down = False

    @classmethod
    def _load_image(cls):
        if cls._IMAGE is None:
            path = os.path.join(ASSETS_DIR, "sprites", "rocket", "rocket.png")
            original = _load_image(path, fallback_size=ROCKET_SIZE)
            rotated = pygame.transform.rotozoom(original, -90, 1.0)
            cls._IMAGE = pygame.transform.smoothscale(rotated, ROCKET_SIZE)
        return cls._IMAGE

    @classmethod
    def _load_turbo_frames(cls):
        if cls._TURBO_FRAMES is not None:
            return
        cls._TURBO_FRAMES = []
        folder = os.path.join(ASSETS_DIR, "sprites", "rocket", "turbo")
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if name.lower().endswith((".png", ".webp")):
                    frame = pygame.image.load(os.path.join(folder, name)).convert_alpha()
                    frame = pygame.transform.flip(frame, True, False)
                    cls._TURBO_FRAMES.append(frame)
        if not cls._TURBO_FRAMES:
            frame = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.polygon(frame, (255, 180, 32), [(0, 0), (16, 32), (32, 0)])
            cls._TURBO_FRAMES = [pygame.transform.flip(frame, True, False)]

    def take_damage(self):
        if self.invincible or self.exploding:
            return False
        self.health -= 1
        self.invincible = True
        self.inv_timer = INVINCIBILITY_FRAMES
        self.blink_timer = 0
        
        # Trigger full-intensity red border on hit
        self.damage_alpha = 255.0
        
        if self.posthit_sound:
            self.posthit_sound.play()
        if self.health <= 0:
            self.start_explosion()
        return True

    def start_explosion(self):
        self.exploding = True
        self.explosion_timer = 0
        self.explosion_done = False
        if self.explosion_sound:
            self.explosion_sound.play()
        self._stop_blast_loop()
        self._spawn_explosion_particles()

    def _spawn_explosion_particles(self):
        """Seed the particle burst used for the death explosion."""
        self._explosion_particles = []
        cx, cy = self.rect.center
        colours = [
            (255, 240, 100),
            (255, 180, 40),
            (255, 100, 30),
            (255, 60, 20),
            (200, 200, 200),
            (255, 255, 255),
        ]
        for _ in range(48):
            angle = random.uniform(0, 360)
            speed = random.uniform(1.2, 6.5)
            vx = math.cos(math.radians(angle)) * speed
            vy = math.sin(math.radians(angle)) * speed
            radius = random.randint(3, 9)
            colour = random.choice(colours)
            life = random.randint(28, 55)
            self._explosion_particles.append([float(cx), float(cy), vx, vy, radius, colour, life, life])

    def _is_channel_playing(self, channel):
        return channel is not None and channel.get_busy()

    def _start_blast_loop(self):
        if self.dash_sound and not self._is_channel_playing(self._blast_channel):
            self._blast_channel = self.dash_sound.play(-1)

    def _stop_blast_loop(self):
        if self._blast_channel is not None:
            self._blast_channel.stop()
            self._blast_channel = None

    def handle_input(self, keys, mouse = False):
        self._left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        self._right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self._up = keys[pygame.K_UP] or keys[pygame.K_w]
        self._down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        self._shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self._space = keys[pygame.K_SPACE]
        
        if mouse and not (self._left or self._right or self._up or self._down):
            pos = pygame.mouse.get_pos()
            
            dx = pos[0] - self.rect.centerx
            dy = pos[1] - self.rect.centery

            start_threshold = 30
            stop_threshold = 12

            # LEFT
            if self.mouse_left:
                self.mouse_left = dx < -stop_threshold
            else:
                self.mouse_left = dx < -start_threshold

            # RIGHT
            if self.mouse_right:
                self.mouse_right = dx > stop_threshold
            else:
                self.mouse_right = dx > start_threshold

            # UP
            if self.mouse_up:
                self.mouse_up = dy < -stop_threshold
            else:
                self.mouse_up = dy < -start_threshold

            # DOWN
            if self.mouse_down:
                self.mouse_down = dy > stop_threshold
            else:
                self.mouse_down = dy > start_threshold

            self._left = self.mouse_left
            self._right = self.mouse_right
            self._up = self.mouse_up
            self._down = self.mouse_down
            
        else:
            self.mouse_left = False
            self.mouse_right = False
            self.mouse_up = False
            self.mouse_down = False
            

    def update(self):
        # Always tick explosion particles so the animation plays out
        self._update_explosion_particles()

        if self.exploding:
            self.explosion_timer += 1
            # Wait for all particles to fade before signalling done
            if self.explosion_timer >= 60 and not self._explosion_particles:
                self.explosion_done = True
            return

        # Block all controls when fuel is empty (unless fuel was just collected,
        # which is handled in scene4 by setting empty_fuel_active = False before
        # this update runs).
        if self.empty_fuel_active and self.fuel <= 0:
            self._left = self._right = self._up = self._down = self._shift = self._space = False

        boosting = (self._shift or self._space) and self.fuel > 0

        if boosting:
            if not self._boosting:
                self._boosting = True
                if self.boost_sound:
                    self._boost_channel = self.boost_sound.play()
                self._blast_loop_pending = True
            if self._boost_channel is None or not self._is_channel_playing(self._boost_channel):
                self._start_blast_loop()
            if self._space:
                self.fuel -= DASH_FUEL_COST
            else:
                self.fuel -= BOOST_FUEL_COST
        else:
            self._boosting = False
            self._blast_loop_pending = False
            self._stop_blast_loop()

        self.fuel -= FUEL_DRAIN
        self.fuel = max(0.0, min(FUEL_MAX, self.fuel))

        if self.invincible:
            speed = INVINCIBLE_SPEED
        elif self._space and self.fuel > 0:
            speed = DASH_SPEED
        elif self._shift and self.fuel > 0:
            speed = BOOST_SPEED
        else:
            speed = BASE_SPEED

        move_x = 0
        move_y = 0
        if self._left:
            move_x -= 1
        if self._right:
            move_x += 1
        if self._up:
            move_y -= 1
        if self._down:
            move_y += 1

        if move_x != 0 or move_y != 0:
            direction = pygame.Vector2(move_x, move_y)
            direction.normalize_ip()
            self.pos += direction * speed

        self.pos.x += 0.7
        self.pos.x = max(64, min(WIDTH - 72, self.pos.x))
        self.pos.y = max(64, min(HEIGHT - 64, self.pos.y))
        self.rect.center = self.pos

        if self.invincible:
            self.inv_timer -= 1
            self.blink_timer = (self.blink_timer + 1) % 16
            if self.inv_timer <= 0:
                self.invincible = False
                self.blink_timer = 0

        self.turbo_stage = self._get_turbo_stage()
        if self.fuel == 0:
            self._boosting = False
            self._blast_loop_pending = False
            self.empty_fuel_active = True
            self._stop_blast_loop()
        elif self.empty_fuel_active and self.fuel > 0:
            self.empty_fuel_active = False

        self._turbo_timer += 1
        if self._turbo_timer >= 6:
            self._turbo_timer = 0
            self._turbo_index = (self._turbo_index + 1) % max(1, len(self._get_turbo_frames()))

        self.distance += speed * 0.24

        # Emit boost sparks
        if self._boosting and self.fuel > 0:
            self._emit_boost_sparks()

        # Tick existing sparks
        self._update_sparks()
        
        # Fade out the damage overlay frame-by-frame
        if self.damage_alpha > 0:
            self.damage_alpha = max(0, self.damage_alpha - 5)

    def _emit_boost_sparks(self):
        """Spawn a few spark particles at the back of the rocket."""
        base_x = float(self.rect.left) - 4
        base_y = float(self.rect.centery)
        for _ in range(3):
            spread_y = random.uniform(-10, 10)
            vx = random.uniform(-10, -3)
            vy = random.uniform(-2, 2)
            radius = random.randint(3, 7)
            life = random.randint(30, 50)
            self._sparks.append([base_x, base_y + spread_y, vx, vy, radius, life, life])

    def _update_sparks(self):
        next_sparks = []
        for s in self._sparks:
            s[0] += s[2]   # x += vx
            s[1] += s[3]   # y += vy
            s[5] -= 1      # life countdown
            if s[5] > 0:
                next_sparks.append(s)
        self._sparks = next_sparks

    def _update_explosion_particles(self):
        next_p = []
        for p in self._explosion_particles:
            p[0] += p[2]   # x
            p[1] += p[3]   # y
            # p[3] += 0.18   # gravity
            p[6] -= 1      # life
            if p[6] > 0:
                next_p.append(p)
        self._explosion_particles = next_p

    def _get_turbo_frames(self):
        self._load_turbo_frames()
        return self._TURBO_FRAMES

    def _turbo_scale(self):
        if self.fuel == 0:
            return 0.24
        if self.fuel >= 75:
            return 0.45
        if self.fuel >= 40:
            return 0.38
        if self.fuel >= 15:
            return 0.32
        return 0.24

    def _turbo_frame_index(self):
        stage = self._get_turbo_stage()
        return min(stage - 1, len(self._get_turbo_frames()) - 1)

    def _get_turbo_stage(self):
        if self._boosting and self.fuel > 0:
            return 1
        if self.fuel > 0:
            return 2
        return 4
    
    def _draw_hp_bar(self, surface: pygame.Surface):
        # one pip per max HP — filled bar for remaining health, empty border for lost
        bar_x, bar_y = WIDTH - 60, 20
        pip_w = 0
        if self.health > 0:
            for i in range(ROCKET_MAX_HP):
                pip_w = self.health_sprites[i].frames[0].get_width()
                self.health_sprites[i].draw(surface, (bar_x - pip_w * i, bar_y), i >= self.health)

    def draw(self, surface):
        # 1. --- Turbo exhaust sprite (Base layer of the engine effect) ---
        turbo_frames = self._get_turbo_frames()
        if turbo_frames and not self.exploding:
            frame_index = self._turbo_frame_index()
            frame = turbo_frames[frame_index]
            scale = self._turbo_scale()
            frame = pygame.transform.smoothscale(
                frame,
                (
                    max(16, int(frame.get_width() * scale)),
                    max(16, int(frame.get_height() * scale)),
                ),
            )
            turbo_rect = frame.get_rect(midright=self.rect.midleft)
            turbo_rect.x -= 4
            if frame_index != 0:
                turbo_rect.y += 15
            surface.blit(frame, turbo_rect)

        # 2. --- Draw boost sparks (Now overlays nicely on top of the turbo flame) ---
        for s in self._sparks:
            ratio = s[5] / s[6]          # 1.0 → 0.0 as it dies
            radius = max(1, int(s[4] * ratio))
            alpha = int(255 * ratio)
            
            # Outer orange
            spark_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(spark_surf, (255, 160, 40, alpha), (radius + 1, radius + 1), radius)
            
            # Inner white-yellow core
            core_r = max(1, radius // 2)
            pygame.draw.circle(spark_surf, (255, 240, 180, min(255, alpha + 60)), (radius + 1, radius + 1), core_r)
            surface.blit(spark_surf, (int(s[0]) - radius - 1, int(s[1]) - radius - 1))

        # 3. --- Explosion particle burst (Rendered independently if dead) ---
        for p in self._explosion_particles:
            ratio = p[6] / p[7]
            radius = max(1, int(p[4] * ratio))
            alpha = int(240 * ratio)
            r, g, b = p[5]
            exp_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(exp_surf, (r, g, b, alpha), (radius + 1, radius + 1), radius)
            surface.blit(exp_surf, (int(p[0]) - radius - 1, int(p[1]) - radius - 1))

        if self.exploding:
            # Central fireball that grows then fades
            radius = 18 + int(self.explosion_timer * 1.4)
            alpha = max(0, 230 - int(self.explosion_timer * 5))
            if alpha > 0:
                explosion = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(explosion, (255, 190, 80, alpha), (radius, radius), radius)
                pygame.draw.circle(explosion, (255, 80, 32, max(0, alpha - 60)), (radius, radius), int(radius * 0.55))
                pygame.draw.circle(explosion, (255, 255, 200, max(0, alpha - 120)), (radius, radius), int(radius * 0.25))
                surface.blit(explosion, explosion.get_rect(center=self.rect.center))
            return

        # 4. --- Main Rocket Body (Always drawn last on top of engine connections) ---
        rocket_image = self.image.copy()
        if self.invincible and (self.blink_timer < 8):
            rocket_image.set_alpha(120)
        elif self.invincible:
            rocket_image.set_alpha(200)
        surface.blit(rocket_image, self.rect)
        
        # 5. Draw HP Bar
        self._draw_hp_bar(surface)