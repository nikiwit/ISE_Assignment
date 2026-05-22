import pygame
import pygame
import os
from settings import WIDTH, HEIGHT, FPS, DARK, GREEN, ASSETS_DIR
from gru import Gru
from progress import load_progress, mark_complete
from pause import run_pause

class Floor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((WIDTH, 50)) 
        self.rect = self.image.get_rect(topleft=(0, HEIGHT - 50))
        self.top = self.rect.top 

def _load_image(subfolder, filename):
    path = os.path.join(ASSETS_DIR, "sprites", subfolder, filename)
    if not os.path.exists(path):
        path = os.path.join(ASSETS_DIR, "backgrounds", subfolder, filename)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    print(f"DEBUG: Could not find {path}")
    return None

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

def scene6(screen, clock):
    # --- ASSET LOADING ---
    def play_music():
        music_path = os.path.join(ASSETS_DIR, "music", "misc_warped.mp3")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)

    laser_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sfx", "moonraylaser.ogg"))
    start_sound_path = os.path.join(ASSETS_DIR, "sfx", "level_start.wav")
    start_sound = pygame.mixer.Sound(start_sound_path) if os.path.exists(start_sound_path) else None
    charge_sound_path = os.path.join(ASSETS_DIR, "sfx", "scificharge.mp3")
    charge_sound = pygame.mixer.Sound(charge_sound_path) if os.path.exists(charge_sound_path) else None
    fluffy_sound_path = os.path.join(ASSETS_DIR, "music", "victory_jingle.wav")
    fluffy_sound = pygame.mixer.Sound(fluffy_sound_path) if os.path.exists(fluffy_sound_path) else None
    charge_channel = pygame.mixer.Channel(2)

    def initialize_scene():
        gru = Gru(x=WIDTH//2 - 50, y=HEIGHT - 200)
        if hasattr(gru, 'state'): gru.state = "idle"
        play_music()
        if start_sound:
            start_sound.play()
        return gru, "charging", 0, 0, 8.9, False, False, 0.0

    gru, stage, charge, curr_line, moon_scale, laser_played, fluffy_played, laser_progress = initialize_scene()
    floor = Floor()
    platforms = [floor]
    
    raw_bg = _load_image("moon_space", "layer_far_stars.png")
    bg_image = pygame.transform.scale(raw_bg, (WIDTH, HEIGHT)) if raw_bg else None
    moon_image = _load_image("moon_space", "moon_sprite.png")
    
    portraits = {
        ("GRU", 0): _load_image("gru/unequipped/knock", "knock1.png"),
        ("GRU", 1): _load_image("gru/unequipped/knock", "knock4.png"),
        ("GRU", 2): _load_image("gru/moonhold", "ismine.png"),
        ("AGNES", 3): _load_image("agnes/stand", "stand.png"),
        ("AGNES", 4): _load_image("agnes/huggywuggy", "huggy.png")
    }

    PORTRAIT_CONFIG = {
        "GRU":   (1.8, 120, -10),
        "AGNES": (0.6, -80, 32)
    }
    
    DIALOGUE = [
        ("GRU", "At last, after all my hard work!"),
        ("GRU", "The Moon...."),
        ("GRU", "IS MINE!"),
        ("AGNES", "HOORAY!"),
        ("AGNES", "IT'S SO FLUFFY!"),
        ("CONGRATS!", "MISSION ACCOMPLISHED")
    ]
    
    SPEAKER_COLOURS = {"GRU": (255, 210, 100), "AGNES": (255, 100, 100), "SYSTEM": (255, 255, 255)}
    max_charge = 180
    playable_scenes = ("scene1", "scene2", "scene6")
    
    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        events = pygame.event.get()
        gru.update(keys, events, platforms)
        
        for event in events:
            if event.type == pygame.QUIT:
                charge_channel.stop()
                return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    charge_channel.stop()
                    action = run_pause(screen, clock)
                    if action == "menu": return "menu"
                    if action == "restart": 
                        gru, stage, charge, curr_line, moon_scale, laser_played, fluffy_played, laser_progress = initialize_scene()
                        continue
                    if action == "resume": play_music()
                
                if stage == "dialogue" and event.key == pygame.K_SPACE:
                    curr_line += 1
                    if curr_line >= len(DIALOGUE):
                        charge_channel.stop()
                        mark_complete("scene6")
                        stage = "stats"
                        continue

                if stage == "stats" and event.key == pygame.K_SPACE:
                    charge_channel.stop()
                    mark_complete("scene6")
                    return "menu"

        if stage == "charging":
            if keys[pygame.K_SPACE]:
                charge += 1
                if charge_sound and not charge_channel.get_busy():
                    charge_channel.play(charge_sound, loops=-1)
            else:
                charge_channel.stop()

            if charge >= max_charge: 
                stage = "firing"
                laser_progress = 0.0
                charge_channel.stop()
                if hasattr(gru, 'state'): gru.state = "shooting"
                if not laser_played:
                    laser_sound.play()
                    laser_played = True

        elif stage == "firing":
            laser_progress = min(1.0, laser_progress + 0.16)
            moon_scale = max(0.0, moon_scale - 0.022)
            if moon_scale <= 0.0: 
                stage = "dialogue"
                if hasattr(gru, 'state'): gru.state = "idle"

        screen.fill(DARK)
        if bg_image: screen.blit(bg_image, (0, 0))
        
        if moon_image and moon_scale > 0:
            w, h = moon_image.get_size()
            scaled_moon = pygame.transform.scale(moon_image, (int(w * moon_scale), int(h * moon_scale)))
            screen.blit(scaled_moon, scaled_moon.get_rect(center=(WIDTH//2, HEIGHT//3)))
        
        if stage == "firing":
            is_facing_right = getattr(gru, 'facing_right', True)
            offset_x = 50 if is_facing_right else -50
            laser_start = (gru.rect.centerx + offset_x, gru.rect.centery - 10)
            laser_target = (WIDTH // 2, HEIGHT // 3)
            laser_end = (
                int(laser_start[0] + (laser_target[0] - laser_start[0]) * laser_progress),
                int(laser_start[1] + (laser_target[1] - laser_start[1]) * laser_progress),
            )
            pygame.draw.line(screen, (180, 255, 180), laser_start, laser_end, 9)
            pygame.draw.line(screen, GREEN, laser_start, laser_end, 5)

        if stage not in ("dialogue", "stats"):
            screen.blit(gru.image, gru.rect)
        
        if stage == "charging":
            pygame.draw.rect(screen, GREEN, (WIDTH//2 - 200, 650, (charge/max_charge)*400, 20))
            font_prompt = pygame.font.Font(None, 42)
            prompt = font_prompt.render("PRESS SPACE TO ACQUIRE THE MOON!", True, (70, 55, 160))
            screen.blit(prompt, prompt.get_rect(center=(WIDTH//2, 570)))
            
        elif stage == "dialogue":
            pygame.draw.rect(screen, (50, 50, 50), (100, 500, WIDTH-200, 150))
            speaker, text = DIALOGUE[curr_line]
            if curr_line == 5 and fluffy_sound and not fluffy_played:
                fluffy_sound.play()
                fluffy_played = True
            portrait = portraits.get((speaker, curr_line))
            
            if portrait:
                config = PORTRAIT_CONFIG.get(speaker, (1.0, 0, 0))
                scale, x_base, y_off = config
                w, h = portrait.get_size()
                scaled_w, scaled_h = int(w * scale), int(h * scale)
                scaled_portrait = pygame.transform.scale(portrait, (scaled_w, scaled_h))
                x_pos = x_base if speaker == "GRU" else WIDTH - scaled_w + x_base 
                y_pos = 500 - scaled_h + y_off
                screen.blit(scaled_portrait, (x_pos, y_pos))
            
            font_s = pygame.font.Font(None, 40)
            font_t = pygame.font.Font(None, 32)
            screen.blit(font_s.render(speaker, True, SPEAKER_COLOURS.get(speaker, (255,255,255))), (120, 520))
            _render_wrapped(screen, text, font_t, (255, 255, 255), 120, 560, WIDTH-240)

        elif stage == "stats":
            completed = load_progress()
            completed_count = sum(1 for scene_id in playable_scenes if scene_id in completed)

            font_title = pygame.font.Font(None, 64)
            font_stat = pygame.font.Font(None, 40)
            font_hint = pygame.font.Font(None, 28)

            title = font_title.render("MISSION ACCOMPLISHED", True, (255, 220, 80))
            screen.blit(title, title.get_rect(center=(WIDTH//2, 210)))

            stats = [
                "Moon Acquired: YES",
                f"Scenes Completed: {completed_count} / {len(playable_scenes)}",
            ]
            for i, line in enumerate(stats):
                stat_text = font_stat.render(line, True, (230, 235, 255))
                screen.blit(stat_text, stat_text.get_rect(center=(WIDTH//2, 300 + i * 52)))

            hint = font_hint.render("SPACE to return to menu", True, (170, 180, 210))
            screen.blit(hint, hint.get_rect(center=(WIDTH//2, 500)))

        pygame.display.flip()
