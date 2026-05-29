import os
import math
import random
import pygame
from settings import (
    WIDTH, HEIGHT, FPS, DARK, WHITE, RED, GREEN, YELLOW, ASSETS_DIR
)
from gru import Gru, PlasmaBolt, ExplosionVFX
from pause import run_pause
from progress import mark_complete


class BossPlatform(pygame.sprite.Sprite):
    """Platform geometry for the arena."""

    def __init__(self, rect: pygame.Rect, color=(70, 80, 100)):
        super().__init__()
        self.rect = rect
        self.image = pygame.Surface((rect.width, rect.height))
        self.image.fill(color)
        self.top = rect.top


class FishProjectile(pygame.sprite.Sprite):
    """Vector's low-flying fish projectiles that must be dodged by jumping."""

    def __init__(self, x: int, y: int, direction_right: bool, speed: float = 6.5):
        super().__init__()
        self.image = pygame.Surface((36, 20), pygame.SRCALPHA)
        # Procedural fallback: bright orange aquatic silhouette
        pygame.draw.ellipse(self.image, (255, 120, 30), (0, 0, 36, 20))
        pygame.draw.polygon(self.image, (255, 90, 0), [(30, 10), (36, 2), (36, 18)])
        pygame.draw.circle(self.image, (255, 255, 255), (8, 6), 4)

        if not direction_right:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect(center=(x, y))
        self.vx = speed if direction_right else -speed

    def update(self):
        self.rect.x += int(self.vx)
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


class VectorBoss(pygame.sprite.Sprite):
    """Vector Boss Entity featuring spritesheet animations and automated pacing."""

    def __init__(self, x: int, y: int):
        super().__init__()

        # Foolproof path checking for the new spritesheet
        paths_to_try = [
            os.path.join(ASSETS_DIR, "sprites", "vector_spritesheet.png"),
            os.path.join(ASSETS_DIR, "sprites", "vector", "vector_spritesheet.png"),
            os.path.join(ASSETS_DIR, "vector_spritesheet.png"),
            "vector_spritesheet.png"
        ]

        sheet_path = None
        for p in paths_to_try:
            if os.path.exists(p):
                sheet_path = p
                break

        self.has_spritesheet = sheet_path is not None
        self.animations = {"moving": [], "attacking": []}

        if self.has_spritesheet:
            sheet = pygame.image.load(sheet_path).convert_alpha()

            # Row 1: Pacing/Moving Animation (4 crisp slices discovered)
            moving_rects = [
                (31, 67, 88, 130),
                (134, 67, 88, 130),
                (242, 67, 88, 130),
                (348, 67, 88, 130)
            ]
            # Row 2: Attacking/Firing Animation (3 Piranha gun slices)
            attacking_rects = [
                (6, 236, 106, 138),
                (126, 236, 106, 138),
                (239, 236, 106, 138)
            ]

            # Scale down slightly to match the pixel-art scale of Gru (Target height: 96px)
            TARGET_H = 96
            scale_move = TARGET_H / 130.0
            scale_atk = TARGET_H / 138.0

            for rx, ry, rw, rh in moving_rects:
                sub = sheet.subsurface(pygame.Rect(rx, ry, rw, rh))
                scaled = pygame.transform.scale(sub, (int(rw * scale_move), TARGET_H))
                self.animations["moving"].append(scaled)

            for rx, ry, rw, rh in attacking_rects:
                sub = sheet.subsurface(pygame.Rect(rx, ry, rw, rh))
                scaled = pygame.transform.scale(sub, (int(rw * scale_atk), TARGET_H))
                self.animations["attacking"].append(scaled)

            self.image = self.animations["moving"][0]
        else:
            # Procedural vector tracking suit fallback if image goes missing
            self.image = pygame.Surface((54, 76), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (240, 90, 30), (0, 16, 54, 60), border_radius=6)
            pygame.draw.circle(self.image, (245, 210, 180), (27, 18), 16)
            pygame.draw.rect(self.image, (50, 40, 40), (12, 10, 30, 8), border_radius=2)

        # Anchor using midbottom to automatically align with platform heights
        self.rect = self.image.get_rect(midbottom=(x, y))

        self.hp = 3
        self.state = "moving"  # "moving", "attacking", "frozen"
        self.state_timer = 0
        self.vx = 3.5
        self.left_bound = 320
        self.right_bound = 960
        self.fish_fired_count = 0
        self.attack_cooldown = 0
        self.is_frozen = False

        # Animation Frame Counters
        self.frame_index = 0
        self.anim_ticks = 0
        self.facing_right = False

    def update(self):
        if self.state == "frozen":
            return False

        # Set facing direction based on movement velocity
        self.facing_right = (self.vx > 0)

        # Progress animation cycle ticks
        self.anim_ticks += 1
        if self.anim_ticks >= 7:  # Swap sprites every 7 ticks for silky animation pacing
            self.anim_ticks = 0
            if self.has_spritesheet and self.state in self.animations:
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])

        # Render current frame texture assignment
        if self.has_spritesheet and self.state in self.animations:
            frame = self.animations[self.state][self.frame_index]
            self.image = pygame.transform.flip(frame, not self.facing_right, False)

            # Recalculate dimensions safely while maintaining ground locking
            old_mb = self.rect.midbottom
            self.rect = self.image.get_rect()
            self.rect.midbottom = old_mb

        if self.state == "moving":
            self.rect.x += int(self.vx)
            if self.rect.left <= self.left_bound:
                self.rect.left = self.left_bound
                self.vx = abs(self.vx)
            elif self.rect.right >= self.right_bound:
                self.rect.right = self.right_bound
                self.vx = -abs(self.vx)

            self.state_timer += 1
            if self.state_timer >= 150:
                self.state = "attacking"
                self.state_timer = 0
                self.fish_fired_count = 0
                self.attack_cooldown = 0
                self.frame_index = 0

        elif self.state == "attacking":
            self.attack_cooldown += 1
            if self.attack_cooldown >= 25 and self.fish_fired_count < 3:
                self.attack_cooldown = 0
                self.fish_fired_count += 1
                return True

            if self.fish_fired_count >= 3 and self.attack_cooldown >= 40:
                self.state = "moving"
                self.state_timer = 0
                self.frame_index = 0

        return False

    def freeze(self):
        """Turns Vector into a frozen solid ice block."""
        self.state = "frozen"
        self.is_frozen = True
        ice_overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        ice_overlay.fill((140, 220, 255, 160))
        self.image.blit(ice_overlay, (0, 0))
        pygame.draw.rect(self.image, (0, 180, 255), (0, 0, self.rect.width, self.rect.height), 3, border_radius=6)


