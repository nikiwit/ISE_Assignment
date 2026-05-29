import math
import os
import random
import pygame

from settings import ASSETS_DIR, WIDTH, HEIGHT, FPS, WHITE, RED, GREEN, YELLOW, RED, BLUE
from rocket import *
# take from scene1_lab for displaying dialogue
from scene1_lab import _load_gru_idle, _load_nefario, _load_background, _render_wrapped
from pause import run_pause

def _load_sound(filename):
    path = os.path.join(ASSETS_DIR, "sfx", filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None


def _load_music(filename):
    path = os.path.join(ASSETS_DIR, "music", filename)
    return path if os.path.exists(path) else None


def _draw_screen_border_warning(surface, color, alpha, thickness=20):
    """Draws a soft, fading full-screen vignette border."""
    if alpha <= 0:
        return
        
    # Create a temporary surface supporting transparency
    border_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Layer multiple rectangles to create a soft glowing gradient effect
    steps = 5
    for i in range(steps):
        # Calculate fading alpha for outer-to-inner steps
        layer_alpha = int(alpha * ((steps - i) / steps))
        layer_color = (color[0], color[1], color[2], layer_alpha)
        
        # Draw the frame lines
        offset = i * (thickness // steps)
        pygame.draw.rect(
            border_surf, 
            layer_color, 
            (offset, offset, WIDTH - (offset * 2), HEIGHT - (offset * 2)), 
            thickness // steps
        )
        
    surface.blit(border_surf, (0, 0))

def _create_starfield():
    choices = [
        "Starfield_01.png",
        "Starfield_02.png",
        "Starfield_03.png",
        "Starfield_04.png",
        "Starfield_05.png",
        "Starfield_06.png",
        "Starfield_07.png",
        "Starfield_08.png",
    ]
    folder = os.path.join(ASSETS_DIR, "backgrounds", "starfields")
    random.shuffle(choices)
    for name in choices:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            starfield = pygame.image.load(path).convert()
            return pygame.transform.scale(starfield, (WIDTH, HEIGHT))
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill((8, 10, 24))
    return surface


def _render_ui(surface, rocket, distance, game_over, victory, fuel_empty=False):
    font = pygame.font.Font(None, 30)
    title = font.render("ASTEROID DODGE", True, WHITE)
    surface.blit(title, (20, 18))

    progress = min(1.0, distance / DISTANCE_GOAL)
    pygame.draw.rect(surface, (40, 40, 60), (20, 58, 420, 24))
    pygame.draw.rect(surface, (80, 200, 240), (22, 60, int(416 * progress), 20))
    label = font.render(f"DISTANCE: {int(distance)} / {DISTANCE_GOAL}", True, WHITE)
    surface.blit(label, (22, 86))

    pygame.draw.rect(surface, (40, 40, 60), (20, 125, 250, 26))
    fuel_width = int(246 * (rocket.fuel / FUEL_MAX))
    pygame.draw.rect(surface, (240, 210, 70), (22, 125, fuel_width, 26))
    fuel_value = font.render(f"{int(rocket.fuel)}%", True, RED)
    surface.blit(fuel_value, (105, 129))
    
    fuel_label = font.render("FUEL", True, WHITE)
    surface.blit(fuel_label, (20, 158))

    help_text = [
        "MOVE: ARROWS / WASD",
        "BOOST: SHIFT",
        "DASH: SPACE",
        "ESC: PAUSE",
    ]
    Y = HEIGHT - 40
    for idx, text in enumerate(help_text):
        hint = font.render(text, True, (200, 200, 220))
        surface.blit(hint, (20 + idx * 350, Y))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        end_font = pygame.font.Font(None, 58)
        if fuel_empty:
            msg = end_font.render("FUEL EMPTY! PRESS R TO RESTART", True, YELLOW)
        else:
            msg = end_font.render("DESTROYED! PRESS R TO RESTART", True, RED)
        surface.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        hint = font.render("PRESS ESC TO GO BACK TO MENU", True, WHITE)
        surface.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    if victory:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        end_font = pygame.font.Font(None, 58)
        msg = end_font.render("MISSION COMPLETE!", True, (120, 255, 120))
        surface.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        hint = font.render("ESC to return to menu", True, WHITE)
        surface.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


def display_dialogue(screen, clock, DIALOGUE, SPEAKER_COLOURS):
    """Refer to scene 1"""
    pygame.mixer.music.load(os.path.join(ASSETS_DIR, "music", "cutscene.wav"))
    pygame.mixer.music.set_volume(0.6)
    pygame.mixer.music.play(-1)

    lab_bg       = _load_background()
    gru_frame    = _load_gru_idle()
    nefario_surf = _load_nefario()

    font_speaker = pygame.font.Font(None, 30)
    font_text    = pygame.font.Font(None, 28)
    font_hint    = pygame.font.Font(None, 22)

    curr_line = 0  # index into DIALOGUE — bumped on each SPACE press
    finished  = False

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            # advance dialogue on SPACE or ENTER. KEYDOWN (not key.get_pressed)
            # so each press only fires once — otherwise holding SPACE skips everything.
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if event.type == pygame.MOUSEBUTTONDOWN or event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    curr_line += 1
                    if curr_line >= len(DIALOGUE):
                        finished = True
                        
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return False

        if finished:
            pygame.mixer.music.stop()
            return True

        screen.blit(lab_bg, (0, 0))

        # gru on the left (his sprite faces right), nefario on the right —
        # they end up looking at each other without needing any sprite flipping.
        gru_x = WIDTH // 5 - gru_frame.get_width() // 2
        gru_y = HEIGHT - gru_frame.get_height() - 80
        screen.blit(gru_frame, (gru_x, gru_y))

        nef_x = WIDTH * 3 // 4 - nefario_surf.get_width() // 2
        nef_y = HEIGHT - nefario_surf.get_height() - 80
        screen.blit(nefario_surf, (nef_x, nef_y))
        
        if curr_line < len(DIALOGUE):

            speaker, text = DIALOGUE[curr_line]

            # semi-transparent dialogue box. it's 160 tall (a bit taller than strictly
            # needed) so the speaker name has some breathing room above the text.
            box = pygame.Surface((WIDTH - 80, 160), pygame.SRCALPHA)
            box.fill((10, 10, 20, 200))
            screen.blit(box, (40, HEIGHT - 190))

            colour = SPEAKER_COLOURS.get(speaker, WHITE)
            name_surf = font_speaker.render(speaker, True, colour)
            screen.blit(name_surf, (60, HEIGHT - 155))

            _render_wrapped(screen, text, font_text, WHITE, 60, HEIGHT - 125, WIDTH - 120)

            hint = font_hint.render("SPACE / ENTER to continue", True, (160, 160, 160))
            screen.blit(hint, (WIDTH - hint.get_width() - 50, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()

def scene4(screen, clock):
    if not pygame.get_init():
        pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        
    # Dialogue to introduce the flow of the story (follow scene1 design)
    DIALOGUE = [
        ("DR. NEFARIO", "Sir — the rocket is fully prepped and ready."),
        ("GRU", "Perfect. I'm entering the rocket — the moon will be mine."),
    ]
    SPEAKER_COLOURS = {"DR. NEFARIO": (160, 220, 255), "GRU": (255, 210, 100)}
    if not display_dialogue(screen, clock, DIALOGUE, SPEAKER_COLOURS):
        return "back"

    bg = _create_starfield()

    sound_scale = 0.7
    start_sound = _load_sound("level_start.wav")
    boost_sound = _load_sound("rocket_boost.mp3")
    if boost_sound:
        boost_sound.set_volume(0.9 * sound_scale)
    dash_sound = _load_sound("rocket_dash.mp3")
    if dash_sound:
        dash_sound.set_volume(0.4 * sound_scale)
    posthit_sound = _load_sound("posthit_invicible.mp3")
    explosion_sound = _load_sound("rocket_explosion.mp3")
    collect_sound = _load_sound("collect_fuel.mp3")
    if collect_sound:
        collect_sound.set_volume(0.3 * sound_scale)
    empty_sound = _load_sound("empty_fuel.mp3")
    if empty_sound:
        empty_sound.set_volume(0.9 * sound_scale)
    music_path = _load_music("space.mp3")
    music_length = 0.0
    music_start_time = 0
    music_pause_pos = 0.0

    def _play_scene_music(start_pos: float = 0.0):
        nonlocal music_length, music_start_time
        if music_path:
            music_length = pygame.mixer.Sound(music_path).get_length()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5 * sound_scale)
            if start_pos and music_length:
                start_pos = start_pos % music_length
            pygame.mixer.music.play(0, start_pos)
            music_start_time = pygame.time.get_ticks() - int(start_pos * 1000)

    if music_path:
        _play_scene_music()
    if start_sound:
        start_sound.play()

    rocket = Rocket(boost_sound, dash_sound, posthit_sound, explosion_sound)
    asteroids = pygame.sprite.Group()
    comets = pygame.sprite.Group()
    fuels = pygame.sprite.Group()
    broken_asteroids = pygame.sprite.Group()
    empty_fuel_started = False
    empty_fuel_timer = 0
    
    def _stop_scene_audio():
        if music_path and pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(400)
        rocket._stop_blast_loop()

    asteroid_timer = ASTEROID_INTERVAL
    comet_timer = COMET_INTERVAL
    fuel_timer = FUEL_INTERVAL
    victory = False
    game_over = False
    fuel_empty = False
    
    mission_delay = 0
    
    mouse = False

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if victory :
                        _stop_scene_audio()
                        return "victory"
                    
                    if game_over:
                        _stop_scene_audio()
                        return "back"
                    
                    if music_path and pygame.mixer.music.get_busy():
                        paused_ms = pygame.mixer.music.get_pos()
                        if paused_ms >= 0:
                            music_pause_pos = paused_ms / 1000.0
                        else:
                            music_pause_pos = 0.0

                    choice = run_pause(screen, clock)
                    if choice == "resume":
                        _play_scene_music(start_pos=music_pause_pos)
                    elif choice == "restart":
                        _stop_scene_audio()
                        return "restart"
                    else:
                        _stop_scene_audio()
                        return "back"
                    
                if game_over and event.key == pygame.K_r:
                    _stop_scene_audio()
                    return "restart"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = True
                if victory:
                    _stop_scene_audio()
                    return "victory"
                if game_over:
                    _stop_scene_audio()
                    return "restart"
            if event.type == pygame.MOUSEBUTTONUP:
                mouse = False

        keys = pygame.key.get_pressed()
        rocket.handle_input(keys, mouse)

        if not game_over and not victory:
            rocket.update()

            asteroid_timer -= 1
            comet_timer -= 1
            fuel_timer -= 1

            progress = min(1.0, rocket.distance / DISTANCE_GOAL)
            speed_scale = 1.0 + progress * 0.4
            if rocket._boosting:
                speed_scale += 0.6

            asteroid_interval = max(26, int(ASTEROID_INTERVAL - progress * 14))
            comet_interval = max(130, int(COMET_INTERVAL - progress * 35))

            # Fuel spawns more frequently as speed increases.  The base interval
            # already shrinks with progress; additionally the current speed_scale
            # (which is boosted further while the player is dashing) compresses
            # it extra so fuel opportunities keep pace with how fast hazards arrive.
            fuel_interval = max(
                80,
                int((FUEL_INTERVAL - progress * 80) / max(1.0, speed_scale * 0.85))
                - (30 if rocket._boosting else 0),
            )

            if asteroid_timer <= 0:
                asteroid = Asteroid(speed_scale)
                asteroids.add(asteroid)
                asteroid_timer = random.randint(asteroid_interval, asteroid_interval + 18)

            if comet_timer <= 0:
                comet = Comet()
                comet.vx *= speed_scale
                comet.vy *= speed_scale
                comets.add(comet)
                comet_timer = random.randint(comet_interval, comet_interval + 26)

            if fuel_timer <= 0:
                fuel_can = FuelCanister()
                # Fuel canisters also move faster at higher speed scales so they
                # don't lag behind the rest of the scrolling hazards.
                fuel_can.speed = 5.0 * speed_scale
                fuels.add(fuel_can)
                fuel_timer = random.randint(fuel_interval, fuel_interval + 36)

            for asteroid in asteroids:
                asteroid.speed_multiplier = 1.6 if rocket._boosting else 1.0
            for comet in comets:
                comet.speed_multiplier = 1.6 if rocket._boosting else 1.0
            # Fuel canisters already have their base speed set at spawn; also
            # apply the boost multiplier so they keep up when the player dashes.
            for fuel in fuels:
                fuel.speed = 5.0 * speed_scale * (1.6 if rocket._boosting else 1.0)

            asteroids.update()
            comets.update()
            fuels.update()
            broken_asteroids.update()

            # --- Fuel-empty logic ---
            if rocket.fuel <= 0 and not rocket.exploding:
                if not empty_fuel_started:
                    empty_fuel_started = True
                    rocket.empty_fuel_active = True
                    fuel_empty = True
                    if empty_sound:
                        empty_sound.play()
                        empty_fuel_timer = int(empty_sound.get_length() * FPS)
                    else:
                        empty_fuel_timer = FPS * 2
                elif empty_fuel_timer > 0:
                    empty_fuel_timer -= 1
                else:
                    game_over = True
                    mission_delay = 0

            # --- Fuel collection ---
            fuel_hits = pygame.sprite.spritecollide(rocket, fuels, True)
            if fuel_hits:
                rocket.fuel = min(FUEL_MAX, rocket.fuel + 30)
                rocket.turbo_stage = rocket._get_turbo_stage()
                # If the player was in the empty-fuel countdown, rescue them.
                if empty_fuel_started and rocket.fuel > 0:
                    empty_fuel_started = False
                    empty_fuel_timer = 0
                    rocket.empty_fuel_active = False
                    fuel_empty = False
                if collect_sound:
                    collect_sound.play()

            # --- Collision with hazards ---
            hazards = pygame.sprite.spritecollide(rocket, asteroids, True, pygame.sprite.collide_mask)
            hazards += pygame.sprite.spritecollide(rocket, comets, True, pygame.sprite.collide_mask)
            for hazard in hazards:
                if isinstance(hazard, Asteroid):
                    broken = BrokenAsteroid(hazard.rect.center)
                    broken_asteroids.add(broken)
                if rocket.take_damage():
                    if rocket.health <= 0:
                        fuel_empty = False
                    if rocket.exploding:
                        break

            rocket.distance = min(DISTANCE_GOAL, rocket.distance)

            # Wait for explosion animation before showing game-over screen
            if rocket.exploding:
                if rocket.explosion_done:
                    game_over = True
                    mission_delay = 0
            elif rocket.distance >= DISTANCE_GOAL and not fuel_empty:                
                victory = True
                mission_delay = 90

        # Draw
        screen.blit(bg, (0, 0))
        asteroids.draw(screen)
        comets.draw(screen)
        fuels.draw(screen)
        broken_asteroids.draw(screen)
        rocket.draw(screen)
        
        if not game_over and not victory:
            # 1. COLD BLUE BORDER (Triggers when fuel is lower than 35%)
            if rocket.fuel < 35:
                # Calculate how desperate the situation is (0.0 at 35% fuel -> 1.0 at 0% fuel)
                severity = (35.0 - rocket.fuel) / 35.0
                
                # Create a pulsing heartbeat effect using time ticks
                pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2 # Ranges safely between 0.0 and 1.0
                
                # Base intensity climbs up to 160 alpha, fluctuating with the pulse
                blue_alpha = int((100 * severity) + (60 * severity * pulse))
                
                _draw_screen_border_warning(screen, BLUE, blue_alpha, thickness=100)

            # 2. DAMAGE RED BORDER (Overtakes the screen on impact)
            if rocket.damage_alpha > 0:
                _draw_screen_border_warning(screen, RED, int(rocket.damage_alpha), thickness=75)
        
        _render_ui(screen, rocket, rocket.distance, game_over, victory, fuel_empty)

        if victory:
            rocket._stop_blast_loop()
            pygame.mixer.music.set_volume(0.2)
            mission_delay -= 1
            if mission_delay <= 0:
                if music_length > 0:
                    elapsed = (pygame.time.get_ticks() - music_start_time) / 1000.0
                    if elapsed < music_length:
                        mission_delay = 1
                        pygame.display.flip()
                        clock.tick(FPS)
                        continue
                _stop_scene_audio()

        if game_over:
            mission_delay += 1

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    scene4(screen, clock)
