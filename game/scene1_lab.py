"""Scene 1 — Lab Cutscene.

I based the dialogue system on the timed dialogue box we made in a lab exercise —
a currLine index that advances when the player presses SPACE, with each line
rendered using font.render and screen.blit. The rest is just loading sprites
and playing background music.
"""

import os
import pygame
from settings import ASSETS_DIR, WIDTH, HEIGHT, DARK, WHITE, FPS


DIALOGUE = [
    ("DR. NEFARIO", "Sir! Vector has all five shrink ray components locked in his fortress."),
    ("DR. NEFARIO", "Without those parts, stealing the moon is completely impossible."),
    ("GRU",         "No one steals from the greatest villain in the world."),
    ("GRU",         "Not even Vector. Prepare the Plasma Blaster — we leave tonight."),
]

# each speaker gets their own colour so the player can tell at a glance who's talking
SPEAKER_COLOURS = {
    "DR. NEFARIO": (160, 220, 255),
    "GRU":         (255, 210, 100),
}


def scene1(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """Run the Scene 1 lab cutscene. Returns the next scene state when the player finishes."""
    pygame.display.set_caption("Scene 1 — Gru's Lab")

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
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    curr_line += 1
                    if curr_line >= len(DIALOGUE):
                        finished = True

        if finished:
            break

        screen.blit(lab_bg, (0, 0))

        # gru on the left (his sprite faces right), nefario on the right —
        # they end up looking at each other without needing any sprite flipping.
        gru_x = WIDTH // 5 - gru_frame.get_width() // 2
        gru_y = HEIGHT - gru_frame.get_height() - 80
        screen.blit(gru_frame, (gru_x, gru_y))

        nef_x = WIDTH * 3 // 4 - nefario_surf.get_width() // 2
        nef_y = HEIGHT - nefario_surf.get_height() - 80
        screen.blit(nefario_surf, (nef_x, nef_y))

        _draw_dialogue(screen, curr_line, font_speaker, font_text, font_hint)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()
    return "scene2"


def _draw_dialogue(screen, curr_line, font_speaker, font_text, font_hint):
    if curr_line >= len(DIALOGUE):
        return

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


def _render_wrapped(surface, text, font, colour, x, y, max_width):
    """Break a string into multiple lines so it fits within max_width.

    I build each line word by word — if adding the next word would overflow
    the box, I blit the current line and start a new one. This avoids the
    text running off the edge of the dialogue box for longer lines.
    """
    words  = text.split()
    line   = ""
    line_y = y
    for word in words:
        test = line + word + " "
        if font.size(test)[0] > max_width and line:
            rendered = font.render(line.rstrip(), True, colour)
            surface.blit(rendered, (x, line_y))
            line_y += font.get_linesize() + 2
            line = word + " "
        else:
            line = test
    if line:
        rendered = font.render(line.rstrip(), True, colour)
        surface.blit(rendered, (x, line_y))


def _load_background() -> pygame.Surface:
    """Load the lab background image, or draw a placeholder if the file isn't there yet."""
    for name in ("bg.png", "bg.jpg", "bg.jpeg"):
        bg_path = os.path.join(ASSETS_DIR, "backgrounds", "lab", name)
        if os.path.exists(bg_path):
            bg = pygame.image.load(bg_path).convert()
            return pygame.transform.scale(bg, (WIDTH, HEIGHT))

    # fallback: hand-drawn lab silhouette using pygame primitives. keeps the
    # scene readable as a dark lab even before real background art is dropped in.
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill((15, 15, 30))
    pygame.draw.rect(surf, (40, 40, 55), (0, HEIGHT - 90, WIDTH, 90))
    for mx in (80, 300, 520, WIDTH - 300, WIDTH - 120):
        pygame.draw.rect(surf, (20, 60, 100), (mx, HEIGHT - 370, 160, 240))
        pygame.draw.rect(surf, (30, 140, 200), (mx + 8, HEIGHT - 362, 144, 200))
        for sy in range(HEIGHT - 362, HEIGHT - 162, 12):
            pygame.draw.line(surf, (10, 80, 130), (mx + 8, sy), (mx + 152, sy))
    for px in range(0, WIDTH, 120):
        pygame.draw.rect(surf, (60, 60, 75), (px, 0, 30, HEIGHT // 3))
    return surf


def _load_gru_idle() -> pygame.Surface:
    """Load the first idle frame and scale it to a reasonable height for the cutscene."""
    path = os.path.join(ASSETS_DIR, "sprites", "gru", "iceray", "idle", "idle0.png")
    img = pygame.image.load(path).convert_alpha()
    scale = 280 / img.get_height()
    return pygame.transform.scale_by(img, scale)


def _load_nefario() -> pygame.Surface:
    """Load Dr. Nefario's sprite if the file exists, otherwise draw a simple stand-in."""
    path = os.path.join(ASSETS_DIR, "sprites", "nefario", "idle.png")
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        scale = 280 / img.get_height()
        return pygame.transform.scale_by(img, scale)

    # rough lab-coat-and-goggles silhouette as a stand-in until the real
    # nefario sprite is finished. just enough shapes to read as "scientist".
    surf = pygame.Surface((80, 200), pygame.SRCALPHA)
    pygame.draw.rect(surf, (180, 180, 190), (15, 60, 50, 100))   # body / coat
    pygame.draw.ellipse(surf, (230, 200, 170), (20, 10, 40, 50)) # head
    pygame.draw.ellipse(surf, (80, 160, 220), (22, 25, 16, 14))  # left goggle
    pygame.draw.ellipse(surf, (80, 160, 220), (42, 25, 16, 14))  # right goggle
    font = pygame.font.Font(None, 18)
    surf.blit(font.render("Nefario", True, (255, 255, 255)), (0, 180))
    return surf
