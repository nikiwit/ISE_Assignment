import os
import math
import random
import pygame
from settings import (
    WIDTH, HEIGHT, FPS, DARK, WHITE, RED, GREEN, YELLOW, ASSETS_DIR
)
import gru as gru_module
from gru import Gru, PlasmaBolt, ExplosionVFX
from pause import run_pause
from progress import mark_complete


class MoonPlatform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, is_bedrock=True):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height))
        color = (90, 95, 110) if is_bedrock else (120, 125, 140)
        self.image.fill(color)
        pygame.draw.rect(self.image, (140, 145, 160), (0, 0, width, 6))
        self.top = self.rect.top


class FracturePlatform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height))
        self.image.fill((110, 115, 125))
        pygame.draw.rect(self.image, (230, 90, 40), (0, 0, width, 6))
        self.top = self.rect.top

        self.stepped_on = False
        self.timer = 0
        self.is_sunk = False
        self.width = width

    def update(self, gru_player):
        if self.is_sunk:
            self.rect.y += 12
            return

        if not self.stepped_on:
            if gru_player.rect.colliderect(self.rect) and abs(gru_player.rect.bottom - self.rect.top) <= 6:
                self.stepped_on = True

        if self.stepped_on:
            self.timer += 1
            if (self.timer // 6) % 2 == 0:
                self.image.fill((180, 70, 70))
            else:
                self.image.fill((110, 115, 125))
            pygame.draw.rect(self.image, (255, 0, 0), (0, 0, self.width, 6))

            if self.timer >= 120:
                self.is_sunk = True


class MoonGuard(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, left_bound: int, right_bound: int):
        super().__init__()
        self.image = pygame.Surface((44, 64), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (170, 185, 200), (4, 14, 36, 50), border_radius=6)
        pygame.draw.circle(self.image, (0, 160, 255), (22, 26), 10)
        self.rect = self.image.get_rect(bottomleft=(x, y))

        self.vx = 2.0
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.is_frozen = False

    def update(self):
        if self.is_frozen:
            return

        self.rect.x += int(self.vx)
        if self.rect.left <= self.left_bound:
            self.rect.left = self.left_bound
            self.vx = abs(self.vx)
        elif self.rect.right >= self.right_bound:
            self.rect.right = self.right_bound
            self.vx = -abs(self.vx)

    def freeze(self):
        self.is_frozen = True
        ice_tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        ice_tint.fill((130, 215, 255, 175))
        self.image.blit(ice_tint, (0, 0))


class FuelCell(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = pygame.Surface((28, 36), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (40, 255, 110), (4, 6, 20, 30), border_radius=4)
        pygame.draw.rect(self.image, (200, 255, 220), (8, 0, 12, 6), border_radius=1)
        self.rect = self.image.get_rect(center=(x, y))
        self.bob_angle = random.uniform(0, 360)

    def update(self):
        self.bob_angle += 0.06
        self.rect.y += int(math.sin(self.bob_angle) * 0.6)


class LunarBackground:
    def __init__(self):
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT - 200)) for _ in range(60)]
        self.moon_radius = 180
        self.moon_scale = 1.0

    def draw(self, screen: pygame.Surface, camera_x: int, climax_progress: float = 0.0):
        for sx, sy in self.stars:
            px = (sx - int(camera_x * 0.2)) % WIDTH
            pygame.draw.circle(screen, WHITE, (px, sy), random.choice([1, 2]))

        current_radius = int(self.moon_radius * self.moon_scale)
        if current_radius > 2:
            target_x = int(WIDTH * 0.75 - (camera_x * 0.05)) if climax_progress == 0 else int(WIDTH // 2)
            target_y = 200 if climax_progress == 0 else int(HEIGHT // 2 - 50)

            if climax_progress > 0:
                pygame.draw.circle(screen, (100, 200, 255, 50), (target_x, target_y), current_radius + 15)

            pygame.draw.circle(screen, (220, 225, 240), (target_x, target_y), current_radius)
            pygame.draw.circle(screen, (190, 195, 210), (target_x - 40, target_y - 30), 35)
            pygame.draw.circle(screen, (190, 195, 210), (target_x + 50, target_y + 40), 25)


def scene5(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """Runs Scene 5 — Featuring Lunar Surface Scrolling and the Shrink Ray Climax."""
    pygame.display.set_caption("Scene 5 — Operations: Capture The Moon")

    # Low-Gravity Physics Engine Tweaks
    orig_gravity = getattr(gru_module, "GRAVITY", 0.6)
    gru_module.GRAVITY = 0.3

    sfx_laser = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "laser_freeze_ray.ogg"))
    sfx_explode = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "explosion.wav"))
    sfx_pickup = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "minion_hit_1.wav"))

    bg = LunarBackground()
    camera_x = 0
    total_level_width = 3200
    climax_trigger_x = 2650
    floor_y = HEIGHT - 60

    static_platforms = pygame.sprite.Group()
    fracture_platforms = pygame.sprite.Group()
    guards_group = pygame.sprite.Group()
    fuel_cells = pygame.sprite.Group()

    terrain_blueprints = [(0, 750), (1200, 500), (2200, 1000)]
    for sx, w in terrain_blueprints:
        static_platforms.add(MoonPlatform(sx, floor_y, w, 60, is_bedrock=True))

    fracture_platforms.add(FracturePlatform(750, floor_y, 200, 60))
    fracture_platforms.add(FracturePlatform(1900, floor_y, 150, 60))
    fracture_platforms.add(FracturePlatform(2050, floor_y - 60, 150, 20))

    fuel_cells.add(FuelCell(850, floor_y - 120))
    fuel_cells.add(FuelCell(1450, floor_y - 180))
    fuel_cells.add(FuelCell(2125, floor_y - 220))
    fuel_cells_collected = 0
    show_fuel_warning = False
    warning_timer = 0

    guards_group.add(MoonGuard(400, floor_y, 250, 650))
    guards_group.add(MoonGuard(1350, floor_y, 1220, 1650))
    guards_group.add(MoonGuard(2400, floor_y, 2250, 2800))

    gru = Gru(x=100, y=floor_y - 200)
    plasma_bolts = pygame.sprite.Group()
    vfx_group = pygame.sprite.Group()

    # Boots directly into rocket landing sequence
    stage = "rocket_landing"
    rocket_rect = pygame.Rect(200, -150, 64, 110)
    rocket_target_y = floor_y - 110
    landing_timer = 0

    climax_timer = 0
    charge_particles = []
    screen_shake = 0

    running = True
    while running:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                gru_module.GRAVITY = orig_gravity
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = run_pause(screen, clock)
                    if action in ("menu", "restart"):
                        gru_module.GRAVITY = orig_gravity
                        return action

                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if stage == "victory":
                        gru_module.GRAVITY = orig_gravity
                        mark_complete("scene5")
                        return "menu"

        # --- PHASE B.1: ROCKET TOUCH DOWN CUTSCENE ---
        if stage == "rocket_landing":
            if rocket_rect.y < rocket_target_y:
                rocket_rect.y += int(max(1.5, (rocket_target_y - rocket_rect.y) * 0.08))
            else:
                rocket_rect.y = rocket_target_y
                landing_timer += 1
                if landing_timer >= 60:
                    gru.rect.centerx = rocket_rect.centerx + 60
                    gru.rect.bottom = floor_y
                    stage = "moon_surface"

        # --- PHASE B.2: ACTIVE LOW-GRAVITY PLATFORMING ---
        elif stage == "moon_surface":
            # Extracts the raw pygame.Rect boundaries from sprites so gru.py can calculate collisions
            active_solids = [p.rect for p in static_platforms.sprites()] + [f.rect for f in fracture_platforms.sprites()
                                                                            if not f.is_sunk]

            fired_bolt = gru.update(keys, events, active_solids)
            if fired_bolt:
                ray, flash = fired_bolt
                plasma_bolts.add(ray)
                vfx_group.add(flash)
                pygame.mixer.Channel(1).play(sfx_laser, maxtime=250)

            fracture_platforms.update(gru)
            guards_group.update()
            fuel_cells.update()
            plasma_bolts.update()
            vfx_group.update()

            for bolt in list(plasma_bolts):
                hit_guard = pygame.sprite.spritecollideany(bolt, guards_group)
                if hit_guard and not hit_guard.is_frozen:
                    bolt.kill()
                    hit_guard.freeze()
                    sfx_pickup.play()

            collected = pygame.sprite.spritecollide(gru, fuel_cells, True)
            if collected:
                fuel_cells_collected += len(collected)
                sfx_pickup.play()

            for guard in guards_group.sprites():
                if not guard.is_frozen and gru.rect.colliderect(guard.rect):
                    if gru.take_damage():
                        sfx_pickup.play()

            if gru.rect.left < 0:
                gru.rect.left = 0

            if gru.rect.centerx > WIDTH // 2:
                camera_x = gru.rect.centerx - WIDTH // 2
                if camera_x > total_level_width - WIDTH:
                    camera_x = total_level_width - WIDTH

            if gru.rect.top > HEIGHT or gru.hp <= 0:
                pygame.time.delay(500)
                gru_module.GRAVITY = orig_gravity
                return "restart"

            if gru.rect.x >= climax_trigger_x:
                if fuel_cells_collected >= 3:
                    stage = "climax_charge"
                    climax_timer = 0
                else:
                    show_fuel_warning = True
                    warning_timer = 90

            if show_fuel_warning:
                warning_timer -= 1
                if warning_timer <= 0:
                    show_fuel_warning = False

        # --- PHASE C.1: CLIMAX: SHRINK RAY POWER CHARGE ---
        elif stage == "climax_charge":
            climax_timer += 1
            gru.vx = 0
            gun_x = gru.rect.centerx + 20 - camera_x
            gun_y = gru.rect.centery - 10

            if climax_timer % 2 == 0:
                angle = random.uniform(0, math.pi * 2)
                dist = random.randint(100, 250)
                charge_particles.append({
                    "x": gun_x + math.cos(angle) * dist,
                    "y": gun_y + math.sin(angle) * dist,
                    "target_x": gun_x, "target_y": gun_y,
                    "speed": random.uniform(0.08, 0.15)
                })

            for p in charge_particles[:]:
                p["x"] += (p["target_x"] - p["x"]) * p["speed"]
                p["y"] += (p["target_y"] - p["y"]) * p["speed"]
                if math.hypot(p["target_x"] - p["x"], p["target_y"] - p["y"]) < 8:
                    charge_particles.remove(p)

            if climax_timer > 90:
                screen_shake = random.randint(-3, 3)
            if climax_timer >= 180:
                stage = "climax_shrink"
                climax_timer = 0
                sfx_laser.play()

        # --- PHASE C.2: CLIMAX: DISCHARGE & MOON SHRINK ---
        elif stage == "climax_shrink":
            climax_timer += 1
            screen_shake = random.randint(-5, 5)
            if bg.moon_scale > 0.02:
                bg.moon_scale -= 0.008
            else:
                bg.moon_scale = 0.01
                screen_shake = 0

                # FIXED: Stops the continuous laser humming track loop right before exploding
                sfx_laser.stop()
                sfx_explode.play()

                stage = "victory"

        # ==========================================
        # GRAPHICS DISPLAY PIPELINE
        # ==========================================
        render_surf = pygame.Surface((WIDTH, HEIGHT))
        render_surf.fill(DARK)

        climax_active = 1.0 if stage in ("climax_charge", "climax_shrink", "victory") else 0.0
        bg.draw(render_surf, camera_x, climax_active)

        for plat in static_platforms:
            render_surf.blit(plat.image, plat.rect.move(-camera_x, 0))
        for plat in fracture_platforms:
            if not plat.is_sunk or stage == "moon_surface":
                render_surf.blit(plat.image, plat.rect.move(-camera_x, 0))
        for cell in fuel_cells:
            render_surf.blit(cell.image, cell.rect.move(-camera_x, 0))
        for guard in guards_group:
            render_surf.blit(guard.image, guard.rect.move(-camera_x, 0))

        if stage == "rocket_landing":
            pygame.draw.polygon(render_surf, RED,
                                [(rocket_rect.centerx, rocket_rect.top), (rocket_rect.left, rocket_rect.top + 30),
                                 (rocket_rect.right, rocket_rect.top + 30)])
            pygame.draw.rect(render_surf, WHITE, (rocket_rect.x, rocket_rect.y + 30, rocket_rect.width, 60))
            if rocket_rect.y < rocket_target_y:
                pygame.draw.polygon(render_surf, YELLOW,
                                    [(rocket_rect.centerx, rocket_rect.bottom + random.randint(10, 30)),
                                     (rocket_rect.left + 15, rocket_rect.bottom),
                                     (rocket_rect.right - 15, rocket_rect.bottom)])

        if stage != "rocket_landing":
            old_x = gru.rect.x
            gru.rect.x -= camera_x
            gru.draw(render_surf)
            gru.rect.x = old_x

        if stage == "moon_surface":
            plasma_bolts.draw(render_surf)
            vfx_group.draw(render_surf)

        if stage == "climax_charge":
            for p in charge_particles:
                pygame.draw.circle(render_surf, (130, 230, 255), (int(p["x"]), int(p["y"])), random.randint(2, 4))
            pygame.draw.circle(render_surf, (200, 245, 255), (gru.rect.centerx + 20 - camera_x, gru.rect.centery - 10),
                               int(climax_timer // 6))

        if stage == "climax_shrink":
            gun_x = gru.rect.centerx + 20 - camera_x
            gun_y = gru.rect.centery - 10
            pygame.draw.line(render_surf, (230, 255, 255), (gun_x, gun_y), (WIDTH // 2, HEIGHT // 2 - 50),
                             int(25 - climax_timer // 4))
            pygame.draw.circle(render_surf, WHITE, (WIDTH // 2, HEIGHT // 2 - 50), random.randint(30, 60))

        screen.blit(render_surf, (screen_shake, screen_shake))

        if stage == "moon_surface":
            ui_font = pygame.font.Font(None, 26)
            cell_txt = ui_font.render(f"FUEL CELLS: {fuel_cells_collected} / 3", True,
                                      GREEN if fuel_cells_collected == 3 else YELLOW)
            screen.blit(cell_txt, (25, 25))

            if show_fuel_warning:
                warn_font = pygame.font.Font(None, 32)
                warn_lbl = warn_font.render("CRITICAL ERROR: COLLECT ALL 3 FUEL CELLS TO CHARGE LASER!", True, RED)
                pygame.draw.rect(screen, (30, 10, 10), (WIDTH // 2 - 360, 80, 720, 45))
                pygame.draw.rect(screen, RED, (WIDTH // 2 - 360, 80, 720, 45), 2)
                screen.blit(warn_lbl, (WIDTH // 2 - warn_lbl.get_width() // 2, 92))

        if stage == "victory":
            box = pygame.Surface((WIDTH - 80, 140), pygame.SRCALPHA)
            box.fill((10, 10, 20, 230))
            screen.blit(box, (40, HEIGHT - 170))
            f_speaker = pygame.font.Font(None, 34)
            f_text = pygame.font.Font(None, 28)
            f_hint = pygame.font.Font(None, 22)
            screen.blit(f_speaker.render("GRU", True, (160, 220, 255)), (60, HEIGHT - 150))
            screen.blit(
                f_text.render("I did it! Look at that, it's completely... miniscule! Next stop, the bank!", True,
                              WHITE), (60, HEIGHT - 115))
            screen.blit(f_hint.render("Press SPACE / ENTER to return to Main Menu", True, (160, 160, 160)),
                        (WIDTH - 360, HEIGHT - 50))

        pygame.display.flip()

    gru_module.GRAVITY = orig_gravity
    return "menu"