def _render_wrapped(surface, text, font, colour, x, y, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    for i, line in enumerate(lines):
        surf = font.render(line, True, colour)
        surface.blit(surf, (x, y + i * font.get_linesize()))


def scene3(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """Runs Scene 3 — Vector Boss Fight Arena."""
    pygame.display.set_caption("Scene 3 — Vector's Showdown")

    def play_boss_music():
        music_path = os.path.join(ASSETS_DIR, "music", "level1_great_mission.mp3")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)

    play_boss_music()

    sfx_explode = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "explosion.wav"))
    sfx_hit = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "minion_hit_1.wav"))
    sfx_laser = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "laser_freeze_ray.ogg"))
    sfx_start = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "level_start.wav"))
    laser_channel = pygame.mixer.Channel(1)
    start_channel = pygame.mixer.Channel(3)

    def play_level_start():
        start_channel.stop()
        start_channel.play(sfx_start)

    floor = BossPlatform(pygame.Rect(0, HEIGHT - 60, WIDTH, 60))
    raised_platform = BossPlatform(pygame.Rect(300, 460, 680, 24))
    platforms = [floor, raised_platform]

    # Spawn Vector directly centered right on top of the Y=460 platform!
    gru = Gru(x=100, y=HEIGHT - 130)
    vector = VectorBoss(x=WIDTH // 2, y=460)

    plasma_bolts = pygame.sprite.Group()
    fish_projectiles = pygame.sprite.Group()
    vfx_group = pygame.sprite.Group()

    font_speaker = pygame.font.Font(None, 34)
    font_text = pygame.font.Font(None, 28)
    font_hint = pygame.font.Font(None, 22)

    stage = "intro_cutscene"
    curr_line = 0

    intro_dialogue = [
        ("VECTOR", "YOU?! A villain? Please. I have PYRAMIDS.")
    ]

    win_dialogue = [
        ("DR. NEFARIO", "Ze components are secured! Ze rocket awaits, Gru!")
    ]

    running = True
    while running:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = run_pause(screen, clock)
                    if action == "menu":
                        return "menu"
                    if action == "restart":
                        return "restart"
                    if action == "resume":
                        play_boss_music()

                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if stage == "intro_cutscene":
                        curr_line += 1
                        if curr_line >= len(intro_dialogue):
                            stage = "fight"
                            curr_line = 0
                            play_level_start()
                    elif stage == "win_cutscene":
                        curr_line += 1
                        if curr_line >= len(win_dialogue):
                            mark_complete("scene3")
                            return "menu"

        if stage == "fight":
            fired_bolt = gru.update(keys, events, [floor])
            if fired_bolt:
                ray, flash = fired_bolt
                plasma_bolts.add(ray)
                vfx_group.add(flash)
                laser_channel.play(sfx_laser, maxtime=300)

            should_fire_fish = vector.update()
            if should_fire_fish:
                target_right = gru.rect.centerx > vector.rect.centerx
                # Dynamically calculate fish weapon level height from tracking rect
                fish = FishProjectile(vector.rect.centerx, vector.rect.centery + 12, target_right)
                fish_projectiles.add(fish)

            plasma_bolts.update()
            fish_projectiles.update()
            vfx_group.update()

            for bolt in list(plasma_bolts):
                if bolt.rect.colliderect(vector.rect):
                    bolt.kill()
                    if vector.state == "moving":
                        vector.hp -= 1
                        vfx_group.add(ExplosionVFX(vector.rect.centerx, vector.rect.centery, 1))
                        sfx_explode.play()
                        if vector.hp <= 0:
                            vector.freeze()
                            stage = "win_cutscene"
                            curr_line = 0
                            pygame.mixer.music.stop()

            if pygame.sprite.spritecollide(gru, fish_projectiles, True):
                if gru.take_damage():
                    sfx_hit.play()

            if gru.hp <= 0:
                pygame.time.delay(600)
                return "restart"

        screen.fill(DARK)

        for plat in platforms:
            pygame.draw.rect(screen, (70, 80, 100), plat.rect)

        screen.blit(vector.image, vector.rect)
        if stage != "win_cutscene":
            gru.draw(screen)

        if stage == "fight":
            plasma_bolts.draw(screen)
            fish_projectiles.draw(screen)
            vfx_group.draw(screen)

            boss_lbl = font_text.render("VECTOR HP:", True, RED)
            screen.blit(boss_lbl, (WIDTH // 2 - 120, 20))
            for i in range(3):
                col = RED if i < vector.hp else (50, 20, 20)
                pygame.draw.rect(screen, col, (WIDTH // 2 + 10 + i * 30, 22, 22, 16))

        if stage in ("intro_cutscene", "win_cutscene"):
            active_dialogue = intro_dialogue if stage == "intro_cutscene" else win_dialogue
            speaker, text = active_dialogue[curr_line]

            box = pygame.Surface((WIDTH - 80, 140), pygame.SRCALPHA)
            box.fill((10, 10, 20, 220))
            screen.blit(box, (40, HEIGHT - 170))

            speaker_color = YELLOW if speaker == "VECTOR" else (160, 220, 255)
            name_surf = font_speaker.render(speaker, True, speaker_color)
            screen.blit(name_surf, (60, HEIGHT - 150))

            _render_wrapped(screen, text, font_text, WHITE, 60, HEIGHT - 115, WIDTH - 120)

            hint = font_hint.render("SPACE / ENTER to continue", True, (160, 160, 160))
            screen.blit(hint, (WIDTH - hint.get_width() - 60, HEIGHT - 50))

        pygame.display.flip()

    return "menu"
